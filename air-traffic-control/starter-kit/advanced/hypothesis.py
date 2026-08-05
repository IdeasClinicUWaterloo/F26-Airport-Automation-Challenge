"""Represent and score one possible aircraft route."""

# Multiplicative weight adjustments applied when a message supports or
# conflicts with a hypothesis's route.
SUPPORT_BOOST = 1.4
CONFLICT_PENALTY = 0.35


class RouteHypothesis:
    def __init__(self, route, weight=1.0, origin_message_id=None):
        self.route = list(route)
        self.weight = weight
        self.consistency_score = 0.0
        self.supporting = []
        self.conflicting = []
        # Index into `route` of the waypoint the aircraft is currently at/past.
        self._index = 0
        self.eta = None
        if origin_message_id is not None:
            self.supporting.append(origin_message_id)

    @property
    def current_waypoint(self):
        if 0 <= self._index < len(self.route):
            return self.route[self._index]
        return None

    @property
    def next_waypoint(self):
        if 0 <= self._index + 1 < len(self.route):
            return self.route[self._index + 1]
        return None

    def remaining_route(self):
        return self.route[self._index:]

    def _support(self, message_id):
        self.weight *= SUPPORT_BOOST
        self.consistency_score += 1
        if message_id is not None:
            self.supporting.append(message_id)

    def _conflict(self, message_id):
        self.weight *= CONFLICT_PENALTY
        self.consistency_score -= 1
        if message_id is not None:
            self.conflicting.append(message_id)

    def apply_waypoint_report(self, current_wp, next_wp, message_id=None):
        """Check a waypoint_report against this hypothesis's route. Returns True if
        consistent (and advances the route pointer), False if it conflicts."""

        expected_current = self.current_waypoint
        expected_next = self.next_waypoint

        if current_wp == expected_current and (next_wp is None or next_wp == expected_next):
            self._support(message_id)
            return True

        # Allow reports to advance beyond the currently stored route index.
        if current_wp in self.route:
            idx = self.route.index(current_wp)
            route_next = self.route[idx + 1] if idx + 1 < len(self.route) else None
            next_matches = next_wp is None or next_wp == route_next
            if idx >= self._index and next_matches:
                self._index = idx
                self._support(message_id)
                return True

        self._conflict(message_id)
        return False

    def matches_route_update(self, new_route):
        """Return True when an update keeps every waypoint already visited."""

        visited = self.route[: self._index + 1]
        return new_route[: len(visited)] == visited

    def apply_route_update(self, new_route, message_id=None):
        self.route = list(new_route)
        self._support(message_id)
