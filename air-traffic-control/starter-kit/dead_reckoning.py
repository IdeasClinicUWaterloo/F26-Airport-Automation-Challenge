import math
from datetime import datetime

EARTH_RADIUS_M = 6371e3
KNOTS_TO_MPS = 0.514444


def destination_point(lat, lon, bearing_deg, distance_m):
    """Return the point reached after travelling along a bearing."""

    phi1 = math.radians(lat)
    lambda1 = math.radians(lon)
    theta = math.radians(bearing_deg)
    angular_distance = distance_m / EARTH_RADIUS_M

    phi2 = math.asin(
        math.sin(phi1) * math.cos(angular_distance)
        + math.cos(phi1) * math.sin(angular_distance) * math.cos(theta)
    )

    lambda2 = lambda1 + math.atan2(
        math.sin(theta) * math.sin(angular_distance) * math.cos(phi1),
        math.cos(angular_distance) - math.sin(phi1) * math.sin(phi2)
    )

    return math.degrees(phi2), (math.degrees(lambda2) + 540) % 360 - 180


class DeadReckoning:
    earth_radius = EARTH_RADIUS_M  # metres

    def __init__(self):
        self.current_position = None
        self.current_speed_mps = None
        self.current_heading = None
        self.last_timestamp = None

    def update_from_state_message(self, message: dict):
        """Store the newest known aircraft state from a state message."""

        self.current_position = {
            "lat": message["lat"],
            "lon": message["lon"]
        }
        self.current_speed_mps = message["ground_speed"] * KNOTS_TO_MPS
        self.current_heading = message["heading"]
        self.last_timestamp = datetime.fromisoformat(message["timestamp"])

    def predict_at(self, timestamp: str):
        """Predict at a later timestamp, or return None when prediction is unavailable."""

        if self.current_position is None:
            return None

        target_time = datetime.fromisoformat(timestamp)
        delta_t = (target_time - self.last_timestamp).total_seconds()

        if delta_t < 0:
            return None

        return self.predict(
            self.current_position["lat"],
            self.current_position["lon"],
            delta_t
        )

    def predict(self, lat1, lon1, delta_t):
        """Predict position after `delta_t` seconds at constant speed and heading."""

        distance_m = self.current_speed_mps * delta_t
        lat, lon = destination_point(lat1, lon1, self.current_heading, distance_m)

        return {"lat": lat, "lon": lon}

    def find_distance(self, lat1, lon1, lat2, lon2):
        """Return great-circle distance between two points in kilometres."""

        phi1 = math.radians(lat1)
        lambda1 = math.radians(lon1)
        phi2 = math.radians(lat2)
        lambda2 = math.radians(lon2)

        a = (math.sin((phi2 - phi1)/2))**2 + math.cos(phi1) \
            * math.cos(phi2) * math.sin((lambda2 - lambda1) / 2)**2

        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

        dist = self.earth_radius * c

        return dist / 1000

    def find_bearing(self, lat1, lon1, lat2, lon2):
        """Return the initial bearing from one point to another in degrees."""

        phi1 = math.radians(lat1)
        lambda1 = math.radians(lon1)
        phi2 = math.radians(lat2)
        lambda2 = math.radians(lon2)

        y = math.sin(lambda2 - lambda1) * math.cos(phi2)

        x = ( math.cos(phi1) * math.sin(phi2)
            - math.sin(phi1) * math.cos(phi2) * math.cos(lambda2 - lambda1)
        )

        theta_rad = math.atan2(y, x)

        return (math.degrees(theta_rad) + 360) % 360

    def print_distance(self, lat1, lon1, lat2, lon2):
        dist = self.find_distance(lat1, lon1, lat2, lon2)
        print(f"Distance between ({lat1}, {lon1}) and ({lat2}, {lon2}) is {dist} km.")

    def print_bearing(self, lat1, lon1, lat2, lon2):
        bearing = self.find_bearing(lat1, lon1, lat2, lon2)
        print(f"Bearing from ({lat1}, {lon1}) to ({lat2}, {lon2}) is {bearing} degrees")
