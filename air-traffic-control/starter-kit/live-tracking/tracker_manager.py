"""Maintain one tracker per aircraft in the live OpenSky feed."""

from datetime import datetime, timezone

STALE_AFTER_SECONDS = 120


class AircraftTrack:
    """Store one aircraft's tracker and radar-display state."""

    def __init__(self, tracker_class, aircraft_id, callsign):
        self.aircraft_id = aircraft_id
        self.callsign = callsign
        self.tracker = tracker_class()

        self.anomalies = []
        self.last_message_flagged = False
        self.last_seen = None
        self.history = []  # reported positions, for the trail drawn behind the aircraft

    def process_state_message(self, message):
        timestamp = datetime.fromisoformat(message["timestamp"])

        if not self.tracker.started:
            self.tracker.start(
                message["lat"], message["lon"], message["altitude"],
                message["ground_speed"], message["heading"], timestamp,
            )
            self.last_message_flagged = False
        else:
            self.tracker.predict(timestamp)
            gap_km, was_flagged = self.tracker.update(
                message["lat"], message["lon"], message["altitude"],
                message["ground_speed"], message["heading"],
            )

            # The display shows whether the latest report was flagged.
            self.last_message_flagged = was_flagged

            if was_flagged:
                self.anomalies.append({
                    "message_id": message["message_id"],
                    "reason": (
                        f"Reported position is {gap_km:.1f} km from the predicted "
                        f"position, beyond what the current uncertainty explains"
                    ),
                })

        self.callsign = message.get("callsign") or self.callsign
        self.last_seen = timestamp
        self.history.append({"lat": message["lat"], "lon": message["lon"]})

    def is_stale(self, now):
        if self.last_seen is None:
            return True
        return (now - self.last_seen).total_seconds() > STALE_AFTER_SECONDS

    def state(self):
        return {
            "aircraft_id": self.aircraft_id,
            "callsign": self.callsign,
            "estimated_position": self.tracker.position,
            "uncertainty_km": self.tracker.uncertainty_km,
            "state": self.tracker.state(),
            "anomalous": self.last_message_flagged,
            "anomaly_count": len(self.anomalies),
        }


class TrackerManager:
    def __init__(self, tracker_class):
        self.tracker_class = tracker_class
        self.tracks = {}

    def ingest(self, message):
        aircraft_id = message["aircraft_id"]

        track = self.tracks.get(aircraft_id)
        if track is None:
            track = AircraftTrack(self.tracker_class, aircraft_id, message.get("callsign"))
            self.tracks[aircraft_id] = track

        track.process_state_message(message)

    def active_tracks(self):
        """Return tracks with a report inside the stale-time limit."""

        now = datetime.now(timezone.utc)
        return [track for track in self.tracks.values() if not track.is_stale(now)]
