HOME = "YYZ"


def get_gate_window(legs: list):
    """
    Determine the gate occupancy window for a flight from its YYZ-relevant legs.

    Returns (arrival_min, departure_min) in minutes since midnight.
    """

    arrival_min = None
    departure_min = None

    for leg in legs:
        if leg["arrivalStation"] == HOME:
            arrival_min = leg["arrival_min"]

        if leg["departureStation"] == HOME:
            departure_min = leg["departure_min"]

    if arrival_min is not None and departure_min is not None:
        return (min(arrival_min, departure_min), max(arrival_min, departure_min))

    if arrival_min is not None:
        return (arrival_min, arrival_min)

    if departure_min is not None:
        return (departure_min, departure_min)

    return (None, None)


def gate_compatible(airplane_type: int, wingspan: int, jetbridge_required: bool, gate: dict) -> bool:
    """
    Check hard compatibility constraints between a flight and a gate.

    Gate dict contains: gate_type, max_wingspan, jetbridge, dist
    airplane_type: 0=cargo, 1=domestic, 2=international

    Returns True if the gate can accept this flight, False otherwise.
    """

    if wingspan > gate["max_wingspan"]:
        return False

    if jetbridge_required and not gate["jetbridge"]:
        return False

    if airplane_type == 2 and gate["gate_type"] != 2:
        return False
    
    if airplane_type == 1 and gate["gate_type"] != 1:
        return False
    
    if airplane_type == 0 and gate["gate_type"] != 0:
        return False

    return True


def check_time_conflict(gate_id: str, arrival_min: int, departure_min: int, gate_assignments: dict) -> bool:
    """
    Check whether a [arrival_min, departure_min] window conflicts with any
    existing booking at gate_id in gate_assignments.

    Returns True if there is a conflict, False otherwise.
    """

    BUFFER = 0

    for booking in gate_assignments.get(gate_id, []):
        if arrival_min <= booking["departure_min"] + BUFFER and departure_min >= booking["arrival_min"] - BUFFER:
            return True

    return False

def determine_reassignment(flight_id:str, bookings: list, arrival_min: int, departure_min: int) -> str:
    #if there is a conflict, determine which flight to reassign based on timing, and gate compatibility, returning the flight_id to reassign
    
    current_latest_time = max(arrival_min, departure_min)

    for booking in bookings:
        conflict = (arrival_min <= booking["departure_min"] and 
                    departure_min >= booking["arrival_min"])

        if not conflict:
            continue

        booking_latest_time = max(booking["arrival_min"], booking["departure_min"])

        if current_latest_time > booking_latest_time:
            return flight_id
        else:
            return booking["flight_id"]

    return None

def remove_booking(flight_id: str, gate_id: str, local_assignments: dict) -> dict | None:

    bookings = local_assignments.get(gate_id, [])

    for booking in bookings:
        if booking["flight_id"] == flight_id:
            bookings.remove(booking)
            return booking
        
    return None

def gate_optimization(legs: list, gate: dict) -> int:
    score = 0

    jetbridge_required = legs[0]["jetbridge_required"]
    wingspan = legs[0]["wingspan"]

    # Score 1: avoid wasting jetbridge gates
    if not jetbridge_required and gate["jetbridge"]:
        score += 100

    # Score 2: prefer smallest gate that still fits
    score += gate["max_wingspan"] - wingspan

    # Score 3: prefer closer gate
    score += gate["dist"]

    return score


def find_best_gate(legs, arrival_min, departure_min, gates, local_assignments):
    best_gate_id = None
    best_score = None

    airplane_type = legs[0]["airplane_type"]   # 0=cargo, 1=domestic, 2=international
    wingspan = legs[0]["wingspan"]
    jetbridge_required = legs[0]["jetbridge_required"]

    for gate_id, gate in gates.items():
        if not gate_compatible(airplane_type, wingspan, jetbridge_required, gate):
            continue

        if check_time_conflict(gate_id, arrival_min, departure_min, local_assignments):
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
    flight_lookup
):
    best_gate_id = None
    best_score = None
    best_move = None

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

        if flight_to_move is None:
            continue

        # If the rule says the current flight should move, this gate does not help us.
        if flight_to_move == flight_id:
            continue

        score = gate_optimization(legs, gate)

        if best_score is None or score < best_score:
            best_score = score
            best_gate_id = gate_id
            best_move = flight_to_move

    if best_gate_id is None or best_move is None:
        return None

    removed_booking = remove_booking(
        best_move,
        best_gate_id,
        local_assignments
    )

    if removed_booking is None:
        return None

    moved_flight = flight_lookup[best_move]
    moved_legs = moved_flight["legs"]

    best_gate_id = find_best_gate(
        moved_legs,
        removed_booking["arrival_min"],
        removed_booking["departure_min"],
        gates,
        local_assignments
    )

    if best_gate_id is None:
        # Put it back because cascade failed.
        local_assignments[best_gate_id].append(removed_booking)
        return None

    if best_gate_id not in local_assignments:
        local_assignments[best_gate_id] = []

    local_assignments[best_gate_id].append(removed_booking)
    reassignments.append((best_move, best_gate_id))

    return best_gate_id


def decide(observation):
    assignments = []
    reassignments = []

    waiting_flights = observation["waiting_flights"]
    gates = observation["gates"]
    gate_assignments = observation.get("gate_assignments", {})

    local_assignments = {
        gate_id: list(bookings)
        for gate_id, bookings in gate_assignments.items()
    }

    flight_lookup = {
        flight_id : flight
        for flight_id, flight in waiting_flights.items()
    }

    for flight_id, flight in waiting_flights.items():
        legs = flight["legs"]

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

        if gate_id not in local_assignments:
            local_assignments[gate_id] = []

        local_assignments[gate_id].append({
            "flight_id": flight_id,
            "arrival_min": arrival_min,
            "departure_min": departure_min,
        })

    return {
        "assignments": assignments,
        "reassignments": reassignments
    }