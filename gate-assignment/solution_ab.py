HOME = "YYZ"


def get_gate_window(legs: list):
    """
    Determine the gate occupancy window for a flight from its YYZ-relevant legs.

    Returns (arrival_min, departure_min) in minutes since midnight.

    Hint: look for a leg where arrivalStation == HOME (inbound)
          and a leg where departureStation == HOME (outbound).
    - Both inbound and outbound: occupied from inbound arrival to outbound departure
    - Inbound only: use arrival_min for both
    - Outbound only: use departure_min for both
    """

    arrival_min = None
    departure_min = None

    for leg in legs:
        if leg["arrivalStation"] == HOME:
            arrival_min = leg["arrival_min"]

        if leg["departureStation"] == HOME:
            departure_min = leg["departure_min"]

    print(f"arrival_min={arrival_min}, departure_min={departure_min}")

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

    if airplane_type != gate["gate_type"]:
        return False

    return True


def check_time_conflict(gate_id: str, arrival_min: int, departure_min: int, gate_assignments: dict) -> bool:
    """
    Check whether a [arrival_min, departure_min] window conflicts with any
    existing booking at gate_id in gate_assignments.

    Returns True if there is a conflict, False otherwise.
    """

    BUFFER = 90

    for booking in gate_assignments.get(gate_id, []):
        if arrival_min <= booking["departure_min"] + BUFFER and departure_min >= booking["arrival_min"] - BUFFER:
            return True

    return False


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