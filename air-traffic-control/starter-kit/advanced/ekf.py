"""Extended Kalman Filter with the same interface as `AircraftTracker`.

The state vector contains east, north, altitude, speed, heading, and vertical
speed. A 6x6 covariance matrix tracks uncertainty and relationships between
those values. See `advanced/README.md` before changing its noise settings.
"""

import math

import numpy as np

EARTH_RADIUS_M = 6371e3
KNOTS_TO_MPS = 0.514444

STATE_DIM = 6
MEAS_DIM = 5  # east, north, altitude, speed, and heading


# Chi-square 95th percentile for five measured values. Higher flags fewer reports.
NIS_THRESHOLD = 11.07

# Reports beyond this multiple of the threshold are rejected.
HARD_GATE_MULTIPLE = 5.0

# Process-noise variances added per second for the six state values.
PROCESS_NOISE = np.array([4.0, 4.0, 9.0, 1.0, math.radians(1.5) ** 2, 4.0])

# Measurement-error variances for position, altitude, speed, and heading.
MEASUREMENT_NOISE = np.array([2500.0, 2500.0, 900.0, 1.0, math.radians(2.0) ** 2])


class AircraftEKF:
    def __init__(self):
        self.x = np.zeros(STATE_DIM)
        # The first report replaces this intentionally broad prior uncertainty.
        self.P = np.diag([1e6, 1e6, 1e6, 1e4, 10.0, 1e4])

        self.last_timestamp = None
        self.started = False

        self.last_gap_km = None
        self.last_nis = None

        # These only change after an accepted report, not after prediction.
        self.last_accepted_position = None
        self.last_accepted_timestamp = None

        self._lat0 = None
        self._lon0 = None

    # ---- lat/lon <-> local east/north in metres ----

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

    # ---- the interface the core message_parser expects ----

    @property
    def position(self):
        if not self.started:
            return None
        lat, lon = self._to_latlon(self.x[0], self.x[1])
        return {"lat": lat, "lon": lon}

    @property
    def altitude(self):
        return self.x[2] if self.started else None

    @property
    def ground_speed(self):
        return self.x[3] / KNOTS_TO_MPS if self.started else None

    @property
    def heading(self):
        return math.degrees(self.x[4]) % 360 if self.started else None

    @property
    def uncertainty_km(self):
        """Return the ellipse's major radius in kilometres for API compatibility."""

        ellipse = self.uncertainty_ellipse()
        return ellipse[0] / 1000 if ellipse else None

    def start(self, lat, lon, altitude, ground_speed, heading, timestamp):
        east, north = self._to_local(lat, lon)
        self.x = np.array([
            east,
            north,
            float(altitude),
            ground_speed * KNOTS_TO_MPS,
            math.radians(heading),
            0.0,
        ])
        self.P = np.diag([2500.0, 2500.0, 900.0, 25.0, math.radians(10.0) ** 2, 100.0])
        self.last_timestamp = timestamp
        self.started = True

        self.last_accepted_position = {"lat": lat, "lon": lon}
        self.last_accepted_timestamp = timestamp

    def predict(self, timestamp):
        """Predict forward to `timestamp` and grow the covariance."""

        if not self.started or self.last_timestamp is None or timestamp is None:
            return

        dt = (timestamp - self.last_timestamp).total_seconds()
        if dt <= 0:
            return

        east, north, alt, speed, heading, vertical_speed = self.x
        sin_h, cos_h = math.sin(heading), math.cos(heading)

        self.x = np.array([
            east + speed * sin_h * dt,
            north + speed * cos_h * dt,
            alt + vertical_speed * dt,
            speed,
            heading,
            vertical_speed,
        ])

        # Linearize the motion model so the covariance can be propagated.
        F = np.eye(STATE_DIM)
        F[0, 3] = sin_h * dt
        F[0, 4] = speed * cos_h * dt
        F[1, 3] = cos_h * dt
        F[1, 4] = -speed * sin_h * dt
        F[2, 5] = dt

        self.P = F @ self.P @ F.T + np.diag(PROCESS_NOISE * dt)
        self.last_timestamp = timestamp

    def update(self, lat, lon, altitude, ground_speed, heading):
        """Apply a report and return `(gap_km, was_flagged)` like the simple tracker."""

        east, north = self._to_local(lat, lon)
        z = np.array([
            east, north, float(altitude),
            ground_speed * KNOTS_TO_MPS, math.radians(heading),
        ])

        H = np.zeros((MEAS_DIM, STATE_DIM))
        for i in range(MEAS_DIM):
            H[i, i] = 1.0

        # Innovation: reported values minus predicted values.
        y = z - H @ self.x
        # Wrap heading error so 359 to 1 degrees is treated as a 2-degree change.
        y[4] = math.atan2(math.sin(y[4]), math.cos(y[4]))

        R = np.diag(MEASUREMENT_NOISE)
        S = H @ self.P @ H.T + R
        nis = float(y.T @ np.linalg.solve(S, y))

        gap_km = math.hypot(y[0], y[1]) / 1000
        was_flagged = nis > NIS_THRESHOLD

        self.last_nis = nis
        self.last_gap_km = gap_km

        if was_flagged and nis > NIS_THRESHOLD * HARD_GATE_MULTIPLE:
            # A hard-gated report does not change the estimate.
            return gap_km, was_flagged

        if was_flagged:
            # Down-weight a mild conflict by increasing its measurement noise.
            R = R * (nis / NIS_THRESHOLD)

        S = H @ self.P @ H.T + R
        K = self.P @ H.T @ np.linalg.inv(S)

        self.x = self.x + K @ y
        self.P = (np.eye(STATE_DIM) - K @ H) @ self.P

        self.last_accepted_position = {"lat": lat, "lon": lon}
        self.last_accepted_timestamp = self.last_timestamp

        return gap_km, was_flagged

    def state(self):
        """Return the current estimate and EKF-specific diagnostics."""

        if not self.started:
            return None

        return {
            "position": self.position,
            "altitude": self.altitude,
            "ground_speed": self.ground_speed,
            "heading": self.heading,
            "uncertainty_km": self.uncertainty_km,
            "vertical_speed_fpm": self.x[5] * 60,
            "last_nis": self.last_nis,
            "nis_threshold": NIS_THRESHOLD,
        }

    # ---- the part a single radius can't express ----

    def uncertainty_ellipse(self, n_std=2.0):
        """Return position uncertainty as major radius, minor radius, and rotation."""

        if not self.started:
            return None

        cov_xy = self.P[:2, :2]
        eigenvalues, eigenvectors = np.linalg.eigh(cov_xy)
        eigenvalues = np.clip(eigenvalues, 0, None)

        order = np.argsort(eigenvalues)[::-1]
        eigenvalues, eigenvectors = eigenvalues[order], eigenvectors[:, order]

        semi_major = n_std * math.sqrt(eigenvalues[0])
        semi_minor = n_std * math.sqrt(eigenvalues[1])
        major_axis = eigenvectors[:, 0]
        rotation_deg = math.degrees(math.atan2(major_axis[0], major_axis[1]))

        return semi_major, semi_minor, rotation_deg
