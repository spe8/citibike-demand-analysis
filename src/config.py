"""Shared settings for the pipeline. Values come from the .env file in the repo root."""
import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")

PROJECT_ID = os.getenv("GCP_PROJECT_ID")
DATASET = os.getenv("BQ_DATASET", "citibike")
LOCATION = os.getenv("BQ_LOCATION", "US")

# Months to pull, inclusive, as YYYY-MM. Test with a few months first, then
# widen to the full study window: 2024-01 (before tolls) to 2025-12 (after).
START_MONTH = os.getenv("START_MONTH", "2024-12")
END_MONTH = os.getenv("END_MONTH", "2025-02")

DATA_DIR = ROOT / "data"
RAW_TRIPS_DIR = DATA_DIR / "raw" / "trips"
RAW_WEATHER_DIR = DATA_DIR / "raw" / "weather"
RAW_ZONE_DIR = DATA_DIR / "raw" / "zone"
SQL_DIR = ROOT / "sql"

# NOAA station for Central Park, NY
WEATHER_STATION = "USW00094728"


def months_between(start: str = START_MONTH, end: str = END_MONTH) -> list[str]:
    """Return ['202501', '202502', ...] for every month from start to end, inclusive."""
    y, m = map(int, start.split("-"))
    end_y, end_m = map(int, end.split("-"))
    months = []
    while (y, m) <= (end_y, end_m):
        months.append(f"{y}{m:02d}")
        m += 1
        if m == 13:
            y, m = y + 1, 1
    return months


def require_project_id() -> str:
    if not PROJECT_ID:
        raise SystemExit(
            "GCP_PROJECT_ID is not set. Copy .env.example to .env and fill it in "
            "(see docs/SETUP_BIGQUERY.md)."
        )
    return PROJECT_ID
