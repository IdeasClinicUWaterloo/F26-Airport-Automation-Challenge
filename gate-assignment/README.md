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
| Airline preferences         | Business rules and stakeholder constraints      |
| Hidden test scenarios       | Robustness against real operational variability |

---

## What You Are Building

You will write your gate assignment logic in `solution.py`.

The evaluator will read flight schedule information, gate information, and flight update messages from JSON files. These messages follow the project's JSON flight message specification. To keep the challenge focused, the evaluator will convert the messages into simpler flight and gate update calls before passing them to your solution.

Your job is to decide which gate each aircraft should use and to update those decisions when new information arrives.

---

## Core Requirements

Your solution must:

- Assign arriving and departing flights to valid gates
- Avoid gate occupancy conflicts
- Respect aircraft-gate compatibility
- Account for aircraft size limits
- Account for jet bridge requirements where applicable
- Respect domestic, international, cargo, and security restrictions
- Handle delays and cascading schedule changes
- Handle missing, corrupted, or incomplete data safely
- Reassign flights efficiently when disruptions occur
- Produce clear output that the evaluator can check

A solution that works only for the provided sample scenario is not enough. Your logic should generalize to different airport layouts and schedules.

---

## Example Constraints

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

## Starter Files

This folder may include files such as:

- `solution.py` — where you implement your algorithm
- `evaluator.py` — used to test your solution
- `JsonFlightMessageSpecification.md` — describes the JSON message format
- `simple.json`, `cascade_1.json`, `cascade_2.json` — example flight schedule JSON files
- `static_info.json` — gate and aircraft information

Do not modify the evaluator unless the challenge staff specifically tells you to. Your submitted logic should be in `solution.py`.

---

## Suggested Solution Approaches

There is no single correct algorithm. You can use any approach that produces valid, robust assignments.

---

## Evaluation

Your solution may be evaluated using visible tests and hidden tests.

### Hard Failures

Hard failures may stop the simulation or produce a major penalty.

Examples:

- Two aircraft assigned to the same gate at the same time
- Aircraft assigned to an incompatible gate
- Invalid output format

### Scored Metrics

Solutions may also be scored on softer performance metrics.

Examples:

- Total delay minutes
- Waiting time
- Taxi or towing time
- Gate idle time
- Number of reassignments
- Passenger walking distance
- Airline preference satisfaction
- Recovery time after disruptions
- Robustness under missing or changing data

The final evaluator may use airport layouts and flight schedules that are different from the examples provided.

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