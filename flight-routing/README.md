# Air Traffic Control System

## Challenge Overview

In real aviation systems, aircraft tracking is not just about drawing a line between reported points. Automation software must answer questions such as:

- Where is the aircraft likely to be right now?
- Which route hypothesis best explains the messages received so far?
- How uncertain is the current estimate?
- Which waypoint is the aircraft most likely heading toward?
- What is the estimated arrival time?
- Did a new message confirm the current route, modify it, or contradict it?
- Is a message suspicious enough to flag for review?

This challenge captures the core software ideas behind those questions without requiring students to build a full production-grade ATC system.

**Note: In real world scenarios, flight messages are received in a much greater quantity within a short period of time. For this challenge, you will be given spaced out, delayed, and incomplete messages to encourage and build skills in state estimation.**

---

## Industry Context

### How Aircraft Are Tracked in the Real World

Modern Air Traffic Control and Air Traffic Management systems are among the most complex, safety-critical software ecosystems in existence. They combine surveillance data, flight plans, aircraft intent, weather information, controller inputs, and operational constraints to maintain a continuously updated picture of every aircraft moving through controlled airspace.

No single data source is treated as perfect. Aircraft position may come from primary radar, secondary radar, ADS-B (Automatic Dependent Surveillance–Broadcast), multilateration, Mode-S transponders, satellite-based surveillance, or a combination of several feeds. Flight intent comes from filed flight plans, route clearances, trajectory predictions from airline operations systems, and controller updates. These sources arrive at different rates, carry different levels of accuracy, and sometimes contradict each other.

This is why modern ATC software does not simply display the last known position of an aircraft. It fuses multiple data streams, estimates the most likely current state, predicts where the aircraft is heading, and flags anything that looks inconsistent or suspicious. This class of software engineering, combining noisy, delayed, and conflicting inputs into a reliable operational picture, is called surveillance data processing, track management, or more broadly, sensor fusion.

### Real Systems That Solve This Problem

Several operational systems in use today embody these ideas:

**FAA ERAM (En Route Automation Modernization)** is the United States' primary en-route ATC system, replacing the older HOST system. It processes surveillance data from across the national airspace, maintains track files for thousands of aircraft simultaneously, performs trajectory prediction, and supports controller decision-making across Air Route Traffic Control Centers (ARTCCs).

**FAA STARS (Standard Terminal Automation Replacement System)** handles the terminal domain, where aircraft are arriving and departing and the pace of updates is much faster. STARS correlates radar returns with flight plan data and presents controllers with a fused, labeled picture of all traffic.

**EUROCONTROL ARTAS (ATM Surveillance Tracker and Server)** is widely deployed across European airspace. ARTAS is specifically designed as a multi-sensor tracker: it receives inputs from many different radar and ADS-B stations and fuses them into a single coherent track for each aircraft. It uses advanced filtering and track association algorithms to handle the noise, delays, and gaps that arise from real surveillance infrastructure.

**NAV CANADA's automated flight data processing systems**, used to manage one of the world's largest and most complex airspaces by area, acombining radar surveillance, ADS-B data, and flight plan information into actionable tracks for controllers.

Beyond ATC, similar tracking and estimation problems appear in:

- **Defense and missile tracking systems**, where radar returns must be fused and targets must be distinguished from noise
- **Autonomous vehicle perception**, where LIDAR, camera, radar, and GPS readings are fused into a consistent model of the environment
- **Maritime vessel tracking**, where AIS messages may be delayed, spoofed, or missing
- **Space situational awareness**, where orbital mechanics models are updated with noisy observations to track objects in Earth orbit

### Where Brock Solutions Fits

While Brock Solutions is best known for its **SmartSuite** baggage and passenger operations platform, the broader SmartSuite ecosystem also connects to flight-level data. **SmartSuite Enterprise**, Brock's operational management layer, ingests real-time flight information alongside baggage and passenger data to give airports and airlines a unified view of operations. It consumes flight schedule data, live arrival and departure updates, and gate assignment information, the same categories of flight data that ATC systems produce and downstream airport systems consume.

This makes the connection direct: the flight tracking and state estimation problem you are solving in this challenge represents the upstream source of the live flight data that systems like SmartSuite Enterprise depend on. ATC systems produce the authoritative picture of where aircraft are and when they will arrive; airport operations systems like SmartSuite consume that picture to coordinate baggage, gates, ground handlers, and passengers.

### The Full Data Pipeline

At a high level, the pipeline from surveillance to operations looks like this:

```
Raw surveillance data (radar, ADS-B, multilateration) + filed flight plans
        ↓
Message validation and normalization
        ↓
Track association: does this report belong to a known aircraft?
        ↓
State estimation: where is the aircraft most likely to be right now?
        ↓
Trajectory prediction: where is it going, and when will it arrive?
        ↓
Conflict, anomaly, and consistency checks
        ↓
Controller display + downstream systems (airport ops, baggage, gates, FIDS)
```

A real system may process thousands of surveillance reports per minute. For each report, it must decide whether it belongs to an existing track, whether it contradicts the expected trajectory, whether it represents a genuine route change or a sensor error, and how much confidence to place in the new information. This is not a database lookup, it is a continuous estimation problem.

### How the Hackathon Maps to Real Systems

| Hackathon Concept          | Industry Analogue                                    |
| -------------------------- | ---------------------------------------------------- |
| Message parsing            | Surveillance and flight message normalization        |
| Route reconstruction       | Flight data processing and trajectory management     |
| Dead reckoning             | Track prediction between radar updates               |
| Extended Kalman Filter     | Probabilistic state estimation (used in ARTAS, etc.) |  
| Multi-hypothesis routing   | Track ambiguity and route ambiguity management       |
| Innovation monitoring      | Anomaly and spoofing detection                       |
| ETA prediction             | Trajectory prediction                                |
| Map visualization          | Controller and operations display systems            |

---

## Challenge Summary

You will build a flight routing and tracking module that consumes a stream of simulated aircraft messages and outputs a continuously updated route estimate.

Your system should:

- Parse and interpret aircraft messages
- Maintain an ordered route state
- Estimate the aircraft's current position and movement state
- Predict future position, next waypoint, and ETA
- Handle delayed and out-of-order messages
- Detect conflicts between messages
- Maintain multiple possible route hypotheses when the correct route is ambiguous
- Flag suspicious or inconsistent messages
- Optionally visualize the estimated route and uncertainty

---

## Basic Solution Path

A basic solution can treat this as a deterministic reconstruction problem.

Students can:

- Parse each incoming message
- Extract reported position, altitude, speed, heading, waypoint, and ETA fields
- Update a route object when new waypoints are reported
- Compare new messages against the current route
- Flag obvious conflicts
- Estimate the next waypoint using the most recent known route
- Estimate arrival time using simple distance and speed calculations

This approach is easier to implement and gives students a working baseline. A basic solution might be called a Message Parser and Route Reconstructor. It rewards clean parsing, good data structures, consistency checks, and reasonable route updates.

---

## Advanced Solution Path

An advanced solution treats the problem as probabilistic aircraft tracking, the approach used in real ATC systems like ARTAS and ERAM.

Instead of assuming every message is perfectly correct, the system maintains an estimated aircraft state and uncertainty. As new messages arrive, the estimate is updated. When messages are missing, the system predicts forward. When messages conflict, the system compares different possible explanations.

Advanced techniques may include:

- Extended Kalman Filtering
- Multi-hypothesis tracking
- Innovation-based anomaly detection
- Late-message correction
- Probabilistic route scoring
- Weather-aware or constraint-aware path planning

This version more closely resembles the sensor fusion and state estimation logic used in operational ATC, autonomous vehicles, radar tracking, and defense systems.

---

## State Estimation

The aircraft state may include:

- Latitude and longitude
- Altitude
- Ground speed
- Vertical speed
- Heading
- Fuel estimate
- Current route index
- Next waypoint
- Estimated time of arrival
- Uncertainty values

The tracker should perform two core operations.

**Predict:** When no new message has arrived, the tracker predicts the aircraft's next state using a simplified flight dynamics model, estimating how far the aircraft has traveled, whether altitude should have changed, how much closer it should be to the next waypoint, and how uncertainty has grown.

**Update:** When a new message arrives, the tracker updates its state estimate, pulling the estimated position toward the reported position, reducing uncertainty after a reliable message, increasing uncertainty if the message conflicts with prior data, recalculating the next waypoint and ETA, and flagging the message if the mismatch is too large.

A strong implementation should show uncertainty increasing when messages are sparse and decreasing when reliable messages arrive.

---

## Multi-Hypothesis Routing

Sometimes one route explanation is not enough. A message may suggest the aircraft is proceeding to waypoint A, while a later message implies a reroute to waypoint B, and a delayed message appears to support the original route. A weather constraint may make one hypothesis less plausible. A reported ETA may only be consistent with one of the candidates.

Instead of immediately discarding one explanation, the system can maintain multiple route hypotheses. Each hypothesis should carry a route candidate, a current aircraft state, a probability or weight, a consistency score, and a history of supporting and conflicting messages. As more messages arrive, the system updates the weights, prunes unlikely hypotheses, and selects the most likely current route.

---

## Anomaly Detection

The system should flag messages that are inconsistent with the current estimate. Examples of suspicious messages include:

- A position jump that is physically unrealistic given elapsed time
- An altitude change too large for the time interval
- A heading that conflicts with the route geometry
- A reported waypoint inconsistent with the aircraft's trajectory
- An ETA that is impossible given current speed and distance
- A route update that contradicts several recent reliable messages
- A delayed message that would have been plausible earlier but no longer matches the current state

Advanced solutions may use innovation-based anomaly detection: comparing the predicted state to the observed message and flagging the message if the difference exceeds what the current uncertainty would expect. This is the approach used in operational multi-sensor trackers like ARTAS.

A note on the term "innovation": In estimation theory and Kalman filter literature, innovation is the difference between what the filter predicted a message would report and what the message actually reports. For example, if your filter predicted the aircraft would be at a certain position and altitude, and the incoming message reports something significantly different, that gap is the innovation. If the gap is larger than what your current uncertainty estimate considers plausible, the message is flagged as suspicious. The word has nothing to do with creativity, it is standard terminology used in real multi-sensor tracking systems like EUROCONTROL ARTAS.

---

## Autonomous Mapping and Path Planning (Stretch Goal)

Teams may optionally add autonomous route planning. In this version, the system does not only reconstruct the route, it can also reason about better or safer routes.

For example, the system may:

- Avoid storm cells or restricted areas
- Infer the likely destination from partial route data
- Use A*, Dijkstra's algorithm, or another graph-search method to find a feasible path
- Score candidate routes by distance, fuel cost, delay, safety margin, or weather risk
- Suggest a reroute when the current route appears inconsistent or blocked

---

## Front-End Visualization (Optional)

A useful visualization could include:

- A map of the current estimated route
- The aircraft's latest reported position and the tracker's estimated current position
- The next predicted waypoint and ETA
- Route alternatives
- Uncertainty ellipses or confidence regions
- Alerts for suspicious messages
- A timeline of received messages and delayed corrections

---

## Inputs

The evaluator provides a stream of simulated aircraft messages. Messages may include aircraft identifier, timestamp, latitude and longitude, altitude, speed, heading, fuel estimate, current and next waypoints, ETA, route update, and weather or constraint indicators.

Messages may arrive in order, out of order, late, with noise, with missing fields, or in conflict with earlier messages.

---

## Expected Outputs

Your solution should output an updated route and tracking estimate after processing the message stream. Expected outputs may include:

- Current estimated position, altitude, speed, and heading
- Current route hypothesis
- Next waypoint and estimated arrival time
- Uncertainty estimate
- List of detected conflicts and anomaly alerts
- Final reconstructed route

---

## Evaluation

Solutions may be scored on:

- **Route Reconstruction Accuracy** - how close is the reconstructed route to the true route?
- **State Estimation Accuracy** - how close are estimated position, altitude, speed, and heading to the true simulated state?
- **ETA Accuracy** - how close are predicted arrival times to ground truth?
- **Conflict Handling** - does the solution correctly identify contradictory messages?
- **Late Message Handling** - can the solution incorporate delayed or out-of-order messages correctly?
- **Hypothesis Management** - does the solution maintain and select the correct route hypothesis when ambiguous?
- **Anomaly Detection** - does the solution flag suspicious messages without too many false alarms?
- **Code Quality** - is the solution modular, readable, and maintainable?
- **Optional Visualization** - does the solution clearly display route, uncertainty, and alerts?

---

## Suggested Student Milestones

**Milestone 1 - Working Parser:** Parse all message types into structured Python objects.

**Milestone 2 - Deterministic Route State:** Maintain a route and update it when new waypoint messages arrive.

**Milestone 3 - Basic Prediction:** Estimate current position and ETA using speed, heading, and waypoint distance.

**Milestone 4 - Consistency Checks:** Detect impossible jumps, conflicting waypoints, and invalid ETAs.

**Milestone 5 - KF/EKF or other Filter:** Add probabilistic state estimation with uncertainty.

**Milestone 6 - Multi-Hypothesis Tracking:** Maintain several possible route explanations and select the most likely one.

**Milestone 7 - Anomaly Detection:** Use prediction error or innovation magnitude to flag suspicious messages.

**Milestone 8 - Visualization:** Display the route, aircraft state, uncertainty, and alerts on a map.

---

## Final Goal

By the end of the challenge, your system should be able to read a messy stream of aircraft messages and answer:

> "Where is this aircraft most likely going, where is it now, when will it arrive, and which messages should we not fully trust?"

This is the same question that systems like ARTAS, ERAM, and STARS answer thousands of times per minute, for every aircraft in controlled airspace.
