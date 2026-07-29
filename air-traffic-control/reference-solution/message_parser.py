"""
Turns a stream of aircraft messages into an answer to four questions:

    Where is it now?  Where is it going next?  When does it get there?
    Which messages shouldn't we trust?

Each message type gets its own handler, and everything they learn feeds one
shared AircraftTracker (see tracker.py) that holds the current best guess.
"""

import json
from datetime import datetime, timedelta

from dead_reckoning import DeadReckoning
from tracker import AircraftTracker


# ---------------------------------------------------------------------------
# Tuning knobs. See tracker.py for the ones that govern the estimate itself.
# ---------------------------------------------------------------------------

# How close, in km, counts as having reached a waypoint. Waypoints are just
# points in the sky, so an aircraft never passes exactly through one.
# RAISE IT if the tracker seems slow to admit it has passed a waypoint.
WAYPOINT_REACHED_KM = 30.0

# The fastest a large aircraft could plausibly be going, in knots. A position
# that would need more than this to explain isn't a fast aircraft, it's a bad
# message -- wrong units, a typo, or a corrupted field.
MAX_PLAUSIBLE_SPEED_KT = 700.0

KM_PER_NAUTICAL_MILE = 1.852


class FlightRoutingSolution:
    def __init__(self, nav_data_path="air-traffic-control/data/route.json"):
        self.waypoints = self._load_waypoints(nav_data_path)

        self.tracker = AircraftTracker()
        self.dead_reckoning = DeadReckoning()

        self.route = []
        self.latest_reported_position = None
        self.predicted_position = None
        self.eta = None
        self.anomalies = []

        # How far along self.route we think we are.
        self._route_index = 0

        # Every message we've been handed, so that a late arrival can be
        # slotted into the right place and the stream replayed in order.
        self._message_log = []
        self._last_timestamp = None

        # Which messages turned up late. Kept outside the replay reset, since a
        # second late arrival would otherwise wipe the record of the first.
        self._late_arrivals = []

    @staticmethod
    def _load_waypoints(path):
        """Load the waypoint database. Missing file just means no route geometry,
        which is survivable -- position tracking still works without it."""

        try:
            with open(path, "r") as file:
                return json.load(file)["waypoints"]
        except (FileNotFoundError, KeyError):
            return {}

    # ---- entry point ----

    def process_message(self, message: dict):
        """
        Hand a message to the right handler.

        A message that's older than one we've already processed can't just be
        applied on top -- our estimate has already moved past it. So we log
        every message, and when a late one shows up we throw the estimate away
        and rebuild it with the whole stream in timestamp order. Slower than
        patching it up, but it's obviously correct, which matters more here.
        """

        timestamp = self._parse_timestamp(message.get("timestamp"))
        self._message_log.append((timestamp, len(self._message_log), message))

        is_late = (
            timestamp is not None
            and self._last_timestamp is not None
            and timestamp < self._last_timestamp
        )

        if is_late:
            self._late_arrivals.append(message)
            self._replay()
        else:
            self._apply(message, timestamp)

    def get_state(self) -> dict:
        tracked = self.tracker.state()

        return {
            "route": self.route,
            "latest_position": self.latest_reported_position,
            "predicted_position": self.predicted_position,
            "estimated_position": tracked["position"] if tracked else None,
            "uncertainty_km": tracked["uncertainty_km"] if tracked else None,
            "altitude": tracked["altitude"] if tracked else None,
            "speed": tracked["ground_speed"] if tracked else None,
            "heading": tracked["heading"] if tracked else None,
            "current_waypoint": self.current_waypoint,
            "next_waypoint": self.next_waypoint,
            "eta": self.eta,
            "last_gap_km": self.tracker.last_gap_km,
            "anomalies": self.anomalies,
        }

    # ---- where we are on the route ----

    @property
    def current_waypoint(self):
        if 0 <= self._route_index < len(self.route):
            return self.route[self._route_index]
        return None

    @property
    def next_waypoint(self):
        if 0 <= self._route_index + 1 < len(self.route):
            return self.route[self._route_index + 1]
        return None

    # ---- replay ----

    def _replay(self):
        """Rebuild the estimate from scratch with the log sorted by time. The index
        in each log entry keeps messages that share a timestamp in arrival order."""

        self.tracker = AircraftTracker()
        self.route = []
        self.latest_reported_position = None
        self.predicted_position = None
        self.eta = None
        self.anomalies = []
        self._route_index = 0
        self._last_timestamp = None

        for timestamp, _, message in sorted(self._message_log, key=self._sort_key):
            self._apply(message, timestamp)

        # Re-flag the late arrivals, since the loop above just cleared the list.
        for message in self._late_arrivals:
            self.add_anomaly(
                message,
                "Message arrived out of order, so the whole stream was "
                "reprocessed in timestamp order"
            )

    @staticmethod
    def _sort_key(log_entry):
        """Order the log by timestamp, falling back to arrival order for ties.

        A message with no usable timestamp can't be placed in time at all, so it
        sorts to the front rather than crashing the comparison.
        """

        timestamp, arrival_index, _ = log_entry
        return (timestamp or datetime.min, arrival_index)

    def _apply(self, message, timestamp):
        """Coast the estimate up to this message's time, then let the right handler
        fold the message in."""

        if timestamp is not None:
            self.tracker.predict(timestamp)
            self._last_timestamp = timestamp

        # Snapshot rather than alias, so this keeps saying where we thought the
        # aircraft was *before* the message below gets folded in.
        self.predicted_position = dict(self.tracker.position) if self.tracker.position else None

        msg_type = message.get("type")

        if msg_type == "route_update":
            self.process_route_update(message)
        elif msg_type == "state":
            self.process_state_message(message)
        elif msg_type == "waypoint_report":
            self.process_waypoint_report(message)
        else:
            self.add_anomaly(message, "Unknown message type")

        self._advance_route_progress()
        self.eta = self._estimate_eta()

    # ---- message handlers ----

    def process_state_message(self, message):
        """
        Fold a reported position, altitude, speed and heading into the estimate.

        Two different checks run here, and they catch different things. The field
        check rejects values that are impossible on their own (a latitude of 95).
        The tracker's gap check rejects values that are individually fine but
        don't square with where the aircraft just was.
        """

        if not self.check_state_message(message):
            return

        lat, lon = message["lat"], message["lon"]
        altitude = message["altitude"]
        speed = message["ground_speed"]
        heading = message["heading"]

        if not self.check_position_jump(message, lat, lon):
            return

        if not self.tracker.started:
            self.tracker.start(
                lat, lon, altitude, speed, heading,
                self._parse_timestamp(message.get("timestamp"))
            )
        else:
            gap_km, was_flagged = self.tracker.update(lat, lon, altitude, speed, heading)
            if was_flagged:
                self.add_anomaly(
                    message,
                    f"Reported position is {gap_km:.0f} km from where we expected "
                    f"the aircraft to be, which is further off than our current "
                    f"uncertainty can explain"
                )

        self.latest_reported_position = {"lat": lat, "lon": lon}

    def process_route_update(self, message):
        """
        Replace the planned route.

        A reroute is normal and expected -- but a new route that disagrees about
        waypoints we've already flown past is not a reroute, it's a contradiction,
        so it gets flagged. We still accept it, because refusing to would leave
        us tracking a route nobody is flying.
        """

        new_route = message.get("route", [])
        if not new_route:
            return

        already_flown = self.route[: self._route_index + 1]
        if already_flown and new_route[: len(already_flown)] != already_flown:
            self.add_anomaly(
                message,
                f"Route update disagrees with waypoints we've already passed "
                f"({' -> '.join(already_flown)})"
            )

        # Read the current waypoint off the old route before replacing it, since
        # the same index means something different on the new one.
        waypoint_we_were_at = self.current_waypoint

        self.route = list(new_route)

        if waypoint_we_were_at in new_route:
            self._route_index = new_route.index(waypoint_we_were_at)
        else:
            self._route_index = 0

    def process_waypoint_report(self, message):
        """
        Take the aircraft's word for which waypoint it's at.

        The reported ETA is deliberately not stored. We recompute ETA ourselves
        from where we think the aircraft is and how fast it's going, because
        that stays honest when the aircraft's own estimate goes stale.
        """

        current_wp = message.get("current_waypoint")

        if current_wp in self.route:
            self._route_index = self.route.index(current_wp)
        elif current_wp is not None and self.route:
            self.add_anomaly(
                message,
                f"Reported waypoint {current_wp} isn't anywhere on the current route"
            )

    # ---- checks ----

    def check_state_message(self, message):
        """
        Sanity check for the aircraft's state.
        Ensures position present, and other states
        are not unreasonable.

        If they are, function calls helper which attaches an
        anomaly message to the report.
        """

        valid = True

        lat = message.get("lat")
        lon = message.get("lon")
        altitude = message.get("altitude")
        speed = message.get("ground_speed")
        heading = message.get("heading")

        if lat is None or lon is None:
            self.add_anomaly(message, "Missing latitude or longitude")
            valid = False

        # Everything downstream is time-based -- coasting forward, ETAs, deciding
        # whether a jump was possible. A position with no time attached can't
        # feed any of it, so it's rejected here rather than breaking them later.
        if self._parse_timestamp(message.get("timestamp")) is None:
            self.add_anomaly(message, "Missing or unreadable timestamp")
            valid = False

        if lat is not None and not (-90 <= lat <= 90):
            self.add_anomaly(message, "Latitude out of range")
            valid = False

        if lon is not None and not (-180 <= lon <= 180):
            self.add_anomaly(message, "Longitude out of range")
            valid = False

        if altitude is not None and altitude < 0:
            self.add_anomaly(message, "Altitude cannot be negative")
            valid = False

        if speed is not None and speed < 0:
            self.add_anomaly(message, "Ground speed cannot be negative")
            valid = False

        if heading is not None and not (0 <= heading <= 360):
            self.add_anomaly(message, "Heading out of range")
            valid = False

        return valid

    def check_position_jump(self, message, lat, lon):
        """
        Reject a position no aircraft could have reached in the time available.

        This is a blunter check than the tracker's, and it's here to catch the
        genuinely broken rather than the merely surprising -- swapped lat/lon,
        a decimal point in the wrong place. Returns True if the message is usable.

        It measures from the last position we actually believed, not from our
        current prediction. That distinction matters: if we rejected the previous
        message, our prediction is stale, and measuring against it would make the
        next perfectly good message look impossible too.
        """

        anchor = self.tracker.last_accepted_position
        anchor_time = self.tracker.last_accepted_timestamp

        if anchor is None or anchor_time is None or self._last_timestamp is None:
            return True

        seconds = (self._last_timestamp - anchor_time).total_seconds()
        if seconds <= 0:
            return True

        travelled_km = self.dead_reckoning.find_distance(
            anchor["lat"], anchor["lon"], lat, lon
        )
        furthest_possible_km = MAX_PLAUSIBLE_SPEED_KT * KM_PER_NAUTICAL_MILE * (seconds / 3600)

        if travelled_km > furthest_possible_km:
            self.add_anomaly(
                message,
                f"Position implies {travelled_km:.0f} km travelled in "
                f"{seconds / 60:.0f} minutes, which is physically impossible"
            )
            return False

        return True

    # ---- derived answers ----

    def _advance_route_progress(self):
        """
        Walk our route index forward past every waypoint we've now left behind.

        A loop rather than a single step, because one long gap between messages
        can carry the aircraft past more than one waypoint.
        """

        if not self.route or not self.tracker.position:
            return

        while self._route_index + 1 < len(self.route):
            waypoint = self.waypoints.get(self.route[self._route_index + 1])
            if not waypoint or not self._has_passed(waypoint):
                break

            self._route_index += 1

    def _has_passed(self, waypoint):
        """
        Have we left this waypoint behind?

        Two ways to say yes. Either we're close enough to call it reached -- a
        waypoint is just a point in the sky, so nothing flies exactly through
        one. Or it's behind us: we'd have to turn more than a right angle to fly
        back to it.

        The second test is what stops route progress from getting stuck. Messages
        here can be tens of minutes apart, so a single gap can easily carry the
        aircraft from well before a waypoint to well past it without ever
        reporting a position near it.
        """

        distance_km = self.dead_reckoning.find_distance(
            self.tracker.position["lat"], self.tracker.position["lon"],
            waypoint["lat"], waypoint["lon"]
        )
        if distance_km <= WAYPOINT_REACHED_KM:
            return True

        if self.tracker.heading is None:
            return False

        bearing_to_waypoint = self.dead_reckoning.find_bearing(
            self.tracker.position["lat"], self.tracker.position["lon"],
            waypoint["lat"], waypoint["lon"]
        )
        angle_off_the_nose = abs((bearing_to_waypoint - self.tracker.heading + 180) % 360 - 180)

        return angle_off_the_nose > 90

    def _estimate_eta(self):
        """
        When we'd reach the next waypoint if we carried on as we are.

        Straight-line distance over current speed. It ignores the fact that the
        aircraft has to turn, so it runs slightly optimistic -- good enough to
        be useful, and simple enough to check by hand.
        """

        waypoint = self.waypoints.get(self.next_waypoint)
        if not waypoint or not self.tracker.started or self.tracker.ground_speed is None:
            return None

        speed_kmh = self.tracker.ground_speed * KM_PER_NAUTICAL_MILE
        if speed_kmh < 1:
            return None

        distance_km = self.dead_reckoning.find_distance(
            self.tracker.position["lat"], self.tracker.position["lon"],
            waypoint["lat"], waypoint["lon"]
        )
        arrival = self.tracker.last_timestamp + timedelta(hours=distance_km / speed_kmh)

        return arrival.isoformat()

    # ---- helpers ----

    @staticmethod
    def _parse_timestamp(value):
        """Parse an ISO timestamp, or return None if it's missing or malformed."""

        if not value:
            return None
        try:
            return datetime.fromisoformat(value)
        except ValueError:
            return None

    def add_anomaly(self, message, reason):
        """
        Function adds an anomaly message to the report.
        """

        self.anomalies.append({
            "message_id": message.get("message_id"),
            "reason": reason
        })
