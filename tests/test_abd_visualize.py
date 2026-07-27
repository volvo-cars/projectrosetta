import xml.etree.ElementTree as ET
from unittest.mock import MagicMock, patch

from project_rosetta.cli.abd_visualize import main


@patch("project_rosetta.cli.abd_visualize.run_esmini")
def test_abd_visualize_runs_esmini_with_window(mock_run, tmp_path):
    """Convert an ABD log and launch esmini."""
    log_path = tmp_path / "abd.txt"
    log_path.write_text(
        "\n".join(
            [
                "Anthony Best Dynamics Ltd",
                "Points=2",
                (
                    "System Time\tActual X (front axle)\tActual Y (front axle)"
                    "\tActual X (rear axle)\tActual Y (rear axle)"
                    "\tObject 1 actual X (front axle)\tObject 1 actual Y (front axle)"
                    "\tObject 1 yaw"
                ),
                "s\tm\tm\tm\tm\tm\tm\tdeg",
                "10,0\t3,0\t0,0\t0,0\t0,0\t5,0\t6,0\t0,0",
                "11,0\t5,0\t0,0\t2,0\t0,0\t7,0\t8,0\t0,0",
            ]
        ),
        encoding="ISO-8859-1",
    )
    vehicle_path = tmp_path / "Vehicle0062.txt"
    vehicle_path.write_text(
        "\n".join(
            [
                "Vehicle Dimensions",
                "==================",
                "Front Overhang\t1",
                "Wheelbase\t3",
                "Vehicle Length\t5",
                "Vehicle Width\t2",
                "Front Axle To Reference Point\t-3",
                "",
                "Vehicle Dimensions (Other Vehicle)",
                "==================================",
                "Front Overhang\t1",
                "Wheelbase\t3",
                "Vehicle Length\t6",
                "Vehicle Width\t2",
                "Front Axle To Reference Point\t-3",
            ]
        )
    )
    config_contents = []
    scenarios = []

    def run_esmini(config_path):
        config_contents.append(config_path.read_text())
        scenario_path = config_path.parent / "abd_replay.xosc"
        scenarios.append(ET.parse(scenario_path).getroot())
        return MagicMock(returncode=0)

    mock_run.side_effect = run_esmini

    assert main([str(log_path), "--vehicle-info", str(vehicle_path)]) == 0
    assert "window: 60 60 800 400" in config_contents[0]
    object_vehicle = scenarios[0].find("./Entities/ScenarioObject[@name='object_1']/Vehicle")
    dimensions = object_vehicle.find("BoundingBox/Dimensions")
    assert dimensions.attrib["length"] == "6.0"
    assert dimensions.attrib["width"] == "2.0"
