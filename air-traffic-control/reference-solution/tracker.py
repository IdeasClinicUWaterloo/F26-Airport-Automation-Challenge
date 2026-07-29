"""
Keeps a running best guess of where the aircraft is, and how sure we are of it.

The whole idea in one paragraph: we hold a guess about the aircraft's position,
plus one number saying roughly how wrong that guess could be. Between messages
we coast forward on the last known speed and heading, and we get less sure.
When a message arrives we move the guess toward what it reported -- a long way
if we were unsure, barely at all if we were confident -- and we get more sure.

That "how far do I move toward the message" fraction is the one clever bit, and
it falls out of the two numbers we already have:

    gain = our_uncertainty / (our_uncertainty + expected_message_error)

If we're lost and the message looks reliable, gain is near 1 and we jump to it.
If we're confident and the message could be noisy, gain is near 0 and we hold
our ground. Nothing else in this file is more complicated than that.

Real ATC trackers do the same two steps, but track uncertainty as a matrix
covering position, altitude, speed and heading together, which lets them model
how being wrong about heading makes you wrong about position later. That's an
Extended Kalman Filter -- see STRETCH_GOALS.md if you want to build one.
"""

from dead_reckoning import DeadReckoning, destination_point, KNOTS_TO_MPS


# ---------------------------------------------------------------------------
# Tuning knobs.
#
# These are the numbers to reach for when the tracker misbehaves. Every one of
# them says what raising it does, so you can guess-and-check your way to
# sensible values instead of deriving them.
# ---------------------------------------------------------------------------

# How far off a reported position typically is, in km.
# RAISE IT to trust the aircraft's own reports less and our prediction more.
MEASUREMENT_ERROR_KM = 3.0

# How much confidence we lose for every minute we go without a message, in km.
# RAISE IT if the aircraft manoeuvres a lot between messages, so that coasting
# for a long time honestly reflects how little we know by the end of it.
#
# For scale: an airliner covers about 9 km a minute, so 1.0 says "after a
# minute of coasting, we could be off by roughly a tenth of the distance flown".
# That sounds pessimistic until you remember we have no idea whether it turned.
DRIFT_PER_MINUTE_KM = 1.0

# How unsure we are the instant the very first message arrives, in km.
# This one matters less than the others -- it washes out after a few messages.
INITIAL_UNCERTAINTY_KM = 5.0

# Flag a message when it lands further from our prediction than this many
# uncertainty-radii.
# RAISE IT to be more forgiving (fewer false alarms, more missed bad messages).
# LOWER IT to be stricter (catches more, cries wolf more).
ANOMALY_SIGMA = 3.0

# How much of a flagged message to believe anyway, from 0.0 to 1.0.
#   0.0 -> ignore flagged messages completely, keep coasting on the prediction
#   0.3 -> let them nudge the estimate, but not drag it
#   1.0 -> flag them but otherwise treat them as normal
#
# Do not set this to 0.0 without reading the note in update() first. It sounds
# like the safe choice and it measurably isn't.
ANOMALY_TRUST = 0.3


def blend_headings(current, target, fraction):
    """
    Move `fraction` of the way from one compass heading to another, going the
    short way round.

    Needed because headings wrap: 350 degrees and 10 degrees are 20 degrees
    apart, but subtracting them gives 340. Without this, an aircraft crossing
    due north would look like it spun most of the way around.
    """

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

        # The last position we actually believed, and when. Different from
        # `position` and `last_timestamp`, which move every time we coast forward
        # or reject a message. Anything asking "how long since we really knew
        # where this aircraft was?" wants these two.
        self.last_accepted_position = None
        self.last_accepted_timestamp = None

        self.dead_reckoning = DeadReckoning()

    def start(self, lat, lon, altitude, ground_speed, heading, timestamp):
        """Take the first message at face value -- we have nothing to compare it to."""

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
        """
        Coast the guess forward to `timestamp` and get less sure of it.

        This is what happens when no message has arrived: the aircraft kept
        flying, so our guess should keep moving, but we have no evidence it
        held its heading, so our confidence should decay.
        """

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
        """
        Fold a reported state into our guess.

        Returns (gap_km, was_flagged) so the caller can record an anomaly. The
        gap is how far the report landed from where we predicted, which is the
        single most useful number for understanding what the tracker is doing.
        """

        gap_km = self.dead_reckoning.find_distance(
            self.position["lat"], self.position["lon"], lat, lon
        )

        # How far off we'd tolerate before calling the message suspicious. Note
        # this widens on its own as we coast: a surprising report right after a
        # long silence is much more believable than the same report arriving
        # seconds after a confident fix.
        tolerance_km = ANOMALY_SIGMA * (self.uncertainty_km + MEASUREMENT_ERROR_KM)
        was_flagged = gap_km > tolerance_km

        fraction = self.uncertainty_km / (self.uncertainty_km + MEASUREMENT_ERROR_KM)
        if was_flagged:
            fraction *= ANOMALY_TRUST

        self.last_gap_km = gap_km

        # Why ANOMALY_TRUST defaults to 0.3 rather than 0.0:
        #
        # Ignoring flagged messages outright sounds safer, and it's the obvious
        # first guess. It also loses the aircraft. A sharp turn at a waypoint puts
        # the next report tens of km from our straight-line prediction, so it gets
        # flagged -- and if we then ignore it, we keep flying the old heading and
        # the next report is further off still. The gap grows at cruise speed
        # while the tolerance only widens at DRIFT_PER_MINUTE_KM, so it never
        # catches up and the track is gone.
        #
        # Measured against the simulator in advanced/, dropping this to 0.0 roughly
        # doubles the tracker's error. Letting a suspicious message pull the
        # estimate part of the way is what allows a real course change to win the
        # argument eventually, while a single corrupt message still can't drag us.
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

        # Keep the dead-reckoning helper in step with our corrected estimate, so
        # anything else asking it to project forward starts from the fused guess
        # rather than the last raw report.
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
        """Everything we currently believe, in one printable dict."""

        if not self.started:
            return None

        return {
            "position": dict(self.position),
            "altitude": self.altitude,
            "ground_speed": self.ground_speed,
            "heading": self.heading,
            "uncertainty_km": self.uncertainty_km,
        }
