"""Estimate aircraft state between noisy position reports.

The tracker predicts movement between reports and blends each new report into
the estimate. One uncertainty radius controls how strongly reports are weighted.
"""

from dead_reckoning import DeadReckoning, destination_point, KNOTS_TO_MPS


# Expected position-report error. Higher values trust reports less.
MEASUREMENT_ERROR_KM = 3.0

# Uncertainty added for each minute without a report.
DRIFT_PER_MINUTE_KM = 1.0

# Uncertainty assigned to the first report.
INITIAL_UNCERTAINTY_KM = 5.0

# Higher values allow a larger prediction error before a report is flagged.
ANOMALY_SIGMA = 3.0

# Fraction of the normal update applied to a flagged report.
ANOMALY_TRUST = 0.3


def blend_headings(current, target, fraction):
    """Blend compass headings across the 0/360-degree boundary."""

    difference = (target - current + 180) % 360 - 180
    return (current + fraction * difference) % 360


class AircraftTracker:
    def __init__(self):
        self.position = None            # {"lat": ..., "lon": ...}
        self.altitude = None            # feet
        self.ground_speed = None        # knots
        self.heading = None             # degrees
        self.uncertainty_km = None      # roughly how wrong `position` could be
        self.last_timestamp = None
        self.last_gap_km = None         # how far the last message was from our guess
        self.started = False

        # Unlike the predicted position, these only change after an accepted report.
        self.last_accepted_position = None
        self.last_accepted_timestamp = None

        self.dead_reckoning = DeadReckoning()

    def start(self, lat, lon, altitude, ground_speed, heading, timestamp):
        """Initialize the tracker from the first valid report."""

        self.position = {"lat": lat, "lon": lon}
        self.altitude = altitude
        self.ground_speed = ground_speed
        self.heading = heading
        self.uncertainty_km = INITIAL_UNCERTAINTY_KM
        self.last_timestamp = timestamp
        self.started = True

        self.last_accepted_position = {"lat": lat, "lon": lon}
        self.last_accepted_timestamp = timestamp

    def predict(self, timestamp):
        """Predict forward to `timestamp` and increase uncertainty."""

        if not self.started or self.last_timestamp is None or timestamp is None:
            return

        seconds = (timestamp - self.last_timestamp).total_seconds()
        if seconds <= 0:
            return

        distance_m = self.ground_speed * KNOTS_TO_MPS * seconds
        lat, lon = destination_point(
            self.position["lat"], self.position["lon"], self.heading, distance_m
        )

        self.position = {"lat": lat, "lon": lon}
        self.uncertainty_km += DRIFT_PER_MINUTE_KM * (seconds / 60)
        self.last_timestamp = timestamp

    def update(self, lat, lon, altitude, ground_speed, heading):
        """Blend a report into the estimate and return `(gap_km, was_flagged)`."""

        gap_km = self.dead_reckoning.find_distance(
            self.position["lat"], self.position["lon"], lat, lon
        )

        # The allowed gap grows with uncertainty after long reporting gaps.
        tolerance_km = ANOMALY_SIGMA * (self.uncertainty_km + MEASUREMENT_ERROR_KM)
        was_flagged = gap_km > tolerance_km

        fraction = self.uncertainty_km / (self.uncertainty_km + MEASUREMENT_ERROR_KM)
        if was_flagged:
            fraction *= ANOMALY_TRUST

        self.last_gap_km = gap_km

        # Partial trust lets the tracker recover from real turns that initially
        # look suspicious. Full rejection can leave it following the old heading.
        if fraction <= 0:
            return gap_km, was_flagged

        bearing = self.dead_reckoning.find_bearing(
            self.position["lat"], self.position["lon"], lat, lon
        )
        moved_lat, moved_lon = destination_point(
            self.position["lat"], self.position["lon"],
            bearing, fraction * gap_km * 1000
        )
        self.position = {"lat": moved_lat, "lon": moved_lon}

        self.altitude += fraction * (altitude - self.altitude)
        self.ground_speed += fraction * (ground_speed - self.ground_speed)
        self.heading = blend_headings(self.heading, heading, fraction)

        self.uncertainty_km *= (1 - fraction)

        self.last_accepted_position = {"lat": lat, "lon": lon}
        self.last_accepted_timestamp = self.last_timestamp

        # Future predictions must start from the corrected estimate.
        self.dead_reckoning.current_position = dict(self.position)
        self.dead_reckoning.current_speed_mps = self.ground_speed * KNOTS_TO_MPS
        self.dead_reckoning.current_heading = self.heading
        self.dead_reckoning.last_timestamp = self.last_timestamp

        return gap_km, was_flagged

    def uncertainty_radius_m(self):
        """The uncertainty as a circle radius in metres, for drawing on the map."""

        if self.uncertainty_km is None:
            return None
        return self.uncertainty_km * 1000

    def state(self):
        """Return the current estimate."""

        if not self.started:
            return None

        return {
            "position": dict(self.position),
            "altitude": self.altitude,
            "ground_speed": self.ground_speed,
            "heading": self.heading,
            "uncertainty_km": self.uncertainty_km,
        }
