"""Build radar data and predict each active track to the current time."""

from copy import deepcopy
from datetime import datetime, timezone


def build_snapshot(manager):
    now = datetime.now(timezone.utc)
    aircraft = []

    for track in manager.active_tracks():
        # Predict a copy for display so a browser refresh cannot move the real
        # tracker ahead of the next OpenSky report.
        display_tracker = deepcopy(track.tracker)
        if display_tracker.started:
            display_tracker.predict(now)

        position = display_tracker.position
        state = display_tracker.state()
        if position is None or state is None:
            continue

        aircraft.append({
            "id": track.aircraft_id,
            "callsign": track.callsign or track.aircraft_id,
            "lat": position["lat"],
            "lon": position["lon"],
            "heading": state["heading"],
            "altitude": state["altitude"],
            "ground_speed": state["ground_speed"],
            "uncertainty_km": state["uncertainty_km"],
            "anomalous": track.last_message_flagged,
            "anomaly_count": len(track.anomalies),
        })

    return {"generated_at": now.isoformat(), "aircraft": aircraft}
