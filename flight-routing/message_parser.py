import json

class MessageParser:

    def __init__(self, filepath="flight-routing/data/flight_msgs.json"):
        with open(filepath, "r") as f:
            self.data = json.load(f)

    
    def get_info(self):
        return self.data["messages"]

    def display_info(self):
        for message in self.get_messages():
            print(message)


parser = MessageParser()
parser.display_messages()