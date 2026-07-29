# OpenSky Live Tracking (Optional Alternate)

Runs the tracker against **real aircraft, right now**, instead of a scenario file.
It pulls live ADS-B reports from the [OpenSky Network](https://openskynetwork.github.io/opensky-api/index.html#)
for everything currently in a bounding box (default: around Toronto Pearson) and
draws them on a radar scope.

## What this actually is

A **message source**, not a tracker. That's the whole design:

```
../scenarios/*.json                 canned messages, fixed and repeatable
../reference-solution/advanced/      synthetic messages with a known true track
    simulator.py
this folder                          real messages, live, many aircraft at once
```

All three produce the same `state` message shape, so none of the tracking code
knows the difference. [adapter.py](adapter.py) is where that happens, and it's 15
lines — the interesting part of this folder is how little translation real data
needs once the message format is settled.

There is deliberately **no filter in here**. The tracking is done by
`../reference-solution/`, borrowed at startup by [tracker_source.py](tracker_source.py).
Earlier versions of this folder carried their own copy of the EKF; it drifted out
of date the moment the reference version was refactored, which is exactly why it's
gone.

## Running it

```bash
pip install -r air-traffic-control/opensky-live-tracking/requirements.txt
python air-traffic-control/opensky-live-tracking/live_tracker.py
```

Opens `http://127.0.0.1:8765/` automatically. Leave the tab open — it polls this
process and animates, so reloading isn't needed. Ctrl+C to stop.

The only dependency is `requests`. The radar page is served by the standard
library and the default tracker is pure Python.

### Comparing the two trackers on real data

```bash
python air-traffic-control/opensky-live-tracking/live_tracker.py --ekf
```

This swaps in the matrix Kalman filter from `../reference-solution/advanced/`
(needs `numpy`). Same feed, same everything else — the cheapest way to see what
the extra machinery buys you on data nobody staged for you.

### Authentication (optional)

Anonymous access works with no setup but is heavily rate-limited. For a smoother
demo, create a free OpenSky account, add an API client under your account
settings, then:

```bash
export OPENSKY_CLIENT_ID=...
export OPENSKY_CLIENT_SECRET=...
```

Check OpenSky's docs for current limits before relying on this live — they've
changed both the quotas and the auth flow before.

### Watching somewhere else

Edit `YYZ_BBOX = (lat_min, lon_min, lat_max, lon_max)` in
[live_tracker.py](live_tracker.py).

## What's in here

| File | Role |
| --- | --- |
| `adapter.py` | Turns an OpenSky state vector into a challenge `state` message |
| `opensky_client.py` | Wraps `GET /api/states/all`, scoped to a bounding box |
| `tracker_source.py` | Borrows a tracker from `../reference-solution/` and retunes it for this data rate |
| `tracker_manager.py` | One tracker per aircraft, with stale tracks swept when they leave the box |
| `snapshot.py` | Predicts every track forward to *now* and builds the JSON the page polls |
| `radar_server.py` | Stdlib-only local HTTP server |
| `static/index.html` | The radar scope: Leaflet, sweep, range rings, animated aircraft |
| `live_tracker.py` | Entry point: starts the server, polls OpenSky on a loop |

## The two things worth learning here

### Tuning depends on the data rate

The reference tracker's defaults assume messages minutes apart. OpenSky reports
every ~15 seconds, and the same numbers are wrong at that rate — left alone, the
gain works out around 0.08 and the estimate crawls along permanently behind the
aircraft. `SIMPLE_TRACKER_TUNING` in [tracker_source.py](tracker_source.py)
overrides four knobs, and one of them flips outright:

`ANOMALY_TRUST` is `0.3` in the reference solution and `0.0` here. In the
scenarios, a surprising report is usually a real turn the constant-heading model
couldn't anticipate, and refusing to believe it loses the aircraft. Over 15
seconds an aircraft barely turns, so a report far from the prediction is bad data
instead — and coasting uncertainty grows fast enough that a rejected track
re-acquires within a poll or two anyway. Set it to `0.3` here and one corrupted
position drags the estimate ~30 km off and keeps it flagged for several polls.

Notably the matrix EKF needs **no** retuning at all: its noise is specified per
second and scaled by elapsed time internally, so it adapts to the sampling rate
on its own. That robustness is a better argument for the extra machinery than raw
accuracy is.

### Dead reckoning becomes visible

OpenSky updates every ~15 s; the page polls every 2 s. [snapshot.py](snapshot.py)
predicts each track forward to *now* on every poll, so aircraft coast smoothly
along their last known heading between real reports rather than sitting still and
then jumping. That's the same `predict()` from the main challenge, just called
continuously — and it's the clearest demonstration in the whole project of why
prediction matters at all.

## What this can't do

OpenSky reports aircraft **state** only — position, altitude, speed, heading.
There is no flight plan, route, or waypoint data behind ADS-B, so nothing here
maps to the challenge's `route_update` or `waypoint_report` messages. That rules
out:

- next-waypoint prediction and ETA
- route reconstruction and route-consistency checks
- multi-hypothesis routing

So this exercises the **state-estimation half** of the challenge (dead reckoning,
filtering, anomaly detection — now across many aircraft at once) and none of the
**route-reasoning half**. It's a complement to the scenario-based challenge, not a
replacement for it. If you demo this, demo `../reference-solution/stream.py` too,
or half the judging criteria have nothing to point at.
