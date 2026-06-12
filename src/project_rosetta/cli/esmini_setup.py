"""esmini setup for project-rosetta."""

import logging
import os
import shutil
import stat
import zipfile

import requests

logger = logging.getLogger(__name__)

logger = logging.getLogger(__name__)

ESMINI_RELEAVE_VERSION = "v3.0.1"

# Currently not used, only demo atm
ESMINI_BIN_URL = f"https://github.com/esmini/esmini/releases/download/{ESMINI_RELEAVE_VERSION}/esmini-bin_Linux.zip"
ESMINI_SRC_URL = f"https://github.com/esmini/esmini/archive/refs/tags/{ESMINI_RELEAVE_VERSION}.zip"
ESMINI_BIN = "esmini_bin"
ESMINI_SRC = "esmini_src"

ESMINI_DEMO_URL = f"https://github.com/esmini/esmini/releases/download/{ESMINI_RELEAVE_VERSION}/esmini-demo_Linux.zip"
ESMINI_DEMO = "esmini_demo"

OUTPUT_FOLDER = "esmini"


def ensure_executable(path):
    """
    Ensure the given file is executable.

    Args:
        path: Path to the file to check and modify.

    Raises:
        FileNotFoundError: If the specified file does not exist.

    """
    if not os.path.isfile(path):
        raise FileNotFoundError(f"{path} not found")

    st = os.stat(path)
    if not (st.st_mode & stat.S_IXUSR):
        # Add execute bit for user (and optionally group/others)
        os.chmod(path, st.st_mode | stat.S_IXUSR)
        logger.debug(f"Made {path} executable")


def esmini_directory() -> None:
    """Ensure the output directory for esmini exists and is clean."""
    if os.path.exists(OUTPUT_FOLDER):
        shutil.rmtree(OUTPUT_FOLDER)
    os.mkdir(OUTPUT_FOLDER)


def fetch_esmini_zip(url: str, output_path: str) -> None:
    """
    Fetch a zip file from the given URL and save it to the specified output path.

    Args:
        url: URL of the zip file to fetch.
        output_path: Path to save the fetched zip file (without .zip extension).

    """
    response = requests.get(url)
    response.raise_for_status()

    with open(output_path + ".zip", "wb") as f:
        f.write(response.content)


def unzip_esmini(zip_file: str, output_dir: str) -> None:
    """
    Unzip the specified zip file into the given output directory.

    Args:
        zip_file: Path to the zip file (without .zip extension).
        output_dir: Directory to extract the contents to.

    """
    with zipfile.ZipFile(zip_file + ".zip", "r") as zip_ref:
        zip_ref.extractall(output_dir)


def setup_esmini() -> None:
    """Set up esmini by fetching and extracting necessary files."""
    logger.info("Setting up esmini...")

    esmini_directory()

    files_to_fetch = [
        # [ESMINI_BIN_URL, ESMINI_BIN],
        # [ESMINI_SRC_URL, ESMINI_SRC],
        [ESMINI_DEMO_URL, ESMINI_DEMO]
    ]
    for url, output in files_to_fetch:
        logger.info(f"Fetching {url}...")
        fetch_esmini_zip(url, output)
        logger.info(f"Unzipping {output}...")
        unzip_esmini(output, OUTPUT_FOLDER)

    for binary in ["esmini", "dat2csv", "replayer"]:
        ensure_executable(os.path.join(OUTPUT_FOLDER, "esmini-demo", "bin", binary))


def main() -> int:
    """
    Run the hello-world CLI command.

    Returns:
        Exit status code.

    """
    logger.info("Hello from setup esmini")

    setup_esmini()

    logger.info("Setup of esmini complete")

    return 0
