import math

class DeadReckoning:
    def __init__(self):
        self.current_position = None
        self.current_speed = None
        self.current_heading = None

    def find_distance(self, lat1, lon1, lat2, lon2):
        """
        Use Haversine formula to find the minimum Earth dist. 
        btwn two points.
        """

        earth_radius = 6371e3

        phi1 = math.radians(lat1)
        lambda1 = math.radians(lon1)
        phi2 = math.radians(lat2)
        lambda2 = math.radians(lon2)

        a = (math.sin((phi2 - phi1)/2))**2 + math.cos(phi1) \
            * math.cos(phi2) * (math.sin((lambda2-lambda1))/2)**2
        
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        
        dist = earth_radius * c

        return dist/1000 #return in km
    
    def find_bearing(self, lat1, lon1, lat2, lon2):

        phi1 = math.radians(lat1)
        lambda1 = math.radians(lon1)
        phi2 = math.radians(lat2)
        lambda2 = math.radians(lon2)

        y = math.sin(lambda2 - lambda1) * math.cos(phi2)

        x = ( math.cos(phi1) * math.sin(phi2)
            - math.sin(phi1) * math.cos(phi2) * math.cos(lambda2 - lambda1)
        )

        theta_rad = math.atan2(y, x)
        theta = math.degrees(theta_rad)

        return theta
        
    def print_distance(self, lat1, lon1, lat2, lon2):
        dist = self.find_distance(lat1, lon1, lat2, lon2)
        print(f"Distance between ({lat1}, {lon1}) and ({lat2}, {lon2}) is {dist} km.")
    
    def print_bearing(self, lat1, lon1, lat2, lon2):
        bearing = self.find_bearing(lat1, lon1, lat2, lon2)
        print(f"Bearing from ({lat1}, {lon1}) to ({lat2}, {lon2}) is {bearing} degrees")

dr = DeadReckoning()
dr.print_distance(43.6777, -79.6248, 40.6413, -73.7781)
dr.print_bearing(43.6777, -79.6248, 40.6413, -73.7781)

        