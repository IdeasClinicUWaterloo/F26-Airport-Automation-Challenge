"""Find a short waypoint route while avoiding blocked waypoints.

The supplied data has no airway connections, so every waypoint is treated as
connected to every other waypoint.
"""

import heapq

from dead_reckoning import DeadReckoning

_dr = DeadReckoning()


def find_shortest_path(waypoints, start, goal, blocked=None):
    """Return `(path, distance_km)`, or `(None, None)` when no path exists."""

    blocked = set(blocked or ())
    if start in blocked or goal in blocked:
        return None, None
    if start not in waypoints or goal not in waypoints:
        return None, None

    nodes = [w for w in waypoints if w not in blocked]

    distances = {node: float("inf") for node in nodes}
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

    if distances.get(goal, float("inf")) == float("inf"):
        return None, None

    path = []
    node = goal
    while node is not None:
        path.append(node)
        node = previous[node]
    path.reverse()

    return path, distances[goal]


def suggest_reroute(waypoints, current_hypothesis, blocked):
    """Suggest a replacement for a route containing a blocked waypoint."""

    remaining = current_hypothesis.remaining_route()
    if not remaining:
        return None, None

    start, goal = remaining[0], remaining[-1]
    if not any(wp in blocked for wp in remaining):
        return None, None

    return find_shortest_path(waypoints, start, goal, blocked=blocked)
