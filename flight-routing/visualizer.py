import json
import webbrowser
from pathlib import Path

import folium


class FlightVisualizer:
    def __init__(self, nav_data_path):
        with open(nav_data_path, "r") as file:
            self.waypoints = json.load(file)["waypoints"]

        self.reported_points = []
        self.predicted_points = []
