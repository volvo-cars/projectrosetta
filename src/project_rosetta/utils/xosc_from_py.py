import importlib.util
import sys
from pathlib import Path

from project_rosetta.utils.utils import BASE_DIR


def py2xosc(py_file: str | Path) -> list[Path]:
    """
    py2xosc
    Converts a Python scenario definition file into OpenSCENARIO files.
    The Python file must define a class named `Scenario` with a method `generate(self, path)`
    that returns a tuple of (scenarios, roads), where `scenarios` is a list of OpenSCENARIO file

    Args:
        py_file (str | Path): The path to the Python file containing the scenario definition.

    Returns:
        list[Path]: A list of paths to the generated OpenSCENARIO files.

    Raises:
        ImportError: If the module cannot be loaded from the specified file.

    Raises:
        ImportError: If the module cannot be loaded from the specified file.

    """
    py_file = Path(py_file)
    module_name = py_file.stem  # ✅ important fix

    spec = importlib.util.spec_from_file_location(module_name, py_file)
    module = importlib.util.module_from_spec(spec)

    sys.modules[module_name] = module  # must match actual module name

    if spec.loader is None:
        raise ImportError(f"Could not load module from {py_file}")

    spec.loader.exec_module(module)

    Scenario = getattr(module, "Scenario")

    obj = Scenario()
    obj.naming = "numerical"

    scenarios, _ = obj.generate(py_file.parent)
    scenarios = [Path(BASE_DIR, scenario) for scenario in scenarios]

    return scenarios
