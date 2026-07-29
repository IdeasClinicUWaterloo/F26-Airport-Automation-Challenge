"""
Converts a raw OpenSky state dict (see opensky_client.STATE_FIELDS) into the
same "state" message shape air-traffic-control/message_parser.py already
consumes, so the EKF-based tracking logic works on real data unmodified.

OpenSky has no flight-plan, route, or waypoint data -- there is no equivalent
of "route_update" or "waypoint_report" here, only continuous state reports.
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
