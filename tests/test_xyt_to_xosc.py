import xml.etree.ElementTree as ET

import pandas as pd

from project_rosetta.cli.xyt2xosc import main
from project_rosetta.trajectory_conversions.xyt_to_xosc import xyt_files_to_xosc


def test_xyt_files_to_xosc_writes_trajectory_replay(tmp_path):
    """Test a minimal XYT to OpenSCENARIO replay."""
    xyt_path = tmp_path / "subject.xyt"
    output_path = tmp_path / "replay.xosc"
    pd.DataFrame([(0.0, 0.0, 0.0), (1.0, 0.0, 1.0)]).to_csv(
        xyt_path,
        index=False,
        header=False,
        sep=" ",
        decimal=",",
    )

    xyt_files_to_xosc([xyt_path], output_path)

    root = ET.parse(output_path).getroot()
    assert root.find("RoadNetwork/LogicFile") is None
    assert root.find("Entities/ScenarioObject").attrib["name"] == "subject"
    assert root.find(".//TimeReference/Timing").attrib["domainAbsoluteRelative"] == "absolute"
    vertices = root.findall(".//Polyline/Vertex")
    assert [vertex.attrib["time"] for vertex in vertices] == ["0.0", "1.0"]
    assert vertices[-1].find("Position/WorldPosition").attrib["x"] == "1.0"


def test_xyt2xosc_single_argument_defaults_output_path(tmp_path):
    """Test the exact one-file CLI path."""
    xyt_path = tmp_path / "subject.xyt"
    pd.DataFrame([(0.0, 0.0, 0.0), (1.0, 0.0, 1.0)]).to_csv(
        xyt_path,
        index=False,
        header=False,
        sep=" ",
        decimal=",",
    )

    assert main([str(xyt_path)]) == 0
    assert (tmp_path / "subject.xosc").exists()


def test_xyt_files_to_xosc_samples_car_models_with_replacement(tmp_path):
    """Test that car model sampling wraps when there are more actors than models."""
    output_path = tmp_path / "replay.xosc"
    xyt_paths = [tmp_path / f"actor_{index}.xyt" for index in range(5)]
    for path in xyt_paths:
        pd.DataFrame([(0.0, 0.0, 0.0), (1.0, 0.0, 1.0)]).to_csv(
            path,
            index=False,
            header=False,
            sep=" ",
            decimal=",",
        )

    xyt_files_to_xosc(xyt_paths, output_path)

    root = ET.parse(output_path).getroot()
    assert [vehicle.attrib["model3d"] for vehicle in root.findall(".//Vehicle")] == [
        "car_white.osgb",
        "car_blue.osgb",
        "car_red.osgb",
        "car_yellow.osgb",
        "car_white.osgb",
    ]
