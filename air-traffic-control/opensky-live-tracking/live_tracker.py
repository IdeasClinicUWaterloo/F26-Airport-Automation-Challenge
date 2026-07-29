"""
Entry point: polls OpenSky for live aircraft states around a bounding box, feeds
each aircraft's reports through its own tracker, and serves an animated
radar-style view of the result.

Run from the repository root:

    pip install -r air-traffic-control/opensky-live-tracking/requirements.txt
    python air-traffic-control/opensky-live-tracking/live_tracker.py
    python air-traffic-control/opensky-live-tracking/live_tracker.py --ekf

Opens http://127.0.0.1:8765/ in your browser. The page polls this process every
couple of seconds and animates aircraft between updates, so leave the tab open
rather than reloading it. Ctrl+C to stop.

`--ekf` runs the same live feed through the matrix Kalman filter in
../reference-solution/advanced/ instead of the simple tracker, which is the
cheapest way to see the difference between them on real data.
"""

import itertools
import sys
import time
import webbrowser
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from adapter import to_state_message
from opensky_client import OpenSkyClient
from radar_server import start_server
from tracker_manager import TrackerManager
from tracker_source import load_tracker

# Roughly the airspace around Toronto Pearson (YYZ). Move or widen this to watch
# somewhere else -- (lat_min, lon_min, lat_max, lon_max).
YYZ_BBOX = (43.0, -80.5, 44.5, -78.5)

# OpenSky asks for a gap between queries even when scoped to a bounding box.
# Conservative default rather than a hard requirement.
POLL_INTERVAL_SECONDS = 15

SERVER_PORT = 8765


def main(use_ekf=False):
    tracker_class = load_tracker(use_ekf=use_ekf)
    print(f"Tracking with {tracker_class.__module__}.{tracker_class.__name__}")

    client = OpenSkyClient()
    manager = TrackerManager(tracker_class)
    message_ids = itertools.count(1)

    start_server(manager, port=SERVER_PORT)
    url = f"http://127.0.0.1:{SERVER_PORT}/"
    print(f"Radar view live at {url}")
    webbrowser.open(url)

    print(f"Polling OpenSky every {POLL_INTERVAL_SECONDS}s for traffic near YYZ...")
    print("Press Ctrl+C to stop.\n")

    try:
        while True:
            _poll_once(client, manager, message_ids)
            time.sleep(POLL_INTERVAL_SECONDS)
    except KeyboardInterrupt:
        print("\nStopped.")


def _poll_once(client, manager, message_ids):
    """One fetch-and-ingest cycle. A failed request is reported and skipped rather
    than fatal -- a rate limit or a dropped connection shouldn't end a live demo,
    and the trackers coast forward until the next successful poll anyway."""

    try:
        states = client.fetch_states(bbox=YYZ_BBOX)
    except Exception as error:
        print(f"  OpenSky request failed ({error}); coasting until the next poll")
        return

    for raw in states:
        manager.ingest(to_state_message(raw, message_id=next(message_ids)))

    active = manager.active_tracks()
    print(f"Fetched {len(states)} aircraft, {len(active)} active track(s)")

    for track in active:
        position = track.tracker.position
        if position is None:
            continue
        flag = "  ANOMALY" if track.last_message_flagged else ""
        print(
            f"  {(track.callsign or track.aircraft_id):>10}  "
            f"lat={position['lat']:8.4f} lon={position['lon']:9.4f}  "
            f"+/-{track.tracker.uncertainty_km:5.1f}km{flag}"
        )


if __name__ == "__main__":
    main(use_ekf="--ekf" in sys.argv)
