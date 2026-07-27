from unittest.mock import MagicMock, patch

import pytest

from project_rosetta.utils.run_dat2csv import run_dat2csv


@patch("project_rosetta.utils.run_dat2csv.subprocess.run")
def test_run_dat2csv_success(mock_run):
    """Test that run_dat2csv correctly runs the subprocess and returns the expected result."""
    mock_run.return_value = MagicMock(returncode=0, stdout="ok", stderr="")

    result = run_dat2csv("input.dat", "output.csv", cwd=".")

    assert result.returncode == 0
    assert result.stdout == "ok"
    assert result.stderr == ""


@patch("project_rosetta.utils.run_dat2csv.subprocess.run")
def test_run_dat2csv_failure(mock_run):
    """Test that run_dat2csv correctly handles subprocess errors."""
    mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="error occurred")

    with pytest.raises(RuntimeError, match="dat2csv failed"):
        run_dat2csv("input.dat", "output.csv", cwd=".")
