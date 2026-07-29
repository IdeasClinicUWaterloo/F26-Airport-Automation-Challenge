"""Build radar data and predict each active track to the current time."""

from datetime import datetime, timezone


def build_snapshot(manager):
    now = datetime.now(timezone.utc)
    aircraft = []

    for track in manager.active_tracks():
        if track.tracker.started:
            track.tracker.predict(now)

        position = track.tracker.position
        state = track.tracker.state()
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
