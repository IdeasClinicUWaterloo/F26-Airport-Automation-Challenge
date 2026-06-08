# Airplane Gate Assignment

## Challenge Overview

Airports must assign aircraft to gates while managing timing, aircraft size, passenger needs, airline preferences, security rules, cargo restrictions, and unpredictable disruptions.

In a real airport, a gate assignment that looks valid at one moment can become invalid later because of a delayed arrival, a gate outage, an aircraft type change, or a late departure. Your task is to build a system that can assign gates over time while avoiding conflicts and adapting to changing information.

You are not just trying to place flights into empty gates. You are building the core decision logic of a simplified Gate Management System.

## Industry Context

Modern airports rely on connected operations software to manage flights, passengers, baggage, gates, stands, check-in counters, ground handlers, and disruption recovery. Gate planning is usually not handled as an isolated spreadsheet problem. It is part of a larger airport operations software environment.

In industry, this type of problem is commonly connected to systems such as:

* Airport Operational Database, or AODB
* Resource Management System, or RMS
* Fixed Resource Management
* Gate and stand allocation tools
* Airport Collaborative Decision Making, or A-CDM
* Flight Information Display Systems, or FIDS
* Baggage Handling Systems, or BHS
* Baggage Reconciliation Systems, or BRS
* Ground handling and turnaround management systems
* Airport Operations Control Center dashboards

The AODB is often treated as the central operational data source. It stores and distributes flight schedules, arrival and departure updates, aircraft information, airport resource assignments, gate changes, baggage information, and operational messages. Other systems consume this data so that airlines, airport operators, ground handlers, passenger information displays, baggage systems, and control-room staff can work from a shared operational picture.

A Resource Management System uses this operational data to assign limited airport resources. These resources can include:

```text id="dwv83l"
Gates
Remote stands
Check-in counters
Baggage belts
Bus gates
Tow positions
Ground handling resources
Terminal facilities
```

Gate and stand management systems must solve a dynamic planning problem. They need to assign aircraft to suitable gates while considering operational rules, infrastructure limits, airline preferences, passenger experience, and disruptions.

Industry platforms from companies such as SITA, Collins Aerospace, Amadeus, INFORM, TAV Technologies, Copenhagen Optimization, ISO, Brock Solutions, and others support different parts of this airport operations technology stack. Some focus on AODB and resource management. Some focus on baggage, passenger processing, real-time operational dashboards, integration, or disruption management. The common theme is that airports need software that can combine live operational data with decision support.

At a high level, a gate management system works like this:

```text id="e6vgha"
Flight schedules + aircraft data + gate inventory + live updates
        ↓
Operational database / shared airport state
        ↓
Constraint checking
        ↓
Candidate gate generation
        ↓
Optimization or rule-based assignment
        ↓
Conflict detection and disruption recovery
        ↓
Updated gate plan sent to displays, staff, airlines, and downstream systems
```

In real airport operations, a gate plan must constantly adapt. A delayed arrival can block a gate. A late departure can affect the next aircraft. A gate outage can force multiple reassignments. A widebody aircraft swap can invalidate the original plan. An international flight may require a secure gate. A cargo flight may need a different stand. A medical or emergency flight may need priority handling.

This is why the challenge is framed as a **Gate Management System**, not just a gate assignment algorithm.

A simple gate assignment algorithm answers:

> Which gate should this flight use?

A gate management system answers:

> How should the airport manage all gates and stands over time as the operation changes?

The hackathon version is a simplified model of this industry problem. Students are not expected to build production airport operations software. Instead, they are building the core decision logic behind one important part of that software: assigning and reassigning aircraft to gates safely and efficiently under changing conditions.

The concepts in this challenge map to real airport systems as follows:

| Hackathon Concept           | Industry Analogue                               |
| --------------------------- | ----------------------------------------------- |
| Static gate data            | Airport resource inventory                      |
| Flight schedule JSON        | AODB flight schedule data                       |
| Flight update messages      | Live operational updates                        |
| Gate outage messages        | Resource availability updates                   |
| Aircraft-gate compatibility | Stand/gate planning rules                       |
| Occupancy conflicts         | Gate/stand collision detection                  |
| Delay handling              | Disruption and IROPS recovery                   |
| Reassignment minimization   | Operational stability and passenger experience  |
| Walking distance score      | Passenger service optimization                  |
| Airline preferences         | Business rules and stakeholder constraints      |
| Hidden test scenarios       | Robustness against real operational variability |

The final goal is to build a simplified airport decision-support module that can answer:

> Given the current schedule, gate inventory, live updates, and operational constraints, where should each aircraft go, and how should the plan change when the airport operation changes?

---

# What You Are Building

You will write your gate assignment logic in `solution.py`.

The evaluator will read flight schedule information, gate information, and flight update messages from JSON files. These messages follow the project’s JSON flight message specification. To keep the challenge focused, the evaluator will convert the messages into simpler flight and gate update calls before passing them to your solution.

Your job is to decide which gate each aircraft should use and to update those decisions when new information arrives.

---

# Core Requirements

Your solution must:

* Assign arriving and departing flights to valid gates
* Avoid gate occupancy conflicts
* Respect aircraft-gate compatibility
* Account for aircraft size limits
* Account for jet bridge requirements where applicable
* Respect domestic, international, cargo, and security restrictions
* Handle delays and cascading schedule changes
* Handle missing, corrupted, or incomplete data safely
* Reassign flights efficiently when disruptions occur
* Produce clear output that the evaluator can check

A solution that works only for the provided sample scenario is not enough. Your logic should generalize to different airport layouts and schedules.

---

# Example Constraints

Your solution may need to consider constraints such as:

| Constraint Type          | Example                                                           |
| ------------------------ | ----------------------------------------------------------------- |
| Occupancy                | Two aircraft cannot use the same gate at the same time            |
| Aircraft Size            | A large aircraft cannot be assigned to a small gate               |
| Jet Bridge               | Some aircraft or passenger flights may require a jet bridge       |
| Domestic / International | Some gates may only handle domestic flights                       |
| Cargo                    | Some gates may only handle cargo flights                          |
| Security                 | Flights from certain origins may require restricted gates         |
| Airline Preference       | Some airlines may prefer gates closer to baggage claim or lounges |
| Turnaround Time          | Aircraft may need service time before the next departure          |
| Gate Outage              | A gate may become unavailable during the simulation               |
| Delay                    | A delayed aircraft may block a gate longer than expected          |

---

# Starter Files

This folder may include files such as:

* `solution.py` - where you implement your algorithm
* `evaluator.py` - used to test your solution
* `JsonFlightMessageSpecification.md` — describes the JSON message format
* `simple.json`, `cascade_1.json`, `cascade_2.json`  - Example flight schedule JSON files
* `static_info.json` - Gate and aircraft information

Do not modify the evaluator unless the challenge staff specifically tells you to. Your submitted logic should be in `solution.py`.

---

# Suggested Solution Approaches

There is no single correct algorithm. You can use any approach that produces valid, robust assignments.

---

# Recommended Roadmap

---

# Evaluation

Your solution may be evaluated using visible tests and hidden tests.

## Hard Failures

Hard failures may stop the simulation or produce a major penalty.

Examples:

* Two aircraft assigned to the same gate at the same time
* Aircraft assigned to an incompatible gate
* Invalid output format

## Scored Metrics

Solutions may also be scored on softer performance metrics.

Examples:

* Total delay minutes
* Waiting time
* Taxi or towing time
* Gate idle time
* Number of reassignments
* Passenger walking distance
* Airline preference satisfaction
* Recovery time after disruptions
* Robustness under missing or changing data

The final evaluator may use airport layouts and flight schedules that are different from the examples provided.

---

# Example Score Output


The exact scoring rules may differ during final evaluation.

---

# Design Tips

* Keep an internal record of gates, aircraft, and assignments.
* Validate an assignment before committing it.
* Do not assume all gates are identical.
* Think carefully before reassigning an aircraft that was already assigned.
* Make your simple solution correct before making it clever.

---

# Deliverables

Your team should submit:

* `solution.py`
* Any helper files needed by your solution
* A short explanation of your approach
* Optional visualizations, dashboards, UI, or simulations
* A list of assumptions and edge cases handled

During judging, be ready to explain:

* How your solution prevents conflicts
* How it handles invalid data
* How it responds to delays or outages
* What optimization strategy you used
* What limitations remain
