from dataclasses import dataclass
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent

LOGS_DIR = BASE_DIR / "logs"

ESMINI_DIR = BASE_DIR / "esmini"


@dataclass
class CommandResult:
    """Result of running a command, including return code, stdout, and stderr."""

    returncode: int
    stdout: str
    stderr: str
