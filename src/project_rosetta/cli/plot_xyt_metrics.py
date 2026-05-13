import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

GRAVITY_M_S2 = 9.80665


def _positive_float(value: str) -> float:
    parsed_value = float(value)
    if parsed_value <= 0:
        raise argparse.ArgumentTypeError("Value must be greater than zero.")
    return parsed_value


def xyt_path_arg(value: str) -> Path:
    """
    Validate and normalize an XYT file path.

    Args:
        value: The XYT file path as a string.

    Returns:
        The validated XYT file path.

    Raises:
        argparse.ArgumentTypeError: If the file does not exist.

    """
    path = Path(value)
    if not path.is_file():
        raise argparse.ArgumentTypeError(f"{path} does not exist or is not a file.")
    return path


def args(argv: list[str] | None = None) -> argparse.Namespace:
    """
    Parse CLI arguments for plotting XYT motion metrics.

    Args:
        argv: Optional list of command-line arguments. If None, defaults to sys.argv.

    Returns:
        Parsed CLI arguments.

    """
    parser = argparse.ArgumentParser(description="Plot motion metrics derived from an XYT file.")
    parser.add_argument("xyt_path", type=xyt_path_arg, help="Path to the input .xyt file.")
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional output image path. If omitted, the plot is shown interactively.",
    )
    parser.add_argument(
        "--max-speed",
        type=_positive_float,
        help="Optional robot speed limit [m/s].",
    )
    parser.add_argument(
        "--max-longitudinal-acceleration",
        type=_positive_float,
        help="Optional longitudinal acceleration limit [m/s^2].",
    )
    parser.add_argument(
        "--max-lateral-acceleration",
        type=_positive_float,
        help="Optional lateral acceleration limit [m/s^2].",
    )
    parser.add_argument(
        "--max-total-acceleration",
        type=_positive_float,
        help="Optional total acceleration limit [m/s^2].",
    )
    parser.add_argument(
        "--max-yaw-rate",
        type=_positive_float,
        help="Optional yaw-rate limit [rad/s].",
    )
    parser.add_argument(
        "--max-jerk",
        type=_positive_float,
        help="Optional total jerk limit [m/s^3].",
    )
    parser.add_argument(
        "--min-turn-radius",
        type=_positive_float,
        help="Optional minimum turning radius [m].",
    )
    return parser.parse_args(argv)


def load_xyt(xyt_path: Path) -> pd.DataFrame:
    """
    Load an XYT file that uses spaces as separators and commas as decimals.

    Args:
        xyt_path: Path to the XYT file.

    Returns:
        A DataFrame with x, y, and time columns.

    """
    return pd.read_csv(
        xyt_path,
        sep=r"\s+",
        header=None,
        names=["x", "y", "time"],
        decimal=",",
        engine="python",
    )


def _gradient(values: pd.Series, time_values: pd.Series) -> np.ndarray:
    values_array = values.to_numpy(dtype=float)
    time_array = time_values.to_numpy(dtype=float)
    return np.gradient(values_array, time_array)


def _safe_inverse(values: pd.Series, min_abs_value: float = 1e-9) -> np.ndarray:
    values_array = values.to_numpy(dtype=float)
    inverse = np.full_like(values_array, np.inf, dtype=float)
    valid = np.abs(values_array) > min_abs_value
    inverse[valid] = 1.0 / values_array[valid]
    return inverse


def calculate_motion_metrics(xyt_data: pd.DataFrame) -> pd.DataFrame:
    """
    Derive motion metrics from XYT coordinates.

    Args:
        xyt_data: DataFrame with x, y, and time columns.

    Returns:
        A copy of the input data with derived motion-metric columns.

    Raises:
        ValueError: If the time values are not strictly increasing.

    """
    metrics_data = xyt_data.copy()
    dt = metrics_data["time"].diff()

    invalid_time_steps = dt.iloc[1:] <= 0
    if invalid_time_steps.any():
        raise ValueError("XYT time values must be strictly increasing to compute motion metrics.")

    metrics_data["vx_m_s"] = _gradient(metrics_data["x"], metrics_data["time"])
    metrics_data["vy_m_s"] = _gradient(metrics_data["y"], metrics_data["time"])
    metrics_data["ax_m_s2"] = _gradient(metrics_data["vx_m_s"], metrics_data["time"])
    metrics_data["ay_m_s2"] = _gradient(metrics_data["vy_m_s"], metrics_data["time"])
    metrics_data["speed_m_s"] = np.hypot(
        metrics_data["vx_m_s"],
        metrics_data["vy_m_s"],
    )
    metrics_data["longitudinal_acceleration_m_s2"] = _gradient(
        metrics_data["speed_m_s"],
        metrics_data["time"],
    )

    yaw_rad = np.unwrap(np.arctan2(metrics_data["vy_m_s"], metrics_data["vx_m_s"]))
    metrics_data["yaw_rad"] = yaw_rad
    metrics_data["yaw_rate_rad_s"] = _gradient(metrics_data["yaw_rad"], metrics_data["time"])
    metrics_data["yaw_acceleration_rad_s2"] = _gradient(
        metrics_data["yaw_rate_rad_s"],
        metrics_data["time"],
    )
    metrics_data["lateral_acceleration_m_s2"] = (
        metrics_data["speed_m_s"] * metrics_data["yaw_rate_rad_s"]
    )
    metrics_data["acceleration_magnitude_m_s2"] = np.hypot(
        metrics_data["ax_m_s2"],
        metrics_data["ay_m_s2"],
    )
    metrics_data["curvature_rad_m"] = np.divide(
        metrics_data["yaw_rate_rad_s"],
        metrics_data["speed_m_s"],
        out=np.zeros_like(metrics_data["yaw_rate_rad_s"].to_numpy(dtype=float)),
        where=metrics_data["speed_m_s"].to_numpy(dtype=float) > 1e-9,
    )
    metrics_data["turn_radius_m"] = np.abs(_safe_inverse(metrics_data["curvature_rad_m"]))
    metrics_data["jerk_m_s3"] = _gradient(
        metrics_data["acceleration_magnitude_m_s2"],
        metrics_data["time"],
    )
    metrics_data["required_friction_coeff"] = (
        metrics_data["acceleration_magnitude_m_s2"] / GRAVITY_M_S2
    )
    return metrics_data


def summarize_motion_metrics(metrics_data: pd.DataFrame) -> dict[str, float]:
    """
    Return peak metrics useful for trajectory feasibility checks.

    Returns:
        A mapping with the peak speed, acceleration, jerk, curvature, friction,
        and minimum turn radius derived from the XYT data.

    """
    finite_turn_radius = metrics_data.loc[
        np.isfinite(metrics_data["turn_radius_m"]),
        "turn_radius_m",
    ]
    return {
        "peak_speed_m_s": float(metrics_data["speed_m_s"].max()),
        "peak_longitudinal_acceleration_m_s2": float(
            metrics_data["longitudinal_acceleration_m_s2"].abs().max()
        ),
        "peak_lateral_acceleration_m_s2": float(
            metrics_data["lateral_acceleration_m_s2"].abs().max()
        ),
        "peak_total_acceleration_m_s2": float(metrics_data["acceleration_magnitude_m_s2"].max()),
        "peak_yaw_rate_rad_s": float(metrics_data["yaw_rate_rad_s"].abs().max()),
        "peak_yaw_acceleration_rad_s2": float(metrics_data["yaw_acceleration_rad_s2"].abs().max()),
        "peak_jerk_m_s3": float(metrics_data["jerk_m_s3"].abs().max()),
        "max_curvature_rad_m": float(metrics_data["curvature_rad_m"].abs().max()),
        "min_turn_radius_m": (
            float(finite_turn_radius.min()) if not finite_turn_radius.empty else float("inf")
        ),
        "peak_required_friction_coeff": float(metrics_data["required_friction_coeff"].max()),
    }


def evaluate_limits(
    metrics_summary: dict[str, float],
    parsed_args: argparse.Namespace,
) -> list[str]:
    """
    Compare derived metrics against optional robot limits.

    Returns:
        A list of human-readable limit violations. The list is empty when all
        configured limits are satisfied.

    """
    limit_definitions = [
        ("max_speed", "peak_speed_m_s", "speed"),
        (
            "max_longitudinal_acceleration",
            "peak_longitudinal_acceleration_m_s2",
            "longitudinal acceleration",
        ),
        (
            "max_lateral_acceleration",
            "peak_lateral_acceleration_m_s2",
            "lateral acceleration",
        ),
        (
            "max_total_acceleration",
            "peak_total_acceleration_m_s2",
            "total acceleration",
        ),
        ("max_yaw_rate", "peak_yaw_rate_rad_s", "yaw rate"),
        ("max_jerk", "peak_jerk_m_s3", "jerk"),
    ]

    violations: list[str] = []
    for arg_name, summary_key, label in limit_definitions:
        limit = getattr(parsed_args, arg_name)
        if limit is None:
            continue
        measured_value = metrics_summary[summary_key]
        if measured_value > limit:
            violations.append(f"{label} exceeds limit: {measured_value:.3f} > {limit:.3f}")

    if parsed_args.min_turn_radius is not None:
        min_turn_radius = metrics_summary["min_turn_radius_m"]
        if min_turn_radius < parsed_args.min_turn_radius:
            violations.append(
                "turn radius exceeds limit: "
                "required "
                f"{min_turn_radius:.3f} m < allowed minimum "
                f"{parsed_args.min_turn_radius:.3f} m"
            )

    return violations


def print_motion_summary(metrics_summary: dict[str, float], violations: list[str]) -> None:
    """Print a compact summary for terminal use."""
    print("Motion summary:")
    print(f"  Peak speed: {metrics_summary['peak_speed_m_s']:.3f} m/s")
    print(
        "  Peak longitudinal acceleration: "
        f"{metrics_summary['peak_longitudinal_acceleration_m_s2']:.3f} m/s^2"
    )
    print(
        "  Peak lateral acceleration: "
        f"{metrics_summary['peak_lateral_acceleration_m_s2']:.3f} m/s^2"
    )
    print(f"  Peak total acceleration: {metrics_summary['peak_total_acceleration_m_s2']:.3f} m/s^2")
    print(f"  Peak yaw rate: {metrics_summary['peak_yaw_rate_rad_s']:.3f} rad/s")
    print(f"  Peak jerk: {metrics_summary['peak_jerk_m_s3']:.3f} m/s^3")
    print(f"  Minimum turn radius: {metrics_summary['min_turn_radius_m']:.3f} m")
    print(
        "  Peak required friction coefficient: "
        f"{metrics_summary['peak_required_friction_coeff']:.3f}"
    )

    if violations:
        print("Limit check: trajectory exceeds the provided limits.")
        for violation in violations:
            print(f"  - {violation}")
        return

    print("Limit check: no provided limits were violated.")


def plot_motion_metrics(
    metrics_data: pd.DataFrame,
    xyt_path: Path,
    output_path: Path | None = None,
) -> None:
    """
    Plot derived motion metrics and either save or show the figure.

    Args:
        metrics_data: DataFrame with derived motion-metric columns.
        xyt_path: Source XYT file path for labeling.
        output_path: Optional image file path.

    """
    figure, axes = plt.subplots(5, 2, figsize=(15, 18))
    plot_axes = axes.flatten()

    plot_axes[0].plot(metrics_data["time"], metrics_data["speed_m_s"], linewidth=2)
    plot_axes[0].set_title("Speed")
    plot_axes[0].set_xlabel("Time [s]")
    plot_axes[0].set_ylabel("Speed [m/s]")

    plot_axes[1].plot(
        metrics_data["time"],
        metrics_data["longitudinal_acceleration_m_s2"],
        linewidth=2,
    )
    plot_axes[1].set_title("Longitudinal Acceleration")
    plot_axes[1].set_xlabel("Time [s]")
    plot_axes[1].set_ylabel("Acceleration [m/s^2]")

    plot_axes[2].plot(
        metrics_data["time"],
        metrics_data["lateral_acceleration_m_s2"],
        linewidth=2,
    )
    plot_axes[2].set_title("Lateral Acceleration")
    plot_axes[2].set_xlabel("Time [s]")
    plot_axes[2].set_ylabel("Acceleration [m/s^2]")

    plot_axes[3].plot(
        metrics_data["time"],
        metrics_data["acceleration_magnitude_m_s2"],
        linewidth=2,
    )
    plot_axes[3].set_title("Total Acceleration Magnitude")
    plot_axes[3].set_xlabel("Time [s]")
    plot_axes[3].set_ylabel("Acceleration [m/s^2]")

    plot_axes[4].plot(metrics_data["time"], metrics_data["yaw_rate_rad_s"], linewidth=2)
    plot_axes[4].set_title("Yaw Rate")
    plot_axes[4].set_xlabel("Time [s]")
    plot_axes[4].set_ylabel("Yaw Rate [rad/s]")

    plot_axes[5].plot(metrics_data["time"], metrics_data["yaw_acceleration_rad_s2"], linewidth=2)
    plot_axes[5].set_title("Yaw Acceleration")
    plot_axes[5].set_xlabel("Time [s]")
    plot_axes[5].set_ylabel("Yaw Acceleration [rad/s^2]")

    plot_axes[6].plot(metrics_data["time"], metrics_data["curvature_rad_m"], linewidth=2)
    plot_axes[6].set_title("Curvature")
    plot_axes[6].set_xlabel("Time [s]")
    plot_axes[6].set_ylabel("Curvature [rad/m]")

    plot_axes[7].plot(metrics_data["time"], metrics_data["turn_radius_m"], linewidth=2)
    plot_axes[7].set_title("Turn Radius")
    plot_axes[7].set_xlabel("Time [s]")
    plot_axes[7].set_ylabel("Radius [m]")

    plot_axes[8].plot(metrics_data["time"], metrics_data["x"], label="x", linewidth=2)
    plot_axes[8].plot(metrics_data["time"], metrics_data["y"], label="y", linewidth=2)
    plot_axes[8].set_title("Position vs Time")
    plot_axes[8].set_xlabel("Time [s]")
    plot_axes[8].set_ylabel("Position [m]")
    plot_axes[8].legend()

    plot_axes[9].plot(metrics_data["x"], metrics_data["y"], linewidth=2)
    plot_axes[9].set_title("XY Trajectory")
    plot_axes[9].set_xlabel("x [m]")
    plot_axes[9].set_ylabel("y [m]")
    plot_axes[9].axis("equal")

    for axis in plot_axes:
        axis.grid(True)

    figure.suptitle(f"XYT Motion Metrics: {xyt_path.name}")
    figure.tight_layout()

    if output_path is not None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        figure.savefig(output_path, dpi=150)
        print(f"Saved plot to {output_path}")
        plt.close(figure)
        return

    if "agg" in plt.get_backend().lower():
        default_output_path = xyt_path.with_name(f"{xyt_path.stem}_motion_metrics.png")
        default_output_path.parent.mkdir(parents=True, exist_ok=True)
        figure.savefig(default_output_path, dpi=150)
        print(f"No interactive Matplotlib backend detected; saved plot to {default_output_path}")
        plt.close(figure)
        return

    plt.show()


def main(argv: list[str] | None = None) -> int:
    """
    Run the XYT motion-metrics plot CLI command.

    Args:
        argv: Optional list of command-line arguments.

    Returns:
        Exit status code.

    """
    parsed_args = args(argv)
    xyt_data = load_xyt(parsed_args.xyt_path)
    metrics_data = calculate_motion_metrics(xyt_data)
    metrics_summary = summarize_motion_metrics(metrics_data)
    violations = evaluate_limits(metrics_summary, parsed_args)
    print_motion_summary(metrics_summary, violations)
    plot_motion_metrics(metrics_data, parsed_args.xyt_path, parsed_args.output)
    return 0
