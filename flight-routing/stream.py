import json
from pprint import pprint

from message_parser import FlightRoutingSolution


def load_scenario(filepath="flight-routing/scenarios/simple_route.json"):
    with open(filepath, "r") as f:
        return json.load(f)


def main():
    scenario = load_scenario()

    flight_id = scenario.get("flight_id")
    messages = scenario.get("messages", [])

    solution = FlightRoutingSolution()

    print(f"Starting demo for flight: {flight_id}")
    print("=" * 50)

    for message in messages:
        print(f"\nProcessing message: {message.get('message_id')}")
        print(f"Message type: {message.get('type')}")

        solution.process_message(message)

        print("\nCurrent state:")
        pprint(solution.get_state())

        print("-" * 50)


if __name__ == "__main__":
    main()