"""Draw the route, reports, estimates, uncertainty, and alerts on a map."""

import json
import webbrowser
from pathlib import Path

import folium


DEFAULT_OUTPUT = (
    Path(__file__).resolve().parent / "advanced" / "output" / "flight_map.html"
)


class FlightVisualizer:
    def __init__(self, nav_data_path):
        with open(nav_data_path, "r") as file:
            self.waypoints = json.load(file)["waypoints"]

        self.reported_points = []
        self.estimated_points = []   # (position, uncertainty_radius_m)
        self.anomaly_markers = []    # (position, message_id, reason)

        # Record only alerts added since the previous message.
        self._anomalies_drawn = 0

    def record(self, message, state):
        """Snapshot the current estimate. Call once per message, after processing it."""

        if message.get("type") == "state" and state.get("latest_position"):
            self.reported_points.append(dict(state["latest_position"]))

        if state.get("estimated_position"):
            uncertainty_km = state.get("uncertainty_km")
            self.estimated_points.append((
                dict(state["estimated_position"]),
                uncertainty_km * 1000 if uncertainty_km else None
            ))

        anomalies = state.get("anomalies", [])
        for anomaly in anomalies[self._anomalies_drawn:]:
            position = state.get("estimated_position") or state.get("latest_position")
            if position:
                self.anomaly_markers.append((
                    dict(position), anomaly.get("message_id"), anomaly.get("reason")
                ))
        self._anomalies_drawn = len(anomalies)

    def show(self, flight_id, state,
             output_path=DEFAULT_OUTPUT,
             open_browser=True):
        """Build the map, save it, and optionally open it in a browser."""

        route = state.get("route", []) if isinstance(state, dict) else state

        flight_map = folium.Map(
            location=[42.5, -92],
            zoom_start=5,
            tiles=None,
            control_scale=True
        )

        folium.TileLayer(
            tiles=(
                "https://server.arcgisonline.com/ArcGIS/rest/services/"
                "World_Imagery/MapServer/tile/{z}/{y}/{x}"
            ),
            attr="Esri World Imagery",
            name="Satellite",
            max_zoom=18
        ).add_to(flight_map)

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
        ).add_to(flight_map)

        bounds = []
        self._draw_route(flight_map, route, state, bounds)
        self._draw_reported(flight_map, bounds)
        self._draw_estimated(flight_map, bounds)
        self._draw_anomalies(flight_map, bounds)

        if bounds:
            flight_map.fit_bounds(bounds)

        folium.LayerControl().add_to(flight_map)

        output_file = Path(output_path).resolve()
        output_file.parent.mkdir(parents=True, exist_ok=True)
        flight_map.save(str(output_file))

        if open_browser:
            webbrowser.open(output_file.as_uri())

        print(f"\nMap for {flight_id} saved to: {output_file}")

    # ---- layers ----

    def _draw_route(self, flight_map, route, state, bounds):
        """Draw the planned route and highlight the next waypoint."""

        next_waypoint = state.get("next_waypoint") if isinstance(state, dict) else None
        eta = state.get("eta") if isinstance(state, dict) else None

        route_points = []

        for waypoint_id in route:
            waypoint = self.waypoints.get(waypoint_id)
            if not waypoint:
                continue

            location = [waypoint["lat"], waypoint["lon"]]
            route_points.append(location)
            bounds.append(location)

            is_next = waypoint_id == next_waypoint
            popup_lines = [
                f"<b>{waypoint_id}</b>",
                waypoint["name"],
                f"Type: {waypoint['type']}",
                f"Latitude: {waypoint['lat']}",
                f"Longitude: {waypoint['lon']}",
            ]
            if is_next and eta:
                popup_lines.append(f"<b>Next waypoint</b> -- ETA {eta}")

            folium.Marker(
                location=location,
                tooltip=f"{waypoint_id} (next)" if is_next else waypoint_id,
                popup=folium.Popup("<br>".join(popup_lines), max_width=260),
                icon=folium.Icon(
                    color="red" if is_next else "blue",
                    icon="plane",
                    prefix="fa"
                )
            ).add_to(flight_map)

        if route_points:
            folium.PolyLine(
                locations=route_points,
                color="#2563eb",
                weight=4,
                opacity=0.85,
                tooltip="Planned route"
            ).add_to(flight_map)

    def _draw_reported(self, flight_map, bounds):
        """Draw raw positions from state reports."""

        for index, position in enumerate(self.reported_points, start=1):
            location = [position["lat"], position["lon"]]
            bounds.append(location)

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
            ).add_to(flight_map)

    def _draw_estimated(self, flight_map, bounds):
        """Draw estimated positions and their uncertainty circles."""

        for index, (position, radius_m) in enumerate(self.estimated_points, start=1):
            location = [position["lat"], position["lon"]]
            bounds.append(location)
            is_latest = index == len(self.estimated_points)

            if radius_m:
                folium.Circle(
                    location=location,
                    radius=radius_m,
                    color="#f97316",
                    weight=2 if is_latest else 1,
                    opacity=0.9 if is_latest else 0.25,
                    fill=True,
                    fill_color="#f97316",
                    fill_opacity=0.15 if is_latest else 0.04,
                    tooltip=f"Uncertainty {index}: about {radius_m / 1000:.1f} km"
                ).add_to(flight_map)

            folium.Marker(
                location=location,
                tooltip=f"Estimated position {index}",
                popup=(
                    f"<b>Estimated position {index}</b><br>"
                    f"Latitude: {position['lat']:.4f}<br>"
                    f"Longitude: {position['lon']:.4f}<br>"
                    + (f"Uncertainty: about {radius_m / 1000:.1f} km" if radius_m else "")
                ),
                icon=folium.DivIcon(
                    html=(
                        '<div style="font-size: 22px; color: #f97316; '
                        'font-weight: bold;">X</div>'
                    )
                )
            ).add_to(flight_map)

    def _draw_anomalies(self, flight_map, bounds):
        """Draw alerts at the estimated position where they occurred."""

        for position, message_id, reason in self.anomaly_markers:
            location = [position["lat"], position["lon"]]
            bounds.append(location)

            folium.Marker(
                location=location,
                tooltip=f"Flagged: {message_id}",
                popup=folium.Popup(
                    f"<b>Flagged message {message_id}</b><br>{reason}",
                    max_width=280
                ),
                icon=folium.Icon(color="red", icon="triangle-exclamation", prefix="fa")
            ).add_to(flight_map)
