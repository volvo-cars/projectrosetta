import argparse
from pathlib import Path

from project_rosetta.utils.scenario_runner import ScenarioBatch

ALLOWED_SCENARIO_SUFFIXES = {".py", ".xosc"}


def scenario_path_arg(value: str) -> Path:
    """
    Validate and normalize supported scenario file paths.

    Args:
        value: The scenario file path as a string.

    Returns:
        The validated and normalized scenario file path as a Path object.

    Raises:
        argparse.ArgumentTypeError: If the file extension is not supported.

    """
    path = Path(value)
    suffix = path.suffix.lower()
    if suffix not in ALLOWED_SCENARIO_SUFFIXES:
        allowed = ", ".join(sorted(ALLOWED_SCENARIO_SUFFIXES))
        raise argparse.ArgumentTypeError(
            f"Unsupported scenario file extension '{path.suffix}'. Expected one of: {allowed}."
        )
    return path


def args(argv: list[str] | None = None) -> argparse.Namespace:
    """
    Parse CLI arguments for scenario-to-XYT conversion.

    Args:
        argv: Optional list of command-line arguments. If None, defaults to sys.argv.

    Returns:
        An argparse.Namespace object containing the parsed arguments.

    """
    parser = argparse.ArgumentParser(description="Convert a scenario into XYT files.")
    parser.add_argument(
        "scenario_path",
        type=scenario_path_arg,
        help="Path to a scenario file (.py or .xosc).",
    )
    parser.add_argument(
        "--window",
        default=False,
        action="store_true",
        help="Run esmini with viewer.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """
    Run the scenario2xyt CLI command.

    Returns:
        Exit status code.

    """
    parsed_args = args(argv)
    scenario_path = parsed_args.scenario_path

    scenario_batch = ScenarioBatch(scenario_path)

    scenario_batch.run_all()

    return 0
