from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from project_rosetta.utils.scenario_runner import ScenarioBatch, ScenarioRunner


@patch("project_rosetta.utils.scenario_runner.copy_file_to_folder")
@patch("project_rosetta.utils.scenario_runner.setup_run_config")
def test_scenario_runner_setup(
    mock_setup_run_config,
    mock_copy_file,
):
    """
    Test that the ScenarioRunner setup method correctly sets up the paths and
    calls the necessary functions.
    """
    scenario_path = Path("/tmp/test_scenario.xosc")

    mock_setup_run_config.return_value = Path("config.yml")
    mock_copy_file.return_value = Path("/logs/config.yml")

    runner = ScenarioRunner(scenario_path)

    runner.setup()

    assert runner.dat_file == runner.log_folder / "test_scenario.dat"
    assert runner.csv_file == runner.log_folder / "test_scenario.csv"
    assert runner.xyt_dir == runner.log_folder / "test_scenario_xyt"

    mock_setup_run_config.assert_called_once()
    mock_copy_file.assert_called_once()


@patch("project_rosetta.utils.scenario_runner.run_csv2xyt")
@patch("project_rosetta.utils.scenario_runner.run_dat2csv")
@patch("project_rosetta.utils.scenario_runner.run_esmini")
def test_scenario_runner_run(
    mock_run_esmini,
    mock_run_dat2csv,
    mock_run_csv2xyt,
):
    """Test that the ScenarioRunner run method correctly calls the necessary functions."""
    runner = ScenarioRunner(Path("/tmp/test.xosc"))

    runner.dat_file = Path("/tmp/test.dat")
    runner.csv_file = Path("/tmp/test.csv")
    runner.xyt_dir = Path("/tmp/test_xyt")
    runner.esmini_run_config = Path("/tmp/config.yml")
    runner.esmini_log_file = Path("/tmp/esmini.log")
    mock_run_esmini.return_value = MagicMock(returncode=0)

    runner.run()

    mock_run_esmini.assert_called_once_with(
        runner.esmini_run_config,
        log_file=runner.esmini_log_file,
    )

    mock_run_dat2csv.assert_called_once_with(
        runner.dat_file,
        runner.csv_file,
    )

    mock_run_csv2xyt.assert_called_once_with(
        runner.csv_file,
        runner.xyt_dir,
        columns=["x", "y", "time"],
    )


@patch("project_rosetta.utils.scenario_runner.run_csv2xyt")
@patch("project_rosetta.utils.scenario_runner.run_dat2csv")
@patch("project_rosetta.utils.scenario_runner.run_esmini")
def test_scenario_runner_run_raises_when_esmini_fails(
    mock_run_esmini,
    mock_run_dat2csv,
    mock_run_csv2xyt,
):
    """Test that the ScenarioRunner stops the chain when esmini fails."""
    runner = ScenarioRunner(Path("/tmp/test.xosc"))

    runner.dat_file = Path("/tmp/test.dat")
    runner.csv_file = Path("/tmp/test.csv")
    runner.xyt_dir = Path("/tmp/test_xyt")
    runner.esmini_run_config = Path("/tmp/config.yml")
    runner.esmini_log_file = Path("/tmp/esmini.log")
    mock_run_esmini.return_value = MagicMock(returncode=3)

    with pytest.raises(RuntimeError, match="exit code 3") as exc_info:
        runner.run()

    assert str(runner.esmini_log_file) in str(exc_info.value)

    mock_run_dat2csv.assert_not_called()
    mock_run_csv2xyt.assert_not_called()


@patch("project_rosetta.utils.scenario_runner.ScenarioRunner")
@patch("project_rosetta.utils.scenario_runner.copy_to")
@patch("project_rosetta.utils.scenario_runner.scenario_list_handler")
def test_scenario_batch_initialization(
    mock_handler,
    mock_copy_to,
    mock_runner,
):
    """Test that the ScenarioBatch initialization correctly sets up the runners."""
    mock_handler.return_value = [Path("/tmp/test.xosc")]

    mock_copy_to.return_value = Path("/logs/test.xosc")

    batch = ScenarioBatch(["test.xosc"], log_path="logs")

    assert len(batch.runners) == 1

    mock_handler.assert_called_once()
    mock_copy_to.assert_called_once()
    mock_runner.assert_called_once()


def test_run_all_calls_setup_and_run():
    """
    Test that the run_all method of ScenarioBatch calls setup and run on
    each ScenarioRunner.
    """
    batch = ScenarioBatch.__new__(ScenarioBatch)

    runner = MagicMock()

    batch.runners = [runner]

    batch.run_all()

    runner.setup.assert_called_once()
    runner.run.assert_called_once()
