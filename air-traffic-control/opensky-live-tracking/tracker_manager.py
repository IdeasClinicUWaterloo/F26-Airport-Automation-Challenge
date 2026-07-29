"""
Keeps one AircraftEKF per aircraft (icao24) seen in the polled airspace and
applies incoming state messages to the right one -- extending the ATC
challenge's single-aircraft tracking to many aircraft at once.

The aircraft population is dynamic: active_tracks() excludes any aircraft not
updated within STALE_AFTER_SECONDS, so a track that left the bounding box
(or dropped off ADS-B coverage) stops being drawn/tracked without anyone
telling us explicitly that it's gone.
"""

from datetime import datetime, timezone

from ekf import AircraftEKF, NIS_THRESHOLD

STALE_AFTER_SECONDS = 120


class AircraftTrack:
    def __init__(self, aircraft_id, callsign):
        self.aircraft_id = aircraft_id
        self.callsign = callsign
        self.ekf = AircraftEKF()
        self.anomalies = []
        self.last_seen = None
        self.history = []  # reported {"lat", "lon"} points, for the map trail

    def process_state_message(self, message):
        ts = datetime.fromisoformat(message["timestamp"])

        if not self.ekf.initialized:
            self.ekf.initialize(
                message["lat"], message["lon"], message["altitude"],
                message["ground_speed"], message["heading"], ts,
            )
        else:
            self.ekf.predict(ts)
            nis, is_anomalous = self.ekf.update(
                message["lat"], message["lon"], message["altitude"],
                message["ground_speed"], message["heading"],
            )
            if is_anomalous:
                self.anomalies.append({
                    "message_id": message["message_id"],
                    "reason": (
                        f"Innovation NIS={nis:.1f} exceeds threshold "
                        f"{NIS_THRESHOLD:.1f}"
                    ),
                })

        self.callsign = message.get("callsign") or self.callsign
        self.last_seen = ts
        self.history.append({"lat": message["lat"], "lon": message["lon"]})

    def is_stale(self, now):
        return self.last_seen is None or (now - self.last_seen).total_seconds() > STALE_AFTER_SECONDS

    def state(self):
        return {
            "aircraft_id": self.aircraft_id,
            "callsign": self.callsign,
            "estimated_position": self.ekf.position(),
            "uncertainty_ellipse_m": self.ekf.uncertainty_ellipse(),
            "state": self.ekf.state_dict(),
            "anomalies": self.anomalies,
        }


class TrackerManager:
    def __init__(self):
        self.tracks = {}

    def ingest(self, message):
        aircraft_id = message["aircraft_id"]
        track = self.tracks.get(aircraft_id)
        if track is None:
            track = AircraftTrack(aircraft_id, message.get("callsign"))
            self.tracks[aircraft_id] = track
        track.process_state_message(message)

    def active_tracks(self):
        now = datetime.now(timezone.utc)
        return [t for t in self.tracks.values() if not t.is_stale(now)]
