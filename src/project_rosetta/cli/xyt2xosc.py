import sys
from pathlib import Path

from project_rosetta.trajectory_conversions.xyt_to_xosc import xyt_files_to_xosc


def main(argv: list[str] | None = None) -> int:
    """
    Convert positional .xyt inputs to one output .xosc.

    Returns:
        Exit status code.

    """
    paths = [Path(arg) for arg in (sys.argv[1:] if argv is None else argv)]
    xyt_paths = paths if len(paths) == 1 else paths[:-1]
    output_path = paths[0].with_suffix(".xosc") if len(paths) == 1 else paths[-1]
    print(xyt_files_to_xosc(xyt_paths, output_path))
    return 0
