"""
Autonomous reroute suggestion (stretch goal).

The provided nav data only lists waypoints, not an airway network between
them, so this treats the waypoint set as a complete graph weighted by
great-circle distance and runs Dijkstra to find the shortest path from a
start waypoint to a destination, optionally avoiding a set of blocked/
restricted waypoints (e.g. a storm cell or a waypoint an anomalous message
implicated).
"""

import heapq

from dead_reckoning import DeadReckoning

_dr = DeadReckoning()


def find_shortest_path(waypoints, start, goal, blocked=None):
    """
    waypoints: dict of waypoint_id -> {"lat":, "lon":, ...} (as in data/route.json)
    Returns (path: list of waypoint ids, total_distance_km) or (None, None) if
    no feasible path exists.
    """

    blocked = set(blocked or ())
    if start in blocked or goal in blocked:
        return None, None
    if start not in waypoints or goal not in waypoints:
        return None, None

    nodes = [w for w in waypoints if w not in blocked]

    distances = {node: math_inf() for node in nodes}
    previous = {node: None for node in nodes}
    distances[start] = 0.0

    queue = [(0.0, start)]
    visited = set()

    while queue:
        dist, node = heapq.heappop(queue)
        if node in visited:
            continue
        visited.add(node)

        if node == goal:
            break

        for neighbor in nodes:
            if neighbor == node or neighbor in visited:
                continue
            edge = _dr.find_distance(
                waypoints[node]["lat"], waypoints[node]["lon"],
                waypoints[neighbor]["lat"], waypoints[neighbor]["lon"],
            )
            candidate = dist + edge
            if candidate < distances[neighbor]:
                distances[neighbor] = candidate
                previous[neighbor] = node
                heapq.heappush(queue, (candidate, neighbor))

    if distances.get(goal, math_inf()) == math_inf():
        return None, None

    path = []
    node = goal
    while node is not None:
        path.append(node)
        node = previous[node]
    path.reverse()

    return path, distances[goal]


def math_inf():
    return float("inf")


def suggest_reroute(waypoints, current_hypothesis, blocked):
    """Given a hypothesis whose remaining route is blocked (or an anomaly implicated
    a waypoint on it), find an alternate path from the current waypoint to the
    route's final destination that avoids `blocked` waypoints."""

    remaining = current_hypothesis.remaining_route()
    if not remaining:
        return None, None

    start, goal = remaining[0], remaining[-1]
    if not any(wp in blocked for wp in remaining):
        return None, None  # nothing to avoid, current route is still fine

    return find_shortest_path(waypoints, start, goal, blocked=blocked)
