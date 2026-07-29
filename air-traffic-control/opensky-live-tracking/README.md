# OpenSky Live Tracking (Stretch / Parallel Path)

This is an optional addition to the ATC challenge: instead of replaying a
synthetic message stream for one aircraft, this pulls **real live ADS-B data**
from the [OpenSky Network API](https://openskynetwork.github.io/opensky-api/index.html#)
for every aircraft currently in a bounding box (default: around Toronto
Pearson / YYZ), and feeds each one through the same kind of Extended Kalman
Filter tracking used in `../reference-solution/`, extended to handle many
aircraft at once instead of just one.

It's self-contained (its own copy of `ekf.py`, importing only itself) so it
won't collide with whatever you build in `../` or `../reference-solution/`.

## What's in here

- `opensky_client.py` -- wraps `GET /api/states/all`, scoped to a bounding
  box. Works anonymously (rate-limited) or authenticated via OAuth2
  client-credentials for a higher quota (see below).
- `adapter.py` -- maps a raw OpenSky state vector into the same `"state"`
  message shape `../message_parser.py` already consumes.
- `ekf.py` -- unmodified copy of `../reference-solution/ekf.py`.
- `tracker_manager.py` -- keeps one `AircraftEKF` per aircraft (`icao24`)
  currently in range, and drops aircraft that haven't reported in
  `STALE_AFTER_SECONDS` so tracks disappear when a plane leaves the bbox.
- `snapshot.py` -- builds the JSON payload served to the page: predicts every
  active track's EKF forward to "now" (not just to its last real message)
  each time it's called, so aircraft keep coasting smoothly even between
  OpenSky's actual ~15s updates.
- `radar_server.py` -- a small stdlib-only local HTTP server: serves
  `static/index.html` and `/tracks.json`.
- `static/index.html` -- the live view: a dark, green phosphor-style radar
  scope (Leaflet map, rotating sweep, range rings) that polls `/tracks.json`
  every 2s and smoothly animates aircraft between positions rather than
  snapping. Anomalous aircraft (last message tripped the innovation gate)
  render red instead of green, with a fading trail behind each aircraft.
- `live_tracker.py` -- the entry point: starts the server, opens it in your
  browser, and polls OpenSky on a loop, ingesting states into the trackers.

## Running it

```bash
pip install -r air-traffic-control/opensky-live-tracking/requirements.txt
python air-traffic-control/opensky-live-tracking/live_tracker.py
```

This opens `http://127.0.0.1:8765/` in your browser automatically -- leave
the tab open, it updates itself. Stop the script with Ctrl+C.

### Authentication (optional but recommended)

Anonymous access works with no setup but is heavily rate-limited. For a
smoother demo, create a free OpenSky account and an API client under your
account settings, then set:

```bash
export OPENSKY_CLIENT_ID=...
export OPENSKY_CLIENT_SECRET=...
```

Check OpenSky's docs for current rate limits and auth details before relying
on this for a live demo -- they've changed both before.

### Watching a different airport

Edit `YYZ_BBOX = (lamin, lomin, lamax, lomax)` in `live_tracker.py`.

## Known limitation

OpenSky only reports live aircraft **state** (position, altitude, speed,
heading) -- there's no flight-plan, route, or waypoint data behind it. That
means there's no real equivalent of the main challenge's `route_update` or
`waypoint_report` messages, so multi-hypothesis routing, next-waypoint
prediction, and ETA don't apply to this feed. This is a real-data complement
to the state-estimation half of the challenge (dead reckoning / EKF /
anomaly detection, now across many aircraft at once), not a full replacement
for the main scenario-based challenge.
