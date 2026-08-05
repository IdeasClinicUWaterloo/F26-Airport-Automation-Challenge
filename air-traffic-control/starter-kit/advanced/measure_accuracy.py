"""Measure tracker error against a simulated flight with known positions.

Run from the repository root:

    python air-traffic-control/starter-kit/advanced/measure_accuracy.py
    python air-traffic-control/starter-kit/advanced/measure_accuracy.py --ekf

Use `--ekf` to measure the matrix-based tracker instead.
"""

import math
import statistics
import sys
from datetime import datetime
from pathlib import Path

# Import the main tracker from the parent directory.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import matplotlib
matplotlib.use("Agg")  # headless-safe: charts are written to disk, not popped up
import matplotlib.pyplot as plt

import simulator
from dead_reckoning import distance_km
from message_parser import FlightRoutingSolution
from tracker import AircraftTracker
from visualizer import FlightVisualizer

ADVANCED_DIR = Path(__file__).resolve().parent
STARTER_DIR = ADVANCED_DIR.parent
OUTPUT_DIR = ADVANCED_DIR / "output"
NAV_DATA = STARTER_DIR / "data" / "route.json"

def run(use_ekf=False, seed=42):
    if use_ekf:
        from ekf import AircraftEKF
        tracker_class = AircraftEKF
    else:
        tracker_class = AircraftTracker

    label = "matrix EKF (ekf.py)" if use_ekf else "simple tracker (tracker.py)"
    messages, truth, _ = simulator.build_scenario(seed=seed)

    solution = FlightRoutingSolution(NAV_DATA, tracker_class=tracker_class)
    visualizer = FlightVisualizer(NAV_DATA)

    history = []

    for message in messages:
        solution.process_message(message)
        state = solution.get_state()
        visualizer.record(message, state)

        # Score estimates at tracker time and reports at their own message time.
        applied_at = solution.tracker.last_timestamp
        reported_at = _parse(message.get("timestamp"))
        reported = message if message["type"] == "state" and "lat" in message else None

        history.append({
            "timestamp": applied_at,
            "true": simulator.nearest_truth(applied_at, truth) if applied_at else None,
            "true_when_reported": simulator.nearest_truth(reported_at, truth) if reported_at else None,
            "reported": {"lat": reported["lat"], "lon": reported["lon"]} if reported else None,
            "estimated": state["estimated_position"],
            "uncertainty_km": state["uncertainty_km"],
            "altitude": state["altitude"],
            "speed": state["speed"],
            "heading": state["heading"],
            "anomalies_so_far": len(state["anomalies"]),
        })

    _print_summary(label, messages, solution, history)

    suffix = "ekf" if use_ekf else "tracker"
    visualizer.show(
        "SIM100", solution.get_state(),
        output_path=OUTPUT_DIR / f"accuracy_map_{suffix}.html",
        open_browser=False,
    )
    _plot(history, OUTPUT_DIR / f"accuracy_{suffix}.png", label)

    return solution, history


# ---- scoring ----

def _error_km(truth_sample, position):
    """Return position error in kilometres, or None for missing data."""

    if not truth_sample or not position:
        return None
    return distance_km(
        truth_sample["lat"], truth_sample["lon"], position["lat"], position["lon"]
    )


def _rmse(values):
    """Return root-mean-square error, which emphasizes large misses."""

    if not values:
        return float("nan")
    return math.sqrt(sum(v * v for v in values) / len(values))


def _median(values):
    """Return median error, which is less affected by large outliers."""

    if not values:
        return float("nan")
    return statistics.median(values)


def _parse(value):
    try:
        return datetime.fromisoformat(value) if value else None
    except ValueError:
        return None


def _print_summary(label, messages, solution, history):
    state_count = sum(1 for m in messages if m["type"] == "state")
    reported_errors = [e for h in history
                      if (e := _error_km(h["true_when_reported"], h["reported"])) is not None]
    estimated_errors = [e for h in history if (e := _error_km(h["true"], h["estimated"])) is not None]

    print(f"Filter under test: {label}")
    print(f"Processed {len(messages)} messages "
          f"({state_count} state, {len(messages) - state_count} other).\n")

    print(f"  error vs ground truth  {'median':>9} {'RMSE':>9} {'worst':>9}   (km)")
    print(f"  {'raw reported':22} {_median(reported_errors):>9.2f} {_rmse(reported_errors):>9.2f} "
          f"{max(reported_errors, default=0):>9.2f}")
    print(f"  {'tracker estimate':22} {_median(estimated_errors):>9.2f} {_rmse(estimated_errors):>9.2f} "
          f"{max(estimated_errors, default=0):>9.2f}")
    print("\n  Read both numbers. The median is how well it tracks normally; the RMSE\n"
          "  and worst case are dominated by a few big misses right after sharp\n"
          "  waypoint turns, which a constant-heading model can't anticipate.")

    anomalies = solution.get_state()["anomalies"]
    print(f"\n  {len(anomalies)} message(s) flagged.")

    injected = next((m for m in messages if m.get("_anomalous")), None)
    if injected is not None:
        caught = any(a["message_id"] == injected["message_id"] for a in anomalies)
        print(f"  The deliberately corrupted message ({injected['message_id']}) was "
              f"{'CAUGHT' if caught else 'MISSED'}.")

    for anomaly in anomalies:
        print(f"    - {anomaly['message_id']}: {anomaly['reason']}")


# ---- charts ----

def _plot(history, output_path, label):
    times = [h["timestamp"] for h in history if h["timestamp"]]
    if not times:
        print("Nothing to plot.")
        return

    start = times[0]
    minutes = [(h["timestamp"] - start).total_seconds() / 60 if h["timestamp"] else None
               for h in history]

    figure, axes = plt.subplots(2, 3, figsize=(16, 8))
    figure.suptitle(f"Tracker accuracy against known ground truth -- {label}", fontsize=13)

    _plot_position_error(axes[0][0], minutes, history)
    _plot_uncertainty(axes[0][1], minutes, history)
    _plot_cumulative_anomalies(axes[0][2], minutes, history)
    _plot_against_truth(axes[1][0], minutes, history, "altitude", "altitude", "Altitude", "ft")
    _plot_against_truth(axes[1][1], minutes, history, "speed", "ground_speed", "Ground speed", "knots")
    _plot_against_truth(axes[1][2], minutes, history, "heading", "heading", "Heading", "degrees")

    figure.tight_layout(rect=[0, 0, 1, 0.95])
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(out, dpi=120)
    plt.close(figure)
    print(f"\nCharts saved to: {out.resolve()}")


def _plot_position_error(ax, minutes, history):
    """Plot raw-report and tracker position errors."""

    for key, truth_key, colour, name in (
        ("reported", "true_when_reported", "#22c55e", "raw reported"),
        ("estimated", "true", "#7c3aed", "tracker estimate"),
    ):
        xs, ys = [], []
        for minute, h in zip(minutes, history):
            error = _error_km(h[truth_key], h[key])
            if error is not None and minute is not None:
                xs.append(minute)
                ys.append(error)
        ax.plot(xs, ys, "o-", color=colour, label=name, alpha=0.8, markersize=3)

    ax.set_title("Position error vs ground truth")
    ax.set_xlabel("minutes")
    ax.set_ylabel("km")
    ax.legend(fontsize=8)


def _plot_uncertainty(ax, minutes, history):
    """Plot the tracker's reported uncertainty over time."""

    xs = [m for m, h in zip(minutes, history) if h["uncertainty_km"] is not None]
    ys = [h["uncertainty_km"] for h in history if h["uncertainty_km"] is not None]
    ax.plot(xs, ys, "-", color="#a78bfa")
    ax.set_title("How unsure the tracker says it is")
    ax.set_xlabel("minutes")
    ax.set_ylabel("km")


def _plot_cumulative_anomalies(ax, minutes, history):
    ax.plot(minutes, [h["anomalies_so_far"] for h in history], "o-",
            color="#ef4444", markersize=3)
    ax.set_title("Messages flagged (running total)")
    ax.set_xlabel("minutes")
    ax.set_ylabel("count")


def _plot_against_truth(ax, minutes, history, state_key, truth_key, title, unit):
    true_x, true_y, est_x, est_y = [], [], [], []

    for minute, h in zip(minutes, history):
        if minute is None:
            continue
        if h["true"]:
            true_x.append(minute)
            true_y.append(h["true"][truth_key])
        if h[state_key] is not None:
            est_x.append(minute)
            est_y.append(h[state_key])

    ax.plot(true_x, true_y, "-", color="#111827", alpha=0.5, label="true")
    ax.plot(est_x, est_y, "-", color="#7c3aed", label="estimated")
    ax.set_title(title)
    ax.set_xlabel("minutes")
    ax.set_ylabel(unit)
    ax.legend(fontsize=8)


if __name__ == "__main__":
    run(use_ekf="--ekf" in sys.argv)
