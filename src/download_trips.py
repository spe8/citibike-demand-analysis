"""Download monthly Citi Bike trip files and unzip them into data/raw/trips/<YYYYMM>/.

Usage:
    python src/download_trips.py                 # uses START_MONTH / END_MONTH from .env
    python src/download_trips.py 2025-04 2025-06 # or pass a range
"""
import io
import sys
import zipfile
from pathlib import Path

import requests
from tqdm import tqdm

from config import RAW_TRIPS_DIR, months_between

BASE_URL = "https://s3.amazonaws.com/tripdata"
# Citi Bike has used a couple of naming patterns over the years; try each.
NAME_PATTERNS = ["{ym}-citibike-tripdata.zip", "{ym}-citibike-tripdata.csv.zip"]


def download(url: str) -> bytes | None:
    resp = requests.get(url, stream=True, timeout=60)
    if resp.status_code != 200:
        return None
    total = int(resp.headers.get("content-length", 0))
    buf = io.BytesIO()
    with tqdm(total=total, unit="B", unit_scale=True, desc=url.rsplit("/", 1)[-1]) as bar:
        for chunk in resp.iter_content(chunk_size=1 << 20):
            buf.write(chunk)
            bar.update(len(chunk))
    return buf.getvalue()


def extract_csvs(zip_bytes: bytes, out_dir: Path) -> int:
    """Extract every CSV in the zip (including zips nested inside it). Returns CSV count."""
    count = 0
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        for name in zf.namelist():
            if name.startswith("__MACOSX") or name.endswith("/"):
                continue
            if name.lower().endswith(".zip"):
                count += extract_csvs(zf.read(name), out_dir)
            elif name.lower().endswith(".csv"):
                (out_dir / Path(name).name).write_bytes(zf.read(name))
                count += 1
    return count


def fetch_month(ym: str) -> None:
    out_dir = RAW_TRIPS_DIR / ym
    if out_dir.exists() and any(out_dir.glob("*.csv")):
        print(f"{ym}: already downloaded, skipping")
        return

    for pattern in NAME_PATTERNS:
        data = download(f"{BASE_URL}/{pattern.format(ym=ym)}")
        if data:
            out_dir.mkdir(parents=True, exist_ok=True)
            n = extract_csvs(data, out_dir)
            print(f"{ym}: extracted {n} CSV file(s) to {out_dir}")
            return

    print(
        f"{ym}: no monthly file found. Older years are bundled into one yearly zip; "
        f"check https://s3.amazonaws.com/tripdata/index.html for the exact file name."
    )


if __name__ == "__main__":
    months = months_between(*sys.argv[1:3]) if len(sys.argv) >= 3 else months_between()
    for ym in months:
        fetch_month(ym)
