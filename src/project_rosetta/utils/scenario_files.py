import logging
import shutil
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict

from project_rosetta.utils.xosc_from_py import py2xosc

logger = logging.getLogger(__name__)

XOSC_DIR_NAME = "xosc"
XODR_DIR_NAME = "xodr"
CATALOGS_DIR_NAME = "catalogs"


def copy_file_to_folder(file_path: Path, folder: Path) -> Path:
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


def scenario_list_handler(scenario_paths: list[str | Path]):
    """
    scenario_list_handler
    Handles a list of scenario paths, which can be either OpenSCENARIO files or Python files
    that generate OpenSCENARIO files. It validates the paths and generates OpenSCENARIO files
    from Python files as needed.

    Args:
        scenario_paths (list[str | Path]): A list of paths to scenario files,
        which can be either .xosc or .py files.

    Returns:
        list[Path]: A list of paths to the valid OpenSCENARIO files.

    Raises:
        ValueError: If any of the provided paths are invalid (not .xosc or .py files).

    """
    valid_paths = []

    for scenario_path in scenario_paths:
        path = Path(scenario_path)

        if path.suffix == ".py":
            valid_paths.extend(py2xosc(path))
        elif path.suffix == ".xosc":
            valid_paths.append(path)
        else:
            raise ValueError(f"Invalid scenario path: {path}")
    return valid_paths


def copy_to(dest_dir_path: Path, original_scenario_file_path: Path, xosc_file_path: Path):
    """
    copy_to
    Copies the scenario file to the destination directory, along with the referenced OpenDRIVE
    file and catalogs.

    Args:
        dest_dir_path (Path): The destination directory where the scenario file and its
        references will be copied.
        original_scenario_file_path (Path): The path to the original scenario file, used to
        resolve relative references.
        xosc_file_path (Path): The path to the OpenSCENARIO file to be copied.

    Raises:
        FileNotFoundError: If the destination directory does not exist.

    Returns:
        Path: The path to the copied OpenSCENARIO file.

    """
    (dest_xosc_dir_path, dest_xodr_dir_path) = generate_scenario_dir_tree(dest_dir_path)
    xodr_file_path = get_xodr_file_path_from_xosc_file_path(xosc_file_path)
    if xodr_file_path is None:
        raise FileNotFoundError(f"Could not find OpenDRIVE reference in {xosc_file_path}")
    if not xodr_file_path.is_absolute():
        xodr_file_path = (xosc_file_path.parent / xodr_file_path).resolve()
    xosc_file_path = Path(shutil.copy2(xosc_file_path, dest_xosc_dir_path))
    xodr_file_path = Path(shutil.copy2(xodr_file_path, dest_xodr_dir_path))
    adjust_references(original_scenario_file_path, xosc_file_path, xodr_file_path)
    return xosc_file_path


def generate_scenario_dir_tree(dest_dir_path: Path):
    """
    generate_scenario_dir_tree
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


def get_xodr_file_path_from_xosc_file_path(xosc_file_path) -> Path | None:
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
        logger.error(f"Element 'RoadNetwork' was not found in {xosc_file_path}")
        return None
    if len(road_network_element) == 0:
        logger.error(f"Element 'RoadNetwork' does not contain any logic file in {xosc_file_path}")
        return None
    logic_file_element = road_network_element[0]
    return Path(logic_file_element.attrib["filepath"])


def adjust_references(
    original_scenario_file_path, xosc_file_path: Path, xodr_file_path: Path
) -> None:
    """
    Copies and adjust scenario references.

    All scenario references are interpreted as either absolute references,
    relative references to the python scenario, or to the generated scenario.
    This method resolves those references, copies the files and folders so that
    they are placed where the generated xosc is located, and then updates
    the references to be relative to the xosc.

    Args:
    original_scenario_file_path (Path): The path to the original Python scenario file,
    used to resolve relative references.
    xosc_file_path (Path): The path to the generated OpenSCENARIO file.
    xodr_file_path (Path): The path to the OpenDRIVE file referenced in the OpenSCENARIO file.

    Raises:
        ValueError: If the catalogs cannot be resolved or adjusted.

    """
    catalog_locations_dict = get_catalog_locations_dict(xosc_file_path)

    if catalog_locations_dict is None:
        raise ValueError(f"No CatalogLocations in {xosc_file_path}")

    catalog_locations_dict = adjust_catalogs(
        original_scenario_file_path, xosc_file_path, catalog_locations_dict
    )

    if catalog_locations_dict is None:
        raise ValueError("Failed to adjust catalogs")

    write_xosc_with_updated_catalogs_and_xodr_reference(
        xosc_file_path, xodr_file_path, catalog_locations_dict
    )


def get_catalog_locations_dict(xosc_file_path) -> Dict:
    """
    get_catalog_locations_dict

    Returns:
        A dictionary mapping catalog names to their paths as specified in the OpenSCENARIO file.

    """
    with xosc_file_path.open("r", encoding="utf-8") as f:
        xosc_element_root = ET.parse(f)
    catalog_locations_element = xosc_element_root.find("CatalogLocations")
    if catalog_locations_element is None:
        logger.error(f"Element 'CatalogLocations' was not found in {xosc_file_path}")
        return None
    catalog_locations_dict = {}
    for catalog_element in catalog_locations_element:
        directory_element = catalog_element[0]
        catalog_locations_dict[catalog_element.tag] = directory_element.attrib["path"]

    return catalog_locations_dict


def adjust_catalogs(original_scenario_file_path, xosc_file_path, catalogs_path_dict: Dict) -> dict:
    """
    Copies catalogs and adjust references.

    The catalogs references are resolved by looking for the paths in the following order:
    1. Use absolute path. If relative, then;
    2. Look for catalogs relative to python scenario

    Args:
        original_scenario_file_path (Path): Path to the original Python scenario file.
        xosc_file_path (Path): Path to the generated OpenSCENARIO file.
        catalogs_path_dict (Dict): contains xosc catalogs' paths

    Returns:
        dict: Updated catalogs_path_dict with the new paths relative to the generated xosc file.

    """
    dest_catalogs_dir_path = xosc_file_path.parent / CATALOGS_DIR_NAME
    dest_catalogs_dir_path.mkdir(exist_ok=True)

    updated = {}

    for sub_catalog_name, src_sub_catalog_rel_dir_path_str in catalogs_path_dict.items():
        src_sub_catalog_rel_dir_path = Path(src_sub_catalog_rel_dir_path_str)

        src_sub_catalog_dir_path = None
        if src_sub_catalog_rel_dir_path.is_absolute():
            src_sub_catalog_dir_path = src_sub_catalog_rel_dir_path
        else:
            src_sub_catalog_rel_py_scenario_dir_path = (
                original_scenario_file_path.parent / src_sub_catalog_rel_dir_path_str
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
            logger.error(
                f"Could not resolve '{src_sub_catalog_rel_dir_path}'!\n"
                + f"{not_exist_file_path_list_str} does NOT exist!"
            )
            logger.error("Faulty scenario file: %s", xosc_file_path)
            return None

        sub_catalog_dir_name = src_sub_catalog_dir_path.name
        dest_sub_catalog_dir_path = Path(
            shutil.copytree(src_sub_catalog_dir_path, dest_catalogs_dir_path / sub_catalog_dir_name)
        )
        updated[sub_catalog_name] = str(
            dest_sub_catalog_dir_path.relative_to(xosc_file_path.parent)
        )
    return updated


def write_xosc_with_updated_catalogs_and_xodr_reference(
    xosc_file_path: Path, xodr_file_path: Path, catalogs_locations_dict: Dict
) -> None:
    """_write_xosc_with_updated_catalogs_and_xodr_reference"""
    with xosc_file_path.open("r", encoding="utf-8") as f:
        xosc_element_root = ET.parse(f)
    catalog_locations_element = xosc_element_root.find("CatalogLocations")
    for catalog_element in catalog_locations_element:
        directory_element = catalog_element[0]
        directory_element.attrib["path"] = catalogs_locations_dict[catalog_element.tag]
    road_network_element = xosc_element_root.find("RoadNetwork")
    logic_file_element = road_network_element[0]
    logic_file_element.attrib["filepath"] = str(Path("../xodr") / xodr_file_path.name)
    xosc_element_root.write(xosc_file_path)
