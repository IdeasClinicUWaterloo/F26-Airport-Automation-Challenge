"""Generate a known flight and a noisy message stream for accuracy testing."""

import json
import random
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Allow this file to be imported or run directly from the repository root.
STARTER_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(STARTER_DIR))

from dead_reckoning import destination_point, distance_km, initial_bearing

DEFAULT_ROUTE = ["YYZ", "WP001", "WP002", "OMAHA", "DEN"]
DEFAULT_WAYPOINTS = Path(__file__).resolve().parent.parent / "data" / "route.json"


def load_waypoints(path=DEFAULT_WAYPOINTS):
    with open(path) as f:
        return json.load(f)["waypoints"]


def build_ground_truth(waypoints, route, start_time, cruise_speed_kt=310.0, sample_dt_s=15, cruise_alt_ft=28000):
    """Generate state samples and waypoint arrival times for a route."""

    speed_mps = cruise_speed_kt * 0.514444
    samples = []
    waypoint_times = {}
    t = start_time
    num_legs = len(route) - 1
    bearing = 0.0

    for leg_index in range(num_legs):
        wp_a, wp_b = route[leg_index], route[leg_index + 1]
        waypoint_times[wp_a] = t
        a, b = waypoints[wp_a], waypoints[wp_b]

        leg_distance_km = distance_km(a["lat"], a["lon"], b["lat"], b["lon"])
        bearing = initial_bearing(a["lat"], a["lon"], b["lat"], b["lon"])
        leg_duration_s = (leg_distance_km * 1000) / speed_mps
        steps = max(1, round(leg_duration_s / sample_dt_s))

        for step in range(steps):
            frac = step / steps
            lat, lon = destination_point(
                a["lat"], a["lon"], bearing, frac * leg_distance_km * 1000
            )

            if leg_index == 0:
                altitude = cruise_alt_ft * frac
            elif leg_index == num_legs - 1:
                altitude = cruise_alt_ft * (1 - frac)
            else:
                altitude = cruise_alt_ft

            samples.append({
                "timestamp": t, "lat": lat, "lon": lon,
                "altitude": altitude, "ground_speed": cruise_speed_kt, "heading": bearing,
            })
            t += timedelta(seconds=sample_dt_s)

    final_wp = route[-1]
    b = waypoints[final_wp]
    waypoint_times[final_wp] = t
    samples.append({
        "timestamp": t, "lat": b["lat"], "lon": b["lon"],
        "altitude": 0.0, "ground_speed": cruise_speed_kt, "heading": bearing,
    })

    return samples, waypoint_times


def nearest_truth(timestamp, truth_samples):
    """Return the ground-truth sample closest to `timestamp`."""

    return min(truth_samples, key=lambda s: abs((s["timestamp"] - timestamp).total_seconds()))


def build_scenario(
    seed=42,
    flight_id="SIM100",
    waypoints_path=DEFAULT_WAYPOINTS,
    route=None,
    start_time=None,
    cruise_speed_kt=310.0,
    msg_interval_s=300,
    pos_noise_m=45,
    alt_noise_ft=25,
    speed_noise_kt=1.5,
    heading_noise_deg=1.5,
    drop_rate=0.12,
    late_message_shuffles=2,
    inject_anomaly=True,
    inject_conflicting_route=True,
):
    """Return messages in delivery order, truth samples, and waypoint data."""

    rng = random.Random(seed)
    waypoints = load_waypoints(waypoints_path)
    route = list(route or DEFAULT_ROUTE)
    start_time = start_time or datetime(2026, 6, 5, 10, 0, 0)

    truth, waypoint_times = build_ground_truth(waypoints, route, start_time, cruise_speed_kt)

    counter = {"n": 0}

    def next_id(prefix):
        counter["n"] += 1
        return f"{prefix}{counter['n']}"

    messages = []

    messages.append({
        "message_id": next_id("r"),
        "type": "route_update",
        "timestamp": start_time.isoformat(),
        "route": route,
    })

    step = max(1, round(msg_interval_s / 15))
    for sample in truth[::step]:
        if rng.random() < drop_rate:
            continue  # simulated comms dropout

        lat, lon = destination_point(
            sample["lat"], sample["lon"],
            rng.uniform(0, 360), abs(rng.gauss(0, pos_noise_m)),
        )
        messages.append({
            "message_id": next_id("s"),
            "type": "state",
            "timestamp": sample["timestamp"].isoformat(),
            "lat": lat,
            "lon": lon,
            "altitude": max(0.0, sample["altitude"] + rng.gauss(0, alt_noise_ft)),
            "ground_speed": max(0.0, sample["ground_speed"] + rng.gauss(0, speed_noise_kt)),
            "heading": (sample["heading"] + rng.gauss(0, heading_noise_deg)) % 360,
        })

    for i in range(len(route) - 1):
        current_wp, next_wp = route[i], route[i + 1]
        messages.append({
            "message_id": next_id("w"),
            "type": "waypoint_report",
            "timestamp": (waypoint_times[current_wp] + timedelta(seconds=30)).isoformat(),
            "current_waypoint": current_wp,
            "next_waypoint": next_wp,
            "eta": waypoint_times[next_wp].isoformat(),
        })

    if inject_conflicting_route and len(route) >= 4:
        # Send a route update that conflicts with a waypoint already passed.
        conflict_route = route[:2] + route[3:]
        conflict_time = waypoint_times[route[2]] + timedelta(minutes=2)
        messages.append({
            "message_id": next_id("r"),
            "type": "route_update",
            "timestamp": conflict_time.isoformat(),
            "route": conflict_route,
        })

    messages.sort(key=lambda m: m["timestamp"])

    if inject_anomaly:
        state_messages = [m for m in messages if m["type"] == "state"]
        if len(state_messages) > 2:
            target = state_messages[len(state_messages) // 2]
            target["lat"] = min(90.0, target["lat"] + rng.choice([-1, 1]) * rng.uniform(1.5, 3.0))
            target["_anomalous"] = True

    # Move selected messages later without changing the order of surrounding data.
    for _ in range(late_message_shuffles):
        eligible = [i for i, m in enumerate(messages) if m["type"] == "state"]
        if len(eligible) < 2:
            break
        i = rng.choice(eligible[:-1])
        delayed = messages.pop(i)
        later_slots = [k for k in range(i + 1, len(messages) + 1)]
        messages.insert(rng.choice(later_slots), delayed)

    return messages, truth, waypoints
