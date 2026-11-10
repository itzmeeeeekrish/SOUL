"""Read SOUL backend settings from the environment."""

import os
from pathlib import Path

from dotenv import load_dotenv

# config.py is inside backend/app, so parents[2] points to the repository root.
REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(REPOSITORY_ROOT / ".env")

APP_NAME = os.getenv("SOUL_APP_NAME", "SOUL API")
APP_VERSION = os.getenv("SOUL_APP_VERSION", "0.1.0")
APP_ENV = os.getenv("SOUL_ENV", "development").lower()
APP_DEBUG = APP_ENV == "development"
