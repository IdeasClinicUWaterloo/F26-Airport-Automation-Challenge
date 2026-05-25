HOME = "YYZ"

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

        for gate_id, gate in gates.items():

            # --- Hard compatibility checks ---
            if wingspan > gate["max_wingspan"]:
                continue
            if jetbridge_required and not gate["jetbridge"]:
                continue
            if airplane_type == 2 and gate["gate_type"] != 2:
                continue
            if airplane_type == 1 and gate["gate_type"] != 1:
                continue

            assignments.append((flight_id, gate_id))
            break

        else:
            print(f"ERROR: No compatible gate found for {flight_id}")

    return {"assignments": assignments, "reassignments": reassignments}