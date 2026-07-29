"""
Borrows a tracker from the reference solution rather than carrying one here.

This folder deliberately contains no filter of its own. OpenSky's job is to be a
*message source* -- the live equivalent of `../scenarios/*.json` -- so the actual
state estimation is done by the same code that handles the canned scenarios. One
copy means a fix over there shows up here, and the two can't drift apart.

Either tracker works, because they expose the same interface:

    tracker.py           one uncertainty radius in km, no numpy   (default)
    advanced/ekf.py      6x6 covariance matrix, needs numpy       (--ekf)

Swapping between them is the whole point of the exercise -- run the live feed
through both and watch which one holds a turning aircraft better.
"""

import sys
from pathlib import Path

REFERENCE_DIR = Path(__file__).resolve().parent.parent / "reference-solution"
ADVANCED_DIR = REFERENCE_DIR / "advanced"


# ---------------------------------------------------------------------------
# Re-tuning for the data rate.
#
# The simple tracker's defaults assume messages minutes apart, because that's what
# the challenge scenarios deliver. OpenSky reports every ~15 seconds, and the same
# numbers are wrong at that rate: MEASUREMENT_ERROR_KM = 3.0 says "a report could
# be 3 km off", which is a fair worry next to a five-minute-old prediction but
# absurd next to a fifteen-second-old one. Left alone, the gain works out around
# 0.08 and the estimate crawls along permanently behind the aircraft.
#
# ADS-B positions are good to roughly 50 m, so that's what we tell it.
# ---------------------------------------------------------------------------

SIMPLE_TRACKER_TUNING = {
    "MEASUREMENT_ERROR_KM": 0.05,
    "DRIFT_PER_MINUTE_KM": 2.0,
    "ANOMALY_SIGMA": 4.0,

    # Note this is 0.0 here and 0.3 in the reference solution, and the reason is
    # the sampling rate rather than a difference of opinion.
    #
    # In the scenarios, messages arrive minutes apart, so a surprising report is
    # usually a real turn the constant-heading model couldn't see coming -- and
    # refusing to believe it loses the aircraft, because the gap grows faster than
    # the tolerance widens. There, partial trust is essential.
    #
    # Here reports arrive every 15 seconds. Fifteen seconds of turning barely moves
    # an aircraft, so a report that lands far from the prediction is not a
    # manoeuvre, it's bad data. And coasting uncertainty grows at 2 km/min, which
    # outpaces anything a real aircraft can do in that window, so a rejected track
    # re-acquires within a poll or two on its own.
    #
    # Leave it at 0.3 and a single corrupted position drags the estimate ~30 km off
    # and it stays flagged for several polls. Try it.
    "ANOMALY_TRUST": 0.0,
}

# The matrix EKF needs none of this, and the reason is worth noticing. Its noise is
# specified per second and scaled by dt inside predict(), and its measurement noise
# is already an ADS-B-scale 2500 m^2 (50 m). So it adapts to the data rate on its
# own, where the simple tracker's flat "3 km" does not. That robustness across
# sampling rates is a real argument for the extra machinery -- a better one than
# raw accuracy.
MATRIX_EKF_TUNING = {}


def load_tracker(use_ekf=False):
    """Return the tracker class to instantiate per aircraft.

    Raises SystemExit with an explanation rather than an ImportError traceback,
    since "the reference solution isn't next door" is a setup problem, not a bug.
    """

    if not REFERENCE_DIR.is_dir():
        raise SystemExit(
            f"Could not find the reference solution at:\n"
            f"  {REFERENCE_DIR}\n\n"
            f"This add-on tracks with that code rather than duplicating it. Either\n"
            f"restore that folder, or edit tracker_source.py to import your own\n"
            f"tracker -- it needs start(), predict(), update(), and a `position`\n"
            f"property. See AircraftTrack in tracker_manager.py for how it's called."
        )

    sys.path.insert(0, str(REFERENCE_DIR))

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
    """Override a tracker module's knobs for this data rate.

    They're module-level constants read inside the methods, so setting them here
    takes effect without editing the reference files -- which matters, because
    those defaults are right for the scenarios and shouldn't change.

    Raises on an unknown knob rather than skipping it. A silent no-op here would
    mean running the live feed with scenario-rate tuning and no indication why the
    tracking looked sluggish.
    """

    for name, value in tuning.items():
        if not hasattr(module, name):
            raise SystemExit(
                f"{module.__name__} has no knob called {name}. tracker_source.py "
                f"needs updating to match it."
            )
        setattr(module, name, value)
