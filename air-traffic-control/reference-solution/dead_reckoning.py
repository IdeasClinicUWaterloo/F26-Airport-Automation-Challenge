import math
from datetime import datetime

EARTH_RADIUS_M = 6371e3


def destination_point(lat, lon, bearing_deg, distance_m):
    """Standard spherical destination-point formula: where do you end up
    starting at (lat, lon), heading `bearing_deg`, for `distance_m` meters.
    A free function (rather than a DeadReckoning method) since it doesn't
    depend on any tracked aircraft state -- used by the simulator to generate
    ground truth and by the visualizer to draw uncertainty ellipses."""

    phi1 = math.radians(lat)
    lambda1 = math.radians(lon)
    theta = math.radians(bearing_deg)
    delta = distance_m / EARTH_RADIUS_M

    phi2 = math.asin(
        math.sin(phi1) * math.cos(delta) + math.cos(phi1) * math.sin(delta) * math.cos(theta)
    )
    lambda2 = lambda1 + math.atan2(
        math.sin(theta) * math.sin(delta) * math.cos(phi1),
        math.cos(delta) - math.sin(phi1) * math.sin(phi2),
    )
    return math.degrees(phi2), (math.degrees(lambda2) + 540) % 360 - 180


class DeadReckoning:
    earth_radius = EARTH_RADIUS_M # in meters

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
        self.current_speed_mps = message["ground_speed"] * 0.514444 # convert from knots to m/s
        self.current_heading = message["heading"]
        self.last_timestamp = datetime.fromisoformat(message["timestamp"])

    def predict_at(self, timestamp: str):
        """Predict position at a later timestamp."""

        if self.current_position is None:
            return None

        target_time = datetime.fromisoformat(timestamp)
        delta_t = (target_time - self.last_timestamp).total_seconds()

        if delta_t < 0:
            raise ValueError("Cannot predict backwards in time")

        return self.predict(
            self.current_position["lat"],
            self.current_position["lon"],
            delta_t
        )

    def predict(self, lat1, lon1, delta_t):
        """
        Predicts the position of the aircraft after delta_t seconds.

        First, it finds the distance, then uses formulas
        with distance and original lat and lon to find the new position."""

        phi1 = math.radians(lat1)
        lambda1 = math.radians(lon1)

        dist = self.current_speed_mps * delta_t
        heading = math.radians(self.current_heading)
        angular_distance = dist/self.earth_radius

        phi2 = math.asin( math.sin(phi1) * math.cos(angular_distance)
                + math.cos(phi1) * math.sin(angular_distance) * math.cos(heading)
        )

        lambda2 = lambda1 + math.atan2(math.sin(heading) * math.sin(angular_distance)
                    * math.cos(phi1) , math.cos(angular_distance)
                    - math.sin(phi1) * math.sin(phi2))

        return {
            "lat": math.degrees(phi2),
            "lon": (math.degrees(lambda2) + 540) % 360 - 180
        }

    def find_distance(self, lat1, lon1, lat2, lon2):
        """
        Uses Haversine formula to find the minimum Earth dist
        btwn two points.
        """

        phi1 = math.radians(lat1)
        lambda1 = math.radians(lon1)
        phi2 = math.radians(lat2)
        lambda2 = math.radians(lon2)

        a = (math.sin((phi2 - phi1)/2))**2 + math.cos(phi1) \
            * math.cos(phi2) * math.sin((lambda2 - lambda1) / 2)**2

        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

        dist = self.earth_radius * c

        return dist/1000 #return in km

    def find_bearing(self, lat1, lon1, lat2, lon2):
        """
        Finds the bearing, the direction from one point
        to another using their respective long and lat
        in radians.
        """

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
