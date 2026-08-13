# OpenSky Live Aircraft Tracking

This optional add-on sends public aircraft reports from the [OpenSky Network](https://openskynetwork.github.io/opensky-api/) through the same tracker used by the prepared scenarios. It displays aircraft near Toronto Pearson on a local radar-style page.

The live feed is useful for demonstrations and for discovering assumptions that were hard to notice in prepared data. It is not required for the Air Traffic Control challenge, and it should not be your only demo because internet services can be slow or unavailable.

## Table of Contents

- [Challenge](#challenge)
- [Potential Solutions](#potential-solutions)
- [Getting Started](#getting-started)
- [Resources](#resources)

## Challenge

Use live aircraft state reports to explore how a tracker behaves with many aircraft and frequent updates.

The live feed can help you test:

- one tracker per aircraft
- prediction between reports
- uncertainty growth and correction
- surprising or noisy positions
- stale-track removal
- a continuously updating visualization

OpenSky state reports include position, altitude, speed, and heading. They do not include the challenge's planned route, next waypoint, or ETA. Use the prepared scenarios when demonstrating route reconstruction, route consistency, or multiple route hypotheses.

## Potential Solutions

| Potential solution | Description | Starting point |
| --- | --- | --- |
| Live radar display | Improve labels, trails, uncertainty circles, or alert presentation. | [`static/index.html`](static/index.html) |
| Tracker comparison | Compare the simple tracker and the Extended Kalman Filter on the same aircraft. | [`tracker_source.py`](tracker_source.py) |
| Multi-aircraft alerts | Summarize stale or suspicious tracks across the selected area. | [`tracker_manager.py`](tracker_manager.py) |
| Message adapter | Add another data source that produces the same challenge `state` message. | [`adapter.py`](adapter.py) |
| Raw ADS-B/Mode S adapter | Use the Python `pyModeS` decoder to turn raw receiver messages into challenge `state` messages. The standard requirements installation already installs `pyModeS`. | [*The 1090 Megahertz Riddle*](https://mode-s.org/1090mhz/) |
| Replay recorder | Save a live session and replay it later without internet access. | [`live_tracker.py`](live_tracker.py) |
| Different operating area | Make the bounding box configurable instead of editing the source file. | [`live_tracker.py`](live_tracker.py) |

## Getting Started

### Run the Live Tracker

Run from the repository root:

```bash
python -m pip install -r air-traffic-control/requirements.txt
python air-traffic-control/starter-kit/live-tracking/live_tracker.py
```

The program opens `http://127.0.0.1:8765/` in your browser. Leave the terminal running and press `Ctrl+C` to stop it.

You need an internet connection. Anonymous OpenSky access may be rate-limited or temporarily unavailable.

### Compare the Two Trackers

The normal command uses the simple tracker. Add `--ekf` to use the supplied matrix-based tracker:

```bash
python air-traffic-control/starter-kit/live-tracking/live_tracker.py --ekf
```

Compare how each tracker follows turns, reacts to a surprising report, and represents uncertainty.

### Optional OpenSky Account

The demo supports OpenSky OAuth client credentials.

On Windows PowerShell:

```powershell
$env:OPENSKY_CLIENT_ID="your-client-id"
$env:OPENSKY_CLIENT_SECRET="your-client-secret"
python air-traffic-control/starter-kit/live-tracking/live_tracker.py
```

On macOS or Linux:

```bash
export OPENSKY_CLIENT_ID="your-client-id"
export OPENSKY_CLIENT_SECRET="your-client-secret"
python air-traffic-control/starter-kit/live-tracking/live_tracker.py
```

Do not commit client secrets. Check the [OpenSky API documentation](https://openskynetwork.github.io/opensky-api/rest.html) for current account and rate-limit information.

### Watch a Different Area

The default bounding box is near Toronto Pearson. Edit `YYZ_BBOX` in [`live_tracker.py`](live_tracker.py) to use another small area:

```python
YYZ_BBOX = (lat_min, lon_min, lat_max, lon_max)
```

### Why Live Settings Differ

Prepared scenario messages may be several minutes apart, while live reports may be only seconds apart. A large surprise after several minutes could be a real turn. The same surprise after a few seconds is more likely to be bad data.

[`tracker_source.py`](tracker_source.py) therefore uses different settings for live data. This is a useful result to discuss: an algorithm must be tuned and tested for the data rate it will actually receive.

## Resources

### Folder Guide

| File | Purpose |
| --- | --- |
| [`live_tracker.py`](live_tracker.py) | Starts the server and polls OpenSky |
| [`opensky_client.py`](opensky_client.py) | Requests positioned aircraft inside the selected area |
| [`adapter.py`](adapter.py) | Converts OpenSky units and fields into challenge messages |
| [`tracker_source.py`](tracker_source.py) | Loads and configures a tracker from the starter kit |
| [`tracker_manager.py`](tracker_manager.py) | Maintains one track per aircraft and removes stale tracks |
| [`snapshot.py`](snapshot.py) | Predicts a display copy of each track to the current time |
| [`radar_server.py`](radar_server.py) | Serves the local radar page and JSON snapshots |
| [`static/index.html`](static/index.html) | Draws the radar interface |

### Compare the Data Sources

| Source | Data | Best use |
| --- | --- | --- |
| [`../scenarios/`](../scenarios/) | Small fixed examples | Building and debugging |
| [`../advanced/simulator.py`](../advanced/simulator.py) | Generated flight with known positions | Measuring accuracy |
| OpenSky live feed | Current reports from many aircraft | Demonstrations and assumption testing |

All three sources produce the same `state` message format. The tracker does not need to know where a message came from.

Keep a scenario-based demonstration ready as a backup. It is repeatable and can show route features that the live feed does not provide.
