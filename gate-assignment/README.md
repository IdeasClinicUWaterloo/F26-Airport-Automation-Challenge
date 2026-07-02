# Gate Management System

## Challenge Overview

Airports must assign aircraft to gates while managing timing, aircraft size, passenger needs, airline preferences, security rules, cargo restrictions, and unpredictable disruptions.

In a real airport, a gate assignment that looks valid at one moment can become invalid later because of a delayed arrival, a gate outage, an aircraft type change, or a late departure. Your task is to build a system that can assign gates over time while avoiding conflicts and adapting to changing information.

You are not just trying to place flights into empty gates. You are building the core decision logic of a simplified Gate Management System, the kind of system that sits at the heart of real airport operations software used at some of the world's busiest airports today.

---

## Industry Context

### How Airports Really Manage Gates

Modern airports rely on tightly integrated software ecosystems to manage the flow of aircraft, passengers, and baggage through the facility. Gate management is never handled in isolation. It is one layer in a stack of interconnected systems that must all agree on the same operational picture at the same time.

Brock Solutions, a global engineering and professional services company headquartered in Waterloo, Ontario, is one example of a company that builds this kind of integrated airport operations software. Their **SmartSuite** platform is used at some of the world's largest and busiest airports, including San Francisco, JFK, Dublin, Sydney, and Toronto, to manage baggage, passenger, and flight operations in a coordinated way.

Within SmartSuite, the **SmartSuite Enterprise** product provides what Brock describes as a "single pane of glass" into airport operations. It collects real-time baggage, passenger, and flight information, consolidates it across multiple systems, and gives operations staff the visibility they need to make decisions quickly, including during disruptions. A core feature of SmartSuite Enterprise is its ability to handle **IROPS** (Irregular Operations), the industry term for the kind of disruptions (delays, gate outages, aircraft swaps, late departures) that make static planning useless and dynamic reassignment essential.

Brock's **SmartClear Boarding Gate Management** module sits even closer to the problem you are solving in this challenge. It manages the departure process at the gate level, giving agents real-time passenger information, tracking the boarding process using touchless technology, and coordinating automated pre-flight seat assignment, standby processing, and upgrade management, all from a single application.

These products exist within a broader airport technology ecosystem. Common systems and platforms in this space include:

- **Airport Operational Database (AODB):** the central data spine of an airport. Stores and distributes flight schedules, arrival and departure updates, aircraft information, resource assignments, gate changes, baggage data, and operational messages. All other systems consume and contribute to the AODB.
- **Resource Management System (RMS):** uses live AODB data to assign limited physical resources (gates, stands, check-in counters, baggage belts, ground handling equipment) to flights and aircraft. Must enforce operational rules, airline preferences, and compatibility constraints in real time.
- **Fixed Resource Management:** a specialized layer within RMS focused on infrastructure that cannot be easily moved or reconfigured, such as gates and remote stands.
- **Airport Collaborative Decision Making (A-CDM):** a framework in which airlines, airports, ground handlers, and air traffic control share information so that all parties can make better-coordinated decisions. Gate assignments are a key data point in the A-CDM picture.
- **Flight Information Display Systems (FIDS):** the screens passengers see in terminals showing gate assignments, departures, and arrivals. Gate assignments must flow downstream to FIDS in real time so that passengers receive accurate information.
- **Ground Handling and Turnaround Management Systems:** coordinate refueling, catering, cleaning, and baggage loading for each aircraft turn. The gate assignment determines where all of this activity takes place.
- **Airport Operations Control Center (AOCC) Dashboards:** give airport operations staff a live view of the gate plan, disruptions, and recovery actions.

Other major industry vendors operating in this space include SITA, Collins Aerospace, Amadeus, INFORM, TAV Technologies, Copenhagen Optimization, and ISO, each offering different parts of this technology stack.

### The Data Flow in a Real Gate Management System

At a high level, a gate management system works like this:

```
Flight schedules + aircraft data + gate inventory + live updates
        ↓
Operational database / shared airport state (AODB)
        ↓
Constraint checking
        ↓
Candidate gate generation
        ↓
Optimization or rule-based assignment
        ↓
Conflict detection and disruption recovery (IROPS handling)
        ↓
Updated gate plan sent to FIDS, staff, airlines, and downstream systems
```

In real operations, this pipeline runs continuously. A delayed arrival can block a gate. A late departure can cascade to the next aircraft. A gate outage can force multiple reassignments in sequence. An aircraft type change can invalidate a perfectly good plan. An international flight may suddenly need a secure gate. The system cannot afford to stop and recalculate from scratch; it must make the best incremental decisions possible with the information currently available.

### Why This Problem Is Harder Than It Looks

A simple gate assignment algorithm answers one question: *which gate should this flight use?*

A gate management system answers a different, harder question: *how should the airport manage all gates and stands over time as the operation changes?*

The difference matters. A static solver can find a globally optimal assignment over a fixed schedule. But real airports do not operate on fixed schedules. They operate on plans that are constantly being revised, where every change to one flight can ripple outward to affect others. A good gate management system must be correct, constraint-aware, and resilient, not just optimal on paper.

This is the type of problem Brock Solutions and companies like them solve every day for airports around the world. This challenge gives you a simplified but structurally similar version of that problem to work through.

---

### How the Hackathon Maps to Real Systems

| Hackathon Concept           | Industry Analogue                               |
| --------------------------- | ----------------------------------------------- |
| Static gate data            | Airport resource inventory (RMS / AODB)         |
| Flight schedule JSON        | AODB flight schedule data                       |
| Flight update messages      | Live operational updates from AODB              |
| Gate outage messages        | Resource availability updates from AODB         |
| Aircraft-gate compatibility | Stand/gate planning rules in RMS                |
| Occupancy conflicts         | Gate/stand collision detection in RMS           |
| Delay handling              | IROPS recovery (as in SmartSuite Enterprise)    |
| Reassignment minimization   | Operational stability and passenger experience  |
| Walking distance score      | Passenger service optimization                  |
| Hidden test scenarios       | Robustness against real operational variability |

---

## What You Are Building

You will write your gate assignment logic in `solution.py`.

This challenge follows how airports actually plan gates: **the full day's flight schedule is filed up front**, and your job is to

1. **build the initial gate plan** for the whole schedule, then
2. **keep it valid as disruptions arrive** during the day — delays, aircraft swaps, cancellations, and gate outages.

The evaluator reads the schedule and live updates from JSON, converts each message into simple flight/gate facts, and calls your `decide(observation)` once per *info-time*:

- At the **opening (planning) tick**, every flight is in the queue — you assign each to a gate. This is your plan for the day.
- At later **disruption ticks**, only changes arrive (a delay, an outage, a cancellation, an equipment swap). You react by reassigning just the affected flights — moving **as few as possible**, since every reassignment costs points.

A good solution produces a valid plan up front and a **stable, low-cost recovery** when things change — not a from-scratch reshuffle every time.

---

## How a Simulated Day Runs

Each scenario file is a timeline keyed by info-time (`"HHMM"`):

```
0500  (planning)   → all CreateFlight messages: the full filed schedule
0900  (disruption) → e.g. a GateOutage, or an UpdateEquipment
1000  (disruption) → e.g. an UpdateTiming (a delay)
```

Your `decide` is called at each tick with the current picture. At `0500` you place the
whole schedule; afterwards you only get disruptions and adjust. The planned schedule is
**known in advance** — but the day can still throw a genuine surprise: an **unscheduled
diversion** (a medical emergency, or a flight that turns back) can arrive mid-day and needs
a gate immediately. Those are flagged `priority`, and you should place them even if it
means a reassignment.

---

## Core Requirements

Your solution must:

- Build an initial gate plan for the full filed schedule at the start of the day
- Assign arriving and departing flights to valid gates
- Avoid gate occupancy conflicts
- Respect aircraft-gate compatibility
- Account for aircraft size limits
- Account for jet bridge requirements where applicable
- Respect domestic, international, and cargo gate rules
- Handle delays, equipment swaps, cancellations, and cascading schedule changes
- React to gate outages by moving affected flights
- Accommodate unscheduled diversions and turnbacks (priority arrivals) that appear mid-day
- Recover from disruptions with as few reassignments as possible
- Fail gracefully — never crash; if a flight cannot be placed, leave it unassigned rather than erroring
- Produce clear output that the evaluator can check

A solution that works only for the provided sample scenario is not enough. Your logic should generalize to different airport layouts and schedules.

---

## Constraints in This Challenge

These are the constraints the evaluator actually enforces:

| Constraint Type          | Rule                                                                          |
| ------------------------ | ----------------------------------------------------------------------------- |
| Occupancy                | Two aircraft cannot occupy the same gate at overlapping times (hard)          |
| Aircraft Size            | A flight's wingspan must fit the gate's `max_wingspan` (hard)                  |
| Jet Bridge               | A jetbridge-required aircraft needs a jetbridge gate (hard)                    |
| Domestic / International | International flights need an international gate; domestic flights may use a domestic *or* international gate; cargo flights need a cargo gate (hard; see asymmetric rule below) |
| Cargo                    | Cargo flights use cargo gates; passenger flights do not (hard)                 |
| Gate Outage              | A gate can go offline for a window; flights there must be moved (hard)         |
| Delay                    | An `UpdateTiming` message can extend a flight's gate window                    |
| Reassignment            | Moving an already-placed flight is allowed but costs soft points               |
| Walking Distance        | Each gate has a distance; total distance is a soft score                       |

---

## Starter Files

- `solution.py` — where you implement your algorithm (a correct minimal baseline is provided)
- `solution_kd.py` — a slightly smarter reference solution you can study
- `evaluator.py` — runs your solution against a scenario (`python evaluator.py --scenario flight_data/simple.json --solution solution`)
- `visualize.py` — renders an interactive HTML timeline of a run (see *Visualizing a Run* below)
- `gms/` — the evaluator's internal domain package (you do not need to touch this)
- `flight_data/*.json` — example flight schedules (`simple`, `cascade_1`, `cascade_2`, and more)
- `static_info.json` — gate inventory, aircraft data, and the station table
- `JsonFlightMessageSpecification.md` — describes the JSON message format

Do not modify the evaluator unless the challenge staff specifically tells you to. Your submitted logic should be in `solution.py`.

---

## Solution Interface

You implement one function:

```python
def decide(observation):
    ...
    return {"assignments": [(flight_id, gate_id)], "reassignments": [(flight_id, gate_id)]}
```

Each tick the evaluator hands you an `observation`:

```python
observation = {
    "time": <minute of day>,
    "gates": { gate_id: {gate_type, max_wingspan, dist, jetbridge} },
    "gate_outages": { gate_id: [ [start, end], ... ] },  # gates unavailable for a window
    "waiting_flights":  { fid: flight_view },             # unassigned, need a gate
    "assigned_flights": { fid: flight_view + gate_id },   # already assigned
    "changed_flights":  { fid: {gate_id, reason, old, new} },  # revisit these
    "gate_assignments": { gate_id: [ {flight_id, intervals} ] },
    "ac_info": { ... },
}
# flight_view = {flight_id, intervals, category, wingspan,
#                jetbridge_required, legs, info_time, priority, reason}
```

- `category` **and** `gate_type` use the same codes: `0` = cargo, `1` = domestic, `2` = international.
- `priority`: `true` for an **unscheduled emergency arrival** (a diversion or turnback) — place it first; leaving one unassigned costs a heavier penalty. `reason` gives the flavor (`"medical"`, `"turnback"`).
- `intervals`: the `(start, end)` minute windows during which the flight occupies a gate.
- `gate_outages`: a gate is unavailable during each listed `[start, end]` window — don't place a flight there across it, and move any flight already there.
- `changed_flights`: a flight you already placed that needs another look, because its own info changed (`reason: "info"`) or an outage hit its gate (`reason: "outage"`). Use `reassignments` to move it.
- Use `assignments` for first-time placement and `reassignments` to move a flight you already placed.

---

## Suggested Solution Approaches

There is no single correct algorithm. You can use any approach that produces valid, robust assignments.

---

## Visualizing a Run

`visualize.py` renders a run as a gate timeline — gates as rows, flight occupancy as bars
on a time axis, gate outages as red blocks, diverted/emergency flights marked with ⚕.
Press **Play** to sweep an operational clock across the day and watch each gate switch
between *free* and *in use* in real time; use the **plan @** stepper to replay how the
plan changed at each decision point (reassignments, outages, diversions); and watch the
**flight queue** panel show the algorithm placing each flight onto a gate.

### Interactive (recommended)

```bash
python visualize.py --serve
```

On Windows you can also just double-click **`launch_visualizer.bat`** in this folder.

This opens one page in your browser with a **scenario dropdown** and a **solution module**
box (defaults to `solution`, i.e. `solution.py`). Pick any scenario, press **Run**, and it
executes your actual code — freshly, so saved edits are picked up immediately, no restart
needed — against that scenario and renders the result. Switch scenarios or edit your
solution and press Run again as many times as you like, all on the same page.

The crowded `busy_day` and `rush_hour` scenarios are the best demos of an algorithm
working under load.

### Static export

```bash
python visualize.py --scenario flight_data/busy_day.json --solution solution_kd --open
python visualize.py --all --solution solution_kd        # render every scenario to disk
```

Writes a self-contained HTML file per scenario into `visualization/` — useful for sharing
a fixed result (e.g. in a report), since it needs no server to open.

---

## Evaluation

Your solution may be evaluated using visible tests and hidden tests.

### Hard Failures

A hard failure stops the simulation and the run scores as FAILED. These are:

- Two aircraft assigned to the same gate at overlapping times (double-booking)
- An aircraft assigned to a gate that is too small, or that lacks a required jetbridge
- A gate-type violation: an **international** flight at a domestic gate, or a cargo/passenger mismatch
- Invalid output format, or assigning/reassigning an unknown or cancelled flight
- Leaving a flight in an invalid gate after its information changed (reassign it instead)

**Gate typing is asymmetric.** An international flight needs an international gate (it
clears customs there). A domestic flight may use a domestic *or* an international gate
— using an international gate is allowed but earns a soft penalty. Cargo flights need a
cargo gate.

### Scored Metrics

If there are no hard failures, your run earns a weighted soft score (lower is better):

- Number of reassignments (heavier once the flight's gate time has already begun)
- Passenger walking distance (gate distance)
- Domestic flights placed on international (premium) gates
- Flights left unassigned at the end of the simulation

Every shipped scenario is guaranteed to be solvable with **zero** hard failures, so a
correct solution can always avoid them. The final evaluator may use airport layouts and
flight schedules that are different from the examples provided.

---

## Not in This Challenge (Possible Future Extensions)

Real gate management systems also handle the following. They are **not** part of this
challenge's evaluator or data, so you do not need to (and cannot) solve for them — they
are listed only as realistic directions the problem could grow in later editions:

- **Security / restricted gates** — flights from certain origins requiring specific secure gates.
- **Airline preferences** — rewarding gates an airline prefers (close to its lounges/baggage).
- **Turnaround service time** — explicit minimum servicing time between two aircraft at a gate (the evaluator currently models gate occupancy directly and uses no separate service buffer).

---

## Design Tips

- Keep an internal record of gates, aircraft, and assignments.
- Validate an assignment before committing it.
- Do not assume all gates are identical.
- Think carefully before reassigning an aircraft that was already assigned.
- Make your simple solution correct before making it clever.

---

## Deliverables

Your team should submit:

- `solution.py`
- Any helper files needed by your solution
- A short explanation of your approach
- Optional visualizations, dashboards, UI, or simulations
- A list of assumptions and edge cases handled

During judging, be ready to explain:

- How your solution prevents conflicts
- How it handles invalid data
- How it responds to delays or outages
- What optimization strategy you used
- What limitations remain