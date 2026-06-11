HOME = "YYZ"
BUFFER_MINUTES = 0

def get_gate_window(legs: list):
    """
    Determine the YYZ gate window using the order of the legs.
    Does not assume arrival at YYZ always happens before departure from YYZ.
    """

    yyz_events = []

    for leg in legs:
        if leg["arrivalStation"] == HOME:
            yyz_events.append({
                "kind": "arrival",
                "time": leg["arrival_min"],
            })

        if leg["departureStation"] == HOME:
            yyz_events.append({
                "kind": "departure",
                "time": leg["departure_min"],
            })

    if not yyz_events:
        return None, None

    if len(yyz_events) == 1:
        t = yyz_events[0]["time"]
        return t, t

    first = yyz_events[0]
    second = yyz_events[1]

    first_time = first["time"]
    second_time = second["time"]

    if second_time < first_time:
        second_time += 24 * 60

    return first_time, second_time


def gate_compatible(airplane_type: int, wingspan: int, jetbridge_required: bool, gate: dict) -> bool:
    """Check hard compatibility constraints between a flight and a gate."""
    if wingspan > gate["max_wingspan"]:
        return False

    if jetbridge_required and not gate["jetbridge"]:
        return False

    if airplane_type != gate["gate_type"]:
        return False

    return True


def check_time_conflict(
    gate_id: str,
    arrival_min: int,
    departure_min: int,
    gate_assignments: dict,
    ignore_flight_id: str | None = None,
) -> bool:
    """Check whether a buffered gate window conflicts with existing bookings."""

    for booking in gate_assignments.get(gate_id, []):
        if ignore_flight_id is not None and booking.get("flight_id") == ignore_flight_id:
            continue

        existing_start = booking["arrival_min"] - BUFFER_MINUTES
        existing_end = booking["departure_min"] + BUFFER_MINUTES

        if arrival_min <= existing_end and departure_min >= existing_start:
            return True

    return False


def determine_reassignment(flight_id: str, bookings: list, arrival_min: int, departure_min: int) -> str | None:
    """
    If there is a conflict, return the flight_id that should be reassigned.
    Rule: move the flight with the later latest time.
    """
    current_latest_time = max(arrival_min, departure_min)

    for booking in bookings:
        conflict = (
            arrival_min <= booking["departure_min"] + BUFFER_MINUTES
            and departure_min >= booking["arrival_min"] - BUFFER_MINUTES
        )

        if not conflict:
            continue

        booking_latest_time = max(
            booking["arrival_min"],
            booking["departure_min"]
        )

        if current_latest_time > booking_latest_time:
            return flight_id
        else:
            return booking["flight_id"]

    return None


def remove_booking(flight_id: str, gate_id: str, local_assignments: dict) -> dict | None:
    bookings = local_assignments.get(gate_id, [])

    for booking in list(bookings):
        if booking["flight_id"] == flight_id:
            bookings.remove(booking)
            return booking

    return None


def add_local_booking(local_assignments: dict, gate_id: str, flight_id: str, arrival_min: int, departure_min: int, legs: list):
    if gate_id not in local_assignments:
        local_assignments[gate_id] = []

    local_assignments[gate_id].append({
        "flight_id": flight_id,
        "arrival_min": arrival_min,
        "departure_min": departure_min,
        "legs": legs,
    })


def gate_optimization(legs: list, gate: dict) -> int:
    """Lower score is better."""
    score = 0

    airplane_type = legs[0]["airplane_type"]
    jetbridge_required = legs[0]["jetbridge_required"]
    wingspan = legs[0]["wingspan"]

    # Prefer not wasting a jetbridge on flights that do not need one.
    if not jetbridge_required and gate["jetbridge"]:
        score += 100

    # Prefer tighter wingspan fits and shorter walking distance.
    score += gate["max_wingspan"] - wingspan
    
    score += gate["dist"]

    return score


def find_best_gate(
    legs,
    arrival_min,
    departure_min,
    gates,
    local_assignments,
    ignore_flight_id: str | None = None,
    blocked_gate_ids: set[str] | None = None,
):
    best_gate_id = None
    best_score = None
    blocked_gate_ids = blocked_gate_ids or set()

    airplane_type = legs[0]["airplane_type"]
    wingspan = legs[0]["wingspan"]
    jetbridge_required = legs[0]["jetbridge_required"]

    for gate_id, gate in gates.items():
        if gate_id in blocked_gate_ids:
            continue

        if not gate_compatible(airplane_type, wingspan, jetbridge_required, gate):
            continue

        if check_time_conflict(gate_id, arrival_min, departure_min, local_assignments, ignore_flight_id):
            continue

        score = gate_optimization(legs, gate)

        if best_score is None or score < best_score:
            best_score = score
            best_gate_id = gate_id

    return best_gate_id


def find_cascade_gate(
    flight_id,
    legs,
    arrival_min,
    departure_min,
    gates,
    local_assignments,
    reassignments,
    flight_lookup,
    blocked_move_gate_ids: set[str] | None = None,
):
    """
    Find a gate by moving one conflicting flight somewhere else first.

    The returned gate is for flight_id. The moved flight's reassignment is
    appended before the caller appends flight_id's assignment/reassignment, so
    the evaluator processes the blocker move first.
    """
    best_gate_id = None
    best_score = None
    best_move = None
    blocked_move_gate_ids = blocked_move_gate_ids or set()

    airplane_type = legs[0]["airplane_type"]
    wingspan = legs[0]["wingspan"]
    jetbridge_required = legs[0]["jetbridge_required"]

    for gate_id, gate in gates.items():
        if not gate_compatible(airplane_type, wingspan, jetbridge_required, gate):
            continue

        if not check_time_conflict(gate_id, arrival_min, departure_min, local_assignments):
            continue

        flight_to_move = determine_reassignment(
            flight_id,
            local_assignments.get(gate_id, []),
            arrival_min,
            departure_min
        )

        if flight_to_move is None or flight_to_move == flight_id:
            continue

        score = gate_optimization(legs, gate)

        if best_score is None or score < best_score:
            best_score = score
            best_gate_id = gate_id
            best_move = flight_to_move

    if best_gate_id is None or best_move is None:
        return None

    removed_booking = remove_booking(best_move, best_gate_id, local_assignments)
    if removed_booking is None:
        return None

    moved_legs = removed_booking.get("legs")
    if moved_legs is None and best_move in flight_lookup:
        moved_legs = flight_lookup[best_move]["legs"]

    if moved_legs is None:
        local_assignments[best_gate_id].append(removed_booking)
        return None

    new_gate_id = find_best_gate(
        moved_legs,
        removed_booking["arrival_min"],
        removed_booking["departure_min"],
        gates,
        local_assignments,
        ignore_flight_id=best_move,
        blocked_gate_ids={best_gate_id, *blocked_move_gate_ids},
    )

    if new_gate_id is None:
        local_assignments[best_gate_id].append(removed_booking)
        return None

    add_local_booking(
        local_assignments,
        new_gate_id,
        best_move,
        removed_booking["arrival_min"],
        removed_booking["departure_min"],
        moved_legs,
    )
    reassignments.append((best_move, new_gate_id))

    return best_gate_id


def seed_local_assignments(gate_assignments: dict, assigned_flights: dict) -> dict:
    """Copy evaluator gate bookings and make sure each booking has legs if possible."""
    local_assignments = {}

    for gate_id, bookings in gate_assignments.items():
        local_assignments[gate_id] = []
        for booking in bookings:
            copied = dict(booking)
            flight_id = copied.get("flight_id")

            if not copied.get("legs") and flight_id in assigned_flights:
                copied["legs"] = assigned_flights[flight_id].get("legs", [])

            local_assignments[gate_id].append(copied)

    return local_assignments


def current_gate_still_valid(flight_id: str, gate_id: str, legs: list, arrival_min: int, departure_min: int, gates: dict, local_assignments: dict) -> bool:
    gate = gates[gate_id]

    if not gate_compatible(
        legs[0]["airplane_type"],
        legs[0]["wingspan"],
        legs[0]["jetbridge_required"],
        gate,
    ):
        return False

    return not check_time_conflict(
        gate_id,
        arrival_min,
        departure_min,
        local_assignments,
        ignore_flight_id=flight_id,
    )


def handle_changed_flights(changed_flights, gates, local_assignments, reassignments, flight_lookup):
    """Reassign already-assigned flights whose timing/equipment changed."""
    for flight_id, flight in changed_flights.items():
        legs = flight.get("legs", [])
        current_gate_id = flight.get("gate_id")

        if not legs or current_gate_id not in gates:
            continue

        arrival_min, departure_min = get_gate_window(legs)
        if arrival_min is None or departure_min is None:
            continue

        # Remove this flight's old local booking while evaluating its new state.
        old_booking = remove_booking(flight_id, current_gate_id, local_assignments)

        if current_gate_still_valid(
            flight_id,
            current_gate_id,
            legs,
            arrival_min,
            departure_min,
            gates,
            local_assignments,
        ):
            add_local_booking(local_assignments, current_gate_id, flight_id, arrival_min, departure_min, legs)
            continue

        # First try a direct move to a currently open compatible gate.
        new_gate_id = find_best_gate(
            legs,
            arrival_min,
            departure_min,
            gates,
            local_assignments,
            ignore_flight_id=flight_id,
        )

        # If no direct move is possible, try moving one blocker first. Do not put
        # the blocker into this flight's old gate because the evaluator processes
        # reassignments sequentially and the changed flight has not moved yet.
        if new_gate_id is None:
            new_gate_id = find_cascade_gate(
                flight_id,
                legs,
                arrival_min,
                departure_min,
                gates,
                local_assignments,
                reassignments,
                flight_lookup,
                blocked_move_gate_ids={current_gate_id},
            )

        if new_gate_id is None:
            # Restore old local booking so later decisions still see reality.
            if old_booking is not None:
                local_assignments.setdefault(current_gate_id, []).append(old_booking)
            print(f"ERROR: No reassignment gate found for updated flight {flight_id}")
            continue

        reassignments.append((flight_id, new_gate_id))
        add_local_booking(local_assignments, new_gate_id, flight_id, arrival_min, departure_min, legs)


def handle_waiting_flights(waiting_flights, gates, local_assignments, reassignments, flight_lookup):
    assignments = []

    for flight_id, flight in waiting_flights.items():
        legs = flight.get("legs", [])

        if not legs:
            continue

        arrival_min, departure_min = get_gate_window(legs)

        if arrival_min is None or departure_min is None:
            continue

        gate_id = find_best_gate(
            legs,
            arrival_min,
            departure_min,
            gates,
            local_assignments
        )

        if gate_id is None:
            gate_id = find_cascade_gate(
                flight_id,
                legs,
                arrival_min,
                departure_min,
                gates,
                local_assignments,
                reassignments,
                flight_lookup
            )

        if gate_id is None:
            print(f"ERROR: No compatible gate found for {flight_id}")
            continue

        assignments.append((flight_id, gate_id))
        add_local_booking(local_assignments, gate_id, flight_id, arrival_min, departure_min, legs)

    return assignments


def decide(observation):
    waiting_flights = observation.get("waiting_flights", {})
    changed_flights = observation.get("changed_flights", {})
    assigned_flights = observation.get("assigned_flights", {})
    gates = observation["gates"]
    gate_assignments = observation.get("gate_assignments", {})

    reassignments = []
    local_assignments = seed_local_assignments(gate_assignments, assigned_flights)

    flight_lookup = {}
    flight_lookup.update(assigned_flights)
    flight_lookup.update(waiting_flights)
    flight_lookup.update(changed_flights)

    # Updated assigned flights are the urgent ones; handle them before assigning
    # new waiting flights so the evaluator's post-update checks pass.
    handle_changed_flights(
        changed_flights,
        gates,
        local_assignments,
        reassignments,
        flight_lookup,
    )

    assignments = handle_waiting_flights(
        waiting_flights,
        gates,
        local_assignments,
        reassignments,
        flight_lookup,
    )

    return {
        "assignments": assignments,
        "reassignments": reassignments,
    }
