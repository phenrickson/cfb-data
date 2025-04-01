import os
from pathlib import Path
from datetime import datetime, timedelta

from dotenv import load_dotenv
from loguru import logger

# Load environment variables from .env file if it exists
load_dotenv()

# API Configuration
CFBD_API_KEY = os.getenv("CFBD_API_KEY")
if not CFBD_API_KEY:
    logger.warning("CFBD_API_KEY not found in environment variables. API requests will fail.")

# API Rate Limiting
# CFBD API has a limit of 5000 calls per month
MAX_MONTHLY_CALLS = 5000
# Calculate a safe daily limit (assuming 30 days per month with some buffer)
DAILY_CALL_LIMIT = int(MAX_MONTHLY_CALLS / 30 * 0.8)  # 80% of even distribution to leave buffer
# Minimum time between API calls in seconds to avoid hitting rate limits
MIN_API_CALL_INTERVAL = 1.0  # seconds

# BigQuery Configuration
GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID")
BQ_DATASET_ID = os.getenv("BQ_DATASET_ID", "cfb_data")
BQ_LOCATION = os.getenv("BQ_LOCATION", "US")  # Default to US region

# Season Configuration
CURRENT_SEASON = datetime.now().year
# If it's before August, the current season hasn't started yet
if datetime.now().month < 8:
    CURRENT_SEASON -= 1
# Historical data range (adjust as needed)
FIRST_SEASON = 2000  # First season to fetch data for
LAST_SEASON = CURRENT_SEASON  # Last season to fetch data for

# Paths
PROJ_ROOT = Path(__file__).resolve().parents[1]
logger.info(f"PROJ_ROOT path is: {PROJ_ROOT}")

DATA_DIR = PROJ_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
INTERIM_DATA_DIR = DATA_DIR / "interim"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
EXTERNAL_DATA_DIR = DATA_DIR / "external"

# API cache directory to store responses and reduce API calls
API_CACHE_DIR = DATA_DIR / "api_cache"
# Create cache directory if it doesn't exist
API_CACHE_DIR.mkdir(parents=True, exist_ok=True)

# API call tracking file to monitor usage
API_CALL_LOG = DATA_DIR / "api_call_log.json"

MODELS_DIR = PROJ_ROOT / "models"

REPORTS_DIR = PROJ_ROOT / "reports"
FIGURES_DIR = REPORTS_DIR / "figures"

# Table names for BigQuery
TABLES = {
    "games": "games",
    "drives": "drives",
    "plays": "plays",
    "play_types": "play_types",
    "teams": "teams",
    "teams_fbs": "teams_fbs",
    "talent": "talent",
    "conferences": "conferences",
    "venues": "venues",
    "coaches": "coaches",
}

# If tqdm is installed, configure loguru with tqdm.write
# https://github.com/Delgan/loguru/issues/135
try:
    from tqdm import tqdm

    logger.remove(0)
    logger.add(lambda msg: tqdm.write(msg, end=""), colorize=True)
except ModuleNotFoundError:
    pass
