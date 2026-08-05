"""Small geographic calculations shared by the tracker and optional tools."""

import math

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
        math.cos(angular_distance) - math.sin(phi1) * math.sin(phi2),
    )

    return math.degrees(phi2), (math.degrees(lambda2) + 540) % 360 - 180


def distance_km(lat1, lon1, lat2, lon2):
    """Return the great-circle distance between two points in kilometres."""

    phi1 = math.radians(lat1)
    lambda1 = math.radians(lon1)
    phi2 = math.radians(lat2)
    lambda2 = math.radians(lon2)

    a = (
        math.sin((phi2 - phi1) / 2) ** 2
        + math.cos(phi1)
        * math.cos(phi2)
        * math.sin((lambda2 - lambda1) / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return EARTH_RADIUS_M * c / 1000


def initial_bearing(lat1, lon1, lat2, lon2):
    """Return the initial bearing from one point to another in degrees."""

    phi1 = math.radians(lat1)
    lambda1 = math.radians(lon1)
    phi2 = math.radians(lat2)
    lambda2 = math.radians(lon2)

    y = math.sin(lambda2 - lambda1) * math.cos(phi2)
    x = (
        math.cos(phi1) * math.sin(phi2)
        - math.sin(phi1) * math.cos(phi2) * math.cos(lambda2 - lambda1)
    )

    return (math.degrees(math.atan2(y, x)) + 360) % 360
