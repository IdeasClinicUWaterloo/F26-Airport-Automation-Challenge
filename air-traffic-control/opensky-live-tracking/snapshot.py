"""
Builds the JSON snapshot served to the radar page.

Each active track's EKF is predicted forward to "now" (not just to its last
real OpenSky message) before being read out. That means the browser can poll
this far more often than OpenSky data actually arrives (OpenSky updates every
~15s; the page polls every couple seconds) and still see aircraft coasting
forward smoothly along their last known heading/speed in between -- the same
dead-reckoning idea as ../dead_reckoning.py, just applied continuously.
"""

from datetime import datetime, timezone


def build_snapshot(manager):
    now = datetime.now(timezone.utc)
    aircraft = []

    for track in manager.active_tracks():
        if track.ekf.initialized:
            track.ekf.predict(now)

        pos = track.ekf.position()
        state = track.ekf.state_dict()
        if pos is None or state is None:
            continue

        aircraft.append({
            "id": track.aircraft_id,
            "callsign": track.callsign or track.aircraft_id,
            "lat": pos["lat"],
            "lon": pos["lon"],
            "heading": state["heading"],
            "altitude": state["altitude"],
            "ground_speed": state["ground_speed"],
            "anomalous": bool(track.anomalies),
        })

    return {"generated_at": now.isoformat(), "aircraft": aircraft}
