"""Load the starter kit's simple tracker or optional EKF for live data."""

import sys
from pathlib import Path

STARTER_DIR = Path(__file__).resolve().parent.parent
ADVANCED_DIR = STARTER_DIR / "advanced"


# OpenSky reports arrive more often than scenario messages, so the simple tracker
# needs lower measurement error and different anomaly handling.
SIMPLE_TRACKER_TUNING = {
    "MEASUREMENT_ERROR_KM": 0.05,
    "DRIFT_PER_MINUTE_KM": 2.0,
    "ANOMALY_SIGMA": 4.0,

    # A large jump over 15 seconds is unlikely to be a real turn.
    "ANOMALY_TRUST": 0.0,
}

# The EKF scales process noise by elapsed time and already uses ADS-B-scale noise.
MATRIX_EKF_TUNING = {}


def load_tracker(use_ekf=False):
    """Return the selected tracker class or exit with a setup error."""

    if not STARTER_DIR.is_dir():
        raise SystemExit(
            f"Could not find the starter kit at:\n"
            f"  {STARTER_DIR}\n\n"
            f"This add-on tracks with that code rather than duplicating it. Either\n"
            f"restore that folder, or edit tracker_source.py to import your own\n"
            f"tracker -- it needs start(), predict(), update(), and a `position`\n"
            f"property. See AircraftTrack in tracker_manager.py for how it's called."
        )

    sys.path.insert(0, str(STARTER_DIR))

    if use_ekf:
        if not ADVANCED_DIR.is_dir():
            raise SystemExit(f"--ekf needs {ADVANCED_DIR}, which isn't there.")
        sys.path.insert(0, str(ADVANCED_DIR))

        import ekf
        _retune(ekf, MATRIX_EKF_TUNING)
        return ekf.AircraftEKF

    import tracker
    _retune(tracker, SIMPLE_TRACKER_TUNING)
    return tracker.AircraftTracker


def _retune(module, tuning):
    """Override module-level tracker settings and reject unknown names."""

    for name, value in tuning.items():
        if not hasattr(module, name):
            raise SystemExit(
                f"{module.__name__} has no knob called {name}. tracker_source.py "
                f"needs updating to match it."
            )
        setattr(module, name, value)
