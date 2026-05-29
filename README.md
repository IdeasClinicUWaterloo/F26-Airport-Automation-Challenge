# Brock Solutions Airport Automation Challenge

Created by: Engineering IDEAs Clinic Co-op Students

## Quick Links



---

# Your Mission

Modern airports rely on many connected software systems to keep passengers, aircraft, baggage, and staff moving safely and efficiently. Brock Solutions works with airport clients to integrate systems that support real-world airport operations.

In this challenge, your team has been invited to prototype a software or software-adjacent solution for an airport automation problem. Your solution should be realistic enough to connect to airport operations, but focused enough to prototype during the challenge.

You are encouraged to think like an airport systems engineer: handle messy data, think about safety and reliability, consider real operational constraints, and design something that could eventually integrate into a larger airport system.

---

# Airport Systems Orientation

Before choosing a subproblem, you should understand a few airport system concepts.

## BHS — Baggage Handling System

A Baggage Handling System tracks, routes, diverts, and sorts bags through conveyors, scanners, carousels, and make-up areas. These systems must be reliable because one wrong routing decision can delay a passenger, flight, or entire baggage pier.

## DCS — Departure Control System

A Departure Control System manages passenger check-in, boarding, flight closeout, and aircraft readiness data. DCS-style messages may include flight numbers, aircraft types, departure stations, arrival stations, passenger/cargo context, and timing updates.

## GMS — Gate Management System

A Gate Management System helps airports assign aircraft to gates while considering gate availability, aircraft size, passenger convenience, international/domestic rules, cargo restrictions, and disruptions such as delays or outages.

## Message-Driven Airport Operations

Airport systems often communicate through message streams. In a real airport, this may involve queues, event streams, or integration middleware. For this challenge, some subproblems may provide simplified JSON messages or simulator data so that you can focus on the logic of your solution.

---

# Subproblems

## 1. Bag Tracking and Sorting

Airports move huge volumes of baggage every day through networks of conveyors, scanners, diverters, and carousels. Your challenge is to design a system that can identify, track, and route baggage through a simplified baggage handling environment.

Potential solution directions:

* Barcode, RFID, or simulated tag-based bag identification
* Real-time bag state tracking dashboard
* Routing logic for conveyors and carousels
* Error handling for unreadable, oversized, overweight, fragile, or untagged bags
* Simulation of bag movement through a simplified conveyor network
* Privacy-conscious tracking that avoids unnecessary passenger personal information

Your solution may be software-only, hardware-assisted, simulation-based, or a mix of all three.

---

## 2. Human / Foreign Object Intrusion Detection

Baggage and airport operations areas can create safety risks when people or foreign objects enter restricted zones. Your challenge is to design a detection system that identifies unsafe human or object presence near conveyor or operational infrastructure.

Potential solution directions:

* Computer vision detection of humans in restricted zones
* Foreign object detection near conveyor tracks
* Zone-based intrusion alerts
* Emergency stop, slowdown, or warning signals
* Handling partial visibility, occlusion, and false positives
* Visual dashboard for safety monitoring

Your system does not need to directly control baggage flow. It should provide reliable safety signals that another system could act on.

---

## 3. Airplane Gate Assignment

Airports must dynamically assign gates to aircraft while balancing efficiency, passenger experience, safety, airline preferences, and unpredictable disruptions.

Your challenge is to design a system that assigns airport gates to arriving and departing flights over time.

Your solution should:

* Respect aircraft-gate compatibility
* Avoid gate occupancy conflicts
* Handle domestic, international, cargo, and security constraints
* Adapt to delays, gate outages, emergencies, and cascading schedule changes
* Minimize delays, reassignments, passenger walking distance, and wasted gate time

This is the primary coding-focused subproblem. Teams will write their logic in `solution.py`, and their solution will be evaluated against visible and hidden test scenarios.

Learn more: 

---

## 4. Flight Route Interpretation

Aircraft often operate across multiple legs, route changes, delays, and partial messages. Your challenge is to design a system that receives flight messages and reconstructs the aircraft’s current planned or actual route.

Potential solution directions:


This subproblem emphasizes state management, data interpretation, estimation, filtering noise for messages, considering the physics of the flight, etc.

---

# Provided Materials

Depending on the subproblem, you may be given:

* Starter Python code
* Example JSON messages
* Flight schedule and airport layout data
* Demo scripts
* Sample solution files
* Evaluator scripts
* Simulator documentation
* Reference resources and academic papers

Do not assume the visible sample data covers every case. Final evaluation may include additional layouts, disruptions, corrupted data, and edge cases.

---

# Recommended Development Approach

1. Understand the airport operation you are modeling.
2. Build a simple working solution first.
3. Add validation and error handling.
4. Test obvious edge cases.
5. Test unrealistic but possible edge cases.
6. Optimize only after the solution is correct.
7.	Innovate! Add interesting and unique ideas that you have, if you find that the original problem is too easy.
8. Prepare a clear explanation of your design decisions.

A simple, reliable, well-explained prototype is better than a complex system that only works on the sample input.

---

# Submission

Teams will present a short 3–5 minute explanation of their solution to the judging panel.

Your presentation should include:

* The problem you chose
* Your system design
* Your prototype or simulation
* Key constraints you considered
* Edge cases you handled
* What you would improve with more time

Your prototype may be:

* Code
* A dashboard
* A simulation
* A hardware/software demonstration
* A design with partial implementation
* Any combination of the above

---

# Judging Criteria

You will be evaluated on the following categories.

| Category              | What Judges Are Looking For                                                    |
| --------------------- | ------------------------------------------------------------------------------ |
| Problem Understanding | Clear connection to airport operations and real constraints                    |
| Functionality         | Prototype works on the provided scenario or demonstrates the core idea         |
| Reliability           | Handles missing data, invalid states, edge cases, or failure modes             |
| Optimization          | Makes thoughtful tradeoffs around time, cost, distance, safety, or efficiency  |
| Safety and Security   | Considers operational safety, access control, privacy, or security constraints |
| Creativity            | Uses an interesting or practical approach                                      |
| Presentation          | Clearly explains the system, decisions, limitations, and next steps            |

For coding subproblems, hidden test cases may be used to evaluate whether your solution generalizes beyond the sample data.

---

# Resources

Suggested resource areas:

* Airport systems integration
* Baggage Handling Systems
* Departure Control Systems
* Gate Management Systems
* Airport common-use systems
* Message queues and event-driven software
* Optimization algorithms
* Simulation and visualization tools

Useful Python libraries may include:

* `numpy`
* `pandas`
* `matplotlib`
* `scipy`
* `networkx`
* `simpy`
* `pulp`

You may use other tools if they are appropriate for your solution.

---

# Final Note

This challenge is not only about building the most complete prototype. It is about showing that you can think through a real operational system, identify constraints, make tradeoffs, and design something that could eventually scale into an airport environment.
