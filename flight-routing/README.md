# Probabilistic Flight Tracking for Air Traffic Control

## Challenge Overview

In real aviation systems, aircraft tracking is not just about drawing a line between reported points. Automation software must answer questions such as:

* Where is the aircraft likely to be right now?
* Which route hypothesis best explains the messages received so far?
* How uncertain is the current estimate?
* Which waypoint is the aircraft most likely heading toward?
* What is the estimated arrival time?
* Did a new message confirm the current route, modify it, or contradict it?
* Is a message suspicious enough to flag for review?

This challenge captures the core software ideas behind those questions without requiring students to build a full production-grade ATC system.

## Industry Context

Modern Air Traffic Control and Air Traffic Management systems are large, safety-critical software ecosystems. They combine surveillance data, flight plans, aircraft intent, weather information, controller inputs, and operational constraints to maintain a live picture of aircraft moving through controlled airspace.

In real operations, no single data source is treated as perfect. Aircraft position may come from radar, ADS-B, multilateration, Mode-S, satellite-based surveillance, or other surveillance feeds. Flight intent may come from flight plans, route clearances, trajectory predictions, airline operations systems, or controller updates. These sources can arrive at different rates, with different levels of accuracy, and sometimes with conflicting information.

This is why modern ATC software uses concepts such as:

* Surveillance data processing
* Flight data processing
* Multi-sensor fusion
* Track correlation
* Trajectory prediction
* Conflict detection
* Safety-net monitoring
* Anomaly detection
* Controller display systems

Systems such as FAA ERAM, FAA STARS, EUROCONTROL ARTAS, and flight data processing platforms used by Air Navigation Service Providers are examples of the broader industry context behind this challenge. These systems maintain tracks, correlate surveillance reports, process flight-plan information, support controller decision-making, and help build a consistent operational picture.

The simplified version in this hackathon focuses on the software ideas behind those systems rather than the full safety-critical operational environment.

At a high level, industry systems work like this:

```text id="nc30tw"
Surveillance reports + flight plan data + operational updates
        ↓
Message validation and normalization
        ↓
Track association and state estimation
        ↓
Trajectory prediction
        ↓
Conflict, anomaly, and consistency checks
        ↓
Controller/operations display and downstream system updates
```

A real system may receive thousands of updates per minute. It must decide whether a new report belongs to an existing aircraft track, whether it contradicts the expected trajectory, whether the aircraft has deviated from its planned route, and how much confidence to place in the latest information.

This challenge captures a simplified version of that problem:

> Given noisy, delayed, incomplete, or conflicting aircraft messages, reconstruct the most likely flight route and estimate the aircraft’s current state.

The advanced parts of this challenge map directly to real software engineering concepts used in aviation, robotics, defense, autonomous vehicles, and sensor-fusion systems:

| Hackathon Concept        | Industry Analogue                                |
| ------------------------ | ------------------------------------------------ |
| Message parsing          | Surveillance and flight message normalization    |
| Route reconstruction     | Flight data processing and trajectory management |
| Dead reckoning           | Track prediction between reports                 |
| Extended Kalman Filter   | Probabilistic state estimation                   |
| Particle filter          | Nonlinear multi-state tracking                   |
| Multi-hypothesis routing | Track ambiguity and route ambiguity management   |
| Innovation monitoring    | Anomaly and spoofing detection                   |
| ETA prediction           | Trajectory prediction                            |
| Map visualization        | Controller and operations display systems        |

The goal is not to build certified ATC software. The goal is to give students a realistic, simplified version of a problem that appears in professional air traffic automation systems: maintaining a trustworthy operational picture from imperfect data.

---

## Challenge Summary

You will build a flight routing and tracking module that consumes a stream of simulated aircraft messages and outputs a continuously updated route estimate.

Your system should:

1. Parse and interpret aircraft messages.
2. Maintain an ordered route state.
3. Estimate the aircraft’s current position and movement state.
4. Predict future position, next waypoint, and ETA.
5. Handle delayed and out-of-order messages.
6. Detect conflicts between messages.
7. Maintain multiple possible route hypotheses when the correct route is ambiguous.
8. Flag suspicious or inconsistent messages.
9. Optionally visualize the estimated route and uncertainty.

---

## Basic Solution Path

A basic solution can treat this as a deterministic reconstruction problem.

Students can:

* Parse each incoming message.
* Extract reported position, altitude, speed, heading, waypoint, and ETA fields.
* Update a route object when new waypoints are reported.
* Compare new messages against the current route.
* Flag obvious conflicts.
* Estimate the next waypoint using the most recent known route.
* Estimate arrival time using simple distance and speed calculations.

This approach is easier to implement and gives students a working baseline.

A basic solution might be called:

> Message Parser and Route Reconstructor

This version is intentionally straightforward. It rewards clean parsing, good data structures, consistency checks, and reasonable route updates.

---

## Advanced Solution Path

An advanced solution can treat the problem as probabilistic aircraft tracking.

Instead of assuming every message is perfectly correct, the system can maintain an estimated aircraft state and uncertainty. As new messages arrive, the estimate is updated. When messages are missing, the system predicts forward. When messages conflict, the system compares different possible explanations.

Advanced techniques may include:

* Extended Kalman Filtering
* Particle Filtering
* Multi-hypothesis tracking
* Innovation-based anomaly detection
* Late-message correction
* Probabilistic route scoring
* Weather-aware or constraint-aware path planning

This version more closely resembles the type of estimation and sensor-fusion logic used in aviation, autonomous systems, robotics, radar tracking, and defense applications.

---

## State Estimation

The aircraft state may include:

* Latitude
* Longitude
* Altitude
* Ground speed
* Vertical speed
* Heading
* Fuel estimate
* Current route index
* Next waypoint
* Estimated time of arrival
* Uncertainty values

The tracker should perform two core operations:

### Predict

When no new message has arrived, the tracker predicts the aircraft’s next state using a simplified flight dynamics model.

For example, it may estimate:

* How far the aircraft has traveled since the last update.
* Whether altitude should have increased, decreased, or remained stable.
* Whether the aircraft should be closer to the next waypoint.
* How uncertainty grows over time.

### Update

When a new message arrives, the tracker updates its state estimate.

For example, it may:

* Pull the estimated position closer to the reported position.
* Reduce uncertainty after a reliable message.
* Increase uncertainty if the message conflicts with previous data.
* Recalculate the next waypoint and ETA.
* Flag the message if the mismatch is too large.

A strong implementation should show uncertainty increasing when messages are sparse and decreasing when reliable messages arrive.

---

## Multi-Hypothesis Routing

Sometimes one route explanation may not be enough.

For example:

* One message says the aircraft is proceeding to waypoint A.
* A later message suggests the aircraft may have been rerouted to waypoint B.
* Another message arrives late and appears to support the original route.
* A weather constraint may make one route less likely.
* A reported ETA may only make sense under one hypothesis.

Instead of immediately discarding one explanation, the system can maintain multiple route hypotheses.

Each hypothesis should have:

* A route candidate.
* A current aircraft state.
* A probability or weight.
* A consistency score.
* A history of supporting and conflicting messages.

As more messages arrive, the system should update the weights, prune unlikely hypotheses, and select the most likely current route.

---

## Anomaly Detection

The system should flag messages that are inconsistent with the current estimate.

Examples of suspicious messages include:

* A position jump that is physically unrealistic.
* An altitude change that is too large for the elapsed time.
* A heading that conflicts with the route geometry.
* A reported waypoint that does not match the aircraft’s trajectory.
* An ETA that is impossible given the current speed and distance.
* A route update that contradicts several recent reliable messages.
* A delayed message that would have been plausible earlier but no longer matches the current state.

Advanced solutions may use innovation-based anomaly detection. In this approach, the system compares the predicted state to the observed message. If the difference is too large relative to the expected uncertainty, the message is flagged.

---

## Autonomous Mapping and Path Planning

As a stretch goal, teams may add autonomous route planning.

In this version, the system does not only reconstruct the route; it can also reason about better or safer routes.

For example, the system may:

* Avoid storm cells or restricted areas.
* Infer the likely destination from partial route data.
* Use A*, Dijkstra’s algorithm, or another graph-search method to find a feasible path.
* Score candidate routes by distance, fuel cost, delay, safety margin, or weather risk.
* Suggest a reroute when the current route appears inconsistent or blocked.

This component is optional, but it creates a natural connection between flight tracking, optimization, and autonomous planning.

---

## Front-End Visualization

Teams may optionally build a front-end display.

A useful visualization could include:

* A map of the current estimated route.
* The aircraft’s latest reported position.
* The tracker’s estimated current position.
* The next predicted waypoint.
* ETA values.
* Route alternatives.
* Uncertainty ellipses or confidence regions.
* Alerts for suspicious messages.
* A timeline of received messages and delayed corrections.

This is not required for the core evaluator, but it can make the project much easier to understand and demo.

---

## Repository Structure

```text

```

---

## Inputs

The evaluator provides a stream of simulated aircraft messages.

Messages may include:

* Aircraft identifier
* Timestamp
* Latitude and longitude
* Altitude
* Speed
* Heading
* Fuel estimate
* Current waypoint
* Next waypoint
* ETA
* Route update
* Weather or constraint indicator

Messages may arrive:

* In order
* Out of order
* Late
* With noise
* With missing fields
* In conflict with earlier messages

---

## Expected Outputs

Your solution should output an updated route and tracking estimate after processing the message stream.

Expected outputs may include:

* Current estimated position
* Current estimated altitude
* Current estimated speed and heading
* Current route hypothesis
* Next waypoint
* Estimated arrival time
* Uncertainty estimate
* List of detected conflicts
* List of anomaly alerts
* Final reconstructed route

---

## Evaluation Ideas

Solutions can be scored on:

### Route Reconstruction Accuracy

How close is the reconstructed route to the true route?

### State Estimation Accuracy

How close is the estimated aircraft position, altitude, speed, and heading to the true simulated state?

### ETA Accuracy

How close are predicted arrival times to the ground truth?

### Conflict Handling

Does the solution correctly identify contradictory messages?

### Late Message Handling

Can the solution correctly incorporate delayed or out-of-order messages?

### Hypothesis Management

Does the solution maintain and select the correct route hypothesis when the route is ambiguous?

### Anomaly Detection

Does the solution flag suspicious messages without creating too many false alarms?

### Code Quality

Is the solution modular, readable, and maintainable?

### Optional Visualization

Does the solution clearly display route, uncertainty, and alerts?

---

## Suggested Student Milestones

### Milestone 1: Working Parser

Parse all message types into structured Python objects.

### Milestone 2: Deterministic Route State

Maintain a route and update it when new waypoint messages arrive.

### Milestone 3: Basic Prediction

Estimate current position and ETA using speed, heading, and waypoint distance.

### Milestone 4: Consistency Checks

Detect impossible jumps, conflicting waypoints, and invalid ETAs.

### Milestone 5: EKF or Particle Filter

Add probabilistic state estimation with uncertainty.

### Milestone 6: Multi-Hypothesis Tracking

Maintain several possible route explanations and select the most likely one.

### Milestone 7: Anomaly Detection

Use prediction error or innovation magnitude to flag suspicious messages.

### Milestone 8: Visualization

Display the route, aircraft state, uncertainty, and alerts on a map.

---

## Real-World Connection

This challenge is inspired by real problems in aviation automation.

Similar ideas appear in:

* Surveillance data processing
* Flight data processing
* Radar and ADS-B tracking
* Sensor fusion
* Trajectory prediction
* Conflict detection
* GNSS/ADS-B anomaly detection
* Controller decision-support tools
* Autonomous vehicle perception
* Defense and missile-tracking systems

For Air Traffic Control in particular, the following are some existing systems which manage and track flights:

ARTAS - 

The hackathon version is simplified. It does not attempt to reproduce any specific operational ATC system, safety-critical process, or certified aviation software. Instead, it gives students a controlled environment to practice the underlying software engineering and algorithmic ideas.

---

## Recommended Framing for Teams

There are two valid ways to approach this challenge.

The baseline approach is to build a reliable message parser and route reconstructor.

The advanced approach is to build a probabilistic flight tracker that can reason under uncertainty.

Both approaches are valuable. However, teams that successfully combine parsing, route state management, probabilistic tracking, hypothesis management, and anomaly detection will produce a system that feels much closer to real-world air traffic automation software.

---

## Final Goal

By the end of the challenge, your system should be able to read a messy stream of aircraft messages and answer:

> “Where is this aircraft most likely going, where is it now, when will it arrive, and which messages should we not fully trust?”
