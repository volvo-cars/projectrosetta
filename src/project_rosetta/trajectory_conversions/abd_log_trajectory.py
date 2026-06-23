from pathlib import Path

import pandas as pd


def read_abd_log(file_path: Path) -> pd.DataFrame:
    """
    Read the ABD tab-log shape used by CMCscp_SFS_VUT.txt.

    Returns:
        Numeric ABD log data.

    """
    data = pd.read_csv(
        Path(file_path),
        sep="\t",
        header=2,
        encoding="ISO-8859-1",
        keep_default_na=False,
        low_memory=False,
    )
    data = data.iloc[1:].reset_index(drop=True)
    data = data.replace(",", ".", regex=True)
    return data.apply(pd.to_numeric, errors="coerce")


def abd_log_to_xyt_frames(file_path: Path) -> dict[str, pd.DataFrame]:
    """
    Convert the ABD subject and object front-axle channels to x y time frames.

    Returns:
        Actor name to x y time frame.

    """
    data = read_abd_log(file_path)
    time = data["System Time"] - data["System Time"].iloc[0]
    frames = {
        "subject": pd.DataFrame(
            {
                "x": (data["Actual X (front axle)"] + data["Actual X (rear axle)"]) / 2,
                "y": (data["Actual Y (front axle)"] + data["Actual Y (rear axle)"]) / 2,
                "time": time,
            }
        )
    }

    for column in data.columns:
        prefix = "Object "
        suffix = " actual X (front axle)"
        if not column.startswith(prefix) or not column.endswith(suffix):
            continue
        object_id = column.removeprefix(prefix).removesuffix(suffix)
        y_column = f"Object {object_id} actual Y (front axle)"
        frames[f"object_{object_id}"] = pd.DataFrame(
            {"x": data[column], "y": data[y_column], "time": time}
        )

    return {name: frame.dropna() for name, frame in frames.items()}


def write_abd_log_xyt_files(file_path: Path, output_dir: Path) -> list[Path]:
    """
    Write one `.xyt` file per actor parsed from an ABD tab log.

    Returns:
        Written file paths.

    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    paths = []
    for name, frame in abd_log_to_xyt_frames(file_path).items():
        path = output_path / f"{name}.xyt"
        frame.to_csv(path, index=False, header=False, sep=" ", decimal=",")
        paths.append(path)
    return paths
