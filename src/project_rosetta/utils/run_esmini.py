import subprocess
from pathlib import Path

from project_rosetta.utils.utils import ESMINI_DEMO_DIR, CommandResult


def run_esmini(
    config_file: Path | str,
    cwd: Path | str = ESMINI_DEMO_DIR,
    log_file: Path | str | None = None,
) -> CommandResult:
    """
    Run the esmini process with the given config file.

    Args:
        config_file: Path to the esmini config file.
        cwd: Current working directory for the esmini process.
        log_file: Optional path where esmini stdout and stderr should be written.

    Returns:
        CommandResult: The result of the esmini process.

    """
    command = [
        "./bin/esmini",
        "--config_file_path",
        str(config_file),
        "--fixed_timestep",
        "0.01",
    ]

    result = subprocess.run(
        command,
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
    )

    if log_file is not None:
        log_path = Path(log_file)
        log_path.write_text(
            "Command: "
            + " ".join(command)
            + "\n"
            + f"Return code: {result.returncode}\n\n"
            + "[stdout]\n"
            + result.stdout
            + ("\n" if result.stdout and not result.stdout.endswith("\n") else "")
            + "\n[stderr]\n"
            + result.stderr
            + ("\n" if result.stderr and not result.stderr.endswith("\n") else "")
        )

    return CommandResult(
        returncode=result.returncode,
        stdout=result.stdout,
        stderr=result.stderr,
    )


def build_esmini_config(
    scenario_path: Path | str,
    record_file: Path | str,
    window: bool = False,
) -> str:
    """
    Return config content as string.

    Args:
        scenario_path: Path to the scenario file.
        record_file: Path to the record file (without .dat extension).
        window: Whether to display the esmini window.

    Returns:
        Config content as string.

    """
    lines = [
        "esmini:",
        f"  osc: {scenario_path}",
        f"  record: {record_file}.dat",
    ]

    if window:
        lines.append("  window: 60 60 800 400")
    else:
        lines.append("  headless: true")

    return "\n".join(lines) + "\n"


def setup_run_config(
    scenario_path: Path | str,
    record_file: Path | str,
    window: bool = False,
    output_path: Path | str = "esmini_run_config.yml",
) -> Path:
    """
    Create a config file for running esmini and return the path to the created file.

    Args:
        scenario_path: Path to the scenario file.
        record_file: Path to the record file.
        window: Whether to display the esmini window.
        output_path: Path to the output config file.

    Returns:
        Path to the created config file.

    """
    content = build_esmini_config(scenario_path, record_file, window)

    output_path = Path(output_path)
    output_path.write_text(content)

    return output_path
