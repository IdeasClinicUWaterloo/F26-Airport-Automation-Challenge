# Starter Kit

This folder contains everything needed to run and extend the tracker. You can change the working example or use only the parts that help your team.

The code answers four questions:

1. Where is the aircraft now?
2. Where is it going next?
3. When might it arrive?
4. Does an incoming message look suspicious?

You do not need to understand every file before you start making changes.

## Run it

From the repository root:

```bash
pip install -r air-traffic-control/starter-kit/requirements.txt
python air-traffic-control/starter-kit/stream.py
```

The program prints an updated estimate after each message and opens a map at the end.

Try a different scenario:

```bash
python air-traffic-control/starter-kit/stream.py invalid.json
python air-traffic-control/starter-kit/stream.py anomalous.json
```

## The files at a glance

| File | Purpose |
| --- | --- |
| `stream.py` | Loads a scenario and sends each message into the solution |
| `message_parser.py` | Validates messages, updates the route, estimates arrival time, and reports alerts |
| `tracker.py` | Predicts and updates the aircraft state |
| `dead_reckoning.py` | Contains distance, bearing, and movement calculations |
| `visualizer.py` | Draws the route, reports, estimate, uncertainty, and alerts on a map |
| `data/` | Airport and waypoint data used by the tracker |
| `scenarios/` | Small message streams for running repeatable tests |
| `advanced/` | Optional additions and the accuracy tool |
| `advanced/output/` | Generated maps and accuracy charts |
| `live-tracking/` | Optional tracking with real OpenSky reports |

If you are unsure where to begin, start with `stream.py`, then follow the call to `FlightRoutingSolution.process_message()` in `message_parser.py`.

## How the tracker works

The tracker repeats two operations.

### Predict

Between messages, it moves the aircraft forward using the last known speed and heading. Its uncertainty grows because the aircraft may have changed direction or speed.

### Update

When a position report arrives, it moves the estimate toward that report. The amount it moves depends on how confident the tracker was and how noisy the report might be.

The basic idea is:

```text
update_fraction = current_uncertainty / (current_uncertainty + expected_message_error)
```

If the tracker is unsure, the fraction is larger and it follows the new report more closely. If the tracker is confident, the fraction is smaller and the change is gentler.

This is a beginner-friendly version of the idea behind a Kalman filter. It uses one uncertainty radius instead of a matrix.

## What gets flagged

The solution uses separate, readable checks:

1. **Invalid fields:** A value is missing or impossible, such as latitude 95 or a negative speed.
2. **Impossible movement:** The aircraft appears to travel farther than its speed and elapsed time allow.
3. **Unexpected position:** The report is much farther from the prediction than the current uncertainty allows.
4. **Route conflict:** A waypoint is not on the route, or a new route disagrees with waypoints already passed.

Keeping these checks separate makes it easier to see why a message was flagged.

## Useful settings to experiment with

The main settings are near the top of `tracker.py` and `message_parser.py`.

| Setting | Default | What it controls |
| --- | --- | --- |
| `MEASUREMENT_ERROR_KM` | `3.0` | How accurate a position report is expected to be |
| `DRIFT_PER_MINUTE_KM` | `1.0` | How quickly uncertainty grows without new data |
| `INITIAL_UNCERTAINTY_KM` | `5.0` | Confidence when the first message arrives |
| `ANOMALY_SIGMA` | `3.0` | How surprising a report must be before it is flagged |
| `ANOMALY_TRUST` | `0.3` | How much a flagged position still affects the estimate |
| `WAYPOINT_REACHED_KM` | `30.0` | How close the aircraft must be to count as reaching a waypoint |
| `MAX_PLAUSIBLE_SPEED_KT` | `700.0` | The maximum believable aircraft speed |

Change one setting at a time, run the same scenario again, and compare the output. That is often the fastest way to understand what a setting does.

`ANOMALY_TRUST` is kept above zero because a surprising report is not always bad data. It might be the first report after a real turn. Ignoring every surprising report can leave the tracker continuing in the old direction.

## Supplied scenarios

| Scenario | What it shows |
| --- | --- |
| `simple_route.json` | A clean flight with one reroute. Nothing should be flagged. |
| `invalid.json` | Missing fields and impossible values. |
| `anomalous.json` | A corrupted position, an off-route movement, a route conflict, and a late message. |

## Good first changes

These are manageable additions for a 12-hour hackathon:

- Add a stale warning after a long gap between messages.
- Compare heading with the direction of the next waypoint.
- Check whether a reported arrival time looks realistic.
- Add clearer explanations to anomaly alerts.
- Improve the map or add a summary panel.
- Write a small scenario for a bug you find.
- Run the accuracy tool and show whether your change helped.

## Measure the result

The advanced folder includes a simulator with a known correct flight. That lets you measure position error instead of judging the map by eye.

```bash
pip install -r air-traffic-control/starter-kit/advanced/requirements.txt
python air-traffic-control/starter-kit/advanced/measure_accuracy.py
```

The current simple tracker has about `1.50 km` median error in the supplied simulation. A few corrupted reports make the worst cases much larger, which is why anomaly handling matters.

Do not worry if your result is not the lowest possible number. Explain the trade-off your team chose and test it consistently.

## Optional advanced code

The [`advanced/`](advanced/) folder contains examples of:

- accuracy measurement
- graph-based rerouting
- multiple route hypotheses
- a matrix-based Extended Kalman Filter

Read [`advanced/README.md`](advanced/README.md) before choosing one. For most teams, one focused extension is plenty.

## Important limitations

This solution is intentionally simplified. For example:

- One number represents position uncertainty.
- The movement model assumes the aircraft keeps roughly the same speed and heading between reports.
- A track can keep predicting forward even when no new message has arrived.
- The route data is much simpler than real aviation route data.
- The code has not been tested or certified for real operations.

These limitations are useful project ideas. They are also worth mentioning in your demo.
