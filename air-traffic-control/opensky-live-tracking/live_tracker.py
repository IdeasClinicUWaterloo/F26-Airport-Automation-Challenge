"""
Demo entry point: polls OpenSky for live state vectors around a bounding box
(default: the airspace around Toronto Pearson / YYZ), feeds each aircraft's
reports through its own AircraftEKF via TrackerManager, and serves a live
animated radar-style view of the result.

Run from the repository root:

    pip install -r air-traffic-control/opensky-live-tracking/requirements.txt
    python air-traffic-control/opensky-live-tracking/live_tracker.py

This opens http://127.0.0.1:8765/ in your browser -- the page polls this
process every couple of seconds and animates aircraft between updates; it
does not need a full page reload to move them. Stop the script with Ctrl+C.
"""

import itertools
import sys
import time
import webbrowser
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from opensky_client import OpenSkyClient
from adapter import to_state_message
from tracker_manager import TrackerManager
from radar_server import start_server

# Roughly the airspace around Toronto Pearson (YYZ). Widen/move this to
# watch a different airport.
YYZ_BBOX = (43.0, -80.5, 44.5, -78.5)

# OpenSky asks for a gap of several seconds between queries even when scoped
# to a bounding box; this is a conservative default, not a hard requirement.
POLL_INTERVAL_SECONDS = 15

SERVER_PORT = 8765


def main():
    client = OpenSkyClient()
    manager = TrackerManager()
    message_ids = itertools.count(1)

    start_server(manager, port=SERVER_PORT)
    url = f"http://127.0.0.1:{SERVER_PORT}/"
    print(f"Radar view live at {url}")
    webbrowser.open(url)

    print(f"Polling OpenSky every {POLL_INTERVAL_SECONDS}s for traffic near YYZ...")
    print("Press Ctrl+C to stop.\n")

    try:
        while True:
            states = client.fetch_states(bbox=YYZ_BBOX)
            print(f"Fetched {len(states)} aircraft in bbox")

            for raw in states:
                message = to_state_message(raw, message_id=next(message_ids))
                manager.ingest(message)

            for track in manager.active_tracks():
                pos = track.ekf.position()
                if pos:
                    print(
                        f"  {(track.callsign or track.aircraft_id):>10}  "
                        f"lat={pos['lat']:.4f} lon={pos['lon']:.4f}  "
                        f"anomalies={len(track.anomalies)}"
                    )

            time.sleep(POLL_INTERVAL_SECONDS)

    except KeyboardInterrupt:
        print("\nStopped.")


if __name__ == "__main__":
    main()
