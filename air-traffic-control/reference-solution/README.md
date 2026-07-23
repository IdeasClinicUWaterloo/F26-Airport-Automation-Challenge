# Reference Solution (Advanced Path) -- Backup Copy

This is a self-contained backup of a completed "Advanced Solution Path" implementation for the ATC challenge, kept here purely as a reference to compare against -- the same role `solution_kd.py` plays for the gate-assignment challenge. It is **not** meant to be edited or built on directly; it's here so you can peek at an approach or check your own results against it while you build `../message_parser.py` etc. yourself from scratch.

## What's in here

- `ekf.py` -- Extended Kalman Filter (position/altitude/speed/heading/vertical speed with uncertainty), with innovation-based (NIS) anomaly gating: mild conflicts are softly down-weighted, wild outliers beyond 5x the anomaly threshold are excluded from the update entirely.
- `hypothesis.py` -- `RouteHypothesis`: a route candidate with weight, consistency score, and supporting/conflicting message history, for multi-hypothesis routing.
- `message_parser.py` -- `FlightRoutingSolution`, wiring the EKF + hypotheses + innovation-based anomaly detection + late-message replay (out-of-order messages trigger a full, correctly-ordered reprocess) together.
- `path_planning.py` -- Dijkstra-based reroute suggestion (stretch goal), avoiding blocked/restricted waypoints.
- `dead_reckoning.py` -- same as the original starter file, plus a standalone `destination_point()` helper used by the visualizer and simulator.
- `visualizer.py` -- the map, extended to show the EKF's estimate with its confidence ellipse, all surviving route hypotheses (best solid, alternates dashed and weight-scaled), red anomaly markers, and (when used with the simulator) the ground-truth track.
- `simulator.py` / `run_simulation.py` -- a synthetic scenario generator (known ground truth, noise, dropouts, a late message, one deliberately corrupted message, one genuinely conflicting route update) plus a diagnostics dashboard (`ekf_dashboard.png`): position error vs. ground truth, uncertainty growth/shrinkage, innovation (NIS) per message, altitude/speed/heading tracking, and hypothesis-weight convergence.
- `stream.py` -- same demo entry point as the original, running the shipped `simple_route.json` scenario.

## Running it

Everything here is self-contained (its own copies of every module, importing each other locally) except the shared, read-only inputs (`../data/route.json`, `../scenarios/*.json`), so it won't collide with whatever you build in the main `air-traffic-control/` folder. Run from the repository root:

```bash
pip install -r air-traffic-control/reference-solution/requirements.txt
python air-traffic-control/reference-solution/stream.py
python air-traffic-control/reference-solution/run_simulation.py
```

Outputs land in `air-traffic-control/reference-solution/output/`.
