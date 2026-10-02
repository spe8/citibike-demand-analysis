"""Download daily Central Park weather from NOAA for the project's date range.

No API key needed: uses NOAA NCEI's public Access Data Service.
Output: data/raw/weather/central_park_daily.csv
"""
import calendar

import requests

from config import END_MONTH, RAW_WEATHER_DIR, START_MONTH, WEATHER_STATION

URL = "https://www.ncei.noaa.gov/access/services/data/v1"
# TMAX/TMIN = high/low temp (F), PRCP = rain (in), SNOW = snowfall (in),
# SNWD = snow depth (in), AWND = average wind speed (mph)
DATA_TYPES = "TMAX,TMIN,PRCP,SNOW,SNWD,AWND"


def main() -> None:
    end_y, end_m = map(int, END_MONTH.split("-"))
    last_day = calendar.monthrange(end_y, end_m)[1]
    params = {
        "dataset": "daily-summaries",
        "stations": WEATHER_STATION,
        "startDate": f"{START_MONTH}-01",
        "endDate": f"{END_MONTH}-{last_day:02d}",
        "dataTypes": DATA_TYPES,
        "units": "standard",
        "format": "csv",
    }
    resp = requests.get(URL, params=params, timeout=120)
    resp.raise_for_status()

    RAW_WEATHER_DIR.mkdir(parents=True, exist_ok=True)
    out = RAW_WEATHER_DIR / "central_park_daily.csv"
    out.write_text(resp.text)
    rows = resp.text.count("\n") - 1
    print(f"Saved {rows} days of weather to {out}")


if __name__ == "__main__":
    main()
