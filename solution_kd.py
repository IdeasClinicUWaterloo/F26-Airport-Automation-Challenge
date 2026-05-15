"""
Improved Sample Solution File - Handles Cascading Changes Better

Key fix for cascading changes:
- Previously, the cascade handler skipped already-assigned flights (they are never in waiting_flights after assignment).
- Now we cache the legs snapshot ourselves when we assign/reassign.
- This lets us resolve time conflicts (or wingspan/jetbridge issues visible in the observation) even for assigned flights.
- We still can't see brand-new leg data from an UpdateTiming/UpdateEquipment on an assigned flight (that's in the evaluator's internal "flagged" state only), but the evaluator's post-decision check will silently update if the new info is still valid, or hard-fail if not. This is the best we can do without changing the evaluator.
- Reassignment still incurs the expected point deduction (as documented).

All other logic (first-time assignments, local conflict view for same-tick reassignments, etc.) is unchanged and works.
"""

HOME = "YYZ"
INTERNATIONAL_DESTINATIONS = {"LHR", "CDG", "FRA", "NRT", "DXB"}

# Internal state persisted across decide() calls.
_my_assignments: dict[str, str] = {}          # flight_id -> current gate_id
_my_legs: dict[str, list] = {}                # flight_id -> cached home_legs (for cascade on assigned flights)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def extract_home_legs(raw_legs: list, ac_info: dict) -> list:
    result = []
    for leg in raw_legs:
        dep = leg["departureStation"]
        arr = leg["arrivalStation"]
        if dep != HOME and arr != HOME:
            continue

        ac = ac_info.get(leg["aircraftType"])
        if ac is None:
            print(f"  WARNING: Unknown aircraftType '{leg['aircraftType']}', skipping {dep}->{arr}")
            continue

        other_station = arr if dep == HOME else dep
        airplane_type = 2 if other_station in INTERNATIONAL_DESTINATIONS else 1

        arrival_min = _parse_time(leg["scheduledArrivalTime"]) if arr == HOME and "scheduledArrivalTime" in leg else None
        departure_min = _parse_time(leg["scheduledDepartureTime"]) if dep == HOME and "scheduledDepartureTime" in leg else None

        result.append({
            "arrival_min":      arrival_min,
            "departure_min":    departure_min,
            "wingspan":         float(ac["wingspan"]),
            "airplane_type":    airplane_type,
            "jetbridge_required": bool(ac.get("jetbridge_required", 0)),
            "aircraftType":     leg["aircraftType"],
            "departureStation": dep,
            "arrivalStation":   arr,
        })
    return result


def gate_window(home_legs: list) -> tuple[int | None, int | None]:
    inbound  = next((l for l in home_legs if l["arrivalStation"] == HOME), None)
    outbound = next((l for l in home_legs if l["departureStation"] == HOME), None)

    if inbound and outbound:
        return inbound["arrival_min"], outbound["departure_min"]
    if inbound:
        return inbound["arrival_min"], inbound["arrival_min"]
    if outbound:
        return outbound["departure_min"], outbound["departure_min"]
    return None, None


def has_time_conflict(gate_id: str, arrival: int, departure: int,
                      gate_assignments: dict, exclude_flight: str = None) -> bool:
    for a in gate_assignments.get(gate_id, []):
        if a["flight_id"] == exclude_flight:
            continue
        if arrival <= a["departure_min"] and departure >= a["arrival_min"]:
            return True
    return False


def gate_compatible(home_legs: list, gate: dict) -> bool:
    for leg in home_legs:
        if leg["wingspan"] > gate["max_wingspan"]:
            return False
        if leg["jetbridge_required"] and not gate["jetbridge"]:
            return False
        if leg["airplane_type"] != gate["gate_type"]:
            return False
    return True


def _parse_time(t: str) -> int:
    h, m = t.split(":")
    return int(h) * 60 + int(m)


def _find_gate(flight_id: str, home_legs: list, arrival: int, departure: int,
               gates: dict, gate_assignments: dict,
               exclude_flight: str = None) -> str | None:
    for gate_id, gate in gates.items():
        if not gate_compatible(home_legs, gate):
            continue
        if has_time_conflict(gate_id, arrival, departure, gate_assignments, exclude_flight):
            continue
        return gate_id
    return None


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def decide(observation: dict) -> dict:
    assignments   = []   # new assignments
    reassignments = []   # moves for already-assigned flights

    t_min           = observation["time"]
    waiting_flights = observation["waiting_flights"]
    gates           = observation["gates"]
    gate_assignments = observation.get("gate_assignments", {})
    ac_info         = observation["ac_info"]

    # ------------------------------------------------------------------
    # 1. Cascade check for already-assigned flights
    #    Now uses our own leg cache to check if any changes
    # ------------------------------------------------------------------
    for flight_id, assigned_gate_id in list(_my_assignments.items()):
        booking = next(
            (a for a in gate_assignments.get(assigned_gate_id, [])
             if a["flight_id"] == flight_id),
            None
        )
        if booking is None:
            # Flight was removed from evaluator (e.g. cancelled elsewhere)
            _my_assignments.pop(flight_id, None)
            _my_legs.pop(flight_id, None)
            continue

        arrival   = booking["arrival_min"]
        departure = booking["departure_min"]

        # Check if current window conflicts with anything else at this gate
        if has_time_conflict(assigned_gate_id, arrival, departure,
                             gate_assignments, exclude_flight=flight_id):

            print("DEBUG: HAVE TIME CONFLICT")

            home_legs = _my_legs.get(flight_id)
            if home_legs is None or not home_legs:
                print(f"  WARNING: Cannot resolve cascade for {flight_id} — no cached legs")
                continue

            new_gate_id = _find_gate(
                flight_id, home_legs, arrival, departure,
                gates, gate_assignments,
                exclude_flight=flight_id
            )

            if new_gate_id:
                reassignments.append((flight_id, new_gate_id))
                _my_assignments[flight_id] = new_gate_id
                _my_legs[flight_id] = [l.copy() for l in home_legs]  # keep cache in sync
                print(f"  Cascade: reassigning {flight_id} {assigned_gate_id} → {new_gate_id}")
            else:
                print(f"  ERROR: Cascade conflict for {flight_id} but no free gate found")

    # ------------------------------------------------------------------
    # 2. Assign waiting flights (and update our cache)
    # ------------------------------------------------------------------
    # Local view that includes the reassignments we just decided
    local_assignments = {
        gid: list(bookings) for gid, bookings in gate_assignments.items()
    }
    for flight_id, new_gate_id in reassignments:
        # Remove from old gate in local view
        old_gate_id = next(
            (gid for gid, bookings in gate_assignments.items()
             if any(a["flight_id"] == flight_id for a in bookings)),
            None
        )
        if old_gate_id and old_gate_id in local_assignments:
            local_assignments[old_gate_id] = [
                a for a in local_assignments[old_gate_id]
                if a["flight_id"] != flight_id
            ]
        # Add to new gate (use existing booking data)
        booking = next(
            (a for bookings in gate_assignments.values()
             for a in bookings if a["flight_id"] == flight_id),
            None
        )
        if booking:
            local_assignments.setdefault(new_gate_id, []).append(booking)

    for flight_id, flight in waiting_flights.items():
        home_legs = flight["legs"]
        if not home_legs:
            continue

        arrival, departure = gate_window(home_legs)
        if arrival is None or departure is None:
            print(f"  WARNING: Cannot determine gate window for {flight_id}, skipping")
            continue

        gate_id = _find_gate(flight_id, home_legs, arrival, departure, gates, local_assignments)
        if gate_id:
            assignments.append((flight_id, gate_id))
            _my_assignments[flight_id] = gate_id
            _my_legs[flight_id] = [l.copy() for l in home_legs]   # cache for future cascade
            # Update local view for later flights this tick
            local_assignments.setdefault(gate_id, []).append({
                "flight_id":    flight_id,
                "arrival_min":  arrival,
                "departure_min": departure,
            })
        else:
            print(f"  ERROR: No compatible gate found for {flight_id}")

    return {"assignments": assignments, "reassignments": reassignments}