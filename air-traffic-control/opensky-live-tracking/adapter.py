"""
Translates a raw OpenSky state vector into the challenge's own message format.

This is the whole trick behind the add-on, and it's 15 lines. Because the message
shape matches what `../scenarios/*.json` contains, real live aircraft become just
another message source -- no tracking code has to know the difference between a
canned scenario, the simulator, and Toronto's actual airspace.

Two fields need care. OpenSky reports speed in m/s where the challenge uses knots,
and barometric altitude is sometimes absent, in which case the GPS-derived figure
is the fallback.

What OpenSky cannot give us is any notion of *intent*: there's no flight plan,
route, or waypoint data behind ADS-B, so nothing here maps to "route_update" or
"waypoint_report". See this folder's README for what that rules out.
"""

from datetime import datetime, timezone

MPS_TO_KNOTS = 1.943844


def to_state_message(raw, message_id):
    timestamp = raw["time_position"] or raw["last_contact"]
    altitude = raw["baro_altitude"] if raw["baro_altitude"] is not None else raw["geo_altitude"]

    return {
        "message_id": message_id,
        "type": "state",
        "aircraft_id": raw["icao24"],
        "callsign": (raw["callsign"] or "").strip(),
        "timestamp": datetime.fromtimestamp(timestamp, tz=timezone.utc).isoformat(),
        "lat": raw["latitude"],
        "lon": raw["longitude"],
        "altitude": altitude if altitude is not None else 0.0,
        "ground_speed": (raw["velocity"] or 0.0) * MPS_TO_KNOTS,
        "heading": raw["true_track"] if raw["true_track"] is not None else 0.0,
    }
