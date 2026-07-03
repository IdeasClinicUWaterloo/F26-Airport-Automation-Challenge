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

This challenge is open-ended. The one fixed point is the **input and output**: a flight
schedule (plus live disruption messages) comes in, and a valid, conflict-free gate plan
must come out, updated as the day's disruptions arrive.

We provide `solution.py` and `solution_kd.py` as one potential solution to the gate
management subproblem, along with `evaluator.py` to score a solution against a scenario.
From there, you can take either path:

- **Write your own gate-assignment algorithm.** Implement `decide(observation)` the way
  `solution.py` and `solution_kd.py` do, and run it through the provided `evaluator.py`.
- **Build something else entirely.** Design a different system or approach to the
  problem, and incorporate our reference algorithm as the gate-assignment logic inside
  it, instead of writing your own.

This challenge follows how airports actually plan gates: **the full day's flight schedule is filed up front**, and a solution must

1. **build the initial gate plan** for the whole schedule, then
2. **keep it valid as disruptions arrive** during the day — delays, aircraft swaps, cancellations, and gate outages.

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

- `solution.py` — reference solution: a correct, minimal baseline (first-fit placement) — one potential approach to the subproblem
- `solution_kd.py` — a more optimized reference solution you can study or use directly
- `evaluator.py` — runs a solution module against a scenario (`python evaluator.py --scenario flight_data/simple.json --solution solution`)
- `visualize.py` — renders an interactive HTML timeline of a run (`python visualize.py --serve`, or double-click `launch_visualizer.bat` on Windows)
- `gms/` — the evaluator's internal domain package (you do not need to touch this)
- `flight_data/*.json` — example flight schedules (`simple`, `cascade_1`, `cascade_2`, and more)
- `static_info.json` — gate inventory, aircraft data, and the station table
- `JsonFlightMessageSpecification.md` — describes the JSON message format

Do not modify `evaluator.py` or `gms/` unless the challenge staff specifically tells you to.

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