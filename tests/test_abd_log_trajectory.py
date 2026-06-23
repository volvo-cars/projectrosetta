import pandas as pd

from project_rosetta.trajectory_conversions.abd_log_trajectory import write_abd_log_xyt_files


def test_abd_log_to_xyt_frames_extracts_subject_and_object(tmp_path):
    """Test the ABD log channel shape used by CMCscp_SFS_VUT.txt."""
    log_path = tmp_path / "abd.txt"
    log_path.write_text(
        "\n".join(
            [
                "Anthony Best Dynamics Ltd",
                "Points=2",
                (
                    "System Time\tActual X (front axle)\tActual Y (front axle)"
                    "\tActual X (rear axle)\tActual Y (rear axle)"
                    "\tObject 1 actual X (front axle)\tObject 1 actual Y (front axle)"
                ),
                "s\tm\tm\tm\tm\tm\tm",
                "10,0\t2,0\t0,0\t0,0\t0,0\t5,0\t6,0",
                "11,0\t4,0\t0,0\t2,0\t0,0\t7,0\t8,0",
            ]
        ),
        encoding="ISO-8859-1",
    )

    output_paths = write_abd_log_xyt_files(log_path, tmp_path / "xyt")
    assert output_paths == [tmp_path / "xyt" / "subject.xyt", tmp_path / "xyt" / "object_1.xyt"]
    assert pd.read_csv(output_paths[0], sep=r"\s+", header=None, decimal=",").iloc[0].tolist() == [
        1.0,
        0.0,
        0.0,
    ]
