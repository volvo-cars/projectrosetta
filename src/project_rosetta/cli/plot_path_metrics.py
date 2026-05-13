import argparse
import xml.etree.ElementTree as ET
from pathlib import Path

import pandas as pd

from project_rosetta.cli.plot_xyt_metrics import (
    _positive_float,
    calculate_motion_metrics,
    evaluate_limits,
    plot_motion_metrics,
    print_motion_summary,
    summarize_motion_metrics,
)

PATH_XML_NAMESPACE = {"abd": "https://www.abdynamics.com/PathV4"}


def path_file_arg(value: str) -> Path:
    """
    Validate and normalize a `.path` file path.

    Args:
        value: The path file path as a string.

    Returns:
        The validated path file path.

    Raises:
        argparse.ArgumentTypeError: If the file does not exist.

    """
    path = Path(value)
    if not path.is_file():
        raise argparse.ArgumentTypeError(f"{path} does not exist or is not a file.")
    return path


def args(argv: list[str] | None = None) -> argparse.Namespace:
    """
    Parse CLI arguments for plotting path spline motion metrics.

    Args:
        argv: Optional list of command-line arguments. If None, defaults to sys.argv.

    Returns:
        Parsed CLI arguments.

    """
    parser = argparse.ArgumentParser(
        description="Plot motion metrics derived from SplinePointList data in a .path file."
    )
    parser.add_argument("path_file", type=path_file_arg, help="Path to the input .path file.")
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


def load_path_spline_points(path_file: Path) -> pd.DataFrame:
    """
    Load all points from the first SplinePointList in a `.path` XML file.

    Args:
        path_file: Path to the `.path` file.

    Returns:
        A DataFrame with x, y, time, velocity, heading, and distance columns.

    Raises:
        ValueError: If the file does not contain any SplinePoint elements.

    """
    xml_root = ET.parse(path_file).getroot()
    spline_points = xml_root.findall(
        ".//abd:SplinePointList/abd:SplinePoint",
        PATH_XML_NAMESPACE,
    )

    if not spline_points:
        raise ValueError(f"{path_file} does not contain any SplinePoint elements.")

    records: list[dict[str, float]] = []
    for spline_point in spline_points:
        records.append(
            {
                "x": float(spline_point.attrib["x"]),
                "y": float(spline_point.attrib["y"]),
                "time": float(spline_point.attrib["time"]),
                "velocity": float(spline_point.attrib.get("velocity", "0")),
                "heading_deg": float(spline_point.attrib.get("heading", "0")),
                "distance": float(spline_point.attrib.get("distance", "0")),
            }
        )

    return pd.DataFrame.from_records(records)


def main(argv: list[str] | None = None) -> int:
    """
    Run the path motion-metrics plot CLI command.

    Args:
        argv: Optional list of command-line arguments.

    Returns:
        Exit status code.

    """
    parsed_args = args(argv)
    path_data = load_path_spline_points(parsed_args.path_file)
    metrics_data = calculate_motion_metrics(path_data)
    metrics_summary = summarize_motion_metrics(metrics_data)
    violations = evaluate_limits(metrics_summary, parsed_args)
    print_motion_summary(metrics_summary, violations)
    plot_motion_metrics(metrics_data, parsed_args.path_file, parsed_args.output)
    return 0
