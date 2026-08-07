# Brock Solutions Airport Automation Challenge

![Aerial view of Toronto Pearson International Airport](images/yyz.jpg)

Created by Engineering IDEAs Clinic co-op students.

## Accessibility

This README uses descriptive headings, meaningful link names, short sections, and alt text for images so it is easier to navigate with screen readers and other assistive technologies. The challenge also welcomes accessible solutions that work for people with different needs and levels of technical experience.

## Table of Contents

- [Accessibility](#accessibility)
- [Quick Links](#quick-links)
- [Your Mission](#your-mission)
- [Sub-Problems](#sub-problems)
  - [Baggage Handling System](#baggage-handling-system)
  - [Gate Management System](#gate-management-system)
  - [Air Traffic Control System](#air-traffic-control-system)
  - [Departure Control System](#departure-control-system)
- [Development Approach](#development-approach)
- [Submission](#submission)
- [Judging Criteria](#judging-criteria)
- [General Resources](#general-resources)

## Quick Links

> **Navigation tip:** Use the headings in this document to move quickly between sections. Screen reader users can navigate by heading level.

- [Baggage Handling System challenge](baggage-handling-system/README.md)
- [Gate Management System challenge](gate-management-system/README.md)
- [Air Traffic Control challenge](air-traffic-control/README.md)
- [Departure Control System challenge](departure-control-system/README.md)
- [Submission expectations](#submission)
- [Judging rubric](#judging-criteria)

## Your Mission

Modern airports rely on connected systems to move passengers, aircraft, baggage, and staff safely and efficiently. Brock Solutions builds and integrates software for these real airport operations.

In this challenge, your team has been invited to prototype a software or software-adjacent solution for an airport automation problem. You may extend the supplied code, combine ideas from several sub-problems, or create a related solution of your own. Your solution should be realistic enough to connect to airport operations, but focused enough to prototype during the challenge.

Toronto Pearson International Airport (YYZ) is the setting for this challenge. Think like an airport systems engineer:

- expect incomplete, late, or conflicting data
- consider safety, privacy, accessibility, and operational constraints
- build a simple working version before adding complexity
- explain the decisions and trade-offs behind your design
- show how your idea could connect to a larger airport system

Airport systems are message driven and closely connected. A passenger update in a Departure Control System can affect baggage handling, aircraft readiness, gate planning, and the operational information used by other teams. Your prototype does not need to model the whole airport, but it should understand where it fits.

Whatever you build, use the [judging criteria](#judging-criteria) to guide your decisions and demonstration.

## Sub-Problems

### [Baggage Handling System](baggage-handling-system/README.md)

A Baggage Handling System (BHS) identifies, tracks, routes, and sorts bags through scanners, conveyors, diverters, make-up areas, and carousels. A bad routing decision can delay a passenger, a flight, or an entire baggage pier.

#### Challenge

Your challenge is to design a BHS that can identify, track, route baggage through a simplified baggage handling environment, and detect anomalies or foreign objects on conveyor systems to ensure operational safety.

![Baggage moving through an airport conveyor system](images/conveyor_system.webp)

#### Potential Directions

Potential solution directions:

* Barcode, RFID, or simulated tag-based bag identification
* Real-time bag state tracking dashboard
* Routing logic for conveyors and carousels
* Error handling for unreadable, oversized, overweight, fragile, or untagged bags
* Foreign object or anomaly detection on conveyor tracks
* Zone-based detection alerts for baggage systems
* Emergency stop, slowdown, or warning signals for conveyor operations
* Simulation of bag movement through a simplified conveyor network
* Privacy-conscious tracking that avoids unnecessary passenger personal information

Your solution may be software-only, hardware-assisted, simulation-based, or a mix of all three.

[Open the Baggage Handling System challenge](baggage-handling-system/README.md).

### [Gate Management System](gate-management-system/README.md)

![Example of aircraft being assigned to airport gates](images/gate_assgt.png)

A Gate Management System (GMS) assigns aircraft to gates while considering timing, aircraft size, passenger needs, customs rules, cargo restrictions, outages, and delays. A gate plan must remain valid as the day changes.

#### Challenge

Your challenge is to produce a conflict-free gate plan and update it when disruption messages arrive. The supplied evaluator checks aircraft-gate compatibility, overlapping occupancy, gate outages, reassignment costs, and other operational rules.

#### Starting Point

This is the most structured coding subproblem. You may write your own assignment algorithm or build a larger tool around the supplied baseline.

[Open the Gate Management System challenge](gate-management-system/README.md).

### [Air Traffic Control System](air-traffic-control/README.md)

![Air traffic controller monitoring aircraft](images/air-traffic-controller.jpg)

Air Traffic Control (ATC) automation combines surveillance reports, flight-plan updates, route information, and controller inputs to estimate where an aircraft is and where it is going. Those messages can be noisy, delayed, incomplete, or contradictory.

#### Challenge

Your challenge is to process a simulated aircraft message stream, reconstruct the likely route, estimate the aircraft state, predict its next waypoint and arrival time, and flag information that should not be trusted without review.

#### Starting Point

The starter kit includes repeatable scenarios, a working tracker, a simulator with known ground truth, optional advanced tools, and a live-aircraft demo.

[Open the Air Traffic Control challenge](air-traffic-control/README.md).

### [Departure Control System](departure-control-system/README.md)

A Departure Control System (DCS) manages the departure side of an airline operation, including check-in, identity and document verification, baggage acceptance, boarding passes, boarding status, and aircraft load control.

#### Challenge

Your challenge is to choose one part of that pipeline and make its state and decisions clear. A strong project might help an operator understand whether a passenger, bag, or flight is ready, what needs attention, and why.

#### Starting Points

Two working examples show an appropriate scope:

- [Unified Identity Gateway](departure-control-system/unified-identity-gateway/README.md), covering identity checks, seat selection, baggage declaration, boarding passes, and agent review
- [Load Control](departure-control-system/load-control/), covering aircraft weight-and-balance optimization

![Departure control system workflow](images/dcs.png)

[Open the Departure Control System challenge](departure-control-system/README.md).

## Development Approach

1. Choose one clear operational problem.
2. Run or inspect the supplied example before changing it.
3. Build the smallest complete version of your idea.
4. Add validation and handle a few meaningful edge cases.
5. Test the same inputs before and after each change.
6. Add one distinctive feature if time allows.
7. Prepare a short demonstration and explain your trade-offs.

A reliable, understandable prototype is stronger than several unfinished features.

## Submission

Teams will give a short presentation of about 3 to 5 minutes. Include:

- the problem you chose and who it affects
- how your solution works
- the prototype, simulation, dashboard, or hardware demonstration
- the constraints and edge cases you considered
- the result you achieved
- what you would improve with more time

Your submission may include code, a dashboard, a simulation, a hardware and software demonstration, a design with partial implementation, or a combination of these.

## Judging Criteria

### Ideation

| Category | What judges are looking for | Score |
| --- | --- | --- |
| Relevance | The solution addresses a meaningful airport problem. | /3 |
| Reasonability | The idea and assumptions are sensible. | /3 |
| Impact | The solution could help its intended users or stakeholders. | /3 |

### Feasibility

| Category | What judges are looking for | Score |
| --- | --- | --- |
| Cost | The cost to build and operate the solution is realistic. | /3 |
| Return on investment | The expected benefit is worth the effort and cost. | /3 |
| Practicality | The solution could fit into a real operational environment. | /3 |
| Reliability | The design considers failures, recovery, and downtime. | /3 |

### Prototype Execution

| Category | What judges are looking for | Score |
| --- | --- | --- |
| Functionality | The prototype works during judging. | /8 |
| Build quality | The implementation or physical prototype is well made. | /3 |

### Safety and Regulations

| Category | What judges are looking for | Score |
| --- | --- | --- |
| Employee and operator safety | The design accounts for risks to workers and users. | /3 |
| Regulatory awareness | The team identifies relevant Canadian or international requirements. | /3 |

### Demo and Presentation

| Category | What judges are looking for | Score |
| --- | --- | --- |
| Clarity | The team explains the problem and solution clearly. | /5 |
| Depth | The team shows meaningful understanding of the problem. | /5 |
| Demo | The demonstration makes the result easy to understand. | /5 |

Coding subproblems may also use hidden test cases to check whether solutions work beyond the visible examples.

## General Resources

Depending on the subproblem, the repository includes starter code, JSON messages, schedules, airport data, demo scripts, evaluators, simulations, and reference implementations. Do not assume the visible examples cover every case.

Useful topics and tools include:

- airport systems integration and event-driven software
- optimization, simulation, and visualization
- `numpy`, `pandas`, `matplotlib`, `scipy`, `networkx`, `simpy`, and `pulp`
- Canadian Aviation Security Regulations and Canadian accessibility requirements
- International Air Transport Association (IATA) and International Civil Aviation Organization (ICAO) guidance

You may use other tools when they are appropriate for your solution. Reference external data, libraries, and research clearly in your final documentation.
