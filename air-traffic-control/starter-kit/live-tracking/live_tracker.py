"""Poll OpenSky, track nearby aircraft, and serve the local radar page.

Run from the repository root:

    python -m pip install -r air-traffic-control/requirements.txt
    python air-traffic-control/starter-kit/live-tracking/live_tracker.py
    python air-traffic-control/starter-kit/live-tracking/live_tracker.py --ekf

Use `--ekf` to select the matrix-based tracker. Press Ctrl+C to stop.
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

# Bounding box near Toronto Pearson: (lat_min, lon_min, lat_max, lon_max).
YYZ_BBOX = (43.0, -80.5, 44.5, -78.5)

# Avoid polling the service too frequently.
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
    """Fetch one batch. On failure, keep existing tracks until the next poll."""

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
