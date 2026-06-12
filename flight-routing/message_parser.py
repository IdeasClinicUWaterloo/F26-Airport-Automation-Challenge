import json
from pprint import pprint

class MessageParser:

    def __init__(self, filepath="flight-routing/data/flight_msgs.json"):
        with open(filepath, "r") as f:
            self.data = json.load(f)

    
    def get_info(self):

        info = {
            "flight": None,
            "route": None,
            "position": None,
            "altitude": None,
            "speed": None,
            "current_waypoint": None,
            "next_waypoint": None,
            "eta": None
        }
        
        info["flight"] = self.data.get("flight_id")

        message_type = self.data.get("type")

        messages = self.data.get("messages", [])

        for message in messages:
            if message_type == "route_update":
                info["route"] = message.get("route")
            
            if message_type == "state":
                info["position"] = (message.get("lat"), message.get("lon"))
                info["altitude"] = message.get("altitude")
                info["speed"] = message.get("speed")

            if message_type == "waypoint_report":
                info["current_waypoint"] = message.get("current_waypoint")
                info["next_waypoint"] = message.get("next_waypoint")
                info["eta"] = message.get("eta")
        
        return info



    def display_info(self):
        pprint(self.get_info())


parser = MessageParser()
parser.display_info()