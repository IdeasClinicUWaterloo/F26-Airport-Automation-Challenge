# Optional Project Ideas

The basic tracker is already a complete hackathon project. Everything in this file is optional.

Before choosing an idea, make sure your project can:

- read a scenario
- process each message
- show or print a useful result
- handle at least one bad message

Once that works, pick **one** improvement your team can finish and explain. A small feature with a clear test makes a strong demo.

## Choose an idea

| If your team wants to... | Try this |
| --- | --- |
| Prove the tracker works | Measure its accuracy |
| Add a practical safety feature | Detect stale tracks |
| Add another useful warning | Check heading or reported ETA |
| Improve the tracking model | Track uncertainty separately |
| Add route planning | Reroute around a blocked waypoint |
| Explore uncertain routes | Keep several route hypotheses |
| Compare a more advanced filter | Run the supplied Extended Kalman Filter |

The times are rough guides for first- and second-year students. Choose based on what your team already knows and how much time remains.

## Good first choices

### Measure the tracker's accuracy

The map may look correct even when the estimate is far from the real position. The supplied accuracy tool tests the tracker against a simulated flight where the correct position is known.

Run it from the repository root:

```bash
pip install -r air-traffic-control/reference-solution/advanced/requirements.txt
python air-traffic-control/reference-solution/advanced/measure_accuracy.py
```

It reports typical error, overall error, and the worst error. This gives your team something concrete to compare before and after a change.

**A finished version:** Run the same test before and after your improvement, then explain what changed and why.

### Detect stale tracks

The current tracker can keep predicting forever after messages stop arriving. Add a warning when the most recent message is too old.

You could add:

- a setting such as `STALE_AFTER_MINUTES`
- the time of the latest trusted message
- an `is_stale` field in `get_state()`
- a visible warning in the output or map

**A finished version:** A normal scenario stays active, while a scenario with a long gap becomes stale.

### Compare heading with the next waypoint

An aircraft may report a valid position but point away from its next waypoint. Compare its heading with the bearing to that waypoint and flag a large disagreement.

Start with:

- `find_bearing()` in `dead_reckoning.py`
- `_has_passed()` in `message_parser.py`, which already compares angles

Choose a clear tolerance and test a normal turn as well as a suspicious heading.

**A finished version:** The tracker explains how far the reported heading differs from the expected direction.

### Check the reported ETA

A `waypoint_report` message includes an ETA. The basic solution calculates its own ETA but does not compare the two.

Use the distance to the waypoint and the reported ETA to work out the speed the aircraft would need. Flag the message if that speed is very different from the tracked speed.

Start with `_estimate_eta()` in `message_parser.py`, which already contains most of the distance and time calculations.

**A finished version:** A believable ETA passes, while an impossible ETA produces a helpful warning.

### Trust suspicious reports by different amounts

The basic tracker uses one `ANOMALY_TRUST` value for every suspicious position. A report that is slightly outside the expected area is treated the same as one hundreds of kilometres away.

Change the trust value based on how surprising the report is. For example:

- slightly unusual: trust some of it
- clearly suspicious: trust very little
- physically impossible: reject it

The `update()` method in `advanced/ekf.py` contains an example with a softer limit and a harder limit.

**A finished version:** Test several position jumps and show that larger errors have less influence.

## Larger additions

### Track uncertainty separately

The basic tracker uses one uncertainty value when updating position, altitude, speed, and heading. In reality, these values do not become uncertain at the same rate.

Give each value its own uncertainty and drift setting. You can build this with the same weighted-update idea already used by the simple tracker. No new matrix mathematics is required.

**A finished version:** After a gap, each measurement has its own uncertainty, and a new report updates each value by a sensible amount.

### Suggest a route around a blocked waypoint

Treat the waypoints as a graph and use Dijkstra's algorithm or A* to find a route that avoids a blocked waypoint.

`advanced/path_planning.py` provides a small starting point and does not require changes to the aircraft tracker.

The supplied navigation data does not contain real airway connections, so the example treats every waypoint as connected. Mention this limitation in your demo.

**A finished version:** Block one waypoint, display the suggested replacement route, and compare its distance with the original.

### Keep several possible routes

The basic solution stores one route. When messages disagree, another approach is to keep several possible routes and assign each one a weight.

Later messages can raise or lower those weights. The route with the highest weight becomes the current best guess.

`advanced/hypothesis.py` provides a `RouteHypothesis` class. Connecting it to `message_parser.py` is the main challenge. You will need to update route progress, ETA, output, and visualization to use the best hypothesis.

**A finished version:** Show two possible routes, process a message that supports one of them, and display how their weights change.

## Explore and compare

### Try the supplied Extended Kalman Filter

`advanced/ekf.py` is a more advanced replacement for the simple tracker. You are not expected to build it from scratch.

Run the accuracy tool with the `--ekf` option:

```bash
python air-traffic-control/reference-solution/advanced/measure_accuracy.py --ekf
```

Compare it with the simple tracker:

- Which has lower typical error?
- Which handles bad reports better?
- How does uncertainty change after a long gap?
- Is the extra complexity useful for your project?

The Extended Kalman Filter uses covariance matrices and other mathematics that may be unfamiliar. It is completely fine to treat it as an example, run it, and explain what you observed.

### Change the simulator

`advanced/simulator.py` creates a flight where the correct route and position are known. It then adds noise and bad data to create test messages.

Try changing one part of the generated flight:

- increase the position noise
- add a longer message gap
- create a sharper turn
- add more corrupted reports
- change the reporting interval

Then compare how the tracker behaves before and after the change.

**A finished version:** Explain what you changed in the simulated data and show how it affected the results.

## Keep the scope manageable

Before committing to an idea, ask:

1. Can we build a basic version in the time remaining?
2. Do we know how we will test it?
3. Will the improvement be visible in our demo?
4. Can every teammate explain what it does?

If the answer is no, choose a smaller version of the idea. Finishing early gives you time to test, improve the presentation, and enjoy the demo.
