"""
Builds the JSON payload served to the radar page.

The interesting part: every active track is predicted forward to *now* before
being read out, not just to its last real OpenSky message. OpenSky reports every
~15 seconds but the page polls every 2, so without this, aircraft would sit still
and then jump. Predicting on demand means they coast smoothly along their last
known heading in between.

That's dead reckoning doing visible work -- the same idea as `predict_at()` in the
reference solution's dead_reckoning.py, just called continuously instead of once
per message.
"""

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
