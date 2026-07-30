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

Real ATC systems (FAA ERAM/STARS, EUROCONTROL ARTAS, NAV CANADA's flight data systems) don't just display an aircraft's last known position. They pull in multiple imperfect, disagreeing data sources: radar, ADS-B, flight plans, controller updates, and fuse them into a best estimate of where the aircraft actually is and where it's headed, flagging anything that looks wrong. That's the same kind of problem behind autonomous vehicle perception and space object tracking, and it's the upstream data source that airport operations platforms (gates, baggage, ground handling) ultimately depend on.

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

## Regulatory & Safety Context

ATC automation isn't just engineered for correctness, it's built to satisfy specific FAA (and international equivalent) regulations, because a bad state estimate or a missed conflict is a safety critical issue. Knowing the real regulations behind this challenge's concepts is useful both for design decisions and for the "Safety and Security" judging category:

| Regulation / Standard | What it governs | Where it shows up in this challenge |
| --- | --- | --- |
| FAA Order 7110.65 (the controllers' handbook) | Separation minima: typically 3 nm lateral in terminal airspace, 5 nm en route, 1,000 ft vertical, plus conflict-alert and MSAW (Minimum Safe Altitude Warning) procedures | The real-world reference point for "conflict detection" and "anomaly flagging", actual separation-loss checks, not just field sanity checks |
| 14 CFR 91.225 (ADS-B Out mandate) | Aircraft in controlled airspace must broadcast position, altitude, ground speed, and heading at defined rates | This is the message schema `state` messages in `message_parser.py` are modeling |
| RTCA DO-260B / ICAO Annex 10 | Defines Navigation Accuracy Category (NACp/NACv): how much confidence to place in a given position report | The real-world analogue of "uncertainty," which an EKF-based advanced solution is expected to track |
| RTCA DO-278A | Software assurance levels for ground-based ATC automation (DO-178C is the airborne-avionics equivalent), tying verification rigor to failure severity | The reason a prototype like this would need far more testing/traceability before any real operational use |
| 14 CFR 91.180 (RVSM) | Reduced Vertical Separation Minimum: 1,000 ft above FL290, requiring tighter altimetry accuracy | Relevant if extending altitude-based anomaly thresholds, tolerance for "how far off is too far" should tighten at higher altitudes |
| 14 CFR 91.183 | Mandatory position reporting over compulsory points under IFR | Background for `waypoint_report` messages |

Two concrete gaps between this prototype and a regulation-grounded system, worth keeping in mind:

- **Field validation vs. separation-minima validation.** `check_state_message()` in [`starter-kit/message_parser.py`](starter-kit/message_parser.py) checks that lat/lon/heading/altitude/speed are physically plausible numbers (e.g. heading in `[0, 360]`). Real conflict-alert logic checks against the actual separation minima in 7110.65 (3/5 nm lateral, 1,000 ft vertical) between aircraft pairs, a different (and harder) problem than what this problem is doing.
- **No staleness/track-timeout logic.** `predict()` in [`starter-kit/tracker.py`](starter-kit/tracker.py) will happily coast a track forward indefinitely between updates. Real systems bound how long a track can be "coasted" before it's flagged as stale, tied to expected radar/ADS-B update rates. This is a natural safety-relevant addition, and a manageable one. It is written up in [`starter-kit/STRETCH_GOALS.md`](starter-kit/STRETCH_GOALS.md).

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

The aircraft state includes:

- Latitude and longitude
- Altitude
- Ground speed
- Vertical speed
- Heading

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

## Front-End Visualization

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

## Running the Code

Everything you need to begin is in [`starter-kit/`](starter-kit). It contains the tracker, scenario files, route data, advanced options, and live-tracking add-on in one place.

The earlier implementation is preserved separately in [`solution-backup/`](solution-backup). It has its own data and scenarios, so changes to the starter kit will not break it.

You can build on the starter kit or create your own solution using the same inputs.

### Folder guide

| Location | What it contains |
| --- | --- |
| [`starter-kit/`](starter-kit) | The main tracker and the best place to begin |
| [`starter-kit/data/`](starter-kit/data/) | Airport and waypoint data |
| [`starter-kit/scenarios/`](starter-kit/scenarios/) | The supplied message streams |
| [`starter-kit/advanced/`](starter-kit/advanced/) | Optional accuracy, routing, and filtering additions |
| [`starter-kit/advanced/output/`](starter-kit/advanced/output/) | Generated maps and accuracy charts |
| [`starter-kit/live-tracking/`](starter-kit/live-tracking/) | The optional OpenSky live-aircraft demo |
| [`solution-backup/`](solution-backup/) | A preserved earlier version with its own data and scenarios |

From the repository root, run:

```bash
pip install -r air-traffic-control/starter-kit/requirements.txt
python air-traffic-control/starter-kit/stream.py
```

These commands assume you are at the repository root. The scripts locate their data and output folders automatically.

### What happens when you run it

The program reads [`starter-kit/scenarios/simple_route.json`](starter-kit/scenarios/simple_route.json) one message at a time. After each message, it prints:

- the estimated aircraft position
- the current uncertainty
- the next waypoint
- the estimated arrival time
- any warnings about suspicious data

When the scenario finishes, a map opens showing the planned route, reported positions, estimated track, and uncertainty.

### Try another scenario

Pass a scenario filename to the program:

```bash
python air-traffic-control/starter-kit/stream.py invalid.json
python air-traffic-control/starter-kit/stream.py anomalous.json
```

You can also copy one of the files in [`starter-kit/scenarios/`](starter-kit/scenarios/) and create your own small test case.

| Scenario | What it shows |
| --- | --- |
| [`simple_route.json`](starter-kit/scenarios/simple_route.json) | A normal flight with one mid-flight reroute. Nothing should be flagged. |
| [`invalid.json`](starter-kit/scenarios/invalid.json) | Missing fields and impossible values, such as an invalid latitude or negative altitude. |
| [`anomalous.json`](starter-kit/scenarios/anomalous.json) | A corrupted position, an off-route movement, an unknown waypoint, a conflicting route update, and a late message. |

Want to understand or change the example?

- [`starter-kit/README.md`](starter-kit/README.md) explains the main files and settings.
- [`starter-kit/STRETCH_GOALS.md`](starter-kit/STRETCH_GOALS.md) suggests optional additions and gives rough time estimates.

---

## Optional: Track Live Aircraft

The [`starter-kit/live-tracking/`](starter-kit/live-tracking/) folder lets you try the tracker with real ADS-B reports from the [OpenSky Network](https://openskynetwork.github.io/opensky-api/index.html#). It displays nearby aircraft on a radar-style page.

This is still the same tracker. Only the source of the messages changes.

The live demo is completely optional. The supplied scenarios are the best place to build and debug because they are small, predictable, and repeatable.

### Three ways to feed the tracker

| Source | Type of data | Correct answer available? | Best for |
| --- | --- | --- | --- |
| [`starter-kit/scenarios/*.json`](starter-kit/scenarios/) | Fixed, hand-written messages | No, but easy to check by hand | Building and debugging |
| [`starter-kit/advanced/simulator.py`](starter-kit/advanced/simulator.py) | Generated messages | Yes | Measuring position accuracy |
| [`starter-kit/live-tracking/`](starter-kit/live-tracking/) | Live reports from many aircraft | No | Demos and testing assumptions with real data |

All three sources create the same `state` message format, so the tracker does not need to know where a message came from.

The translation happens in [`starter-kit/live-tracking/adapter.py`](starter-kit/live-tracking/adapter.py). It is only about fifteen lines long and is worth reading, even if you do not run the live demo.

### What the live feed can test

ADS-B reports include position, altitude, speed, and heading. This makes the live feed useful for testing:

- position prediction
- filtering and uncertainty
- suspicious position reports
- several aircraft at once

ADS-B reports do not include the planned route or next waypoint. The live feed cannot test route reconstruction, next-waypoint prediction, ETA, route consistency, or multiple route hypotheses.

If your project includes route features, show a scenario run alongside the live view.

### Why the live tracker uses different settings

Scenario messages may be several minutes apart. OpenSky reports often arrive about 15 seconds apart.

Over five minutes, an aircraft can make a real turn and end up far from a simple straight-line prediction. The tracker should still give that new report some trust.

Over 15 seconds, the aircraft should not move very far from its prediction. A large jump is more likely to be bad data, so the live tracker can reject more of it.

That is why `ANOMALY_TRUST` is `0.3` for the scenarios and `0.0` for the live feed. The code stays the same, but a useful setting changes with the message rate.

That is a useful result to explain in a demo: algorithms need to be tested with the kind of data they will actually receive.

See [`starter-kit/live-tracking/README.md`](starter-kit/live-tracking/README.md) for setup instructions and limitations.

---

## Things to keep in mind

As you are working through your solution, keep the following questions in mind:

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

**Milestone 5 - EKF or other Filter:** Add probabilistic state estimation with uncertainty.

**Milestone 6 - Multi-Hypothesis Tracking:** Maintain several possible route explanations and select the most likely one.

**Milestone 7 - Anomaly Detection:** Use prediction error or innovation magnitude to flag suspicious messages.

**Milestone 8 - Visualization:** Display the route, aircraft state, uncertainty, and alerts on a map.

---

## Final Goal

By the end of the challenge, your system should be able to read a messy stream of aircraft messages and answer:

> "Where is this aircraft most likely going, where is it now, when will it arrive, and which messages should we not fully trust?"

This is the same question that systems like ARTAS, ERAM, and STARS answer thousands of times per minute, for every aircraft in controlled airspace.
