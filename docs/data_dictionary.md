# Data Dictionary

Fill this in as you build each table. Interviewers (and the NYS job posting) specifically value this.

## Sources

| Source | What | Link |
|---|---|---|
| Citi Bike System Data | One row per ride, published monthly | <https://citibikenyc.com/system-data> |
| NOAA daily summaries | Daily weather, Central Park station `USW00094728` | <https://www.ncei.noaa.gov/cdo-web/> |

## `raw_trips_YYYYMM` (one table per month)

Slimmed down from the source CSV: station names and coordinates live in `raw_stations_YYYYMM` instead, so two years fit in the free tier.

| Column | Type | Description |
|---|---|---|
| started_at | DATETIME | Ride start, NYC local time |
| ended_at | DATETIME | Ride end, NYC local time |
| start_station_id | STRING | Start station ID |
| end_station_id | STRING | End station ID (can be null for some e-bike rides) |
| rideable_type | STRING | `classic_bike` or `electric_bike` |
| member_casual | STRING | `member` (annual subscriber) or `casual` (single ride / day pass) |

## `raw_stations_YYYYMM` (one table per month)

Built by `load_to_bigquery.py` from the trip CSVs.

| Column | Type | Description |
|---|---|---|
| station_id | STRING | Station ID |
| station_name | STRING | Most common name for this ID that month |
| lat, lng | FLOAT | Average coordinates of trips starting/ending there |
| trip_endpoints | INTEGER | Trips that started or ended at the station that month |

## `weather_daily`

| Column | Type | Description |
|---|---|---|
| date | DATE | Calendar day |
| tmax_f / tmin_f | FLOAT | Daily high / low temperature (°F) |
| precip_in | FLOAT | Precipitation (inches) |
| snow_in | FLOAT | Snowfall (inches) |
| snow_depth_in | FLOAT | Snow on the ground (inches) |
| avg_wind_mph | FLOAT | Average wind speed (mph) |

## `trips_clean` (view)

All columns from `raw_trips_*` plus the derived fields below. Cleaning rules are in `sql/01_trips_clean.sql`.

| Column | Type | Description |
|---|---|---|
| ride_date | DATE | Date the ride started |
| start_hour | INT | Hour the ride started (0-23) |
| day_of_week | STRING | e.g. `Monday` |
| duration_min | FLOAT | Ride length in minutes |
| is_post_toll | BOOL | TRUE if the ride started on or after Jan 5, 2025 (congestion pricing start) |

**Rows removed by cleaning:** TODO: record counts for each rule (raw rows, missing fields, duration outliers, final rows).

## `stations`

TODO

## `crz_boundary`

TODO: source of the zone polygon and date retrieved

## `zone_stations`

TODO

## `daily_rides`

TODO

## `station_daily`

TODO
