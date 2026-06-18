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

        return dist

        