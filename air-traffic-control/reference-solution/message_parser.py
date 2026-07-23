import json
from datetime import datetime, timedelta

import path_planning
from dead_reckoning import DeadReckoning
from ekf import AircraftEKF, NIS_THRESHOLD
from hypothesis import RouteHypothesis

MAX_HYPOTHESES = 3
MIN_HYPOTHESIS_WEIGHT = 0.05
HEADING_ROUTE_TOLERANCE_DEG = 60
ETA_SPEED_RATIO_TOLERANCE = 2.0


class FlightRoutingSolution:
    """
    Advanced (probabilistic) flight tracking solution.

    Kinematics (position/altitude/speed/heading/vertical speed, with
    uncertainty) are estimated by a single shared Extended Kalman Filter --
    the aircraft only has one true physical state. What's genuinely ambiguous
    is *route interpretation*, so that part is tracked as a set of weighted
    RouteHypothesis candidates (see hypothesis.py).
    """

    def __init__(self, nav_data_path="air-traffic-control/data/route.json"):
        self.ekf = AircraftEKF()
        self.dead_reckoning = DeadReckoning()  # distance/bearing helpers only
        self.hypotheses = []
        self.anomalies = []
        self.waypoints = self._load_waypoints(nav_data_path)

        # Ordered log of every timestamped message received, kept so a late
        # (out-of-order) arrival can trigger a full, correctly-ordered replay.
        self._message_log = []
        self._last_applied_ts = None

        # Flat fields mirrored after every processed message, kept for
        # backwards compatibility with callers of get_state().
        self.route = []
        self.latest_reported_position = None
        self.predicted_position = None
        self.altitude = None
        self.speed = None
        self.heading = None
        self.current_waypoint = None
        self.next_waypoint = None
        self.eta = None
        self.last_nis = None

    @staticmethod
    def _load_waypoints(path):
        try:
            with open(path) as f:
                return json.load(f)["waypoints"]
        except (FileNotFoundError, KeyError):
            return {}

    # ---- public API ----

    def process_message(self, message: dict):
        """
        Entry point for every incoming message. Messages are appended to a
        timestamp-ordered log; a message that arrives out of order (later
        than the latest one already applied) triggers a full replay of the
        log in the correct order rather than being dropped or corrupting the
        current estimate (late-message correction).
        """

        ts_str = message.get("timestamp")
        ts = datetime.fromisoformat(ts_str) if ts_str else None

        if ts is None:
            self._apply(message, None)
            return

        is_late = self._last_applied_ts is not None and ts < self._last_applied_ts
        self._message_log.append((ts, len(self._message_log), message))

        if is_late:
            self._replay_all()
            return

        self._apply(message, ts)
        self._last_applied_ts = ts

    def get_state(self) -> dict:
        return {
            "route": self.route,
            "latest_position": self.latest_reported_position,
            "predicted_position": self.predicted_position,
            "estimated_position": self.ekf.position(),
            "uncertainty_ellipse_m": self.ekf.uncertainty_ellipse(),
            "altitude": self.altitude,
            "speed": self.speed,
            "heading": self.heading,
            "vertical_speed_fpm": (self.ekf.state_dict() or {}).get("vertical_speed_fpm"),
            "current_waypoint": self.current_waypoint,
            "next_waypoint": self.next_waypoint,
            "eta": self.eta,
            "anomalies": self.anomalies,
            "last_nis": self.last_nis,
            "nis_threshold": NIS_THRESHOLD,
            "last_applied_timestamp": self._last_applied_ts,
            "hypotheses": [
                {
                    "route": h.route,
                    "weight": h.weight,
                    "consistency_score": h.consistency_score,
                    "current_waypoint": h.current_waypoint,
                    "next_waypoint": h.next_waypoint,
                    "eta": h.eta,
                }
                for h in self.hypotheses
            ],
        }

    def suggest_reroute(self, blocked_waypoints):
        """Stretch goal: if the best hypothesis's remaining route runs through a
        blocked/restricted waypoint, find the shortest alternate path around it."""

        best = self.best_hypothesis()
        if best is None:
            return None, None
        return path_planning.suggest_reroute(self.waypoints, best, blocked_waypoints)

    # ---- replay machinery ----

    def _replay_all(self):
        self.ekf = AircraftEKF()
        self.hypotheses = []
        self.anomalies = []
        self.last_nis = None
        self._last_applied_ts = None

        ordered = sorted(self._message_log, key=lambda entry: (entry[0], entry[1]))
        for ts, _, message in ordered:
            self._apply(message, ts)
            self._last_applied_ts = ts

    def _apply(self, message, ts):
        """Dispatch a single message to the right handler. Always predicts the
        filter forward to the message's timestamp first (growing uncertainty),
        mirroring how a real tracker coasts a track between updates."""

        if ts is not None:
            self.ekf.predict(ts)
        self.predicted_position = self.ekf.position()

        msg_type = message.get("type")

        if msg_type == "route_update":
            self.process_route_update(message)
        elif msg_type == "state":
            self.process_state_message(message)
        elif msg_type == "waypoint_report":
            self.process_waypoint_report(message)
        else:
            self.add_anomaly(message, "Unknown message type")

        self._sync_flat_state()

    # ---- message handlers ----

    def process_state_message(self, message):
        """
        Processes a state message. Hard-invalid fields (out-of-range physical
        values) are rejected outright, same as a basic sanity check would.
        Otherwise the message is compared against the EKF's prediction: a
        first message initializes the filter, later ones are fused in via
        update(), which flags the message if the innovation (the gap between
        what was predicted and what was reported) is larger than the current
        uncertainty would expect.
        """

        if not self.check_state_message(message):
            return

        lat, lon = message["lat"], message["lon"]
        altitude, speed, heading = message["altitude"], message["ground_speed"], message["heading"]

        if not self.ekf.initialized:
            ts = datetime.fromisoformat(message["timestamp"]) if message.get("timestamp") else None
            self.ekf.initialize(lat, lon, altitude, speed, heading, ts)
        else:
            nis, is_anomalous = self.ekf.update(lat, lon, altitude, speed, heading)
            self.last_nis = nis
            if is_anomalous:
                self.add_anomaly(
                    message,
                    f"Message deviates from the predicted state beyond expected "
                    f"uncertainty (innovation NIS={nis:.1f}, threshold={NIS_THRESHOLD:.1f})",
                )

        self.latest_reported_position = {"lat": lat, "lon": lon}
        self._check_heading_vs_route(message, heading, lat, lon)

    def process_route_update(self, message):
        """
        Applies a route_update to every hypothesis it's compatible with (i.e.
        it only revises waypoints not yet visited). If it's incompatible with
        every existing hypothesis, it's kept as a new, lower-weight branch
        instead of overwriting history that's already been confirmed.
        """

        new_route = message.get("route", [])
        if not new_route:
            return
        msg_id = message.get("message_id")

        if not self.hypotheses:
            self.hypotheses.append(RouteHypothesis(new_route, weight=1.0, origin_message_id=msg_id))
            return

        matched = [h for h in self.hypotheses if h.matches_route_update(new_route)]
        if matched:
            for h in matched:
                h.apply_route_update(new_route, message_id=msg_id)
        else:
            best = self.best_hypothesis()
            branched = RouteHypothesis(new_route, weight=best.weight * 0.5, origin_message_id=msg_id)
            current_wp = best.current_waypoint
            if current_wp in new_route:
                branched._index = new_route.index(current_wp)
            self.hypotheses.append(branched)
            self.add_anomaly(
                message,
                "Route update contradicts already-visited waypoints on the current best "
                "hypothesis; tracking as an alternate route",
            )

        self._prune_and_normalize()

    def process_waypoint_report(self, message):
        """
        Checks a waypoint_report against every hypothesis, boosting the
        weight of hypotheses it agrees with and penalizing (but not
        necessarily discarding) the ones it contradicts. Recomputes ETA from
        the EKF's current estimate rather than trusting the reported value
        outright, and flags reported ETAs that imply an implausible speed.
        """

        current_wp = message.get("current_waypoint")
        next_wp = message.get("next_waypoint")
        reported_eta = message.get("eta")
        msg_id = message.get("message_id")

        if not self.hypotheses:
            seed_route = [current_wp, next_wp] if next_wp else [current_wp]
            self.hypotheses.append(RouteHypothesis(seed_route, origin_message_id=msg_id))
        else:
            for h in self.hypotheses:
                h.apply_waypoint_report(current_wp, next_wp, message_id=msg_id)
            self._prune_and_normalize()

        best = self.best_hypothesis()
        if best is not None:
            best.eta = self._estimate_eta(next_wp, reported_eta, message)

    # ---- hypothesis bookkeeping ----

    def best_hypothesis(self):
        if not self.hypotheses:
            return None
        return max(self.hypotheses, key=lambda h: h.weight)

    def _prune_and_normalize(self):
        total = sum(h.weight for h in self.hypotheses) or 1.0
        for h in self.hypotheses:
            h.weight /= total

        self.hypotheses.sort(key=lambda h: h.weight, reverse=True)
        self.hypotheses = [h for h in self.hypotheses if h.weight >= MIN_HYPOTHESIS_WEIGHT][:MAX_HYPOTHESES]

        if self.hypotheses:
            total = sum(h.weight for h in self.hypotheses) or 1.0
            for h in self.hypotheses:
                h.weight /= total

    # ---- anomaly helpers ----

    def _check_heading_vs_route(self, message, heading_deg, lat, lon):
        best = self.best_hypothesis()
        if best is None:
            return
        wp = self.waypoints.get(best.next_waypoint)
        if not wp:
            return

        bearing = self.dead_reckoning.find_bearing(lat, lon, wp["lat"], wp["lon"])
        diff = abs((heading_deg - bearing + 180) % 360 - 180)
        if diff > HEADING_ROUTE_TOLERANCE_DEG:
            self.add_anomaly(
                message,
                f"Heading {heading_deg:.0f} deg is inconsistent with route geometry toward "
                f"{best.next_waypoint} (expected bearing ~{bearing:.0f} deg)",
            )

    def _estimate_eta(self, next_wp, reported_eta, message):
        wp = self.waypoints.get(next_wp)
        pos = self.ekf.position()
        state = self.ekf.state_dict()
        if not wp or not pos or not state or not self.ekf.last_timestamp:
            return reported_eta

        distance_km = self.dead_reckoning.find_distance(pos["lat"], pos["lon"], wp["lat"], wp["lon"])
        speed_kmh = state["ground_speed"] * 1.852

        if speed_kmh <= 1:
            return reported_eta

        estimated_eta = self.ekf.last_timestamp + timedelta(hours=distance_km / speed_kmh)

        if reported_eta:
            try:
                reported_dt = datetime.fromisoformat(reported_eta)
                reported_hours = (reported_dt - self.ekf.last_timestamp).total_seconds() / 3600
                if reported_hours > 0:
                    implied_kmh = distance_km / reported_hours
                    ratio = max(implied_kmh, speed_kmh) / max(min(implied_kmh, speed_kmh), 1e-6)
                    if ratio > ETA_SPEED_RATIO_TOLERANCE:
                        self.add_anomaly(
                            message,
                            f"Reported ETA implies a speed (~{implied_kmh:.0f} km/h) inconsistent "
                            f"with the current estimated speed (~{speed_kmh:.0f} km/h)",
                        )
            except ValueError:
                pass

        return estimated_eta.isoformat()

    def check_state_message(self, message):
        """
        Sanity check for the aircraft's state. Ensures position is present and
        other fields are physically plausible, before they're ever fed to the
        filter. This catches obviously corrupt data (wrong units, sensor
        glitches) that no amount of probabilistic fusion should be trusted
        with.
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

    def add_anomaly(self, message, reason):
        self.anomalies.append({
            "message_id": message.get("message_id"),
            "reason": reason,
        })

    def _sync_flat_state(self):
        best = self.best_hypothesis()
        self.route = best.route if best else []
        self.current_waypoint = best.current_waypoint if best else None
        self.next_waypoint = best.next_waypoint if best else None
        self.eta = best.eta if best else None

        state = self.ekf.state_dict()
        if state:
            self.altitude = state["altitude"]
            self.speed = state["ground_speed"]
            self.heading = state["heading"]
