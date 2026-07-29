"""
Replays a scenario file through the tracker, one message at a time.

Run from the repository root:

    python air-traffic-control/starter-kit/stream.py
    python air-traffic-control/starter-kit/stream.py invalid.json
"""

import json
import sys
from pathlib import Path

from message_parser import FlightRoutingSolution
from visualizer import FlightVisualizer

STARTER_DIR = Path(__file__).resolve().parent
SCENARIO_DIR = STARTER_DIR / "scenarios"
NAV_DATA = STARTER_DIR / "data" / "route.json"


def load_scenario(filename="simple_route.json"):
    with open(SCENARIO_DIR / filename, "r") as file:
        return json.load(file)


def describe(state):
    """Print the main state values after one message."""

    position = state["estimated_position"]
    uncertainty = state["uncertainty_km"]

    if position:
        print(f"  estimated position   {position['lat']:.3f}, {position['lon']:.3f}"
              f"  (+/- {uncertainty:.1f} km)")
        print(f"  altitude / speed     {state['altitude']:.0f} ft"
              f" / {state['speed']:.0f} kt, heading {state['heading']:.0f}")
    else:
        print("  estimated position   not tracking yet")

    if state["route"]:
        print(f"  route                {' -> '.join(state['route'])}")
    if state["next_waypoint"]:
        print(f"  heading for          {state['next_waypoint']}, ETA {state['eta']}")
    if state["last_gap_km"] is not None:
        print(f"  message landed       {state['last_gap_km']:.1f} km from our prediction")


def main():
    filename = sys.argv[1] if len(sys.argv) > 1 else "simple_route.json"
    scenario = load_scenario(filename)

    flight_id = scenario.get("flight_id")
    messages = scenario.get("messages", [])

    solution = FlightRoutingSolution(NAV_DATA)
    visualizer = FlightVisualizer(NAV_DATA)

    print(f"Flight {flight_id} -- {len(messages)} messages from {filename}")
    print("=" * 62)

    for message in messages:
        print(f"\n{message.get('message_id')}  {message.get('type')}"
              f"  @ {message.get('timestamp')}")

        solution.process_message(message)
        state = solution.get_state()
        visualizer.record(message, state)

        describe(state)

    print("\n" + "=" * 62)

    state = solution.get_state()
    anomalies = state["anomalies"]

    if anomalies:
        print(f"{len(anomalies)} message(s) flagged:")
        for anomaly in anomalies:
            print(f"  - {anomaly['message_id']}: {anomaly['reason']}")
    else:
        print("No messages flagged.")

    if state["next_waypoint"]:
        print(f"\nFinal answer: heading for {state['next_waypoint']}, ETA {state['eta']}")

    visualizer.show(flight_id, state)


if __name__ == "__main__":
    main()
