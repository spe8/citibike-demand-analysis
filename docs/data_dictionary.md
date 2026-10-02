# Data Dictionary

Fill this in as you build each table. Interviewers (and the NYS job posting) specifically value this.

## Sources

| Source | What | Link |
|---|---|---|
| Citi Bike System Data | One row per ride, published monthly | <https://citibikenyc.com/system-data> |
| NOAA daily summaries | Daily weather, Central Park station `USW00094728` | <https://www.ncei.noaa.gov/cdo-web/> |

## `raw_trips_YYYYMM` (one table per month, loaded as-is)

| Column | Type | Description |
|---|---|---|
| ride_id | STRING | Unique ride identifier |
| rideable_type | STRING | `classic_bike` or `electric_bike` |
| started_at | DATETIME | Ride start, NYC local time |
| ended_at | DATETIME | Ride end, NYC local time |
| start_station_id | STRING | Start station ID |
| start_station_name | STRING | Start station name |
| end_station_id | STRING | End station ID (can be null for some e-bike rides) |
| end_station_name | STRING | End station name |
| start_lat, start_lng | FLOAT | Start coordinates |
| end_lat, end_lng | FLOAT | End coordinates |
| member_casual | STRING | `member` (annual subscriber) or `casual` (single ride / day pass) |

## `weather_daily`

| Column | Type | Description |
|---|---|---|
| date | DATE | Calendar day |
| tmax_f / tmin_f | FLOAT | Daily high / low temperature (°F) |
| precip_in | FLOAT | Precipitation (inches) |
| snow_in | FLOAT | Snowfall (inches) |
| snow_depth_in | FLOAT | Snow on the ground (inches) |
| avg_wind_mph | FLOAT | Average wind speed (mph) |

## `trips_clean`

All columns from `raw_trips_*` plus the derived fields below. Cleaning rules are in `sql/01_trips_clean.sql`.

| Column | Type | Description |
|---|---|---|
| ride_date | DATE | Date the ride started |
| start_hour | INT | Hour the ride started (0-23) |
| day_of_week | STRING | e.g. `Monday` |
| duration_min | FLOAT | Ride length in minutes |

**Rows removed by cleaning:** TODO: record counts for each rule (raw rows, duplicates, missing fields, duration outliers, final rows).

## `daily_rides`

TODO

## `stations`

TODO

## `station_daily`

TODO
