# Advanced Air Traffic Control Tools

This folder contains optional experiments for the [Air Traffic Control starter kit](../README.md). They demonstrate ways to measure accuracy, plan around blocked waypoints, keep several possible routes, and compare a more advanced tracker.

Get the basic scenario running first. Choose at most one advanced addition unless your team already understands the code it uses.

## Table of Contents

- [Challenge](#challenge)
- [Potential Solutions](#potential-solutions)
- [Getting Started](#getting-started)
- [Resources](#resources)

## Challenge

Choose one focused extension, connect it to the main tracker where needed, and show whether it improved the result.

A successful advanced addition should:

- solve a clear limitation of the basic tracker
- use the same scenarios or measurements before and after the change
- expose important assumptions instead of hiding them
- remain understandable enough for the team to explain during judging

None of these files is required for a strong project.

## Potential Solutions

| Potential solution | Description | Suggested level |
| --- | --- | --- |
| Accuracy measurement | Compare raw reports and tracker estimates with a simulated flight whose true positions are known. | Best first choice |
| Blocked-waypoint rerouting | Use Dijkstra's algorithm and the supplied training connections to avoid a blocked waypoint. | Approachable with graph basics |
| Route hypotheses | Keep and score several possible routes when messages disagree. | More involved |
| Extended Kalman Filter (EKF) | Compare the simple uncertainty model with a matrix-based state estimator. | Advanced mathematics |

### Accuracy Measurement

Run from the repository root:

```bash
python -m pip install -r air-traffic-control/requirements.txt
python air-traffic-control/starter-kit/advanced/measure_accuracy.py
```

The tool reports median error, root-mean-square error (RMSE), and worst error. The supplied simulation currently gives results similar to:

```text
error vs ground truth     median      RMSE     worst   (km)
raw reported                0.03     42.72    263.35
simple tracker              1.50     12.15     53.28
```

The raw reports are usually accurate, but one deliberately corrupted report creates a large error. The tracker reduces that worst spike while introducing a small amount of normal tracking delay.

### Blocked-Waypoint Rerouting

[`path_planning.py`](path_planning.py) finds a short route through the training connections in [`../data/route.json`](../data/route.json).

```python
from advanced.path_planning import find_shortest_path

route, distance_km = find_shortest_path(
    solution.waypoints,
    "YYZ",
    "DEN",
    blocked={"WP002"},
    connections=solution.connections,
)
```

The connections are made for this challenge and are not real airways. A useful extension could add weather, restricted areas, fuel, or route-cost information.

### Route Hypotheses

[`hypothesis.py`](hypothesis.py) provides a `RouteHypothesis` class with:

- an ordered route
- a weight and consistency score
- a current route position
- message IDs that support or conflict with the route

Connecting it to the main solution is left as a team challenge. You will need to choose the strongest hypothesis when calculating route progress, ETA, output, and visualization.

### Extended Kalman Filter

Run the accuracy tool with the supplied matrix-based tracker:

```bash
python air-traffic-control/starter-kit/advanced/measure_accuracy.py --ekf
```

The EKF in [`ekf.py`](ekf.py) tracks relationships between position, speed, heading, altitude, and uncertainty. Building one from scratch is not expected for most first- or second-year students. Treat it as code to run, inspect, test, and compare.

Useful questions include:

- Does it improve typical error or only some situations?
- How many normal messages does it flag?
- How does it behave after a long gap or sharp turn?
- Is the extra complexity worthwhile for your project?

## Getting Started

### Try an Advanced Tool

1. Run the basic tracker and record its result.
2. Choose one optional addition.
3. Change or connect the smallest useful part.
4. Run the same test again.
5. Keep the change only if you can explain what improved or what you learned.

One tested improvement is stronger than several unfinished features.

## Resources

| File | Purpose |
| --- | --- |
| [`measure_accuracy.py`](measure_accuracy.py) | Runs the simulator, measures error, and creates charts |
| [`simulator.py`](simulator.py) | Generates messages and known ground-truth positions |
| [`path_planning.py`](path_planning.py) | Finds a route through known waypoint connections |
| [`hypothesis.py`](hypothesis.py) | Represents and scores one possible route |
| [`ekf.py`](ekf.py) | Implements the optional matrix-based tracker |
| `output/` | Stores generated maps and accuracy charts |

Also read the [main starter-kit guide](../README.md) and [challenge overview](../../README.md).
