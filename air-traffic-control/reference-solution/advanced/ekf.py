"""
Extended Kalman Filter -- a drop-in replacement for the core tracker.py.

Same job, same interface, much more machinery. Where tracker.py holds confidence
as one radius in kilometres, this holds a 6x6 covariance matrix over

    [east_m, north_m, altitude_ft, speed_mps, heading_rad, vertical_speed_ftps]

tracked in a flat local frame centred on the first reported position. Carrying a
whole matrix instead of one number buys you the cross-terms: it can represent
"we're unsure about heading, therefore we'll soon be unsure about position in
this particular direction", which a single radius cannot say.

The motion model is nonlinear -- position depends on speed * sin/cos(heading) --
which is the "Extended" part: predict() linearizes it with its Jacobian in order
to propagate the covariance through it.

TO SWAP IT IN, change one line in message_parser.py:

    from tracker import AircraftTracker              # before
    from ekf import AircraftEKF as AircraftTracker   # after

Nothing else in the core needs to change. Read advanced/README.md first -- this
file needs numpy, and it is considerably harder to debug than what it replaces.
"""

import math

import numpy as np

EARTH_RADIUS_M = 6371e3
KNOTS_TO_MPS = 0.514444

STATE_DIM = 6
MEAS_DIM = 5  # east, north, alt, speed, heading (vertical speed is never measured directly)


# ---------------------------------------------------------------------------
# Tuning knobs, in the same spirit as tracker.py's -- but note these are
# variances, not distances, so they are far less intuitive to adjust. That is
# the main practical cost of the upgrade.
# ---------------------------------------------------------------------------

# Chi-square 95th percentile for 5 degrees of freedom: the point past which a
# measurement is more surprising than our own uncertainty can account for.
# The matrix-based equivalent of the core's ANOMALY_SIGMA.
# RAISE IT to flag fewer messages.
NIS_THRESHOLD = 11.07

# Past this multiple of the threshold, a message is discarded outright rather
# than merely down-weighted -- the equivalent of the core's ANOMALY_TRUST, but
# graded: mild surprises are softened, wild ones are dropped.
# RAISE IT to keep believing increasingly implausible messages.
HARD_GATE_MULTIPLE = 5.0

# Process noise per second: how much we let each quantity wander on its own
# between messages. Position and altitude drift slowly; speed, heading and
# vertical speed are free to change, because the aircraft manoeuvres.
# The equivalent of DRIFT_PER_MINUTE_KM, spread over six terms.
PROCESS_NOISE = np.array([4.0, 4.0, 9.0, 1.0, math.radians(1.5) ** 2, 4.0])

# Measurement noise: how wrong we expect each reported field to be, squared.
# Roughly ADS-B accuracy. The equivalent of MEASUREMENT_ERROR_KM.
MEASUREMENT_NOISE = np.array([2500.0, 2500.0, 900.0, 1.0, math.radians(2.0) ** 2])


class AircraftEKF:
    def __init__(self):
        self.x = np.zeros(STATE_DIM)
        # Enormous initial uncertainty, until the first measurement anchors us.
        self.P = np.diag([1e6, 1e6, 1e6, 1e4, 10.0, 1e4])

        self.last_timestamp = None
        self.started = False

        self.last_gap_km = None
        self.last_nis = None

        # Interface parity with tracker.py -- see its comments for why these are
        # tracked separately from `position` and `last_timestamp`.
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
        """The covariance boiled back down to one number, so the rest of the core
        (and the map) can treat this exactly like tracker.py. The full ellipse is
        still available via uncertainty_ellipse()."""

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
        """Advance the estimate to `timestamp`, growing the covariance. No-op if
        we're already caught up."""

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

        # Jacobian of the motion model above: how each new state term responds to
        # each old one. This is what lets the covariance follow a nonlinear model.
        F = np.eye(STATE_DIM)
        F[0, 3] = sin_h * dt
        F[0, 4] = speed * cos_h * dt
        F[1, 3] = cos_h * dt
        F[1, 4] = -speed * sin_h * dt
        F[2, 5] = dt

        self.P = F @ self.P @ F.T + np.diag(PROCESS_NOISE * dt)
        self.last_timestamp = timestamp

    def update(self, lat, lon, altitude, ground_speed, heading):
        """
        Fold a reported state in. Returns (gap_km, was_flagged), matching
        tracker.update() so the core parser can't tell the difference.

        Where tracker.py compares one distance against one radius, this compares
        the whole innovation vector against the whole covariance -- which is what
        lets it notice "the position is fine, but the heading needed to get there
        isn't".
        """

        east, north = self._to_local(lat, lon)
        z = np.array([
            east, north, float(altitude),
            ground_speed * KNOTS_TO_MPS, math.radians(heading),
        ])

        H = np.zeros((MEAS_DIM, STATE_DIM))
        for i in range(MEAS_DIM):
            H[i, i] = 1.0

        # The innovation: what the message said, minus what we predicted it'd say.
        y = z - H @ self.x
        # Wrap the heading residual into [-pi, pi], so a 359 -> 1 degree turn reads
        # as 2 degrees rather than 358. Same reason tracker.py has blend_headings().
        y[4] = math.atan2(math.sin(y[4]), math.cos(y[4]))

        R = np.diag(MEASUREMENT_NOISE)
        S = H @ self.P @ H.T + R
        nis = float(y.T @ np.linalg.solve(S, y))

        gap_km = math.hypot(y[0], y[1]) / 1000
        was_flagged = nis > NIS_THRESHOLD

        self.last_nis = nis
        self.last_gap_km = gap_km

        if was_flagged and nis > NIS_THRESHOLD * HARD_GATE_MULTIPLE:
            # Beyond any reasonable gate. Keep the prediction and wait for
            # corroboration rather than letting one bad message drag us to it.
            # Inflating R wouldn't be enough here: if P is already large, a big
            # enough error still moves the estimate.
            return gap_km, was_flagged

        if was_flagged:
            # Mild conflict: still use it, but treat it as noisier than usual, in
            # proportion to how far past the gate it landed.
            R = R * (nis / NIS_THRESHOLD)

        S = H @ self.P @ H.T + R
        K = self.P @ H.T @ np.linalg.inv(S)

        self.x = self.x + K @ y
        self.P = (np.eye(STATE_DIM) - K @ H) @ self.P

        self.last_accepted_position = {"lat": lat, "lon": lon}
        self.last_accepted_timestamp = self.last_timestamp

        return gap_km, was_flagged

    def state(self):
        """Same shape as tracker.state(), plus the two things only this version
        knows: vertical speed, and how surprising the last message was."""

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
        """
        Position uncertainty as (semi_major_m, semi_minor_m, rotation_deg_from_north).

        The east/north block of the covariance describes an ellipse, and its
        eigenvectors are that ellipse's axes. Being more uncertain along track
        than across it is normal and useful -- and it's exactly the information
        the core tracker's single radius throws away.
        """

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
