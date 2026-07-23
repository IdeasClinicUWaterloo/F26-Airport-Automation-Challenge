"""
Drives a synthetic scenario (see simulator.py) through FlightRoutingSolution
and produces:

  - the existing interactive satellite map, now also showing the ground-truth
    track for comparison against reported/predicted/EKF-estimated positions
  - a diagnostics dashboard of EKF/tracking graphs: position error against
    ground truth, uncertainty growth and shrinkage, innovation (NIS) per
    message with the anomaly threshold marked, altitude/speed/heading
    tracking, and route-hypothesis weight convergence after the injected
    conflicting route update

Run from the repository root:

    python air-traffic-control/reference-solution/run_simulation.py
"""

import math
from pathlib import Path

import matplotlib
matplotlib.use("Agg")  # headless-safe; charts are saved to disk, not popped up
import matplotlib.pyplot as plt

import simulator
from dead_reckoning import DeadReckoning
from message_parser import FlightRoutingSolution
from visualizer import FlightVisualizer

_dr = DeadReckoning()


def run(seed=42, output_dir="air-traffic-control/reference-solution/output"):
    messages, truth, waypoints = simulator.build_scenario(seed=seed)

    solution = FlightRoutingSolution()
    visualizer = FlightVisualizer("air-traffic-control/data/route.json")
    visualizer.record_truth(truth)

    history = []

    for message in messages:
        solution.process_message(message)
        state = solution.get_state()
        visualizer.record(message, state)

        applied_ts = state.get("last_applied_timestamp")
        history.append({
            "timestamp": applied_ts,
            "true": simulator.nearest_truth(applied_ts, truth) if applied_ts else None,
            "reported": state.get("latest_position") if message.get("type") == "state" else None,
            "estimated": state.get("estimated_position"),
            "uncertainty": state.get("uncertainty_ellipse_m"),
            "nis": state.get("last_nis"),
            "nis_threshold": state.get("nis_threshold"),
            "altitude": state.get("altitude"),
            "speed": state.get("speed"),
            "heading": state.get("heading"),
            "anomalies_so_far": len(state.get("anomalies", [])),
            "hypotheses": state.get("hypotheses", []),
        })

    _print_summary(messages, solution, history)

    visualizer.show("SIM100", solution.get_state(), output_path=f"{output_dir}/simulation_map.html")
    _plot_dashboard(history, output_path=f"{output_dir}/ekf_dashboard.png")

    return solution, history


def _distance_km(p1, p2):
    if not p1 or not p2:
        return None
    return _dr.find_distance(p1["lat"], p1["lon"], p2["lat"], p2["lon"])


def _rmse(values):
    return math.sqrt(sum(v * v for v in values) / len(values)) if values else float("nan")


def _print_summary(messages, solution, history):
    state_count = sum(1 for m in messages if m["type"] == "state")
    reported_errors = [e for h in history if (e := _distance_km(h["true"], h["reported"])) is not None]
    estimated_errors = [e for h in history if (e := _distance_km(h["true"], h["estimated"])) is not None]

    print(f"Processed {len(messages)} messages ({state_count} state messages, {len(messages) - state_count} other).")
    print(f"Reported-position RMSE vs ground truth: {_rmse(reported_errors):.2f} km")
    print(f"EKF-estimate RMSE vs ground truth:      {_rmse(estimated_errors):.2f} km")

    anomalies = solution.get_state()["anomalies"]
    print(f"Anomalies flagged: {len(anomalies)} "
          f"(most are small innovation blips right after a sharp waypoint turn -- "
          f"expected, since the motion model assumes constant heading between messages)")

    injected = next((m for m in messages if m.get("_anomalous")), None)
    if injected is not None:
        caught = any(a["message_id"] == injected["message_id"] for a in anomalies)
        print(f"Deliberately injected corrupted message: {injected['message_id']} -- "
              f"{'CAUGHT' if caught else 'MISSED'} by innovation-based anomaly detection")

    for anomaly in anomalies:
        print(f"  - {anomaly['message_id']}: {anomaly['reason']}")


def _plot_dashboard(history, output_path):
    times = [h["timestamp"] for h in history]
    t0 = times[0]
    minutes = [(t - t0).total_seconds() / 60 for t in times]

    fig, axes = plt.subplots(3, 3, figsize=(16, 11))
    fig.suptitle("EKF Tracking Diagnostics", fontsize=14)

    _plot_position_error(axes[0][0], minutes, history)
    _plot_uncertainty(axes[0][1], minutes, history)
    _plot_nis(axes[0][2], minutes, history)
    _plot_series(axes[1][0], minutes, history, "altitude", lambda t: t["altitude"], "Altitude", "ft")
    _plot_series(axes[1][1], minutes, history, "speed", lambda t: t["ground_speed"], "Ground speed", "knots")
    _plot_series(axes[1][2], minutes, history, "heading", lambda t: t["heading"], "Heading", "degrees", marker=".")
    _plot_hypothesis_weights(axes[2][0], minutes, history)
    _plot_cumulative_anomalies(axes[2][1], minutes, history)
    axes[2][2].axis("off")

    fig.tight_layout(rect=[0, 0, 1, 0.96])
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=130)
    plt.close(fig)
    print(f"EKF diagnostics dashboard saved to: {out.resolve()}")


def _plot_position_error(ax, minutes, history):
    rep_x, rep_y, est_x, est_y = [], [], [], []
    for m, h in zip(minutes, history):
        if h["reported"] and h["true"]:
            rep_x.append(m)
            rep_y.append(_distance_km(h["true"], h["reported"]))
        if h["estimated"] and h["true"]:
            est_x.append(m)
            est_y.append(_distance_km(h["true"], h["estimated"]))
    ax.plot(rep_x, rep_y, "o-", color="#22c55e", label="raw reported", alpha=0.8, markersize=4)
    ax.plot(est_x, est_y, "o-", color="#7c3aed", label="EKF estimate", alpha=0.8, markersize=4)
    ax.set_title("Position error vs ground truth")
    ax.set_xlabel("minutes")
    ax.set_ylabel("km")
    ax.legend(fontsize=8)


def _plot_uncertainty(ax, minutes, history):
    xs = [m for m, h in zip(minutes, history) if h["uncertainty"]]
    ys = [h["uncertainty"][0] for h in history if h["uncertainty"]]
    ax.plot(xs, ys, "-", color="#a78bfa")
    ax.set_title("Position uncertainty (semi-major axis)")
    ax.set_xlabel("minutes")
    ax.set_ylabel("meters (~95% confidence)")


def _plot_nis(ax, minutes, history):
    xs = [m for m, h in zip(minutes, history) if h["nis"] is not None]
    ys = [h["nis"] for h in history if h["nis"] is not None]
    threshold = next((h["nis_threshold"] for h in history if h["nis_threshold"] is not None), None)

    colors = ["#ef4444" if (threshold and y > threshold) else "#7c3aed" for y in ys]
    ax.scatter(xs, ys, c=colors, s=18, zorder=3)
    ax.plot(xs, ys, "-", color="#c4b5fd", linewidth=1, zorder=2)
    if threshold:
        ax.axhline(threshold, color="black", linestyle="--", linewidth=1, label="anomaly threshold")
    ax.set_title("Innovation (NIS) per state message")
    ax.set_xlabel("minutes")
    ax.set_ylabel("NIS (log scale)")
    ax.set_yscale("log")
    ax.legend(fontsize=8)


def _plot_series(ax, minutes, history, key, truth_getter, title, unit, marker="-"):
    true_x, true_y, est_x, est_y = [], [], [], []
    for m, h in zip(minutes, history):
        if h["true"]:
            true_x.append(m)
            true_y.append(truth_getter(h["true"]))
        if h[key] is not None:
            est_x.append(m)
            est_y.append(h[key])
    ax.plot(true_x, true_y, marker, color="#111827", alpha=0.5, label="true", markersize=3)
    ax.plot(est_x, est_y, marker, color="#7c3aed", label="estimated", markersize=3)
    ax.set_title(title)
    ax.set_xlabel("minutes")
    ax.set_ylabel(unit)
    ax.legend(fontsize=8)


def _plot_hypothesis_weights(ax, minutes, history):
    seen_routes = []
    for h in history:
        for hyp in h["hypotheses"]:
            key = tuple(hyp["route"])
            if key not in seen_routes:
                seen_routes.append(key)

    for key in seen_routes:
        xs, ys = [], []
        for m, h in zip(minutes, history):
            match = next((hyp for hyp in h["hypotheses"] if tuple(hyp["route"]) == key), None)
            if match:
                xs.append(m)
                ys.append(match["weight"])
        label = " -> ".join(key)
        if len(label) > 40:
            label = label[:37] + "..."
        ax.plot(xs, ys, "o-", markersize=3, label=label)

    ax.set_title("Route hypothesis weights")
    ax.set_xlabel("minutes")
    ax.set_ylabel("weight")
    ax.set_ylim(0, 1.05)
    ax.legend(fontsize=6, loc="best")


def _plot_cumulative_anomalies(ax, minutes, history):
    ax.plot(minutes, [h["anomalies_so_far"] for h in history], "o-", color="#ef4444", markersize=3)
    ax.set_title("Cumulative anomalies flagged")
    ax.set_xlabel("minutes")
    ax.set_ylabel("count")


if __name__ == "__main__":
    run()
