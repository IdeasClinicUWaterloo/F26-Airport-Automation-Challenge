"""
Extended Kalman Filter for aircraft state estimation.

State vector x = [east_m, north_m, alt_ft, speed_mps, heading_rad, vspeed_ftps]
tracked in a local East-North-Up frame centered on the first reported position
(a flat-earth approximation is accurate enough over a single flight leg).

The motion model is nonlinear (position depends on speed*sin/cos(heading)),
which is what makes this an *Extended* KF: predict() linearizes that model
with its Jacobian to propagate the covariance.
"""

import math

import numpy as np

EARTH_RADIUS_M = 6371e3
KNOTS_TO_MPS = 0.514444

STATE_DIM = 6
MEAS_DIM = 5  # east, north, alt, speed, heading (vspeed is never directly measured)

# 95% confidence threshold for a 5-dof normalized innovation squared (chi-square).
NIS_THRESHOLD = 11.07
# Beyond this multiple of the threshold, a message is treated as a hard
# validation-gate failure (excluded from the update) rather than softly
# down-weighted -- otherwise a sufficiently large error can drag the estimate
# toward it no matter how much R is inflated, if P is already large too.
HARD_GATE_MULTIPLE = 5.0


class AircraftEKF:
    def __init__(self):
        self.x = np.zeros(STATE_DIM)
        # Large initial uncertainty until the first measurement anchors the filter.
        self.P = np.diag([1e6, 1e6, 1e6, 1e4, 10.0, 1e4])
        self.last_timestamp = None
        self.initialized = False

        self._lat0 = None
        self._lon0 = None

        # Process noise (per second of elapsed time), tuned loosely for a
        # cruising airliner: position/altitude drift is small, but speed,
        # heading, and vertical speed are allowed to change (maneuvering).
        self.Q_diag = np.array([4.0, 4.0, 9.0, 1.0, math.radians(1.5) ** 2, 4.0])
        # Measurement noise, modeling ADS-B-ish accuracy.
        self.R_diag = np.array([2500.0, 2500.0, 900.0, 1.0, math.radians(2.0) ** 2])

    # ---- lat/lon <-> local ENU (meters) ----

    def _to_local(self, lat, lon):
        if self._lat0 is None:
            self._lat0, self._lon0 = lat, lon
        lat0_rad = math.radians(self._lat0)
        east = math.radians(lon - self._lon0) * EARTH_RADIUS_M * math.cos(lat0_rad)
        north = math.radians(lat - self._lat0) * EARTH_RADIUS_M
        return east, north

    def _to_latlon(self, east, north):
        lat0_rad = math.radians(self._lat0)
        lat = self._lat0 + math.degrees(north / EARTH_RADIUS_M)
        lon = self._lon0 + math.degrees(east / (EARTH_RADIUS_M * math.cos(lat0_rad)))
        return lat, lon

    # ---- filter steps ----

    def initialize(self, lat, lon, altitude, ground_speed_kt, heading_deg, timestamp):
        east, north = self._to_local(lat, lon)
        self.x = np.array([
            east,
            north,
            float(altitude),
            ground_speed_kt * KNOTS_TO_MPS,
            math.radians(heading_deg),
            0.0,
        ])
        self.P = np.diag([2500.0, 2500.0, 900.0, 25.0, math.radians(10.0) ** 2, 100.0])
        self.last_timestamp = timestamp
        self.initialized = True

    def predict(self, timestamp):
        """Advance the state estimate to `timestamp`, growing uncertainty. No-op if
        already caught up. Returns the elapsed dt in seconds."""

        if not self.initialized or self.last_timestamp is None:
            return 0.0

        dt = (timestamp - self.last_timestamp).total_seconds()
        if dt <= 0:
            return dt

        east, north, alt, spd, hdg, vspd = self.x
        sin_h, cos_h = math.sin(hdg), math.cos(hdg)

        self.x = np.array([
            east + spd * sin_h * dt,
            north + spd * cos_h * dt,
            alt + vspd * dt,
            spd,
            hdg,
            vspd,
        ])

        F = np.eye(STATE_DIM)
        F[0, 3] = sin_h * dt
        F[0, 4] = spd * cos_h * dt
        F[1, 3] = cos_h * dt
        F[1, 4] = -spd * sin_h * dt
        F[2, 5] = dt

        Q = np.diag(self.Q_diag * dt)
        self.P = F @ self.P @ F.T + Q
        self.last_timestamp = timestamp
        return dt

    def innovation(self, lat, lon, altitude, ground_speed_kt, heading_deg):
        """Compare a candidate measurement against the current prediction without
        applying it. Returns (innovation vector y, innovation covariance S, NIS)."""

        east, north = self._to_local(lat, lon)
        z = np.array([east, north, float(altitude), ground_speed_kt * KNOTS_TO_MPS, math.radians(heading_deg)])

        H = np.zeros((MEAS_DIM, STATE_DIM))
        for i in range(MEAS_DIM):
            H[i, i] = 1.0

        y = z - H @ self.x
        # Wrap the heading residual into [-pi, pi] so a 359 -> 1 degree turn
        # doesn't look like a 358 degree jump.
        y[4] = math.atan2(math.sin(y[4]), math.cos(y[4]))

        R = np.diag(self.R_diag)
        S = H @ self.P @ H.T + R
        nis = float(y.T @ np.linalg.solve(S, y))
        return y, S, nis, H

    def update(self, lat, lon, altitude, ground_speed_kt, heading_deg):
        """Apply a measurement against an already-initialized filter. Returns
        (nis, is_anomalous) so the caller can decide whether to flag the message.
        Call initialize() first for the very first measurement."""

        y, S, nis, H = self.innovation(lat, lon, altitude, ground_speed_kt, heading_deg)
        is_anomalous = nis > NIS_THRESHOLD

        if not is_anomalous:
            R = np.diag(self.R_diag)
        elif nis <= NIS_THRESHOLD * HARD_GATE_MULTIPLE:
            # Mild conflict: still incorporate it, but down-weight in proportion
            # to how far it exceeds the gate (a message barely over threshold is
            # nudged down slightly, not thrown out).
            R = np.diag(self.R_diag) * (nis / NIS_THRESHOLD)
        else:
            # Wild outlier (e.g. a corrupted position jump): outside any
            # reasonable validation gate, so it's excluded from the update
            # entirely -- the filter keeps its prediction and waits for
            # corroborating messages, rather than letting one bad message drag
            # the estimate toward it.
            return nis, is_anomalous

        S = H @ self.P @ H.T + R
        K = self.P @ H.T @ np.linalg.inv(S)

        self.x = self.x + K @ y
        self.P = (np.eye(STATE_DIM) - K @ H) @ self.P
        return nis, is_anomalous

    # ---- output ----

    def position(self):
        if not self.initialized:
            return None
        lat, lon = self._to_latlon(self.x[0], self.x[1])
        return {"lat": lat, "lon": lon}

    def state_dict(self):
        if not self.initialized:
            return None
        lat, lon = self._to_latlon(self.x[0], self.x[1])
        return {
            "lat": lat,
            "lon": lon,
            "altitude": self.x[2],
            "ground_speed": self.x[3] / KNOTS_TO_MPS,
            "heading": math.degrees(self.x[4]) % 360,
            "vertical_speed_fpm": self.x[5] * 60,
        }

    def uncertainty_ellipse(self, n_std=2.0):
        """2D confidence ellipse for position (east/north submatrix of P), as
        (semi_major_m, semi_minor_m, rotation_deg_from_north)."""

        if not self.initialized:
            return None

        cov_xy = self.P[:2, :2]
        eigvals, eigvecs = np.linalg.eigh(cov_xy)
        eigvals = np.clip(eigvals, 0, None)
        order = np.argsort(eigvals)[::-1]
        eigvals, eigvecs = eigvals[order], eigvecs[:, order]

        semi_major = n_std * math.sqrt(eigvals[0])
        semi_minor = n_std * math.sqrt(eigvals[1])
        major_vec = eigvecs[:, 0]
        # Rotation of the major axis, measured clockwise from true north.
        rotation_deg = math.degrees(math.atan2(major_vec[0], major_vec[1]))
        return semi_major, semi_minor, rotation_deg
