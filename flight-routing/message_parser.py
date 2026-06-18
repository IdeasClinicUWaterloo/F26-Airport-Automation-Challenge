class FlightRoutingSolution:
    def __init__(self):
        self.route = []
        self.latest_position = None
        self.altitude = None
        self.speed = None
        self.heading = None
        self.current_waypoint = None
        self.next_waypoint = None
        self.eta = None
        self.anomalies = []

    def process_message(self, message: dict):
        """
            This function gets the type of message, and based on type,
            hands off to specific functions which process the data.
        """

        msg_type = message.get("type")

        if msg_type == "route_update":
            self.process_route_update(message)

        elif msg_type == "state":
            self.process_state_message(message)

        elif msg_type == "waypoint_report":
            self.process_waypoint_report(message)

        else:
            self.add_anomaly(message, "Unknown message type")

    def process_route_update(self, message):
        """
            Processes route messages, and stores it in route variable 
            within message dict.
            Examples of routes: [YYZ, WP001, WP002, JFK]

        """

        self.route = message.get("route", [])

    def process_state_message(self, message):
        """
        Processes messages for the aircraft's state.
        It receives and stores the position, speed,
        and heading of the aircraft, if valid.
        """

        self.check_state_message(message)

        self.latest_position = {
            "lat": message.get("lat"),
            "lon": message.get("lon")
        }
        self.altitude = message.get("altitude")
        self.speed = message.get("ground_speed")
        self.heading = message.get("heading")

    def process_waypoint_report(self, message):
        """
        Receives and stores the waypoint message.
        Includes current, next waypoint, and eta.

        """

        self.current_waypoint = message.get("current_waypoint")
        self.next_waypoint = message.get("next_waypoint")
        self.eta = message.get("eta")

    def check_state_message(self, message):
        """
        Sanity check for the aircraft's state.
        Ensures position present, and other states
        are not unreasonable.

        If they are, function calls helper which attaches an
        anomaly message to the report.
        """

        lat = message.get("lat")
        lon = message.get("lon")
        altitude = message.get("altitude")
        speed = message.get("ground_speed")
        heading = message.get("heading")

        if lat is None or lon is None:
            self.add_anomaly(message, "Missing latitude or longitude")

        if lat is not None and not (-90 <= lat <= 90):
            self.add_anomaly(message, "Latitude out of range")

        if lon is not None and not (-180 <= lon <= 180):
            self.add_anomaly(message, "Longitude out of range")

        if altitude is not None and altitude < 0:
            self.add_anomaly(message, "Altitude cannot be negative")

        if speed is not None and speed < 0:
            self.add_anomaly(message, "Ground speed cannot be negative")

        if heading is not None and not (0 <= heading <= 360):
            self.add_anomaly(message, "Heading out of range")

    def add_anomaly(self, message, reason):
        """
        Function adds an anomaly message to the report.
        """

        self.anomalies.append({
            "message_id": message.get("message_id"),
            "reason": reason
        })

    def get_state(self) -> dict:
        return {
            "route": self.route,
            "latest_position": self.latest_position,
            "altitude": self.altitude,
            "speed": self.speed,
            "heading": self.heading,
            "current_waypoint": self.current_waypoint,
            "next_waypoint": self.next_waypoint,
            "eta": self.eta,
            "anomalies": self.anomalies
        }