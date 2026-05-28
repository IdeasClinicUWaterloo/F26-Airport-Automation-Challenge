"""
Public Evaluator Script for Solution File - V2
Handles JSON-based flight schedules, per-message simulation, and gate reassignment.
"""
import json
import sys
import importlib
from collections import defaultdict

from scripts.validation import validate_static_info_json, validate_flight_schedule_json

# -------------------------
# Constants
# -------------------------
HOME = "YYZ"
INTERNATIONAL_DESTINATIONS = ["LHR", "CDG", "FRA", "NRT", "DXB"]

# -------------------------
# Utilities
# -------------------------
def hhmm_to_min(hhmm: int) -> int:
    """Convert HHMM integer (e.g. 1430) to minutes since midnight (e.g. 870)."""
    hh = hhmm // 100
    mm = hhmm % 100
    return hh * 60 + mm

def time_str(t_min: int) -> str:
    """Format minutes since midnight as HH:MM string.

    If a normalized gate window rolls past midnight, show the day offset.
    Example: 1500 minutes -> 01:00+1d.
    """
    day_offset = t_min // (24 * 60)
    minute_of_day = t_min % (24 * 60)
    base = f"{minute_of_day // 60:02d}:{minute_of_day % 60:02d}"
    return f"{base}+{day_offset}d" if day_offset else base

def fail(reason, t_min=None):
    t = f"  Time of Failure: {time_str(t_min)}" if t_min is not None else "  Time of Failure: N/A"
    print(f"\nSIMULATION FAILED :: {reason}")
    print(t)
    sys.exit(1)

def negative(reason, t_min=None):
    t = f"(Time: {time_str(t_min)})" if t_min is not None else "(Time: N/A)"
    output = f"Point Deduction: {reason}  {t}"
    return output

# -------------------------
# Flight ID Helper
# -------------------------
def make_flight_id(carrier: str, flight_number: str, originating_date: str, suffix=None) -> str:
    """
    Build a canonical flight ID string.
    e.g. "AC-123-2025-06-15" or "AC-123A-2025-06-15" if suffix present.
    """
    fn = flight_number + (suffix if suffix else "")
    return f"{carrier}-{fn}-{originating_date}"

# -------------------------
# Load Static Info
# -------------------------
def load_static_info(path: str):
    """
    Load gate_info and aircraft_info from static_info.json.
    Returns (gates dict, aircraft_info dict).
    """
    if not validate_static_info_json(path):
        fail("Static Info JSON validation failed.")

    with open(path, "r") as f:
        data = json.load(f)

    gates = data["gate_info"]
    aircraft_info = data["aircraft_info"]
    return gates, aircraft_info

# -------------------------
# Load Flight Schedule
# -------------------------
def load_flight_schedule(path: str) -> dict:
    """
    Load flight_info.json.
    Returns a dict keyed by info_time (int minutes since midnight),
    each value being a list of flight message dicts.

    Expected JSON structure:
    {
      "HHMM": [ { action, flight, legs, ... }, ... ],
      ...
    }
    """
    if not validate_flight_schedule_json(path):
        fail("Flight Schedule JSON validation failed.")

    with open(path, "r") as f:
        raw = json.load(f)

    # Convert "HHMM" string keys to integer minutes
    schedule = {}
    for time_key, messages in raw.items():
        t_min = hhmm_to_min(int(time_key))
        schedule[t_min] = messages

    return schedule

# -------------------------
# Determine Airplane Type from Route
# -------------------------
def get_airplane_type(departure_station: str, arrival_station: str, aircraft_record: dict | None = None) -> int:
    """
    Determine airplane/gate category.

    Returns:
    - 0: Cargo
    - 1: Domestic passenger
    - 2: International passenger

    Cargo is inferred first from aircraft_info if the static data provides any
    common cargo/type flag. If no cargo/type metadata is present, the passenger
    type falls back to route-based domestic/international classification.
    """
    if aircraft_record:
        # Explicit integer/string category fields, if present in static_info.json.
        for key in ("airplane_type", "aircraft_type", "gate_type", "flight_type", "type"):
            if key not in aircraft_record:
                continue
            value = aircraft_record[key]

            if isinstance(value, int) and value in (0, 1, 2):
                return value

            if isinstance(value, str):
                normalized = value.strip().lower()
                if normalized in ("0", "cargo", "freighter", "freight"):
                    return 0
                if normalized in ("1", "domestic", "passenger_domestic"):
                    return 1
                if normalized in ("2", "international", "passenger_international"):
                    return 2

        # Boolean cargo flags, if present.
        for key in ("cargo", "is_cargo", "isCargo", "freighter", "is_freighter"):
            if bool(aircraft_record.get(key, False)):
                return 0

    other = arrival_station if departure_station == HOME else departure_station
    if other in INTERNATIONAL_DESTINATIONS:
        return 2
    return 1

# -------------------------
# Parse Leg for YYZ Relevance
# -------------------------
def extract_yyiz_legs(legs: list, aircraft_info: dict) -> list:
    """
    Extract legs that are relevant to YYZ gate assignment:
    - Inbound leg: arrivalStation == YYZ
    - Outbound leg: departureStation == YYZ

    Returns a list of dicts with normalized fields:
    {
        "arrival_min": int,       # minutes since midnight (arrival at YYZ, or None for outbound)
        "departure_min": int,     # minutes since midnight (departure from YYZ, or None for inbound)
        "wingspan": float,
        "airplane_type": int,     # 0 cargo, 1 domestic, 2 international
        "jetbridge_required": bool,
        "aircraftType": str
    }

    For gate occupancy:
    - Inbound only: gate occupied from arrival until some reasonable turnaround (or next outbound if multi-leg)
    - Outbound only: gate occupied from some prep time until departure
    - Both inbound+outbound on same aircraft: gate occupied from arrival_min to departure_min

    NOTE: The caller is responsible for pairing inbound/outbound legs if they share an aircraft.
    This function just returns each relevant leg.
    """
    results = []
    for leg in legs:
        dep = leg["departureStation"]
        arr = leg["arrivalStation"]
        aircraft_code = leg["aircraftType"]

        ac = aircraft_info.get(aircraft_code)
        if ac is None:
            # Unknown aircraft type - skip with warning
            print(f"  WARNING: Unknown aircraftType '{aircraft_code}', skipping leg {dep}->{arr}")
            continue

        wingspan = float(ac["wingspan"])
        jetbridge_required = bool(ac.get("jetbridge_required", 0))

        if arr == HOME or dep == HOME:
            airplane_type = get_airplane_type(dep, arr, ac)
            
            arrival_min = hhmm_to_min(int(leg["scheduledArrivalTime"].replace(":", ""))) if arr == HOME else None
            departure_min = hhmm_to_min(int(leg["scheduledDepartureTime"].replace(":", ""))) if dep == HOME else None

            results.append({
                "arrival_min": arrival_min,
                "departure_min": departure_min,
                "wingspan": wingspan,
                "airplane_type": airplane_type,
                "jetbridge_required": jetbridge_required,
                "aircraftType": aircraft_code,
                "departureStation": dep,
                "arrivalStation": arr,
            })

    return results

# -------------------------
# Check Gate Time Conflict
# -------------------------
def check_time_conflict(gate_id: str, arrival: int, departure: int, gate_assignments: dict) -> bool:
    """
    Returns True if the [arrival, departure] window overlaps with any existing
    assignment at gate_id.
    """
    if gate_id not in gate_assignments:
        return False
    
    for assignment in gate_assignments[gate_id]:
        # Check for overlapping time windows
        if arrival <= assignment["departure_min"] and departure >= assignment["arrival_min"]:
            return True
    
    return False

# -------------------------
# Process a Single Flight Message
# -------------------------
def process_message(msg: dict, t_min: int, aircraft_info: dict,
                    known_flights: dict, waiting_flights: dict):
    """
    Apply a flight schedule message to the known_flights and waiting_flights state.

    known_flights: flight_id -> current flight state dict (latest info)
    waiting_flights: flight_id -> flight state dict (only unassigned flights)

    Flight state dict:
    {
        "flight_id": str,
        "action": str,          # last action applied
        "legs": list,           # parsed YYZ-relevant legs
        "cancelled": bool,
        "info_time": int,       # t_min when this info was received
    }
    """
    action = msg.get("action")
    flight_meta = msg.get("flight", {})
    carrier = flight_meta.get("carrier", "")
    flight_number = flight_meta.get("flightNumber", "")
    suffix = flight_meta.get("flightSuffix")
    orig_date = flight_meta.get("originatingDate", "")
    flight_id = make_flight_id(carrier, flight_number, orig_date, suffix)

    raw_legs = msg.get("legs", [])
    yyiz_legs = extract_yyiz_legs(raw_legs, aircraft_info)

    if action == "CreateFlight":
        if flight_id in known_flights:
            print(f"  WARNING: CreateFlight for already-known {flight_id} at {time_str(t_min)}, treating as replace.")
        state = {
            "flight_id": flight_id,
            "action": action,
            "legs": yyiz_legs,           # evaluator uses this
            "all_legs": raw_legs,        # solution gets this
            "cancelled": False,
            "info_time": t_min,
        }
        known_flights[flight_id] = state
        if yyiz_legs:
            waiting_flights[flight_id] = state

    elif action == "ReplaceFlight":
        state = known_flights.get(flight_id, {"flight_id": flight_id, "cancelled": False})
        state.update({
            "action": action,
            "legs": yyiz_legs,
            "all_legs": raw_legs,
            "cancelled": False,
            "info_time": t_min,
        })
        known_flights[flight_id] = state
        if yyiz_legs and flight_id in waiting_flights:
            waiting_flights[flight_id] = state  # Update waiting with new info

    elif action == "UpdateTiming":
        if flight_id not in known_flights:
            print(f"  WARNING: UpdateTiming for unknown flight {flight_id} at {time_str(t_min)}, ignoring.")
            return None
        state = known_flights[flight_id]
        # Only update timing (arrival/departure mins) from new legs, keep rest
        state["legs"] = yyiz_legs
        state["all_legs"] = raw_legs
        state["info_time"] = t_min
        state["action"] = action
        if flight_id in waiting_flights:
            waiting_flights[flight_id] = state

    elif action == "CancelFlight":
        if flight_id in known_flights:
            known_flights[flight_id]["cancelled"] = True
            known_flights[flight_id]["action"] = action
        waiting_flights.pop(flight_id, None)  # Remove from waiting

    elif action == "ReinstateFlight":
        if flight_id not in known_flights:
            print(f"  WARNING: ReinstateFlight for unknown flight {flight_id} at {time_str(t_min)}, ignoring.")
            return None
        state = known_flights[flight_id]
        state["cancelled"] = False
        state["action"] = action
        if state.get("legs"):
            waiting_flights[flight_id] = state

    elif action == "UpdateEquipment":
        if flight_id not in known_flights:
            print(f"  WARNING: UpdateEquipment for unknown flight {flight_id} at {time_str(t_min)}, ignoring.")
            return None
        # Re-parse legs with updated aircraft type
        state = known_flights[flight_id]
        state["legs"] = yyiz_legs
        state["all_legs"] = raw_legs
        state["info_time"] = t_min
        state["action"] = action
        if flight_id in waiting_flights:
            waiting_flights[flight_id] = state

    else:
        print(f"  WARNING: Unknown action '{action}' for {flight_id} at {time_str(t_min)}, ignoring.")
        return None

    return flight_id

# -------------------------
# Simulation
# -------------------------

deductions = []

def run_sim(static_info: str, flight_schedule: str, solution_module: str):
    gates, aircraft_info = load_static_info(static_info)
    schedule = load_flight_schedule(flight_schedule)

    gate_assignments = defaultdict(list)
    flight_assignments = {}
    known_flights = {}
    waiting_flights = {}

    solution = importlib.import_module(solution_module)

    sorted_times = sorted(schedule.keys())
    print(f"Starting simulation: {len(sorted_times)} message event(s) across "
          f"{time_str(sorted_times[0])} to {time_str(sorted_times[-1])}\n")

    for t_min in sorted_times:
        messages = schedule[t_min]
        print(f"--- t={time_str(t_min)} | {len(messages)} message(s) ---")

        # ----------------------------------------------------------------
        # 1. Process incoming messages
        # ----------------------------------------------------------------
        updated_flight_ids = []
        for msg in messages:
            fid = process_message(msg, t_min, aircraft_info, known_flights, waiting_flights)
            if fid:
                updated_flight_ids.append(fid)

        # ----------------------------------------------------------------
        # 2. Identify assigned flights whose info changed (flagged for later check)
        #    We record what changed but do NOT fail yet — solution gets first crack.
        # ----------------------------------------------------------------
        flagged = {}   # fid -> {"old_snap": [...], "new_legs": [...]}
        for fid in updated_flight_ids:
            if fid not in flight_assignments:
                continue
            state = known_flights[fid]
            if state["cancelled"]:
                # Cancellation of an assigned flight is an immediate hard fail —
                # the solution cannot meaningfully "handle" this mid-tick since
                # there is no gate to free up via reassignment.
                fail(
                    f"Flight {fid} was CANCELLED after being assigned to gate "
                    f"{flight_assignments[fid]['gate_id']}. "
                    f"Solution must handle CancelFlight by unassigning the gate.",
                    t_min
                )

            old_snap = flight_assignments[fid]["legs_snapshot"]
            new_legs = state["legs"]
            changed = False
            if len(old_snap) != len(new_legs):
                changed = True
            else:
                for old_leg, new_leg in zip(old_snap, new_legs):
                    if (old_leg.get("arrival_min") != new_leg.get("arrival_min") or
                        old_leg.get("departure_min") != new_leg.get("departure_min") or
                        old_leg.get("wingspan") != new_leg.get("wingspan") or
                        old_leg.get("jetbridge_required") != new_leg.get("jetbridge_required") or
                        old_leg.get("airplane_type") != new_leg.get("airplane_type") or
                        old_leg.get("aircraftType") != new_leg.get("aircraftType") or
                        old_leg.get("departureStation") != new_leg.get("departureStation") or
                        old_leg.get("arrivalStation") != new_leg.get("arrivalStation")):
                        changed = True
                        break

            if changed:
                flagged[fid] = {
                    "old_snap": old_snap,
                    "new_legs": new_legs,
                }

        # ----------------------------------------------------------------
        # 3. Build observation for solution
        #    Includes updated info so solution can make informed reassignments.
        # ----------------------------------------------------------------

        # sync updated timing into gate_assignments before snapshot
        for fid, flag_info in flagged.items():
            new_legs = flag_info["new_legs"]
            new_arrival, new_departure = _gate_window(new_legs)
            if new_arrival is None or new_departure is None:
                continue
            assigned_gate_id = flight_assignments[fid]["gate_id"]
            for a in gate_assignments[assigned_gate_id]:
                if a["flight_id"] == fid:
                    a["arrival_min"] = new_arrival
                    a["departure_min"] = new_departure
                    a["legs"] = [l.copy() for l in new_legs]
                    break
        
        waiting_snapshot = {
            fid: {
                "flight_id": fid,
                "legs": state["legs"],
                "info_time": state["info_time"],
            }
            for fid, state in waiting_flights.items()
        }

        changed_snapshot = {
            fid: {
                "flight_id": fid,
                "gate_id": flight_assignments[fid]["gate_id"],
                "legs": known_flights[fid]["legs"],
                "old_legs": flag_info["old_snap"],
                "info_time": known_flights[fid]["info_time"],
            }
            for fid, flag_info in flagged.items()
        }

        assigned_snapshot = {
            fid: {
                "flight_id": fid,
                "gate_id": assignment["gate_id"],
                "legs": known_flights.get(fid, {}).get("legs", assignment["legs_snapshot"]),
                "info_time": known_flights.get(fid, {}).get("info_time"),
            }
            for fid, assignment in flight_assignments.items()
        }

        observation = {
            "time": t_min,
            "waiting_flights": waiting_snapshot,
            "changed_flights": changed_snapshot,
            "assigned_flights": assigned_snapshot,
            "gates": {
                gid: {
                    "gate_type": g["gate_type"],
                    "max_wingspan": g["max_wingspan"],
                    "dist": g["dist"],
                    "jetbridge": g["jetbridge"],
                }
                for gid, g in gates.items()
            },
            "gate_assignments": {
                gid: [
                    {
                        "flight_id": a["flight_id"],
                        "arrival_min": a["arrival_min"],
                        "departure_min": a["departure_min"],
                        "legs": [l.copy() for l in a.get("legs", [])],
                    }
                    for a in assignments
                ]
                for gid, assignments in gate_assignments.items()
            },
            "ac_info": aircraft_info,
        }

        # ----------------------------------------------------------------
        # 4. Get solution decisions
        # ----------------------------------------------------------------
        actions = solution.decide(observation)
        assignments_out = actions.get("assignments", [])
        reassignments_out = actions.get("reassignments", [])

        # ----------------------------------------------------------------
        # 5. Process reassignments (same logic as original, unchanged)
        # ----------------------------------------------------------------
        for flight_id, new_gate_id in reassignments_out:
            if flight_id not in flight_assignments:
                fail(f"Attempted to reassign flight {flight_id} which is not currently assigned.", t_min)

            if new_gate_id not in gates:
                fail(f"Invalid gate ID in reassignment: {new_gate_id}", t_min)

            old_assignment = flight_assignments[flight_id]
            old_gate_id = old_assignment["gate_id"]

            state = known_flights.get(flight_id, {})
            legs = state.get("legs", old_assignment["legs_snapshot"])

            arrival_min, departure_min = _gate_window(legs)
            if arrival_min is None or departure_min is None:
                fail(f"Cannot determine gate window for reassignment of {flight_id}.", t_min)

            new_gate = gates[new_gate_id]

            if check_time_conflict(new_gate_id, arrival_min, departure_min, gate_assignments):
                fail(
                    f"Reassignment conflict: Gate {new_gate_id} already occupied during "
                    f"[{time_str(arrival_min)}, {time_str(departure_min)}] for flight {flight_id}.",
                    t_min
                )

            if legs[0]["wingspan"] > new_gate["max_wingspan"]:
                fail(
                    f"Wingspan violation on reassignment: Flight {flight_id} "
                    f"({legs[0]['wingspan']}m) -> Gate {new_gate_id} (max {new_gate['max_wingspan']}m).",
                    t_min
                )

            # Remove old gate entry
            gate_assignments[old_gate_id] = [
                a for a in gate_assignments[old_gate_id]
                if a["flight_id"] != flight_id
            ]
            # Add new gate entry
            gate_assignments[new_gate_id].append({
                "flight_id": flight_id,
                "arrival_min": arrival_min,
                "departure_min": departure_min,
                "assigned_at": t_min,
                "legs": [l.copy() for l in legs],
            })
            flight_assignments[flight_id] = {
                "gate_id": new_gate_id,
                "assignment_time": t_min,
                "legs_snapshot": [l.copy() for l in legs],
            }
            waiting_flights.pop(flight_id, None)

            _apply_soft_penalties(flight_id, legs, new_gate_id, new_gate, t_min)

            is_changed_flight = flight_id in flagged

            if arrival_min <= t_min:
                deductions.append(negative(
                    f"Flight {flight_id} reassigned from {old_gate_id} to {new_gate_id} "
                    f"AFTER arrival (plane already at gate)", t_min
                ))
            elif not is_changed_flight:
                deductions.append(negative(
                    f"Flight {flight_id} reassigned from {old_gate_id} to {new_gate_id}", t_min
                ))
            else:
                print(
                    f"  ℹ Reassignment for {flight_id} was caused by updated flight info; "
                    f"no deduction."
                )

            print(f"  ↺ Reassigned {flight_id}: {old_gate_id} → {new_gate_id} "
                  f"[{_gate_window_label(legs)}]")

        # ----------------------------------------------------------------
        # 6. Process new assignments (unchanged from original)
        # ----------------------------------------------------------------
        for flight_id, gate_id in assignments_out:
            if gate_id not in gates:
                fail(f"Invalid gate ID: {gate_id}", t_min)

            if flight_id not in waiting_flights:
                fail(
                    f"Attempted to assign flight {flight_id} which is not in the waiting list. "
                    f"(Already assigned or not yet received / cancelled.)",
                    t_min
                )

            gate = gates[gate_id]
            state = waiting_flights[flight_id]
            legs = state["legs"]

            arrival_min, departure_min = _gate_window(legs)
            if arrival_min is None or departure_min is None:
                fail(
                    f"Flight {flight_id} has no determinable gate occupancy window. "
                    f"Check that it has at least one YYZ-relevant leg with times.",
                    t_min
                )

            if check_time_conflict(gate_id, arrival_min, departure_min, gate_assignments):
                fail(
                    f"Gate {gate_id} double-booked: time conflict for flight {flight_id}. "
                    f"Window: [{time_str(arrival_min)}, {time_str(departure_min)}]",
                    t_min
                )

            wingspan = legs[0]["wingspan"]
            if wingspan > gate["max_wingspan"]:
                fail(
                    f"Wingspan violation: Flight {flight_id} ({wingspan}m) "
                    f"assigned to Gate {gate_id} (max {gate['max_wingspan']}m)",
                    t_min
                )

            _apply_soft_penalties(flight_id, legs, gate_id, gate, t_min)

            gate_assignments[gate_id].append({
                "flight_id": flight_id,
                "arrival_min": arrival_min,
                "departure_min": departure_min,
                "assigned_at": t_min,
                "legs": [l.copy() for l in legs],
            })
            flight_assignments[flight_id] = {
                "gate_id": gate_id,
                "assignment_time": t_min,
                "legs_snapshot": [l.copy() for l in legs],
            }
            waiting_flights.pop(flight_id)

            print(f"  ✓ Assigned {flight_id} → {gate_id}  "
                  f"[{_gate_window_label(legs)}]")

        # ----------------------------------------------------------------
        # 7. Post-decision cascade check on flagged flights
        #
        #    For each flight whose info changed this tick:
        #      - If the solution already reassigned it → skip (handled)
        #      - If gate is still valid with new window → silently update records
        #      - If gate is now invalid → hard fail (solution had its chance)
        # ----------------------------------------------------------------
        for fid, flag_info in flagged.items():
            new_legs = flag_info["new_legs"]
            assigned_gate_id = flight_assignments[fid]["gate_id"]
            gate = gates[assigned_gate_id]

            new_arrival, new_departure = _gate_window(new_legs)
            if new_arrival is None or new_departure is None:
                # Can't validate — skip (edge case, outbound-only flights)
                continue

            # Hard: wingspan now violates gate
            if new_legs[0]["wingspan"] > gate["max_wingspan"]:
                fail(
                    f"Flight {fid} equipment change makes gate {assigned_gate_id} invalid "
                    f"(wingspan {new_legs[0]['wingspan']}m > max {gate['max_wingspan']}m). "
                    f"Solution must reassign via reassignments list.",
                    t_min
                )

            # Hard: jetbridge now required but gate doesn't have one
            if new_legs[0]["jetbridge_required"] and not gate["jetbridge"]:
                fail(
                    f"Flight {fid} now requires jetbridge but gate {assigned_gate_id} has none. "
                    f"Solution must reassign via reassignments list.",
                    t_min
                )

            # Hard: new window conflicts with another flight at the same gate
            other_at_gate = [
                a for a in gate_assignments[assigned_gate_id]
                if a["flight_id"] != fid
            ]
            temp_check = defaultdict(list)
            temp_check[assigned_gate_id] = other_at_gate
            if check_time_conflict(assigned_gate_id, new_arrival, new_departure, temp_check):
                fail(
                    f"Flight {fid} timing update creates a gate conflict at {assigned_gate_id} "
                    f"(new window [{time_str(new_arrival)}, {time_str(new_departure)}]). "
                    f"Solution must reassign the affected flight via reassignments list.",
                    t_min
                )

            # Gate is still valid — silently update the snapshot and gate record
            flight_assignments[fid]["legs_snapshot"] = [l.copy() for l in new_legs]
            for a in gate_assignments[assigned_gate_id]:
                if a["flight_id"] == fid:
                    a["arrival_min"] = new_arrival
                    a["departure_min"] = new_departure
                    a["legs"] = [l.copy() for l in new_legs]
                    break

            print(f"  ↻ Updated snapshot for {fid} at {assigned_gate_id} "
                  f"[{_gate_window_label(new_legs)}] (no conflict)")

    # ----------------------------------------------------------------
    # FINAL CHECKS (unchanged)
    # ----------------------------------------------------------------
    print()
    for d in deductions:
        print(d)

    print("\n" + "=" * 60)

    unassigned = [
        fid for fid, state in known_flights.items()
        if fid not in flight_assignments and not state["cancelled"] and state.get("legs")
    ]

    if unassigned:
        print(f"\n  Warning: {len(unassigned)} flight(s) with YYZ legs remained unassigned:")
        for fid in unassigned:
            print(f"    - {fid}")
        deductions.append(negative(f"{len(unassigned)} flights unassigned at end of simulation"))

    print(f"SIMULATION COMPLETED SUCCESSFULLY")
    print(f"Total flights assigned: {len(flight_assignments)} | "
          f"Deductions logged: {len(deductions)} | "
          f"Unassigned: {len(unassigned)}")
    print("=" * 60)


# -------------------------
# Determine Gate Occupancy Window
# -------------------------
def _gate_window(legs: list):
    """
    Determine the YYZ gate window using the order of the legs.

    This avoids assuming that arrival at YYZ always comes before departure from YYZ.
    Example:
    - inbound then outbound: arrival -> departure
    - outbound then inbound: departure -> arrival
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

    # Only roll over if the second YYZ event happens after midnight.
    if second_time < first_time:
        second_time += 24 * 60

    return first_time, second_time

def _gate_window_label(legs: list):
    yyz_events = []

    for leg in legs:
        if leg["arrivalStation"] == HOME:
            yyz_events.append(("arr", leg["arrival_min"]))

        if leg["departureStation"] == HOME:
            yyz_events.append(("dep", leg["departure_min"]))

    if not yyz_events:
        return "arr: N/A, dep: N/A"

    if len(yyz_events) == 1:
        label, t = yyz_events[0]
        return f"{label}: {time_str(t)}"

    first_label, first_time = yyz_events[0]
    second_label, second_time = yyz_events[1]

    if second_time < first_time:
        second_time += 24 * 60

    return f"{first_label}: {time_str(first_time)}, {second_label}: {time_str(second_time)}"


# -------------------------
# Apply Soft Penalties
# -------------------------
def _apply_soft_penalties(flight_id: str, legs: list, gate_id: str, gate: dict, t_min: int):
    """Check soft constraint violations and append to deductions."""
    for leg in legs:
        airplane_type = leg["airplane_type"]
        gate_type = gate["gate_type"]
        jetbridge_required = leg["jetbridge_required"]

        # Gate type mismatches
        if airplane_type == 0 and gate_type != 0:
            deductions.append(negative(
                f"Cargo plane {flight_id} assigned to non-cargo gate {gate_id}", t_min))

        elif airplane_type != 0 and gate_type == 0:
            deductions.append(negative(
                f"Passenger plane {flight_id} assigned to cargo gate {gate_id}", t_min))

        elif airplane_type == 1 and gate_type != 1:
            deductions.append(negative(
                f"Domestic flight {flight_id} assigned to non-domestic gate {gate_id}", t_min))

        elif airplane_type == 2 and gate_type != 2:
            deductions.append(negative(
                f"International flight {flight_id} assigned to non-international gate {gate_id}", t_min))

        # Jetbridge requirement
        if jetbridge_required and not gate["jetbridge"]:
            deductions.append(negative(
                f"Flight {flight_id} requires jetbridge but gate {gate_id} has none", t_min))


# -------------------------
# Entry Point
# -------------------------
if __name__ == "__main__":
    run_sim(
        static_info="static_info.json",
        flight_schedule="flight_data/cascade_1.json",
        solution_module="solution_ab"
    )