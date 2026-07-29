"""Convert an OpenSky state vector into the starter kit's `state` message format.

Speed is converted from metres per second to knots. GPS altitude is used when
barometric altitude is unavailable.
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
