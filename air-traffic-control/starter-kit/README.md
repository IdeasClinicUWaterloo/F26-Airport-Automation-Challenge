# Air Traffic Control Starter Kit

This folder contains a complete working example for the [Air Traffic Control challenge](../README.md). It processes aircraft messages, estimates the aircraft state, updates the route, reports warnings, and draws the result on a map.

You may extend the example, replace one part of it, or use only the pieces that help your team. You do not need to understand every file before making a useful change.

## Table of Contents

- [Challenge](#challenge)
- [Resources](#resources)

## Challenge

Use the starter kit to build a tracker that can answer:

1. Where is the aircraft now?
2. Where is it going next?
3. When might it arrive?
4. Does the latest message look trustworthy?

A successful change should be small enough to finish, tested with repeatable inputs, and easy for your team to explain.

## Resources

### Getting Started

Run these commands from the repository root.

#### Windows PowerShell

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r air-traffic-control/requirements.txt
python air-traffic-control/starter-kit/stream.py
```

#### macOS or Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r air-traffic-control/requirements.txt
python air-traffic-control/starter-kit/stream.py
```

The program prints an updated estimate after each message and opens a map when the scenario finishes.

Try the other scenarios:

```bash
python air-traffic-control/starter-kit/stream.py invalid.json
python air-traffic-control/starter-kit/stream.py anomalous.json
```

Run `deactivate` when you are finished. On later visits, activate `.venv` again; you do not need to recreate it.

### How the Tracker Works

The tracker repeats two operations.

#### Predict

Between messages, it moves the aircraft forward using its current position, speed, and heading. Uncertainty grows because the aircraft may have changed direction or speed.

#### Update

When a new position report arrives, the tracker compares it with the prediction and moves the estimate toward the report.

```text
update_fraction = current_uncertainty / (current_uncertainty + expected_message_error)
```

If the tracker is uncertain, it follows the report more closely. If it is confident, the change is smaller. This is a beginner-friendly version of the predict-and-update idea used by a Kalman filter.

#### What Gets Flagged

The example uses separate checks for:

1. missing, non-numeric, or impossible fields
2. movement that would require an unrealistic speed
3. a report too far from the predicted position
4. a waypoint or route update that conflicts with route history

Keeping the checks separate makes each warning easier to understand and modify.

#### Settings Worth Exploring

| Setting | Default | Purpose |
| --- | --- | --- |
| `MEASUREMENT_ERROR_KM` | `3.0` | Expected position-report error |
| `DRIFT_PER_MINUTE_KM` | `1.0` | Uncertainty growth without new data |
| `INITIAL_UNCERTAINTY_KM` | `5.0` | Uncertainty after the first report |
| `ANOMALY_SIGMA` | `3.0` | How surprising a report must be before it is flagged |
| `ANOMALY_TRUST` | `0.3` | How much a flagged report still changes the estimate |
| `WAYPOINT_REACHED_KM` | `30.0` | Distance that counts as reaching a waypoint |
| `MAX_PLAUSIBLE_SPEED_KT` | `700.0` | Maximum believable aircraft speed |

Change one setting at a time and rerun the same scenario so you can explain its effect.

### File Guide

| File or folder | Purpose |
| --- | --- |
| [`stream.py`](stream.py) | Loads a scenario and sends each message into the solution |
| [`message_parser.py`](message_parser.py) | Validates messages, maintains the route, estimates ETA, and reports alerts |
| [`tracker.py`](tracker.py) | Predicts and updates the aircraft state |
| [`dead_reckoning.py`](dead_reckoning.py) | Shared distance, bearing, and movement calculations |
| [`visualizer.py`](visualizer.py) | Draws the route, reports, estimate, uncertainty, and alerts |
| [`data/`](data/) | Training waypoints, routes, and connections |
| [`scenarios/`](scenarios/) | Repeatable message streams |
| [`advanced/`](advanced/) | Optional measurement, routing, hypothesis, and filter examples |
| [`live-tracking/`](live-tracking/) | Optional tracking with live OpenSky reports |

Start with [`stream.py`](stream.py), then follow its call to `FlightRoutingSolution.process_message()` in [`message_parser.py`](message_parser.py).

### Supplied Scenarios

| Scenario | Purpose |
| --- | --- |
| [`simple_route.json`](scenarios/simple_route.json) | Clean flight with one reroute and no expected alerts |
| [`invalid.json`](scenarios/invalid.json) | Missing fields and impossible values |
| [`anomalous.json`](scenarios/anomalous.json) | Corrupted position, route conflict, unknown waypoint, and late message |

### Measure a Change

```bash
python air-traffic-control/starter-kit/advanced/measure_accuracy.py
```

The simple tracker currently has about `1.50 km` median position error in the supplied simulation. Compare the same metric before and after your change.

### Important Limitations

- One number represents all position uncertainty.
- The movement model assumes roughly constant speed and heading between reports.
- A track can continue predicting even after reports stop.
- The navigation data is much smaller and simpler than real aviation data.
- The code is a learning prototype and is not certified for real operations.
