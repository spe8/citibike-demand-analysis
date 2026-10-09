"""Download Citi Bike trip files and unzip them into data/raw/trips/<YYYYMM>/.

Citi Bike publishes recent months as one zip per month, and bundles older
years into one big yearly zip. This script tries the monthly file first and
falls back to the yearly zip, sorting the CSVs inside into month folders.

Usage:
    python src/download_trips.py                 # uses START_MONTH / END_MONTH from .env
    python src/download_trips.py 2024-01 2024-03 # or pass a range

Disk space: a full year of CSVs is roughly 8-10 GB. After a month is loaded
into BigQuery you can delete its folder in data/raw/trips/.
"""
import re
import shutil
import sys
import tempfile
import time
import zipfile
from pathlib import Path

import requests
from tqdm import tqdm

from config import RAW_TRIPS_DIR, months_between

BASE_URL = "https://s3.amazonaws.com/tripdata"
MONTHLY_NAMES = ["{ym}-citibike-tripdata.zip", "{ym}-citibike-tripdata.csv.zip"]
YEARLY_NAME = "{year}-citibike-tripdata.zip"
MONTH_IN_NAME = re.compile(r"(20\d{2})[-_]?(0[1-9]|1[0-2])")


def download_to_disk(url: str, dest: Path, retries: int = 3) -> bool:
    """Stream a file to disk, retrying if the connection drops partway through."""
    for attempt in range(1, retries + 1):
        try:
            return _download_once(url, dest)
        except requests.exceptions.RequestException as e:
            if attempt == retries:
                raise
            wait = 30 * attempt
            print(f"\nConnection problem ({type(e).__name__}). Retrying in {wait}s "
                  f"(attempt {attempt + 1} of {retries})...")
            time.sleep(wait)
    return False


def _download_once(url: str, dest: Path) -> bool:
    """Stream a file to disk (yearly zips are several GB, too big for memory)."""
    with requests.get(url, stream=True, timeout=60) as resp:
        if resp.status_code != 200:
            return False
        total = int(resp.headers.get("content-length", 0))
        with open(dest, "wb") as f, tqdm(total=total, unit="B", unit_scale=True,
                                         desc=url.rsplit("/", 1)[-1]) as bar:
            for chunk in resp.iter_content(chunk_size=1 << 20):
                f.write(chunk)
                bar.update(len(chunk))
    return True


def month_from_name(name: str, default: str | None) -> str | None:
    match = MONTH_IN_NAME.search(Path(name).name) or MONTH_IN_NAME.search(name)
    return f"{match.group(1)}{match.group(2)}" if match else default


def extract_csvs(zip_path: Path, wanted: set[str], default_month: str | None = None) -> dict[str, int]:
    """Extract CSVs (including ones inside nested zips) into month folders.

    Each CSV goes to data/raw/trips/<YYYYMM>/ based on the month in its file
    name. Only months in `wanted` are kept. Returns {month: csv_count}.
    """
    counts: dict[str, int] = {}
    with zipfile.ZipFile(zip_path) as zf:
        for name in zf.namelist():
            if name.startswith("__MACOSX") or name.endswith("/"):
                continue
            month = month_from_name(name, default_month)
            if name.lower().endswith(".zip"):
                if month and month not in wanted:
                    continue
                with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as tmp:
                    with zf.open(name) as src:
                        shutil.copyfileobj(src, tmp)
                inner = Path(tmp.name)
                try:
                    for m, n in extract_csvs(inner, wanted, month).items():
                        counts[m] = counts.get(m, 0) + n
                finally:
                    inner.unlink()
            elif name.lower().endswith(".csv") and month in wanted:
                out_dir = RAW_TRIPS_DIR / month
                out_dir.mkdir(parents=True, exist_ok=True)
                with zf.open(name) as src, open(out_dir / Path(name).name, "wb") as dst:
                    shutil.copyfileobj(src, dst)
                counts[month] = counts.get(month, 0) + 1
    return counts


def already_have(ym: str) -> bool:
    folder = RAW_TRIPS_DIR / ym
    return folder.exists() and any(folder.glob("*.csv"))


def fetch(months: list[str]) -> None:
    todo = [ym for ym in months if not already_have(ym)]
    for ym in months:
        if ym not in todo:
            print(f"{ym}: already downloaded, skipping")

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_zip = Path(tmpdir) / "download.zip"

        # 1) Try one zip per month
        missing = []
        for ym in todo:
            for pattern in MONTHLY_NAMES:
                if download_to_disk(f"{BASE_URL}/{pattern.format(ym=ym)}", tmp_zip):
                    counts = extract_csvs(tmp_zip, {ym}, default_month=ym)
                    print(f"{ym}: extracted {counts.get(ym, 0)} CSV file(s)")
                    break
            else:
                missing.append(ym)

        # 2) Fall back to the yearly zip for anything not found
        for year in sorted({ym[:4] for ym in missing}):
            wanted = {ym for ym in missing if ym.startswith(year)}
            print(f"{year}: no monthly files for {sorted(wanted)}, trying the yearly zip (large download)...")
            if not download_to_disk(f"{BASE_URL}/{YEARLY_NAME.format(year=year)}", tmp_zip):
                print(f"{year}: yearly zip not found either. Check "
                      f"https://s3.amazonaws.com/tripdata/index.html for the file names.")
                continue
            for ym, n in sorted(extract_csvs(tmp_zip, wanted).items()):
                print(f"{ym}: extracted {n} CSV file(s)")


if __name__ == "__main__":
    fetch(months_between(*sys.argv[1:3]) if len(sys.argv) >= 3 else months_between())
