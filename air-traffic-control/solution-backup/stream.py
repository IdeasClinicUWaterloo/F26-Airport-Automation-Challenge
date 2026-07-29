import json
from pprint import pprint
from pathlib import Path

from visualizer import FlightVisualizer
from message_parser import FlightRoutingSolution


BACKUP_DIR = Path(__file__).resolve().parent
DEFAULT_SCENARIO = BACKUP_DIR / "scenarios" / "simple_route.json"
NAV_DATA = BACKUP_DIR / "data" / "route.json"


def load_scenario(filepath=DEFAULT_SCENARIO):
    with open(filepath, "r") as f:
        return json.load(f)


def main():
    scenario = load_scenario()

    flight_id = scenario.get("flight_id")
    messages = scenario.get("messages", [])

    solution = FlightRoutingSolution()

    visualizer = FlightVisualizer(NAV_DATA)

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
