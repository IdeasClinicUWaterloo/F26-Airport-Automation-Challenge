# Gate Assignment Subproblem

### INTERNAL REPO - DO NOT SHARE

Welcome to the internal repo for the Gate Assignment Subproblem (Brock Airport
Automation Hackathon). This documents how the evaluator works after the V3
rewrite. Start with the Case Study on the Brock SharePoint, then read this.

## Files

| Path                                | Description                                                                                  |
| ----------------------------------- | -------------------------------------------------------------------------------------------- |
| `evaluator.py`                      | **The** evaluator. Single canonical entry point (CLI). Orchestration only.                    |
| `visualize.py`                      | Interactive server (`--serve`) and static HTML export (`--all`/`--scenario --out`) for visualizing a run. |
| `gms/`                              | Domain package the evaluator is built on (see below).                                         |
| `solution.py`                       | Participant starter: correct minimal first-fit baseline.                                       |
| `solution_kd.py`                    | Reference solution: scoring-aware greedy (best gate + cascade repair).                          |
| `scripts/validation.py`             | Input-JSON validators (static info + flight schedules).                                         |
| `static_info.json`                  | Gate inventory, aircraft data (incl. `cargo` flag), and a `stations` table.                     |
| `flight_data/*.json`                | Flight schedules. Top-level keys are `HHMM` info-delivery times.                                |
| `tests/`                            | pytest suite (unit, integration, adversarial, feasibility guard).                              |
| `JsonFlightMessageSpecification.md` | Flight-message spec (by Richard, Brock Solutions).                                              |
| `EVALUATOR_AUDIT.md`                | Audit of the previous (V1/V2) evaluators that motivated this rewrite.                           |

### `gms/` package

| Module                  | Responsibility                                                                 |
| ----------------------- | ------------------------------------------------------------------------------ |
| `config.py`             | Constants + tunable `WEIGHTS`, `PREP_MINUTES`, `GROUND_MINUTES`, buffer.        |
| `timeutil.py`           | Time parsing + `absolutize` (monotonic minutes, overnight-safe).               |
| `occupancy.py`          | Per-presence gate intervals + half-open conflict detection.                    |
| `compat.py`             | Flight classification + asymmetric gate compatibility.                          |
| `profile.py`            | Combine state into a `FlightProfile` (intervals, category, wingspan, jb).       |
| `messages.py`           | Full flight-message lifecycle (`FlightStore`).                                  |
| `scoring.py`            | `HardFailure` + `ScoreCard` (weighted soft score).                             |
| `reference_solver.py`   | Offline feasibility checker + reference assigner (solvability guarantee).        |
| `loader.py`             | JSON loading for static info + schedules.                                       |

## How it works

**Scenario model — plan, then disrupt.** Every `flight_data/*.json` files its full
schedule at an opening planning tick (`0500`: all `CreateFlight`s), then carries only
disruptions (`UpdateTiming`, `GateOutage`, `CancelFlight`, `UpdateEquipment`) at later
ticks. So the solution builds the whole gate plan on the first call, then only adjusts.
The schedule is known up front; there are no surprise same-day flights.

`evaluator.run_sim(static_info, flight_schedule, solution_module)` replays the
schedule one info-time at a time. Each tick it:

1. applies all messages for that time to a `FlightStore`;
2. frees the gate of any assigned flight that was cancelled or lost its YYZ legs;
3. flags assigned flights whose profile changed this tick;
4. builds the **observation** and calls `solution.decide(observation)`;
5. applies the returned reassignments then assignments, enforcing hard rules;
6. runs a post-decision check on still-unrepaired changed flights;
7. accumulates soft penalties.

### Observation contract

```python
observation = {
    "time": t_min,                         # minute of day
    "gates": {gid: {gate_type, max_wingspan, dist, jetbridge}},
    "gate_outages": {gid: [[start, end], ...]},       # gates unavailable for a window
    "waiting_flights":  {fid: flight_view},           # unassigned, need a gate
    "assigned_flights": {fid: flight_view + gate_id}, # currently assigned
    "changed_flights":  {fid: {gate_id, reason, old, new}},  # revisit (reason: "info"|"outage")
    "gate_assignments": {gid: [{flight_id, intervals}]},
    "ac_info": {...},
}
# flight_view = {flight_id, intervals, category, wingspan,
#                jetbridge_required, legs, info_time, priority, reason}
```

`category`: `0` cargo, `1` domestic, `2` international. `intervals` is a list of
`(start, end)` absolute-minute presence windows.

**Return:** `{"assignments": [(fid, gid)], "reassignments": [(fid, gid)]}`.
`assignments` is for first-time placement; `reassignments` is for moving an
already-assigned flight.

### Domain semantics (the decisions baked in)

- **Occupancy = per-presence intervals.** A flight occupies its gate for each
  contiguous stretch it is physically at YYZ. A depart-then-return flight yields
  two intervals; the gate is free in between. Intervals are half-open, so exact
  back-to-back use is allowed.
- **Gate typing = asymmetric, hard.** International flight → international gate
  only. Domestic flight → domestic *or* international gate (international earns a
  soft "premium gate" penalty). Cargo flight → cargo gate. Wrong direction
  (e.g. international at a domestic gate) is a hard failure.
- **Size + jetbridge** are hard constraints (jetbridge is hard in *all* paths).
- **Cargo** is real: aircraft carry a `cargo` flag; cargo gates are usable.
- **Gate outages** (`GateOutage` resource message) mark a gate unavailable for a window;
  a flight cannot occupy it across that window and any flight already there must move.
- **Diversions** (`DivertFlight` message) are unscheduled inbounds (medical emergency, air
  turnback) that appear mid-day flagged `priority`; the scorer charges the heavier
  `unassigned_emergency` weight if one is left unplaced.
- **Time** is single-day with intra-flight rollover for overnight legs.

## Interactive visualizer (`visualize.py --serve`)

A stdlib-only local HTTP server (`http.server.ThreadingHTTPServer`, no new deps) so a
student can run their actual `solution.py` against any scenario from one web page,
switching scenarios without regenerating files:

- `GET /` — the page (scenario dropdown + solution-module box + the Gantt/queue/log UI).
- `GET /api/scenarios` — `{"scenarios": [...]}`, derived from `flight_data/*.json`.
- `GET /api/run?scenario=<name>&solution=<module>` — pops `<module>` from `sys.modules`
  before calling `run_sim(..., record=True)`, forcing a fresh import so saved edits to
  the student's file are picked up without restarting the server. Returns
  `{"trace": {...}}` on success or `{"error": "..."}` (import failure, syntax error,
  unknown scenario) so a broken solution shows a message in the page instead of
  crashing the server.

The same HTML/JS template also supports the older static-export mode (`--all` /
`--scenario --out`): the page embeds `const MODE = {"server": false, "trace": {...}}`
instead of fetching, and hides the scenario/solution controls. `tests/test_visualize.py`
covers both modes, including a test that edits a probe module on disk between two
`/api/run` calls to prove the live-reload actually picks up the change.

## Marking

Two tiers (see `gms/scoring.py`, weights in `gms/config.py`):

1. **Hard failures** (terminate the run, score = FAILED): double-booking,
   oversize aircraft, missing required jetbridge, wrong-direction gate type,
   invalid output, reassigning/assigning an unknown or cancelled flight, or
   leaving a changed flight in an invalid gate after its tick.
2. **Soft penalties** (summed; lower is better): reassignments
   (heavier after the flight's gate presence has begun), domestic-at-international
   gate, total walking distance (`gate.dist`), and unassigned flights at sim end.
   Reassignments forced by the airport (a timing/equipment change or a gate
   outage) are not charged the move cost unless the flight has already arrived.

## Solvability guarantee

Every shipped scenario must be solvable with zero hard failures.
`gms.reference_solver.scenario_feasible` proves this by checking that each tick's
active flight set is statically assignable; `tests/test_feasibility.py` runs it
over every `flight_data/*.json` so an infeasible scenario fails CI before it can
reach a participant.

## Test Cases

| File                      | Exercises                                              |
| ------------------------- | ----------------------------------------------------- |
| `simple.json`             | Basic placement incl. a depart-then-return flight     |
| `cascade_1.json`          | Timing update, gate still valid                       |
| `cascade_2.json`          | Timing update forces a reassignment                   |
| `cargo.json`              | Freighter → cargo gate                                 |
| `overnight.json`          | Legs crossing midnight (rollover)                     |
| `equipment_upgrade.json`  | UpdateEquipment forces a reassignment                 |
| `cancel.json`             | Cancellation frees a gate (no hard fail)              |
| `domestic_787.json`       | Domestic 787 legally uses an international gate        |
| `gate_outage.json`        | A gate goes offline; the flight there must reassign   |
| `busy_day.json`           | ~15 flights, banked; domestic flights spill onto intl gates; a delay + a cancellation |
| `rush_hour.json`          | 6 domestic flights peak near capacity, then a gate outage forces a reshuffle           |
| `emergencies.json`        | A planned day plus a mid-day medical diversion and an air turnback (unscheduled)        |

Run everything: `python -m pytest`. Run one scenario:
`python evaluator.py --scenario flight_data/cascade_2.json --solution solution_kd`.

## Possible future extensions (deliberately out of scope)

Trimmed from the student materials to keep the evaluator and docs in sync; candidates
for a later edition: **security / restricted gates** (origin-specific secure gates),
**airline preferences** (soft reward for preferred gates), and an explicit
**turnaround service buffer** between aircraft (currently `TURNAROUND_BUFFER = 0`).
