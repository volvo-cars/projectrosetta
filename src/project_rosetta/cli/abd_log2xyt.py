import sys
from pathlib import Path

from project_rosetta.trajectory_conversions.abd_log_trajectory import write_abd_log_xyt_files


def main(argv: list[str] | None = None) -> int:
    """
    Convert one ABD log to .xyt files.

    Returns:
        Exit status code.

    """
    log_path, output_dir = [Path(arg) for arg in (sys.argv[1:] if argv is None else argv)]
    for path in write_abd_log_xyt_files(log_path, output_dir):
        print(path)
    return 0
