"""Load downloaded trip and weather files into BigQuery.

Each month goes into its own table (raw_trips_202501, raw_trips_202502, ...).
SQL then reads them all at once with the wildcard `raw_trips_*`.

Why one table per month? The free BigQuery sandbox doesn't allow DELETE/UPDATE,
so re-running a month just overwrites that month's table. Safe to re-run.

Usage:
    python src/load_to_bigquery.py            # trips for every downloaded month + weather
    python src/load_to_bigquery.py weather    # weather only
"""
import sys

import pandas as pd
from google.cloud import bigquery

from config import (DATASET, LOCATION, RAW_TRIPS_DIR, RAW_WEATHER_DIR,
                    months_between, require_project_id)

TRIP_SCHEMA = [
    bigquery.SchemaField("ride_id", "STRING"),
    bigquery.SchemaField("rideable_type", "STRING"),
    bigquery.SchemaField("started_at", "DATETIME"),  # NYC local time, no time zone
    bigquery.SchemaField("ended_at", "DATETIME"),
    bigquery.SchemaField("start_station_id", "STRING"),
    bigquery.SchemaField("start_station_name", "STRING"),
    bigquery.SchemaField("end_station_id", "STRING"),
    bigquery.SchemaField("end_station_name", "STRING"),
    bigquery.SchemaField("start_lat", "FLOAT"),
    bigquery.SchemaField("start_lng", "FLOAT"),
    bigquery.SchemaField("end_lat", "FLOAT"),
    bigquery.SchemaField("end_lng", "FLOAT"),
    bigquery.SchemaField("member_casual", "STRING"),
]
TRIP_COLUMNS = [f.name for f in TRIP_SCHEMA]
STRING_COLUMNS = [f.name for f in TRIP_SCHEMA if f.field_type == "STRING"]

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
    """Read one CSV, keep the columns we need, fix types, and keep only rows from month ym."""
    df = pd.read_csv(path, usecols=lambda c: c in TRIP_COLUMNS, dtype={c: "string" for c in STRING_COLUMNS})
    for col in TRIP_COLUMNS:  # in case a month is missing a column
        if col not in df:
            df[col] = pd.NA
    df = df[TRIP_COLUMNS]
    df["started_at"] = pd.to_datetime(df["started_at"], format="mixed", errors="coerce")
    df["ended_at"] = pd.to_datetime(df["ended_at"], format="mixed", errors="coerce")

    in_month = df["started_at"].dt.strftime("%Y%m") == ym
    return df[in_month], int((~in_month).sum())


def load_trips(client: bigquery.Client) -> None:
    for ym in months_between():
        files = sorted((RAW_TRIPS_DIR / ym).glob("*.csv"))
        if not files:
            print(f"{ym}: no CSVs found, run download_trips.py first")
            continue

        table_id = f"{client.project}.{DATASET}.raw_trips_{ym}"
        total, dropped = 0, 0
        for i, path in enumerate(files):
            df, n_dropped = read_trip_csv(path, ym)
            job_config = bigquery.LoadJobConfig(
                schema=TRIP_SCHEMA,
                # First file replaces the month's table; the rest append to it.
                write_disposition="WRITE_TRUNCATE" if i == 0 else "WRITE_APPEND",
            )
            client.load_table_from_dataframe(df, table_id, job_config=job_config).result()
            total += len(df)
            dropped += n_dropped
            print(f"  {path.name}: {len(df):,} rows")
        print(f"{ym}: loaded {total:,} rows into {table_id} "
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


if __name__ == "__main__":
    client = get_client()
    if sys.argv[1:] != ["weather"]:
        load_trips(client)
    load_weather(client)
