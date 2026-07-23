import json
import math
import webbrowser
from pathlib import Path

import folium

from dead_reckoning import destination_point


def _ellipse_points(lat, lon, semi_major_m, semi_minor_m, rotation_deg, n=24):
    """Boundary points of a confidence ellipse centered at (lat, lon), as a list
    of [lat, lon] pairs suitable for a folium Polygon."""

    points = []
    for i in range(n):
        t = 2 * math.pi * i / n
        # Local ellipse-frame offset (u along the major axis, v along the minor).
        u = semi_major_m * math.cos(t)
        v = semi_minor_m * math.sin(t)

        rot = math.radians(rotation_deg)
        east = u * math.sin(rot) + v * math.sin(rot + math.pi / 2)
        north = u * math.cos(rot) + v * math.cos(rot + math.pi / 2)

        distance = math.hypot(east, north)
        bearing = math.degrees(math.atan2(east, north))
        p_lat, p_lon = destination_point(lat, lon, bearing, distance)
        points.append([p_lat, p_lon])

    return points


class FlightVisualizer:
    def __init__(self, nav_data_path):
        with open(nav_data_path, "r") as file:
            self.waypoints = json.load(file)["waypoints"]

        self.reported_points = []
        self.predicted_points = []
        self.estimated_points = []  # (position, uncertainty_ellipse_m or None)
        self.anomaly_markers = []  # (position, message_id, reason)
        self.truth_points = []  # ground-truth trajectory, simulator-only
        self._seen_anomaly_count = 0

    def record_truth(self, positions):
        """Simulator-only: record the ground-truth trajectory (a list of
        {"lat":, "lon":} points) so it can be drawn for comparison against the
        reported/predicted/estimated tracks."""

        self.truth_points = [p.copy() for p in positions]

    def record(self, message, state):
        """Record reported/predicted/estimated positions and any new anomalies for
        visualization."""

        if message.get("type") == "state" and state.get("latest_position"):
            self.reported_points.append(state["latest_position"].copy())

        if state.get("predicted_position"):
            self.predicted_points.append(state["predicted_position"].copy())

        if state.get("estimated_position"):
            self.estimated_points.append((
                state["estimated_position"].copy(),
                state.get("uncertainty_ellipse_m"),
            ))

        anomalies = state.get("anomalies", [])
        new_anomalies = anomalies[self._seen_anomaly_count:]
        self._seen_anomaly_count = len(anomalies)
        anchor = state.get("estimated_position") or state.get("latest_position")
        if anchor:
            for anomaly in new_anomalies:
                self.anomaly_markers.append((anchor.copy(), anomaly.get("message_id"), anomaly.get("reason")))

    def show(self, flight_id, state, output_path="air-traffic-control/reference-solution/output/flight_map.html", open_browser=True):
        route = state.get("route", [])
        hypotheses = state.get("hypotheses", [])

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

        bounds_points = []

        if self.truth_points:
            truth_locations = [[p["lat"], p["lon"]] for p in self.truth_points]
            bounds_points.extend(truth_locations)
            folium.PolyLine(
                locations=truth_locations,
                color="#111827",
                weight=2,
                opacity=0.7,
                dash_array="2,8",
                tooltip="Ground truth (simulator only)",
            ).add_to(m)

        for waypoint_id in {wp for h in hypotheses for wp in h["route"]} | set(route):
            waypoint = self.waypoints.get(waypoint_id)
            if not waypoint:
                continue

            location = [waypoint["lat"], waypoint["lon"]]
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

        # Route alternatives: the best (highest-weight) hypothesis solid and bold,
        # every other surviving hypothesis dashed and thin, weighted by confidence.
        for h in sorted(hypotheses, key=lambda h: h["weight"], reverse=True):
            points = [
                [self.waypoints[wp]["lat"], self.waypoints[wp]["lon"]]
                for wp in h["route"] if wp in self.waypoints
            ]
            if not points:
                continue

            is_best = h is max(hypotheses, key=lambda h: h["weight"]) if hypotheses else False
            folium.PolyLine(
                locations=points,
                color="#2563eb" if is_best else "#94a3b8",
                weight=5 if is_best else 3,
                opacity=0.9 if is_best else 0.6,
                dash_array=None if is_best else "8,6",
                tooltip=f"Route hypothesis (weight={h['weight']:.2f})" + (" - best" if is_best else ""),
            ).add_to(m)

        if not hypotheses and route:
            points = [
                [self.waypoints[wp]["lat"], self.waypoints[wp]["lon"]]
                for wp in route if wp in self.waypoints
            ]
            if points:
                folium.PolyLine(locations=points, color="#2563eb", weight=4, opacity=0.85, tooltip="Planned route").add_to(m)

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
                tooltip=f"Dead-reckoning prediction {index}",
                popup=(
                    f"<b>Dead-reckoning prediction {index}</b><br>"
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

        # EKF confidence estimate: fused position plus its uncertainty ellipse.
        for index, (position, ellipse) in enumerate(self.estimated_points, start=1):
            location = [position["lat"], position["lon"]]
            bounds_points.append(location)

            folium.CircleMarker(
                location=location,
                radius=4,
                color="#7c3aed",
                fill=True,
                fill_color="#a78bfa",
                fill_opacity=1,
                tooltip=f"EKF estimate {index}",
                popup=(
                    f"<b>EKF estimate {index}</b><br>"
                    f"Latitude: {position['lat']:.4f}<br>"
                    f"Longitude: {position['lon']:.4f}"
                )
            ).add_to(m)

            if ellipse:
                semi_major, semi_minor, rotation_deg = ellipse
                ring = _ellipse_points(position["lat"], position["lon"], semi_major, semi_minor, rotation_deg)
                folium.Polygon(
                    locations=ring,
                    color="#a78bfa",
                    weight=1,
                    fill=True,
                    fill_color="#a78bfa",
                    fill_opacity=0.15,
                    tooltip=f"~95% confidence region (±{semi_major:.0f}m x {semi_minor:.0f}m)",
                ).add_to(m)

        # Alerts for suspicious/flagged messages.
        for position, message_id, reason in self.anomaly_markers:
            location = [position["lat"], position["lon"]]
            bounds_points.append(location)

            folium.Marker(
                location=location,
                tooltip=f"Anomaly: {message_id}",
                popup=folium.Popup(f"<b>{message_id}</b><br>{reason}", max_width=280),
                icon=folium.Icon(color="red", icon="exclamation-triangle", prefix="fa"),
            ).add_to(m)

        if bounds_points:
            m.fit_bounds(bounds_points)

        folium.LayerControl().add_to(m)

        output_file = Path(output_path).resolve()
        output_file.parent.mkdir(parents=True, exist_ok=True)
        m.save(output_file)
        if open_browser:
            webbrowser.open(output_file.as_uri())

        print(f"\nSatellite map saved to: {output_file}")
