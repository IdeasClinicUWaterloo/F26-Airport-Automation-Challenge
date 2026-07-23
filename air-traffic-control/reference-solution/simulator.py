"""
Synthetic scenario generator.

Real ATC messages never come with a ground-truth answer key, which makes it
hard to tell whether the tracker is actually working. This module generates
a known-correct flight (straight legs between waypoints, climb/descent
altitude profile) and derives a realistic message stream from it: Gaussian
sensor noise, dropped messages, a couple delivered out of order, one
deliberately corrupted message, and one route update that genuinely
contradicts an already-confirmed waypoint -- so every advanced-tracking
feature (EKF fusion, innovation-based anomaly flagging, late-message
correction, multi-hypothesis branching) has something to visibly react to.
"""

import json
import random
from datetime import datetime, timedelta

from dead_reckoning import DeadReckoning, destination_point

_dr = DeadReckoning()

DEFAULT_ROUTE = ["YYZ", "WP001", "WP002", "OMAHA", "DEN"]


def load_waypoints(path="air-traffic-control/data/route.json"):
    with open(path) as f:
        return json.load(f)["waypoints"]


def build_ground_truth(waypoints, route, start_time, cruise_speed_kt=310.0, sample_dt_s=15, cruise_alt_ft=28000):
    """Sample (timestamp, lat, lon, altitude, ground_speed, heading) along
    straight legs between consecutive route waypoints at a constant cruise
    speed, climbing on the first leg and descending on the last so vertical
    speed isn't always zero. Returns (samples, {waypoint_id: arrival_time})."""

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

        distance_km = _dr.find_distance(a["lat"], a["lon"], b["lat"], b["lon"])
        bearing = _dr.find_bearing(a["lat"], a["lon"], b["lat"], b["lon"])
        leg_duration_s = (distance_km * 1000) / speed_mps
        steps = max(1, round(leg_duration_s / sample_dt_s))

        for step in range(steps):
            frac = step / steps
            lat, lon = destination_point(a["lat"], a["lon"], bearing, frac * distance_km * 1000)

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
    """The ground-truth sample closest in time to `timestamp` -- used to score
    tracker accuracy, since real messages don't carry an answer key."""

    return min(truth_samples, key=lambda s: abs((s["timestamp"] - timestamp).total_seconds()))


def build_scenario(
    seed=42,
    flight_id="SIM100",
    waypoints_path="air-traffic-control/data/route.json",
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
    """Returns (messages, truth_samples, waypoints). `messages` is in
    *delivery* order (which may differ from timestamp order -- see
    late_message_shuffles), exactly like a real message feed the tracker has
    to reorder on its own."""

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
        # Proposed after the aircraft has already been confirmed past route[2] --
        # genuinely contradicts history, so the tracker should branch rather
        # than blindly overwrite it.
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

    for _ in range(late_message_shuffles):
        eligible = [i for i, m in enumerate(messages) if m["type"] == "state"]
        if len(eligible) < 2:
            break
        i = rng.choice(eligible[:-1])
        j = rng.choice([k for k in eligible if k > i])
        messages[i], messages[j] = messages[j], messages[i]

    return messages, truth, waypoints
