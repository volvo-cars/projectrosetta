import argparse
from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory

import numpy as np
import pandas as pd
from scenariogeneration import xosc

from project_rosetta.trajectory_conversions.abd_log_trajectory import read_abd_log
from project_rosetta.trajectory_conversions.xyt_to_xosc import (
    CAR_MODELS,
    _maneuver_group,
    _position,
    _time_trigger,
)
from project_rosetta.utils.run_esmini import run_esmini, setup_run_config


@dataclass
class _Vehicle:
    length: float = 4.5
    width: float = 1.8
    wheelbase: float = 3.1
    front_overhang: float = 0.65
    front_ref: float = -3.1


def main(argv: list[str] | None = None) -> int:
    """
    Replay an ABD log in the esmini viewer.

    Returns:
        Exit status code.

    """
    parser = argparse.ArgumentParser(description="Replay an ABD log in esmini.")
    parser.add_argument("abd_log", type=Path)
    parser.add_argument("--vehicle-info", type=Path)
    args = parser.parse_args(argv)

    vehicles = (
        _vehicles(args.vehicle_info) if args.vehicle_info else _vehicles_from_log(args.abd_log)
    )
    frames = _frames(args.abd_log, vehicles)

    with TemporaryDirectory() as tmp:
        work_dir = Path(tmp)
        scenario_path = work_dir / "abd_replay.xosc"
        _write_xosc(frames, vehicles, scenario_path)
        config_path = setup_run_config(
            scenario_path,
            work_dir / "abd_replay",
            window=True,
            output_path=work_dir / "esmini.yml",
        )
        result = run_esmini(config_path)
    return result.returncode


def _frames(log_path: Path, vehicles: dict[str, _Vehicle]) -> dict[str, pd.DataFrame]:
    data = read_abd_log(log_path)
    time = data["System Time"] - data["System Time"].iloc[0]
    subject_yaw = np.arctan2(
        data["Actual Y (front axle)"] - data["Actual Y (rear axle)"],
        data["Actual X (front axle)"] - data["Actual X (rear axle)"],
    )
    frames = {
        "subject": _frame(
            data["Actual X (front axle)"],
            data["Actual Y (front axle)"],
            time,
            subject_yaw,
            vehicles["subject"],
        )
    }

    for column in data.columns:
        if not column.startswith("Object ") or not column.endswith(" actual X (front axle)"):
            continue
        object_id = column.removeprefix("Object ").removesuffix(" actual X (front axle)")
        frames[f"object_{object_id}"] = _frame(
            data[column],
            data[f"Object {object_id} actual Y (front axle)"],
            time,
            np.deg2rad(data[f"Object {object_id} yaw"]),
            vehicles.get("object", vehicles["subject"]),
        )
    return {name: frame.dropna() for name, frame in frames.items()}


def _frame(x, y, time, yaw, vehicle: _Vehicle) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "x": x + vehicle.front_ref * np.cos(yaw),
            "y": y + vehicle.front_ref * np.sin(yaw),
            "time": time,
            "yaw": yaw,
        }
    )


def _vehicles_from_log(log_path: Path) -> dict[str, _Vehicle]:
    values = {}
    for line in Path(log_path).read_text(encoding="ISO-8859-1").splitlines():
        if "=" in line:
            key, value = line.split("=", 1)
            values[key] = value
    vehicle = _Vehicle(
        length=_float(values.get("VehicleLength"), 4.5),
        width=_float(values.get("VehicleWidth"), 1.8),
        wheelbase=_float(values.get("WheelBase"), 3.1),
        front_overhang=_float(values.get("FrontOverhang"), 0.65),
    )
    vehicle.front_ref = -vehicle.wheelbase
    return {"subject": vehicle, "object": vehicle}


def _vehicles(vehicle_info: Path) -> dict[str, _Vehicle]:
    sections: dict[str, dict[str, str]] = {}
    section = ""
    for line in vehicle_info.read_text(encoding="ISO-8859-1").splitlines():
        if not line or line.startswith("="):
            continue
        if "\t" not in line:
            section = line
            sections[section] = {}
            continue
        key, value = line.split("\t", 1)
        sections[section][key] = value
    return {
        "subject": _vehicle(sections["Vehicle Dimensions"]),
        "object": _vehicle(sections["Vehicle Dimensions (Other Vehicle)"]),
    }


def _vehicle(values: dict[str, str]) -> _Vehicle:
    return _Vehicle(
        length=_float(values["Vehicle Length"], 4.5),
        width=_float(values["Vehicle Width"], 1.8),
        wheelbase=_float(values["Wheelbase"], 3.1),
        front_overhang=_float(values["Front Overhang"], 0.65),
        front_ref=_float(values["Front Axle To Reference Point"], -3.1),
    )


def _write_xosc(frames: dict[str, pd.DataFrame], vehicles: dict[str, _Vehicle], output_path: Path):
    entities = xosc.Entities()
    init = xosc.Init()
    stop_time = max(frame["time"].iloc[-1] for frame in frames.values())
    act = xosc.Act("act", stoptrigger=_time_trigger("act_stop", stop_time, "stop"))

    for index, (name, frame) in enumerate(frames.items()):
        vehicle = (
            vehicles.get("object", vehicles["subject"])
            if name != "subject"
            else vehicles["subject"]
        )
        entities.add_scenario_object(
            name,
            _xosc_vehicle(name, CAR_MODELS[index % len(CAR_MODELS)], vehicle),
        )
        init.add_init_action(name, xosc.TeleportAction(_position(frame.iloc[0])))
        act.add_maneuver_group(_maneuver_group(name, frame))

    storyboard = xosc.StoryBoard(init, _time_trigger("scenario_stop", stop_time, "stop"))
    storyboard.add_act(act)
    xosc.Scenario(
        "ABD log replay",
        "project-rosetta",
        xosc.ParameterDeclarations(),
        entities,
        storyboard,
        xosc.RoadNetwork(),
        xosc.Catalog(),
        osc_minor_version=1,
    ).write_xml(str(output_path))


def _xosc_vehicle(name: str, model: str, vehicle: _Vehicle) -> xosc.Vehicle:
    return xosc.Vehicle(
        f"{name}_vehicle",
        xosc.VehicleCategory.car,
        xosc.BoundingBox(
            vehicle.width,
            vehicle.length,
            1.8,
            vehicle.front_overhang - vehicle.front_ref - vehicle.length / 2,
            0,
            0.9,
        ),
        xosc.Axle(0.5, 0.6, vehicle.width - 0.2, -vehicle.front_ref, 0.3),
        xosc.Axle(0, 0.6, vehicle.width - 0.2, -(vehicle.wheelbase + vehicle.front_ref), 0.3),
        69,
        10,
        10,
        model3d=model,
    )


def _float(value: str | None, default: float) -> float:
    return default if value is None else float(value.replace(",", "."))
