# Departure Control System Automation

A Departure Control System (DCS) manages the work required to prepare passengers and an aircraft for departure. It connects check-in, identity and document checks, baggage acceptance, seat assignments, boarding passes, boarding status, and aircraft load control.

These activities cannot operate as isolated checkpoints. A document problem may block boarding, a baggage update may affect aircraft load, and a late passenger may change the flight's readiness. Staff need one clear view of what is complete, what is blocked, and what needs manual attention.

This subproblem asks you to build a useful solution somewhere in that pipeline. You may concentrate on one process or connect several processes together.

## Table of Contents

- [Challenge](#challenge)
- [Potential Solutions](#potential-solutions)
- [Getting Started](#getting-started)
- [Evaluation](#evaluation)
- [Resources](#resources)

## Challenge

Develop a solution that improves one part of passenger or aircraft departure processing.

Your project might answer a question such as:

- Is this passenger identified and cleared for travel?
- Which passengers or bags need staff review?
- Is the aircraft load within structural and balance limits?
- Has each bag reached the expected checkpoint?
- Is the flight ready to close and board?
- Can an operator understand the current state from one screen?

Successful solutions should consider:

- a clear model for passengers, bags, flights, or aircraft zones
- traceable state changes and decisions
- missing, late, or conflicting data
- useful explanations when an item is blocked or flagged
- privacy, accessibility, and staff override workflows
- a scope that can be completed and demonstrated clearly

### Industry Context

Airline departure operations rely on passenger records, schedules, seat maps, aircraft configuration, baggage data, document checks, boarding status, and load constraints. All of that information can change until the aircraft departs.

A DCS sits at the centre of this operation. It takes in passenger and booking data, runs check-in, accepts bags, validates documents, issues boarding passes, tracks boarding, and feeds aircraft load control.

Passenger processing is not a set of isolated checkpoints. Identity verification, baggage acceptance, security status, boarding, and manual-review decisions all update the same view of passenger and flight readiness. Real systems in this area include Brock Solutions SmartSuite Enterprise, SITA Horizon DCS, and Amadeus Altéa Departure Control.

The industry is also moving from manually supervised, rule-based workflows toward decision-support tools that estimate bag counts, identify group behaviour, flag no-show risk, and recommend load or staffing actions before a problem reaches the gate.

### Typical Data Flow

1. Load passenger, booking, flight, and aircraft data.
2. A passenger checks in and verifies their identity.
3. Documents are validated and uncertain cases are flagged for review.
4. Bags are accepted, tagged, and linked to the passenger.
5. Bag scans update the live baggage state.
6. Passenger and cargo load is estimated across aircraft zones.
7. The system recommends seat, bag, load, or review actions.
8. An operational view shows passenger and flight readiness.

Your solution does not need to cover this entire flow, but its data and decisions should connect clearly to the rest of the departure process.

### How This Maps to Real Systems

| Challenge concept | Industry analogue |
| --- | --- |
| Check-in flow | DCS passenger acceptance |
| Identity and document entry | Passport, visa, and identity verification |
| Boarding-pass generation | Departure-control passenger acceptance |
| Bag-tag creation | Baggage acceptance and reconciliation |
| Scan events | Baggage Handling System tracking |
| Bag-status dashboard | Baggage operations monitoring |
| Predicted bag count | Passenger behaviour and load forecasting |
| Seat or load recommendation | Aircraft load control |
| Manual-review flags | Agent intervention and exception handling |
| Unified operations dashboard | Departure-readiness control |

### State to Track

Model the entities your problem needs clearly enough that each change can be traced.

- **Passenger:** identity, booking, flight, seat, document status, and boarding status
- **Baggage:** tag ID, passenger, location or status, weight, and exceptions
- **Flight:** aircraft type, seat map, cabin and cargo zones, load, and readiness

### Inputs and Expected Outputs

Inputs may include passenger lists, bookings, seat maps, aircraft layouts, baggage records, scan events, document fields, and schedules. Expect missing fields, late updates, conflicting counts, and inconsistent scans.

Whatever your solution produces should make departure readiness understandable. Show the current status, the decisions made, the exceptions that need attention, and the reason behind each result.

## Potential Solutions

The examples below show several possible scopes. You may extend one of them or build something different.

| Potential solution | Description | Starting point |
| --- | --- | --- |
| Unified identity gateway | Combine booking lookup, document checks, seat selection, baggage declaration, boarding passes, and agent review. | [Working implementation](unified-identity-gateway/README.md) |
| Aircraft load control | Assign passenger and cargo load to aircraft zones while respecting weight and balance limits. | [`load-control/`](load-control/) |
| Passenger-processing monitor | Track passengers through checkpoints and highlight congestion or incomplete steps. | [Passenger-processing ideas](passenger-processing/README.md) |
| Document-review assistant | Validate required fields, identify mismatches, and route uncertain cases to an agent. | [Identity-gateway rules](unified-identity-gateway/apps/api/src/rules/) |
| Boarding-readiness dashboard | Combine document, seat, baggage, and boarding state into one operator view. | [Unified Identity Gateway](unified-identity-gateway/README.md) |
| Baggage reconciliation tool | Link accepted bags to passengers and explain missing or unexpected scans. | [Baggage Handling System](../baggage-handling-system/README.md) |

Teams may also explore forecasting, staff allocation, accessible passenger support, audit logging, or another departure-related need.

### Basic and Advanced Approaches

**Basic:** Build a deterministic workflow on mock data with clear models, rule-based checks, traceable state changes, and a readable interface.

**Advanced:** Build a predictive decision-support system that estimates what is likely to happen and recommends an action before every input is known.

An advanced approach might predict baggage volume, detect passenger groups, estimate no-show risk, recommend seat or cargo changes, prioritize agent review, or explain why a flight is not ready.

### Optional Extensions

You can extend any approach with richer data, predictions, a stronger operator interface, accessible passenger support, or an audit log for staff overrides.

## Getting Started

Choose one of these paths:

### Explore a Working Check-In System

The [Unified Identity Gateway](unified-identity-gateway/README.md) is a full-stack example with a React web app, Fastify API, PostgreSQL database, and rule-based status engine.

Use it when your team wants to improve identity checks, passenger experience, agent workflows, accessibility, or auditability.

### Explore Aircraft Load Control

The [`load-control/`](load-control/) example contains a mixed-integer linear programming optimizer in `load.py`. It assigns passenger and cargo load to aircraft bays and cabin zones, aims for a target centre of gravity, and respects structural and zero-fuel-weight limits. The `weight_balancer_app/` folder exposes the optimizer through a small Flask interface.

Use it when your team is interested in optimization, structural limits, center of gravity, or visual decision support.

### Design an Independent Prototype

The [passenger-processing guide](passenger-processing/README.md) lists projects that can be built with mock data, simulations, dashboards, or simple rules. A paper prototype or focused front end is acceptable when it clearly demonstrates the decision or workflow.

### Suggested Milestones

1. **Mock data and core models:** Define the passengers, bags, flights, aircraft zones, or other entities your solution needs.
2. **Core flow:** Make the main workflow run from input to result.
3. **Exception handling:** Add missing, conflicting, blocked, or review cases and explain them.
4. **Decision support:** Add a prediction or recommendation if it supports your idea.
5. **Operational view:** Make the current state and outstanding work visible in one place.
6. **Polish:** Improve test data, edge cases, accessibility, and the demonstration flow.

## Evaluation

When reviewing your solution, consider:

| Area | What to look for |
| --- | --- |
| Workflow completeness | Does the process work from input to result? |
| Data modelling | Are passengers, bags, flights, seats, or load zones represented clearly? |
| Decision quality | Are recommendations, predictions, and review flags useful? |
| Exception handling | Does the system handle missing or inconsistent data? |
| Dashboard clarity | Can an operator understand readiness and outstanding work quickly? |
| Privacy and accessibility | Is sensitive data minimized, and is feedback usable by people with different needs? |
| Code quality | Is the implementation modular, readable, and maintainable? |
| Demonstration | Does the demo make the value and limitations clear? |

The final goal is to make three things clear: the current state of the problem, what needs attention, and why. That is the same question real DCS platforms answer before an aircraft pushes back.

## Resources

### Challenge Resources

- [Unified Identity Gateway implementation](unified-identity-gateway/README.md)
- [Passenger-processing project ideas](passenger-processing/README.md)
- [Load-control implementation](load-control/)
- [Identity-gateway challenge specification](unified-identity-gateway/docs/challenge-spec.md)

### Safety, Privacy, and Industry References

- [IATA Resolution 753 baggage-tracking implementation guide](https://www.iata.org/contentassets/5c4aa8b8b3b1432697d2bf3301450684/reso753-implementation-guide---2023_issue-4.02.pdf): baggage tracking at defined handoff points
- [ICAO Doc 9303 machine-readable travel documents](https://www.icao.int/publications/pages/publication.aspx?docnum=9303): international specifications for machine-readable passports and identity documents
- [ICAO Annex 9: Facilitation](https://www.icao.int/facilitation-programmes/Annex9): international passenger, border, and document-control context
- [ICAO Annex 6: Operation of Aircraft](https://store.icao.int/en/annex-6-operation-of-aircraft): international aircraft-operation context, including mass and balance responsibilities
- [IATA Weight and Balance Manuals](https://www.iata.org/en/publications/manuals/weight-balance-manuals/): airline load-control procedures and data standards
- [Canadian Aviation Security Regulations, 2012](https://laws-lois.justice.gc.ca/eng/regulations/SOR-2011-318/index.html)
- [Secure Air Travel Regulations](https://laws-lois.justice.gc.ca/eng/regulations/SOR-2015-181/FullText.html)
- [Personal Information Protection and Electronic Documents Act](https://laws-lois.justice.gc.ca/eng/acts/P-8.6/index.html)
- [Accessible Transportation for Persons with Disabilities Regulations](https://laws-lois.justice.gc.ca/eng/regulations/SOR-2019-244/index.html)

Real departure systems require formal security, privacy, accessibility, and operational review. Treat the supplied projects as learning prototypes.
