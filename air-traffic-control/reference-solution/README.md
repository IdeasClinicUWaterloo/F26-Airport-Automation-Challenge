# Reference Solution

A complete, working answer to the ATC challenge, sized for the time you actually
have. Roughly 700 lines across five files, and the hardest maths in it is the
spherical trigonometry already in `dead_reckoning.py`.

This is here to compare against, not to build on. Write your own — then come look.

## What it does

Feed it a stream of messages and it answers the four questions the challenge asks:

| Question | Where |
| --- | --- |
| Where is the aircraft now? | `tracker.py` — predict/update cycle with an uncertainty radius |
| Where is it going next? | `message_parser.py` — `_advance_route_progress()` |
| When does it get there? | `message_parser.py` — `_estimate_eta()` |
| Which messages shouldn't we trust? | four checks, listed below |

```
dead_reckoning.py   distance, bearing, and "fly this heading for this far"
tracker.py          the running estimate and how sure we are of it
message_parser.py   message handling, route progress, ETA, anomaly checks
visualizer.py       satellite map of route, reports, estimate, uncertainty, alerts
stream.py           replays a scenario file through the above
```

## Running it

```bash
pip install -r air-traffic-control/reference-solution/requirements.txt
python air-traffic-control/reference-solution/stream.py
```

From the repository root, not from inside `air-traffic-control/` — the scenario and
nav-data paths are relative to the root. Pass a scenario name to try another:

```bash
python air-traffic-control/reference-solution/stream.py anomalous.json
```

| Scenario | What it shows |
| --- | --- |
| `simple_route.json` | A clean flight with one mid-flight reroute. Nothing gets flagged, which is the correct answer. |
| `invalid.json` | Field-level rubbish: out-of-range latitude, negative altitude, missing longitude, unknown message type. |
| `anomalous.json` | One of each interesting failure: a corrupted position, a genuine off-route deviation, a waypoint that doesn't exist, a route update contradicting history, and a message delivered out of order. |

## How the tracker works

Two operations, alternating forever:

- **predict** — no new information, so coast forward on the last known speed and
  heading, and get less sure.
- **update** — a message arrived, so move the estimate toward it and get more sure.

How far it moves is the only real idea in the file:

```
fraction = our_uncertainty / (our_uncertainty + expected_message_error)
```

Unsure and the message looks reliable, that's near 1, so jump to it. Confident and
the message could be noisy, that's near 0, so hold your ground. That is a Kalman
filter with the linear algebra taken out — a real one tracks uncertainty as a matrix
so it can model how being wrong about heading makes you wrong about position later.

You can watch this happening in the printed output. Early on, messages land within a
kilometre or two of the prediction and uncertainty settles around 2 km. After a long
silence the circle swells, and the next message snaps it shut again.

### The knobs

All of them live at the top of `tracker.py` and `message_parser.py`, and each one
says what raising it does. Change them and re-run — that is the intended way to
build intuition about this, rather than deriving values on paper.

| Knob | Default | Governs |
| --- | --- | --- |
| `MEASUREMENT_ERROR_KM` | 3.0 | How much to trust reported positions |
| `DRIFT_PER_MINUTE_KM` | 1.0 | How fast confidence decays while coasting |
| `INITIAL_UNCERTAINTY_KM` | 5.0 | Confidence at the first message |
| `ANOMALY_SIGMA` | 3.0 | How surprising a message must be to get flagged |
| `ANOMALY_TRUST` | 0.3 | How much of a flagged message to believe anyway |
| `WAYPOINT_REACHED_KM` | 30.0 | How close counts as reaching a waypoint |
| `MAX_PLAUSIBLE_SPEED_KT` | 700.0 | Above this, it's a bad message, not a fast aircraft |

`ANOMALY_TRUST` is the interesting one, and it's worth understanding why it isn't
`0.0`. Ignoring flagged messages outright is the obvious first guess and it's wrong:
a sharp turn at a waypoint puts the next report tens of km from our straight-line
prediction, so it gets flagged — and if we then ignore it, we keep flying the old
heading and the report after that is further off still. The gap grows at cruise
speed while the tolerance only widens at `DRIFT_PER_MINUTE_KM`, so it never catches
up and the aircraft is lost.

Setting it to `0.0` measurably doubles the tracker's error on the accuracy harness in
`advanced/`. Try it and watch. That harness exists precisely so claims like this one
are checkable rather than asserted — it's how the default got picked.

## The four anomaly checks

Deliberately four separate checks rather than one clever one, because they catch
different things and it should be obvious which one fired.

1. **Field validation** (`check_state_message`) — values impossible on their own: a
   latitude of 95, a negative speed.
2. **Physical plausibility** (`check_position_jump`) — a position no aircraft could
   have reached in the time available. Catches swapped coordinates and misplaced
   decimal points. Measured from the last position we actually believed, not from
   our current prediction, so rejecting one message doesn't cascade into rejecting
   the next good one.
3. **Disagreement with the estimate** (in `tracker.update`) — individually plausible
   values that don't square with where the aircraft just was. This is the one that
   scales with confidence: the same 50 km surprise is an alarm after a confident fix
   and unremarkable after twenty minutes of silence.
4. **Route consistency** — a reported waypoint that isn't on the route, or a route
   update that disagrees about waypoints already flown past.

## How good is it?

Measured against a synthetic flight with a known true track (`advanced/measure_accuracy.py`):

```
  error vs ground truth     median      RMSE     worst   (km)
  raw reported                0.03     42.72    263.35
  tracker estimate            1.50     12.15     53.28
```

The reports themselves are near-perfect most of the time — median error 30 m — so the
tracker's job isn't to improve on a good report, it's to survive a bad one. It gives
up 1.5 km of typical accuracy to smoothing lag and in exchange cuts the worst case
from 263 km to 53 km.

Being able to say that with numbers is worth more than any extra feature. If you add
one thing from `advanced/`, add the harness.

## What's deliberately not here

Not because it doesn't matter, but because it doesn't fit in two days, and a
half-finished Kalman filter demos worse than a working simple one:

- a matrix-based Extended Kalman Filter with a real covariance
- multi-hypothesis route tracking
- graph-search rerouting

All three are written up in `STRETCH_GOALS.md` with honest time estimates, and
`advanced/` holds a working implementation of each — as add-ons that plug into this
code, not as a second copy of it. Read that folder's README first.
