"""Load downloaded trips, stations, weather, and the toll-zone boundary into BigQuery.

Tables created:
  raw_trips_YYYYMM     one per month: slim trip records (no names/coordinates,
                       to fit two years inside the free 10 GB sandbox)
  raw_stations_YYYYMM  one per month: each station's name, coordinates, and
                       how many trips started or ended there that month
  weather_daily        NOAA daily weather
  crz_boundary         congestion relief zone polygon (GeoJSON), if downloaded

Why one table per month? The free sandbox doesn't allow DELETE/UPDATE, so
re-running a month just overwrites that month's tables. Safe to re-run.

Usage:
    python src/load_to_bigquery.py           # everything that's been downloaded
    python src/load_to_bigquery.py weather   # just weather
    python src/load_to_bigquery.py zone      # just the zone boundary
"""
import json
import sys

import pandas as pd
from google.cloud import bigquery

from config import (DATASET, LOCATION, RAW_TRIPS_DIR, RAW_WEATHER_DIR,
                    RAW_ZONE_DIR, months_between, require_project_id)

TRIP_SCHEMA = [
    bigquery.SchemaField("started_at", "DATETIME"),  # NYC local time, no time zone
    bigquery.SchemaField("ended_at", "DATETIME"),
    bigquery.SchemaField("start_station_id", "STRING"),
    bigquery.SchemaField("end_station_id", "STRING"),
    bigquery.SchemaField("rideable_type", "STRING"),
    bigquery.SchemaField("member_casual", "STRING"),
]
TRIP_COLUMNS = [f.name for f in TRIP_SCHEMA]

STATION_SCHEMA = [
    bigquery.SchemaField("station_id", "STRING"),
    bigquery.SchemaField("station_name", "STRING"),
    bigquery.SchemaField("lat", "FLOAT"),
    bigquery.SchemaField("lng", "FLOAT"),
    bigquery.SchemaField("trip_endpoints", "INTEGER"),  # trips that started or ended here
]

# Columns we read from the CSV (names/coords are only used for the station table)
CSV_COLUMNS = TRIP_COLUMNS + [
    "start_station_name", "end_station_name", "start_lat", "start_lng", "end_lat", "end_lng",
]
CSV_STRING_COLUMNS = ["start_station_id", "end_station_id", "rideable_type", "member_casual",
                      "start_station_name", "end_station_name"]

WEATHER_SCHEMA = [
    bigquery.SchemaField("date", "DATE"),
    bigquery.SchemaField("tmax_f", "FLOAT"),
    bigquery.SchemaField("tmin_f", "FLOAT"),
    bigquery.SchemaField("precip_in", "FLOAT"),
    bigquery.SchemaField("snow_in", "FLOAT"),
    bigquery.SchemaField("snow_depth_in", "FLOAT"),
    bigquery.SchemaField("avg_wind_mph", "FLOAT"),
]


def get_client() -> bigquery.Client:
    project = require_project_id()
    client = bigquery.Client(project=project, location=LOCATION)
    client.create_dataset(f"{project}.{DATASET}", exists_ok=True)
    return client


def read_trip_csv(path, ym: str) -> tuple[pd.DataFrame, int]:
    """Read one CSV, fix types, and keep only rides that started in month ym."""
    df = pd.read_csv(path, usecols=lambda c: c in CSV_COLUMNS,
                     dtype={c: "string" for c in CSV_STRING_COLUMNS})
    for col in CSV_COLUMNS:  # in case a month is missing a column
        if col not in df:
            df[col] = pd.NA
    df["started_at"] = pd.to_datetime(df["started_at"], format="mixed", errors="coerce")
    df["ended_at"] = pd.to_datetime(df["ended_at"], format="mixed", errors="coerce")

    in_month = df["started_at"].dt.strftime("%Y%m") == ym
    return df[in_month], int((~in_month).sum())


def station_counts(df: pd.DataFrame) -> pd.DataFrame:
    """Per (station_id, station_name): number of trip endpoints and summed coordinates."""
    parts = []
    for side in ("start", "end"):
        part = df[[f"{side}_station_id", f"{side}_station_name", f"{side}_lat", f"{side}_lng"]]
        part.columns = ["station_id", "station_name", "lat", "lng"]
        parts.append(part)
    s = pd.concat(parts).dropna(subset=["station_id", "lat", "lng"])
    s["station_name"] = s["station_name"].fillna("")
    return (s.groupby(["station_id", "station_name"])
             .agg(n=("lat", "size"), lat_sum=("lat", "sum"), lng_sum=("lng", "sum"))
             .reset_index())


def summarize_stations(counts: list[pd.DataFrame]) -> pd.DataFrame:
    """Combine per-file counts into one row per station: most common name, average coordinates."""
    c = pd.concat(counts).groupby(["station_id", "station_name"], as_index=False).sum()
    totals = c.groupby("station_id").agg(trip_endpoints=("n", "sum"),
                                         lat_sum=("lat_sum", "sum"), lng_sum=("lng_sum", "sum"))
    names = c.sort_values("n", ascending=False).drop_duplicates("station_id").set_index("station_id")
    out = totals.join(names["station_name"]).reset_index()
    out["lat"] = out["lat_sum"] / out["trip_endpoints"]
    out["lng"] = out["lng_sum"] / out["trip_endpoints"]
    return out[["station_id", "station_name", "lat", "lng", "trip_endpoints"]]


def load_trips(client: bigquery.Client) -> None:
    for ym in months_between():
        files = sorted((RAW_TRIPS_DIR / ym).glob("*.csv"))
        if not files:
            print(f"{ym}: no CSVs found, run download_trips.py first")
            continue

        table_id = f"{client.project}.{DATASET}.raw_trips_{ym}"
        total, dropped, counts = 0, 0, []
        for i, path in enumerate(files):
            df, n_dropped = read_trip_csv(path, ym)
            counts.append(station_counts(df))
            job_config = bigquery.LoadJobConfig(
                schema=TRIP_SCHEMA,
                # First file replaces the month's table; the rest append to it.
                write_disposition="WRITE_TRUNCATE" if i == 0 else "WRITE_APPEND",
            )
            client.load_table_from_dataframe(df[TRIP_COLUMNS], table_id, job_config=job_config).result()
            total += len(df)
            dropped += n_dropped
            print(f"  {path.name}: {len(df):,} rows")

        stations = summarize_stations(counts)
        client.load_table_from_dataframe(
            stations, f"{client.project}.{DATASET}.raw_stations_{ym}",
            job_config=bigquery.LoadJobConfig(schema=STATION_SCHEMA, write_disposition="WRITE_TRUNCATE"),
        ).result()
        print(f"{ym}: loaded {total:,} trips and {len(stations):,} stations "
              f"({dropped:,} rows dropped for bad or out-of-month start times)")


def load_weather(client: bigquery.Client) -> None:
    path = RAW_WEATHER_DIR / "central_park_daily.csv"
    if not path.exists():
        print("No weather file found, run download_weather.py first")
        return

    raw = pd.read_csv(path)
    df = pd.DataFrame({
        "date": pd.to_datetime(raw["DATE"]).dt.date,
        "tmax_f": raw.get("TMAX"),
        "tmin_f": raw.get("TMIN"),
        "precip_in": raw.get("PRCP"),
        "snow_in": raw.get("SNOW"),
        "snow_depth_in": raw.get("SNWD"),
        "avg_wind_mph": raw.get("AWND"),
    })
    table_id = f"{client.project}.{DATASET}.weather_daily"
    job_config = bigquery.LoadJobConfig(schema=WEATHER_SCHEMA, write_disposition="WRITE_TRUNCATE")
    client.load_table_from_dataframe(df, table_id, job_config=job_config).result()
    print(f"Loaded {len(df):,} days into {table_id}")


def load_zone(client: bigquery.Client) -> None:
    """Load the congestion relief zone polygon(s) from data/raw/zone/*.geojson."""
    files = sorted(RAW_ZONE_DIR.glob("*.geojson")) if RAW_ZONE_DIR.exists() else []
    if not files:
        print("No zone boundary found in data/raw/zone/ (see README, Phase 3). Skipping.")
        return

    gj = json.loads(files[0].read_text())
    features = gj["features"] if gj.get("type") == "FeatureCollection" else [gj]
    rows = [{"geojson": json.dumps(f.get("geometry", f))} for f in features]
    table_id = f"{client.project}.{DATASET}.crz_boundary"
    job_config = bigquery.LoadJobConfig(
        schema=[bigquery.SchemaField("geojson", "STRING")], write_disposition="WRITE_TRUNCATE")
    client.load_table_from_json(rows, table_id, job_config=job_config).result()
    print(f"Loaded {len(rows)} zone shape(s) from {files[0].name} into {table_id}")


if __name__ == "__main__":
    client = get_client()
    what = sys.argv[1] if len(sys.argv) > 1 else "all"
    if what == "all":
        load_trips(client)
    if what in ("all", "weather"):
        load_weather(client)
    if what in ("all", "zone"):
        load_zone(client)
