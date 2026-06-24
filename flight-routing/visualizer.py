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

    def record(self, message, state):
        """Record the reported and predicted positions for visualization.
        If the message received has a position, we note that, if not, we note predicted."""

        if message.get("type") == "state":
            if state.get("latest_position"):
                self.reported_points.append(state["latest_position"].copy())
        
        if state.get("predicted_position"):
            self.predicted_points.append(state["predicted_position"].copy())
    
    def show(self, flight_id, route):

        m = folium.Map(
            location=[42.5, -92],
            zoom_start=5,
            tiles=None,
            control_scale=True
        )

        # Satellite imagery.
        folium.TileLayer(
            tiles=(
                "https://server.arcgisonline.com/ArcGIS/rest/services/"
                "World_Imagery/MapServer/tile/{z}/{y}/{x}"
            ),
            attr="Esri World Imagery",
            name="Satellite",
            max_zoom=18
        ).add_to(m)

        # City, country, road, and boundary labels on top of satellite imagery.
        folium.TileLayer(
            tiles=(
                "https://services.arcgisonline.com/ArcGIS/rest/services/"
                "Reference/World_Boundaries_and_Places/MapServer/tile/"
                "{z}/{y}/{x}"
            ),
            attr="Esri World Boundaries and Places",
            name="City labels",
            overlay=True,
            control=True
        ).add_to(m)

        route_points = []
        bounds_points = []

        for waypoint_id in route:
            waypoint = self.waypoints.get(waypoint_id)

            if not waypoint:
                continue

            location = [waypoint["lat"], waypoint["lon"]]
            route_points.append(location)
            bounds_points.append(location)

            folium.Marker(
                location=location,
                tooltip=waypoint_id,
                popup=folium.Popup(
                    f"""
                    <b>{waypoint_id}</b><br>
                    {waypoint["name"]}<br>
                    Type: {waypoint["type"]}<br>
                    Latitude: {waypoint["lat"]}<br>
                    Longitude: {waypoint["lon"]}
                    """,
                    max_width=240
                ),
                icon=folium.Icon(color="blue", icon="plane", prefix="fa")
            ).add_to(m)

        #For waypoints on the route, connect them to make a route line for the flight.
        if route_points:
            folium.PolyLine(
                locations=route_points,
                color="#2563eb",
                weight=4,
                opacity=0.85,
                tooltip="Planned route"
            ).add_to(m)

        #in the for loops, we are looping through index as well as position,
        #so we can label and number the reported or estimated point

        for index, position in enumerate(self.reported_points, start=1):
            location = [position["lat"], position["lon"]]
            bounds_points.append(location)

            folium.CircleMarker(
                location=location,
                radius=7,
                color="#166534",
                fill=True,
                fill_color="#22c55e",
                fill_opacity=1,
                tooltip=f"Reported position {index}",
                popup=(
                    f"<b>Reported position {index}</b><br>"
                    f"Latitude: {position['lat']:.4f}<br>"
                    f"Longitude: {position['lon']:.4f}"
                )
            ).add_to(m)

        for index, position in enumerate(self.predicted_points, start=1):
            location = [position["lat"], position["lon"]]
            bounds_points.append(location)

            folium.Marker(
                location=location,
                tooltip=f"Estimated position {index}",
                popup=(
                    f"<b>Dead-reckoning estimate {index}</b><br>"
                    f"Latitude: {position['lat']:.4f}<br>"
                    f"Longitude: {position['lon']:.4f}"
                ),
                icon=folium.DivIcon(
                    html=(
                        '<div style="font-size: 22px; color: #f97316; '
                        'font-weight: bold;">X</div>'
                    )
                )
            ).add_to(m)

        if bounds_points:
            m.fit_bounds(bounds_points)
        
        folium.LayerControl().add_to(m)

        output_file = Path("flight-routing/output/flight_map.html").resolve()
        m.save(output_file)
        webbrowser.open(output_file.as_uri())

        print(f"\nSatellite map saved to: {output_file}")
        



        