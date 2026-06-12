import json
from pprint import pprint


class MessageParser:

    def __init__(self, filepath="flight-routing/data/flight_msgs.json"):
        with open(filepath, "r") as f:
            self.data = json.load(f)

    def get_info(self):
        flight = self.data.get("flight_id")

        info = {
            "flight": flight,
            "route": None,
            "position": None,
            "altitude": None,
            "speed": None,
            "current_waypoint": None,
            "next_waypoint": None,
            "eta": None
        }

        messages = self.data.get("messages", [])

        for message in messages:
            msg_type = message.get("type")

            if msg_type == "route_update":
                info["route"] = message.get("route")

            elif msg_type == "state":
                info["position"] = (message.get("lat"), message.get("lon"))
                info["altitude"] = message.get("altitude")
                info["speed"] = message.get("ground_speed")

            elif msg_type == "waypoint_report":
                info["current_waypoint"] = message.get("current_waypoint")
                info["next_waypoint"] = message.get("next_waypoint")
                info["eta"] = message.get("eta")

        return info

    def display_info(self):
        pprint(self.get_info())


parser = MessageParser()
parser.display_info()