import pandas as pd
import pytest

from project_rosetta.utils.csv2xyt import run_csv2xyt, split_dataframe_by_id


def test_split_dataframe_by_id_basic():
    """Test that the dataframe is correctly split by 'id' and filtered by requested columns."""
    df = pd.DataFrame(
        {
            "id": [1, 1, 2],
            "x": [10, 20, 30],
            "y": [100, 200, 300],
        }
    )

    result = split_dataframe_by_id(df, ["id", "x"])

    assert set(result.keys()) == {"1", "2"}
    assert result["1"]["x"].tolist() == [10, 20]
    assert result["2"]["x"].tolist() == [30]


def test_missing_id_column():
    """Test that split_dataframe_by_id raises KeyError when 'id' column is missing."""
    df = pd.DataFrame({"x": [1]})

    with pytest.raises(KeyError):
        split_dataframe_by_id(df, ["x"])


def test_missing_requested_columns():
    """Test that split_dataframe_by_id raises KeyError when requested columns are missing."""
    df = pd.DataFrame({"id": [1], "x": [10]})

    with pytest.raises(KeyError):
        split_dataframe_by_id(df, ["id", "y"])


def test_run_csv2xyt(tmp_path):
    """Test that run_csv2xyt correctly creates .xyt files for each id."""
    input_file = tmp_path / "input.csv"
    output_dir = tmp_path / "out"

    df = pd.DataFrame(
        {
            "id": [1, 2],
            "x": [10, 20],
        }
    )
    df.to_csv(input_file, index=False)

    run_csv2xyt(input_file, output_dir, ["id", "x"])

    file1 = output_dir / "id_1.xyt"
    file2 = output_dir / "id_2.xyt"

    assert file1.exists()
    assert file2.exists()

    df1 = pd.read_csv(file1, header=None, sep=" ", decimal=",")
    assert df1.iloc[0].tolist() == [1, 10]
