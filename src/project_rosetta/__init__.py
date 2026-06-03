"""Project Rosetta Python package."""
import logging
import os


LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

log_level = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(format=LOG_FORMAT, datefmt=LOG_DATE_FORMAT, level=log_level)