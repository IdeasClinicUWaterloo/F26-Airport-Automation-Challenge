# Optional Advanced Add-Ons

This folder contains optional additions that connect to the main tracker in the parent folder.

Get the basic tracker running first. Then choose at most one add-on if your team has time and interest. None of these are required for a strong project.

## Quick guide

| File | What it adds | Suggested level |
| --- | --- | --- |
| `measure_accuracy.py` | Measures tracking error against a known flight | Good first choice |
| `path_planning.py` | Finds a route around blocked waypoints | Approachable if you know graphs |
| `hypothesis.py` | Keeps and scores several possible routes | More involved |
| `ekf.py` | Replaces the simple tracker with a matrix Kalman filter | Read and compare |
| `simulator.py` | Creates the known flight used for accuracy testing | Supporting code |

## Best first option: measure accuracy

Maps can look convincing even when a tracker is wrong. `measure_accuracy.py` tests the tracker against a simulated flight where the correct position is known.

Run it from the repository root:

```bash
pip install -r air-traffic-control/starter-kit/advanced/requirements.txt
python air-traffic-control/starter-kit/advanced/measure_accuracy.py
```

To test the supplied Extended Kalman Filter:

```bash
python air-traffic-control/starter-kit/advanced/measure_accuracy.py --ekf
```

The tool reports:

- **Median error:** A good picture of a typical result.
- **RMSE:** An average that gives extra weight to large errors.
- **Worst error:** The largest mistake in the run.

The supplied simulation currently gives results similar to:

```text
error vs ground truth     median      RMSE     worst   (km)
raw reported                0.03     42.72    263.35
simple tracker              1.50     12.15     53.28
```

Most raw reports are very accurate, but one corrupted report can be far away. The tracker accepts a little delay in normal cases so that one bad message causes less damage.

A useful demo statement would be: "Our typical error is about 1.5 km, and our tracker reduces the worst position spikes in this simulation."

## Option 2: route around a blocked waypoint

`path_planning.py` uses Dijkstra's algorithm to find a short path that avoids blocked waypoints.

```python
from path_planning import find_shortest_path

route, distance_km = find_shortest_path(
    solution.waypoints,
    "YYZ",
    "DEN",
    blocked={"WP002"},
)
```

This is a good extension because it does not require changes to the aircraft tracker.

One limitation is important: the supplied data lists waypoints but does not list real airways between them. This example treats every waypoint as connected to every other waypoint. Real flight planning has many more constraints.

## Option 3: keep several possible routes

The basic solution stores one current route. When messages disagree, `hypothesis.py` lets you keep several possible routes and give each one a weight.

Later messages can raise or lower those weights. The route with the highest weight becomes the current best guess.

`RouteHypothesis` stores:

- a route
- a weight
- a consistency score
- the message IDs that support or conflict with it

The class is provided, but connecting it to the basic solution is left as a team challenge. A possible plan is:

1. Store a list of hypotheses instead of one route.
2. Apply compatible route updates to existing hypotheses.
3. Create a new hypothesis when an update does not fit any existing one.
4. Adjust weights when waypoint reports arrive.
5. Keep only the strongest few hypotheses and show the best one.

This change affects arrival time, route progress, output, and the map. Budget time for those connections.

## Option 4: compare the Extended Kalman Filter

`ekf.py` is a more advanced replacement for `tracker.py`. It has the same main interface, so the accuracy script can run either version.

The simple tracker stores uncertainty as one radius. The Extended Kalman Filter stores relationships between position, speed, and heading in a matrix. This can produce a more useful uncertainty shape and a more accurate estimate.

The supplied filter is useful to run, inspect, and compare. Building one from scratch is not a realistic expectation for most first- or second-year students during a 12-hour event. It normally requires comfort with covariance matrices, derivatives, and matrix operations.

If you explore it, focus on questions such as:

- Does it improve median and worst-case error?
- Does it behave differently after a long gap?
- Is the extra complexity worth it for your project?
- Can your team explain its limitations clearly?

## A simple way to work with an add-on

1. Run the basic solution and record a result.
2. Choose one change.
3. Test the same scenario before and after.
4. Keep the change only if you can explain what improved.
5. Leave enough time to prepare the demo.

One tested improvement is a better hackathon result than several unfinished features.
