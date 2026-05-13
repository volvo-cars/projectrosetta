from datetime import datetime
from pathlib import Path

from project_rosetta.utils.csv2xyt import run_csv2xyt
from project_rosetta.utils.run_dat2csv import run_dat2csv
from project_rosetta.utils.run_esmini import run_esmini, setup_run_config
from project_rosetta.utils.scenario_files import (
    copy_file_to_folder,
    copy_to,
    scenario_list_handler,
)
from project_rosetta.utils.utils import LOGS_DIR


class ScenarioBatch:
    """Takes a scenariopath or list of scenariopaths and creates a ScenarioRunner for each"""

    def __init__(self, scenario_paths: Path | list[Path] | str | list[str], log_path: str = None):
        if isinstance(scenario_paths, (str, Path)):
            scenario_paths = [str(scenario_paths)]
        self.scenario_path_list = scenario_list_handler(scenario_paths)

        if log_path is None:
            self._log_folder = Path(LOGS_DIR, datetime.now().strftime("%Y%m%d_%H%M%S"))
        else:
            self._log_folder = Path(LOGS_DIR, log_path)

        self._setup_log_folder()

        self.runners = [ScenarioRunner(p) for p in self.scenario_path_list]

    def run_all(self) -> None:
        """Run all scenarios in the batch."""
        for runner in self.runners:
            runner.setup()
            runner.run()

    def _setup_log_folder(self):
        self._log_folder.mkdir(parents=True, exist_ok=True)
        new_scenario_paths = []
        for full_scenario_path in self.scenario_path_list:
            scenario_path = full_scenario_path.resolve()
            original_scenario_file_path = scenario_path
            scenario_name = scenario_path.stem
            scenario_log_folder = Path(self._log_folder, scenario_name)
            scenario_log_folder.mkdir(parents=True, exist_ok=True)
            new_scenario_path = copy_to(
                scenario_log_folder, original_scenario_file_path, scenario_path
            )
            new_scenario_paths.append(new_scenario_path)
        self.scenario_path_list = new_scenario_paths


class ScenarioRunner:
    """Class to manage the execution of a scenario and conversion to XYT format."""

    def __init__(self, scenario_path: Path):
        self.scenario_path = scenario_path
        self.scenario_name = scenario_path.stem
        self.log_folder = self.scenario_path.parent.parent

        # print(f"Initialized ScenarioRunner for: {self.scenario_path}")
        # print(f"Scenario name: {self.scenario_name}")
        # print(f"Log folder: {self.log_folder}")

    def setup(self) -> None:
        """Set up the scenario runner by preparing necessary files."""
        self.dat_file = Path(self.log_folder) / f"{self.scenario_name}.dat"
        self.csv_file = Path(self.log_folder) / f"{self.scenario_name}.csv"
        self.xyt_dir = Path(self.log_folder) / f"{self.scenario_name}_xyt"
        self.esmini_log_file = Path(self.log_folder) / "esmini.log"

        self.esmini_run_config = setup_run_config(
            self.scenario_path, self.log_folder / self.scenario_name, window=False
        )
        self.esmini_run_config = copy_file_to_folder(self.esmini_run_config, self.log_folder)

        # print(f"Scenario runner setup complete for: {self.scenario_path}")

    def run(self) -> None:
        """
        Run the scenario through esmini, convert the output to CSV, and then to XYT format.

        Raises:
            RuntimeError: If esmini exits with a non-zero status code.

        """
        # print(f"Running esmini with config: {self.esmini_run_config}")
        result = run_esmini(self.esmini_run_config, log_file=self.esmini_log_file)
        if result.returncode != 0:
            raise RuntimeError(
                f"esmini failed with exit code {result.returncode}. See log: {self.esmini_log_file}"
            )
        run_dat2csv(self.dat_file, self.csv_file)

        run_csv2xyt(self.csv_file, self.xyt_dir, columns=["x", "y", "time"])
