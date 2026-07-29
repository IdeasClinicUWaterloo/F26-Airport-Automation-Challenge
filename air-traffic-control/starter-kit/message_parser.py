"""Process flight messages into a route, state estimate, ETA, and alert list."""

import json
from datetime import datetime, timedelta
from pathlib import Path

from dead_reckoning import DeadReckoning
from tracker import AircraftTracker


# Distance from a waypoint that counts as reaching it.
WAYPOINT_REACHED_KM = 30.0

# Reports that imply a faster speed are treated as invalid.
MAX_PLAUSIBLE_SPEED_KT = 700.0

KM_PER_NAUTICAL_MILE = 1.852
DEFAULT_NAV_DATA = Path(__file__).resolve().parent / "data" / "route.json"


class FlightRoutingSolution:
    def __init__(self, nav_data_path=DEFAULT_NAV_DATA):
        self.waypoints = self._load_waypoints(nav_data_path)

        self.tracker = AircraftTracker()
        self.dead_reckoning = DeadReckoning()

        self.route = []
        self.latest_reported_position = None
        self.predicted_position = None
        self.eta = None
        self.anomalies = []

        self._route_index = 0

        # Keep the full history so late messages can be replayed in time order.
        self._message_log = []
        self._last_timestamp = None

        # This list is not reset during replay, so earlier late arrivals remain flagged.
        self._late_arrivals = []

    @staticmethod
    def _load_waypoints(path):
        """Load waypoint data. Position tracking can run without route geometry."""

        try:
            with open(path, "r") as file:
                return json.load(file)["waypoints"]
        except (FileNotFoundError, KeyError):
            return {}

    # ---- entry point ----

    def process_message(self, message: dict):
        """Process one message, replaying the history if it arrived late."""

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
        """Rebuild the estimate in timestamp order after a late message."""

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

        # Replay resets alerts, so add the late-arrival alerts again.
        for message in self._late_arrivals:
            self.add_anomaly(
                message,
                "Message arrived out of order, so the whole stream was "
                "reprocessed in timestamp order"
            )

    @staticmethod
    def _sort_key(log_entry):
        """Sort by timestamp, then by arrival order. Missing timestamps sort first."""

        timestamp, arrival_index, _ = log_entry
        return (timestamp or datetime.min, arrival_index)

    def _apply(self, message, timestamp):
        """Predict to the message time, then apply the message."""

        if timestamp is not None:
            self.tracker.predict(timestamp)
            self._last_timestamp = timestamp

        # Copy the prediction before the message updates the tracker.
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
        """Validate a state report, then use it to update the tracker."""

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
        """Apply a new route and flag changes to waypoints already passed."""

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

        # Preserve route progress by waypoint name, not by list index.
        waypoint_we_were_at = self.current_waypoint

        self.route = list(new_route)

        if waypoint_we_were_at in new_route:
            self._route_index = new_route.index(waypoint_we_were_at)
        else:
            self._route_index = 0

    def process_waypoint_report(self, message):
        """Update route progress from a waypoint report.

        The ETA is calculated from the tracked position instead of copied from
        the report.
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
        """Check that a state report has usable, physically valid fields."""

        valid = True

        lat = message.get("lat")
        lon = message.get("lon")
        altitude = message.get("altitude")
        speed = message.get("ground_speed")
        heading = message.get("heading")

        if lat is None or lon is None:
            self.add_anomaly(message, "Missing latitude or longitude")
            valid = False

        # Prediction, ETA, and movement checks all require a timestamp.
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
        """Reject a position that requires an impossible travel speed.

        Distance is measured from the last accepted report. Measuring from a
        rejected report could cause the next valid report to be rejected too.
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
        """Advance past every waypoint crossed since the previous message."""

        if not self.route or not self.tracker.position:
            return

        while self._route_index + 1 < len(self.route):
            waypoint = self.waypoints.get(self.route[self._route_index + 1])
            if not waypoint or not self._has_passed(waypoint):
                break

            self._route_index += 1

    def _has_passed(self, waypoint):
        """Return True when a waypoint is close enough or behind the aircraft.

        The heading check handles message gaps that skip over a waypoint.
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
        """Estimate arrival at the next waypoint using distance divided by speed."""

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
        self.anomalies.append({
            "message_id": message.get("message_id"),
            "reason": reason
        })
