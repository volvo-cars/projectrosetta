from pathlib import Path

import pandas as pd


def split_dataframe_by_id(df: pd.DataFrame, columns: list[str]) -> dict[str, pd.DataFrame]:
    """
    Split a dataframe into multiple dataframes by 'id'.

    Returns:
        Dict mapping id -> filtered dataframe

    Raises:
        ValueError: If input dataframe is None.
        KeyError: If 'id' column is missing or if any requested columns are missing.
        KeyError: If requested columns are missing from the dataframe.

    """
    if df is None:
        raise ValueError("Input dataframe cannot be None")

    if "id" not in df.columns:
        raise KeyError("Column 'id' not found in dataframe")

    missing_cols = [col for col in columns if col not in df.columns]
    if missing_cols:
        raise KeyError(f"Missing columns: {missing_cols}")

    result = {}

    for id_val, group in df.groupby("id"):
        result[str(id_val)] = group[columns]

    return result


def run_csv2xyt(csv_file: str, output_dir: str, columns: list[str]) -> None:
    """
    Read CSV and write one file per id.

    Args:
        csv_file: Path to the input CSV file.
        output_dir: Directory where output .xyt files will be saved.
        columns: List of columns to include in the output (must include 'id').

    """
    df = pd.read_csv(csv_file)
    df.columns = df.columns.str.strip()

    split_data = split_dataframe_by_id(df, columns)

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    for id_val, data in split_data.items():
        file_path = output_path / f"id_{id_val}.xyt"
        data.to_csv(file_path, index=False, header=False, sep=" ", decimal=",")
