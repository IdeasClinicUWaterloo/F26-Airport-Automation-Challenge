import json
from pprint import pprint

from visualizer import FlightVisualizer
from message_parser import FlightRoutingSolution


def load_scenario(filepath="air-traffic-control/scenarios/simple_route.json"):
    with open(filepath, "r") as f:
        return json.load(f)


def main():
    scenario = load_scenario()

    flight_id = scenario.get("flight_id")
    messages = scenario.get("messages", [])

    solution = FlightRoutingSolution()

    visualizer = FlightVisualizer(
        "air-traffic-control/data/route.json"
    )

    print(f"Starting demo for flight: {flight_id}")
    print("=" * 50)

    for message in messages:
        print(f"\nProcessing message: {message.get('message_id')}")
        print(f"Message type: {message.get('type')}")

        solution.process_message(message)

        current_state = solution.get_state()
        visualizer.record(message, current_state)

        print("\nCurrent state:")
        pprint(current_state)
        print("-" * 50)

    #Open the route/position chart after all messages are processed.
    visualizer.show(flight_id, solution.get_state()["route"])


if __name__ == "__main__":
    main()