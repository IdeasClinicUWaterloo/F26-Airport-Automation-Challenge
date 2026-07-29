# OpenSky Live Tracking

This optional demo shows real aircraft that are currently flying near Toronto Pearson Airport.

It downloads public ADS-B reports from the [OpenSky Network](https://openskynetwork.github.io/opensky-api/index.html#), sends them through the same tracker used by the scenario files, and displays the results on a radar-style page.

You do not need this folder to complete the hackathon.

## Run it

From the repository root:

```bash
pip install -r air-traffic-control/opensky-live-tracking/requirements.txt
python air-traffic-control/opensky-live-tracking/live_tracker.py
```

The program opens `http://127.0.0.1:8765/` in your browser. Leave the page open while the program is running. Press `Ctrl+C` in the terminal to stop it.

You need an internet connection. Anonymous OpenSky access may be slow or rate-limited.

## What this folder does

This is a new **message source**, not a separate tracker.

| Source | Kind of data | Best use |
| --- | --- | --- |
| `scenarios/*.json` | Small, fixed examples | Building and debugging |
| `reference-solution/advanced/simulator.py` | Generated data with a known correct track | Measuring accuracy |
| `opensky-live-tracking/` | Live reports from many real aircraft | Demonstrating and testing assumptions |

All three sources create the same `state` message format. The tracking code does not need to know where a message came from.

[`adapter.py`](adapter.py) converts an OpenSky report into the challenge format. It is short and is a good example of why a clear data format is useful.

## What you can learn from it

The live feed is useful for exploring:

- tracking several aircraft at once
- predicting movement between reports
- showing uncertainty
- handling noisy or surprising positions
- removing tracks that have stopped reporting
- building a live visualization

The browser asks for a new snapshot every two seconds. OpenSky reports arrive less often, so [`snapshot.py`](snapshot.py) predicts each aircraft forward between real updates. This makes the aircraft move smoothly instead of sitting still and jumping to each new position.

## What it cannot show

ADS-B state reports include position, altitude, speed, and heading. They do not include the challenge's planned route, next waypoint, or arrival time.

That means the live demo does not test:

- route reconstruction
- next-waypoint prediction
- arrival-time prediction
- route consistency
- multiple route hypotheses

Use the scenario files as well if your project includes route features.

## Compare the two supplied trackers

The normal command uses the simple tracker. Add `--ekf` to use the supplied matrix-based Kalman filter:

```bash
python air-traffic-control/opensky-live-tracking/live_tracker.py --ekf
```

This option needs `numpy`, which is included in the advanced requirements:

```bash
pip install -r air-traffic-control/reference-solution/advanced/requirements.txt
```

Try both versions and compare how closely the estimate follows the aircraft, how it reacts to a surprising report, and how the uncertainty changes.

## Optional OpenSky account

The demo can use anonymous access, but OpenSky may apply stricter limits to it. For a smoother demo, you can create an OpenSky account and API client.

In PowerShell:

```powershell
$env:OPENSKY_CLIENT_ID="your-client-id"
$env:OPENSKY_CLIENT_SECRET="your-client-secret"
python air-traffic-control/opensky-live-tracking/live_tracker.py
```

On macOS or Linux:

```bash
export OPENSKY_CLIENT_ID="your-client-id"
export OPENSKY_CLIENT_SECRET="your-client-secret"
python air-traffic-control/opensky-live-tracking/live_tracker.py
```

Do not commit your client secret. Check the OpenSky documentation for current account steps and limits before depending on the live feed for your final demo.

## Watch a different area

The default area is set near Toronto Pearson. To change it, edit `YYZ_BBOX` in [`live_tracker.py`](live_tracker.py):

```python
YYZ_BBOX = (lat_min, lon_min, lat_max, lon_max)
```

Use a reasonably small area so the demo does not request more data than it needs.

## Folder guide

| File | Purpose |
| --- | --- |
| `live_tracker.py` | Starts the server and polls OpenSky |
| `opensky_client.py` | Requests aircraft reports inside the selected area |
| `adapter.py` | Converts OpenSky data into a challenge `state` message |
| `tracker_source.py` | Loads and configures a tracker from the reference solution |
| `tracker_manager.py` | Keeps one tracker per aircraft and removes stale tracks |
| `snapshot.py` | Predicts tracks to the current time and prepares browser data |
| `radar_server.py` | Runs the local web server |
| `static/index.html` | Draws the radar page and aircraft |

## Why the settings are different

The scenario messages may be several minutes apart. Live OpenSky messages are often much closer together. A tracker that works well for one update rate may need different settings for the other.

`SIMPLE_TRACKER_TUNING` in [`tracker_source.py`](tracker_source.py) adjusts the simple tracker for the live feed. In particular, it trusts a surprising live position less because an aircraft normally cannot change very much in a short time.

This is a useful lesson for a demo: an algorithm's settings depend on the data it receives. Testing with both prepared scenarios and live data can reveal assumptions that were hard to notice before.

## Demo tip

Live services can be slow, unavailable, or show no aircraft in a small area. Keep a scenario-based demo ready as a backup. The scenario run is also the better way to show route features and repeat a result exactly.
