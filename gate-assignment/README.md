# Gate Assignment Subproblem

### INTERNAL REPO - DO NOT SHARE

Hey, welcome to the Github Repo for the Gate Assignment Subproblem for the Brock Airport Automation Hackathon!

To get started, be read through the Case Study document on the Brock Sharepoint. Once you're done with that you can get started with understanding how the code/structure works.

## Files

| Filename                            | Description                                                                                                                                                                |
| ----------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `solution.py`                       | Sample empty solution provided to participants.                                                                                                                            |
| `solution_kd.py`                    | Example solution assigning flights to the first available compatible gate (for testing) _This is not a 'clean' solution._                                                  |
| `scripts/validation.py`             | Utility for validating the input JSON files.                                                                                                                               |
| `evaluator_public.py`               | Evaluator code used to score solutions (typically hidden behind a GUI).                                                                                                    |
| `static_info.json`                  | Airport information (gate types, etc.) and airplane data (wingspan, etc.).                                                                                                 |
| `flight_data/*.json`                | Contains the flight schedule/data. Each 'Message Event' has a time attached to it. This time is when the solution can see that particular message event. (explained later) |
| `JsonFlightMessageSpecification.md` | JSON flight messaging specification for airport communications (by Richard from Brock Solutions).                                                                          |

## ToDos

- Sample solution needs to account for updateEquipment
- Reimplement Cargo Aircraft
- More Comprehensive Testing for Evaluator (more flight_info files and edge cases)
- Guide participants to use optimization techniques??
- Create a GUI/Web App for uploading solution files
  - Need to make sure we import all libraries people may use and/or give an option to import other ones.
  - Possible WASM Port for better performance

## How it works

The Evaluator Script goes through the `flight_info.json` and iterates for each 'info_time' that is specified. For each 'info_time' it creates lists to transmit appropriate information to the users solution file.

At each 'info_time' the user has access to `observation` which is structured like:

```python
observation = {
        "time": t_min,
        "waiting_flights": waiting_snapshot,
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
                }
                for a in assignments
            ]
            for gid, assignments in gate_assignments.items()
        },
        "ac_info": aircraft_info,
    }
```

Where:

- `waiting_snapshot` is a snapshot of waiting flights (unassigned, not cancelled)
  ```python
  waiting_snapshot = {
        fid: {
            "flight_id": fid,
            "legs": state["all_legs"],
            "info_time": state["info_time"],
        }
        for fid, state in waiting_flights.items()
    }
  ```
- `ac_info` contains information about the aircraft (primarily for checking wingspan/jetbridge compatibility)

Given this information, the user has to program their solution. **To commit changes**, the function needs to return a dictionary structured like: `{"assignments": assignments, "reassignments": reassignments}`. Note that assignments are reserved for assigning a flight for the first time, and as the naming suggests, the reassignments list should only contain flights you are reassigning (either before/after its arrived)

Where Assignments and Reassignments are lists that will contain tuples of form `(flight_id, gate_id)`.

## Marking

As the marking/scoring exists now there are two types of penalties

1. **Game Ending Errors** -> Wingspan incompatibility, Double Booking Gates
2. **Point Deductions** -> Reassigning flight thats already landed (heavy deduction), flight at wrong gate type,

## Test Cases

| File Name        | Explain                                          |
| ---------------- | ------------------------------------------------ |
| `simple.json`    | Simple Test (No cascading effect)                |
| `cascade_1.json` | Simple Test for Cascading Changes                |
| `cascade_2.json` | Slightly more Complex Test for Cascading Changes |
