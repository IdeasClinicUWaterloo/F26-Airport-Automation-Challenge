HOME = "YYZ"

# def time_to_mins(hhmm: str) -> int:
#     """
#     Convert the time from midnight to minutes.
    
#     Returns time in minutes since midnight
#     """

#     h, m = hhmm.split(":")
#     return int(h)*60 + int (m)
   
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
        elif leg["departureStation"] == HOME:
            departure_min = leg["departure_min"]

    return (arrival_min, departure_min)


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
    return True

def check_time_conflict(gate_id: str, arrival_min: int, departure_min: int, gate_assignments: dict) -> bool:
    """
    Check whether a [arrival_min, departure_min] window conflicts with any
    existing booking at gate_id in gate_assignments.

    Returns True if there is a conflict, False otherwise.
    """
    for booking in gate_assignments.get(gate_id, []):
        if arrival_min <= booking["departure_min"] and departure_min >= booking["arrival_min"]:
            return True

    return False


def decide(observation):
    assignments = []
    reassignments = []

    waiting_flights = observation["waiting_flights"]
    gates = observation["gates"]
    gate_assignments = observation.get("gate_assignments", {})

    for flight_id, flight in waiting_flights.items():
        legs = flight["legs"]

        if not legs:
            continue

        # These fields are already parsed onto the leg dicts by the evaluator
        airplane_type     = legs[0]["airplane_type"]   # 1=domestic, 2=international
        wingspan          = legs[0]["wingspan"]
        jetbridge_required = legs[0]["jetbridge_required"]

        arrival_min, departure_min = get_gate_window(legs)

        if arrival_min is None and departure_min is None:
           continue
        

        for gate_id, gate in gates.items():
            if not gate_compatible(airplane_type, wingspan, jetbridge_required, gate):
                continue

            if check_time_conflict(gate_id, arrival_min, departure_min, gate_assignments):
                continue

            assignments.append((flight_id, gate_id))
            break

        else:
            print(f"ERROR: No compatible gate found for {flight_id}")

    return {"assignments": assignments, "reassignments": reassignments}