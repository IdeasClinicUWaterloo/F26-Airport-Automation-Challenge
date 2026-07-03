# Gate Management System

## Challenge Overview

Airports must assign aircraft to gates while managing timing, aircraft size, passenger needs, security rules, cargo restrictions, and unpredictable disruptions. A gate assignment that looks valid at one moment can become invalid later because of a delayed arrival, a gate outage, an aircraft type change, or a late departure.

Your task is to build a system that assigns gates over time, avoiding conflicts and adapting to changing information. It is the core decision logic of a simplified Gate Management System, the kind that sits at the heart of real airport operations software.

---

## Industry Context

Gate management software sits inside a larger airport tech stack: an **AODB** (Airport Operational Database) holds the shared flight/gate state, a **Resource Management System (RMS)** assigns gates and stands from it, and gate changes flow out to passenger-facing displays, ground handling, and airline systems. Real systems also have to handle **IROPS** (Irregular Operations), the delays, swaps, and outages that make static planning useless.

Brock Solutions, an engineering firm headquartered in Waterloo, Ontario, builds this kind of software today. Their **SmartSuite** platform runs gate and passenger operations at airports including SFO, JFK, Dublin, Sydney, and Toronto. This challenge is a simplified but structurally similar version of the problem they solve.

| Hackathon Concept           | Industry Analogue                                |
| ---------------------------- | ------------------------------------------------- |
| Static gate data             | Airport resource inventory (RMS / AODB)           |
| Flight schedule JSON         | AODB flight schedule data                         |
| Flight update messages       | Live operational updates from AODB                 |
| Gate outage messages         | Resource availability updates from AODB            |
| Aircraft-gate compatibility  | Stand/gate planning rules in RMS                   |
| Occupancy conflicts          | Gate/stand collision detection in RMS              |
| Delay handling               | IROPS recovery                                     |
| Reassignment minimization    | Operational stability and passenger experience     |
| Walking distance score       | Passenger service optimization                     |
| Hidden test scenarios        | Robustness against real operational variability    |

---

## What You Are Building

This challenge is open-ended. The one fixed point is the **input and output**: a flight schedule (plus live disruption messages) comes in, and a valid, conflict-free gate plan must come out, updated as the day's disruptions arrive.

We provide `solution.py` and `solution_kd.py` as one potential solution to the gate management subproblem, along with `evaluator.py` to score a solution against a scenario. From there, you can take either path:

- **Write your own gate-assignment algorithm.** Implement `decide(observation)` the way `solution.py` and `solution_kd.py` do, and run it through the provided `evaluator.py`.
- **Build something else entirely.** Design a different system or approach, and incorporate our reference algorithm as the gate-assignment logic inside it, instead of writing your own.

Airports plan gates the way this challenge is structured: **the full day's flight schedule is filed up front**, then a timeline of updates arrives keyed by info-time (`"HHMM"`):

```
0500  (planning)   → the full filed schedule
0900  (disruption) → e.g. a gate outage, or an equipment swap
1000  (disruption) → e.g. a delay
```

A solution must build the initial plan at the opening tick, then react to each later disruption by adjusting just the affected flights, moving **as few as possible** since every reassignment costs points. The schedule is known in advance, but the day can still throw a genuine surprise: an **unscheduled diversion** (a medical emergency, or a flight that turns back) can arrive mid-day flagged `priority` and needs a gate immediately, even if it means a reassignment.

A good solution produces a valid plan up front and a **stable, low-cost recovery** when things change, not a from-scratch reshuffle every time. It should also generalize: working only on the provided sample scenarios is not enough.

---

## Constraints

These are the rules the evaluator enforces:

| Constraint Type          | Rule                                                                              |
| ------------------------- | ---------------------------------------------------------------------------------- |
| Occupancy                 | Two aircraft cannot occupy the same gate at overlapping times (hard)               |
| Aircraft Size              | A flight's wingspan must fit the gate's `max_wingspan` (hard)                       |
| Jet Bridge                 | A jetbridge-required aircraft needs a jetbridge gate (hard)                         |
| Domestic / International   | International flights need an international gate; domestic flights may use a domestic *or* international gate; cargo flights need a cargo gate (hard, asymmetric; see below) |
| Cargo                      | Cargo flights use cargo gates; passenger flights do not (hard)                      |
| Gate Outage                | A gate can go offline for a window; flights there must be moved (hard)              |
| Delay                      | An `UpdateTiming` message can extend a flight's gate window                         |
| Reassignment               | Moving an already-placed flight is allowed but costs soft points                    |
| Walking Distance           | Each gate has a distance; total distance is a soft score                            |

**Gate typing is asymmetric.** An international flight needs an international gate (it clears customs there). A domestic flight may use a domestic *or* an international gate (using an international gate is allowed but earns a soft penalty). Cargo flights need a cargo gate.

Beyond these, a solution should fail gracefully (never crash: leave an unplaceable flight unassigned rather than erroring) and produce output the evaluator can check.

---

## Starter Files

- `solution.py`: reference solution, a correct minimal baseline (first-fit placement) and one potential approach to the subproblem
- `solution_kd.py`: a more optimized reference solution you can study or use directly
- `evaluator.py`: runs a solution module against a scenario (`python evaluator.py --scenario flight_data/simple.json --solution solution`)
- `visualize.py`: renders an interactive HTML timeline of a run (`python visualize.py --serve`, or double-click `launch_visualizer.bat` on Windows)
- `gms/`: the evaluator's internal domain package (you do not need to touch this)
- `flight_data/*.json`: example flight schedules (`simple`, `cascade_1`, `cascade_2`, and more)
- `static_info.json`: gate inventory, aircraft data, and the station table
- `JsonFlightMessageSpecification.md`: describes the JSON message format

Do not modify `evaluator.py` or `gms/` unless the challenge staff specifically tells you to.

---

## Evaluation

Your solution may be evaluated using visible tests and hidden tests.

### Hard Failures

A hard failure stops the simulation and the run scores as FAILED:

- Two aircraft assigned to the same gate at overlapping times (double-booking)
- An aircraft assigned to a gate that is too small, or that lacks a required jetbridge
- A gate-type violation (see the *asymmetric* rule above), or a cargo/passenger mismatch
- Invalid output format, or assigning/reassigning an unknown or cancelled flight
- Leaving a flight in an invalid gate after its information changed (reassign it instead)

### Scored Metrics

If there are no hard failures, your run earns a weighted soft score (lower is better):

- Number of reassignments (heavier once the flight's gate time has already begun)
- Passenger walking distance (gate distance)
- Domestic flights placed on international (premium) gates
- Flights left unassigned at the end of the simulation

Every shipped scenario is guaranteed to be solvable with **zero** hard failures, so a correct solution can always avoid them. The final evaluator may use airport layouts and flight schedules that are different from the examples provided.
