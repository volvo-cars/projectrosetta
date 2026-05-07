import shutil
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from typing import Dict

from project_rosetta.utils.csv2xyt import run_csv2xyt
from project_rosetta.utils.run_dat2csv import run_dat2csv
from project_rosetta.utils.run_esmini import run_esmini, setup_run_config
from project_rosetta.utils.utils import LOGS_DIR
from project_rosetta.utils.xosc_from_py import py2xosc

XOSC_DIR_NAME = "xosc"
XODR_DIR_NAME = "xodr"
CATALOGS_DIR_NAME = "catalogs"


class ScenarioBatch:
    """Takes a scenariopath or list of scenariopaths and creates a ScenarioRunner for each"""

    def __init__(self, scenario_paths: Path | list[Path] | str | list[str], log_path: str = None):
        self.scenario_runners = []

        if isinstance(scenario_paths, (str, Path)):
            scenario_paths = [str(scenario_paths)]
        self.scenario_path_list = self._scenario_list_handler(scenario_paths)

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
            self.original_scenario_file_path = scenario_path
            scenario_name = scenario_path.stem
            scenario_log_folder = Path(self._log_folder, scenario_name)
            scenario_log_folder.mkdir(parents=True, exist_ok=True)
            new_scenario_path = self.copy_to(scenario_log_folder, scenario_path)
            new_scenario_paths.append(new_scenario_path)
        self.scenario_path_list = new_scenario_paths

    def _scenario_list_handler(self, scenario_paths: list[str]):
        valid_paths = []
        for path in scenario_paths:
            if path.endswith(".py"):
                valid_paths.extend(py2xosc(path))
            elif path.endswith(".xosc"):
                valid_paths.append(Path(path))
            else:
                raise ValueError(f"Invalid scenario path: {path}. Must be a .py or .xosc file.")
        return valid_paths

    def get_xodr_file_path_from_xosc_file_path(self, xosc_file_path) -> Path | None:
        """
        get_xodr_file_path_from_xosc_file_path

        Args:
            xosc_file_path (Path): Path to the OpenSCENARIO file.

        Returns:
            Path to the OpenDRIVE file referenced in the OpenSCENARIO file, or None

        """
        with xosc_file_path.open("r", encoding="utf-8") as f:
            xosc_element_root = ET.parse(f)
        road_network_element = xosc_element_root.find("RoadNetwork")
        if road_network_element is None:
            print(f"Element 'RoadNetwork' was not found in {xosc_file_path}")
            return None
        if len(road_network_element) == 0:
            print(f"Element 'RoadNetwork' does not contain any logic file in {xosc_file_path}")
            return None
        logic_file_element = road_network_element[0]
        return Path(logic_file_element.attrib["filepath"])

    def _get_catalog_locations_dict(self) -> Dict:
        """
        _get_catalog_locations_dict

        Returns:
            A dictionary mapping catalog names to their paths as specified in the OpenSCENARIO file.

        """
        with self.xosc_file_path.open("r", encoding="utf-8") as f:
            xosc_element_root = ET.parse(f)
        catalog_locations_element = xosc_element_root.find("CatalogLocations")
        if catalog_locations_element is None:
            print(f"Element 'CatalogLocations' was not found in {self.xosc_file_path}")
            return None
        catalog_locations_dict = {}
        for catalog_element in catalog_locations_element:
            directory_element = catalog_element[0]
            catalog_locations_dict[catalog_element.tag] = directory_element.attrib["path"]

        return catalog_locations_dict

    def _generate_scenario_dir_tree(self, dest_dir_path: Path):
        """
        _generate_scenario_dir_tree
        Args:
            dest_dir_path (Path): The destination directory where the scenario directory
            tree will be created.

        Returns:
            Tuple[Path, Path]: The paths to the created XOSC and XODR directories.

        """
        xosc_dir_path = dest_dir_path / XOSC_DIR_NAME
        xosc_dir_path.mkdir()
        xodr_dir_path = dest_dir_path / XODR_DIR_NAME
        xodr_dir_path.mkdir()
        return xosc_dir_path, xodr_dir_path

    def copy_to(self, dest_dir_path: Path, xosc_file_path: Path):
        """
        copy_to
        Copies the scenario file to the destination directory, along with the referenced OpenDRIVE
        file and catalogs.

        Args:
            dest_dir_path (Path): The destination directory where the scenario file and its
            references will be copied.
            xosc_file_path (Path): The path to the OpenSCENARIO file to be copied.

        Raises:
            FileNotFoundError: If the destination directory does not exist.

        Returns:
            Path: The path to the copied OpenSCENARIO file.

        """
        (dest_xosc_dir_path, dest_xodr_dir_path) = self._generate_scenario_dir_tree(dest_dir_path)
        xodr_file_path = self.get_xodr_file_path_from_xosc_file_path(xosc_file_path)
        if xodr_file_path is None:
            raise FileNotFoundError(f"Could not find OpenDRIVE reference in {xosc_file_path}")
        if not xodr_file_path.is_absolute():
            xodr_file_path = (xosc_file_path.parent / xodr_file_path).resolve()
        self.xosc_file_path = Path(shutil.copy2(xosc_file_path, dest_xosc_dir_path))
        self.xodr_file_path = Path(shutil.copy2(xodr_file_path, dest_xodr_dir_path))
        self._adjust_references()
        return self.xosc_file_path

    def _adjust_references(self):
        """
        Copies and adjust scenario references.

        All scenario references are interpreted as either absolute references,
        relative references to the python scenario, or to the generated scenario.
        This method resolves those references, copies the files and folders so that
        they are placed where the generated xosc is located, and then updates
        the references to be relative to the xosc.
        """
        catalog_locations_dict = self._get_catalog_locations_dict()

        self._adjust_catalogs(catalog_locations_dict)
        self._write_xosc_with_updated_catalogs_and_xodr_reference(catalog_locations_dict)

    def _adjust_catalogs(self, catalogs_path_dict: Dict) -> dict:
        """
        Copies catalogs and adjust references.

        The catalogs references are resolved by looking for the paths in the following order:
        1. Use absolute path. If relative, then;
        2. Look for catalogs relative to python scenario

        Args:
            catalogs_path_dict (Dict): contains xosc catalogs' paths

        Returns:
            dict: Updated catalogs_path_dict with the new paths relative to the generated xosc file.

        """
        dest_catalogs_dir_path = self.xosc_file_path.parent / CATALOGS_DIR_NAME
        dest_catalogs_dir_path.mkdir()

        for sub_catalog_name, src_sub_catalog_rel_dir_path_str in catalogs_path_dict.items():
            src_sub_catalog_rel_dir_path = Path(src_sub_catalog_rel_dir_path_str)

            src_sub_catalog_dir_path = None
            if src_sub_catalog_rel_dir_path.is_absolute():
                src_sub_catalog_dir_path = src_sub_catalog_rel_dir_path
            else:
                src_sub_catalog_rel_py_scenario_dir_path = (
                    self.original_scenario_file_path.parent / src_sub_catalog_rel_dir_path_str
                ).resolve()
                if src_sub_catalog_rel_py_scenario_dir_path.exists():
                    src_sub_catalog_dir_path = src_sub_catalog_rel_py_scenario_dir_path
            if src_sub_catalog_dir_path is None:
                not_exist_file_path_list_str = "\n".join(
                    str(path)
                    for path in [
                        src_sub_catalog_rel_dir_path,
                        src_sub_catalog_rel_py_scenario_dir_path,
                    ]
                )
                print(
                    f"Could not resolve '{src_sub_catalog_rel_dir_path}'!\n"
                    + f"{not_exist_file_path_list_str} does NOT exist!"
                )
                print("Faulty scenario file: %s", self.xosc_file_path)
                return None

            sub_catalog_dir_name = src_sub_catalog_dir_path.name
            dest_sub_catalog_dir_path = Path(
                shutil.copytree(
                    src_sub_catalog_dir_path, dest_catalogs_dir_path / sub_catalog_dir_name
                )
            )
            catalogs_path_dict[sub_catalog_name] = str(
                dest_sub_catalog_dir_path.relative_to(self.xosc_file_path.parent)
            )
        return catalogs_path_dict

    def _write_xosc_with_updated_catalogs_and_xodr_reference(
        self, catalogs_locations_dict: Dict
    ) -> None:
        """_write_xosc_with_updated_catalogs_and_xodr_reference"""
        with self.xosc_file_path.open("r", encoding="utf-8") as f:
            xosc_element_root = ET.parse(f)
        catalog_locations_element = xosc_element_root.find("CatalogLocations")
        for catalog_element in catalog_locations_element:
            directory_element = catalog_element[0]
            directory_element.attrib["path"] = catalogs_locations_dict[catalog_element.tag]
        road_network_element = xosc_element_root.find("RoadNetwork")
        logic_file_element = road_network_element[0]
        logic_file_element.attrib["filepath"] = str(Path("../xodr") / self.xodr_file_path.name)
        xosc_element_root.write(self.xosc_file_path)


class ScenarioRunner:
    """Class to manage the execution of a scenario and conversion to XYT format."""

    def __init__(self, scenario_path: Path):
        self.scenario_path = scenario_path
        self.scenario_name = scenario_path.stem
        self.log_folder = self.scenario_path.parent.parent

        print(f"Initialized ScenarioRunner for: {self.scenario_path}")
        print(f"Scenario name: {self.scenario_name}")
        print(f"Log folder: {self.log_folder}")

    def setup(self) -> None:
        """Set up the scenario runner by preparing necessary files."""
        self.dat_file = Path(self.log_folder) / f"{self.scenario_name}.dat"
        self.csv_file = Path(self.log_folder) / f"{self.scenario_name}.csv"
        self.xyt_dir = Path(self.log_folder) / f"{self.scenario_name}_xyt"

        self.esmini_run_config = setup_run_config(
            self.scenario_path, self.log_folder / self.scenario_name, window=False
        )
        self.esmini_run_config = copy_file_to_folder(self.esmini_run_config, self.log_folder)

        print(f"Scenario runner setup complete for: {self.scenario_path}")

    def run(self) -> None:
        """Run the scenario through esmini, convert the output to CSV, and then to XYT format."""
        print(f"Running esmini with config: {self.esmini_run_config}")
        run_esmini(self.esmini_run_config)

        run_dat2csv(self.dat_file, self.csv_file)

        run_csv2xyt(self.csv_file, self.xyt_dir, columns=["x", "y", "time"])


def copy_file_to_folder(file_path: Path, folder: Path) -> None:
    """
    Copy a file to a specified folder.

    Args:
        file_path: The path to the file to be copied.
        folder: The destination folder.

    Returns:
        The path to the copied file.

    Raises:
        FileNotFoundError: If the source file does not exist.
        NotADirectoryError: If the destination folder does not exist.

    """
    if not file_path.is_file():
        raise FileNotFoundError(f"{file_path} does not exist or is not a file.")
    if not folder.is_dir():
        raise NotADirectoryError(f"{folder} does not exist or is not a directory.")
    destination = folder / file_path.name
    shutil.copy2(file_path, destination)
    return destination
