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

**Rows removed by cleaning (Jan 2024 - Dec 2025):**

| Step | Rows |
|---|---|
| Raw rows loaded | 90060645 |
| Missing start or end time | 0 |
| Missing start or end station | 283466 |
| Under 1 minute | 919 |
| over 24 hours | 19321 |
| **Final rows in 'trips_clean'** | 89775789 |



## `stations`

One row per station across Jan 2024 – Dec 2025. Built by `sql/02_stations.sql` from `raw_stations_*`. **Rows:** 2499 (`station_id` verified unique).

| Column | Type | Description |
| --- | --- | ---|
| station_id | STRING | Station ID (unique) |
| station_name | STRING | Name from the most recent month the station appears |
| lat, lng | FLOAT | Station coordinates: monthly averages weighted by trip count |
| trip_endpoints | INTEGER | Total trips that started or ended at the station, 2024-2025 |
| first_month / last_month | STRING | First and last month (YYYYMM) the station appears; flags stations that opened or closed during the study |

## `crz_boundary`

Congestion relief zone boundary (Manhattan at/below 60th St, excluding FDR Drive and West Side Highway). Source: MTA Central Business District Geofence, data.ny.gov (dataset `srxy-5nxn`), downloaded 10/12/26. Stored as GeoJSON text; converted with `ST_GEOGFROMGEOJSON` in SQL.

| Column | Type | Description |
|---|---|---|
| geojson | STRING | Zone polygon geometry as GeoJSON text |

## `zone_stations`

Every station labeled inside or outside the congestion relief zone. Built by `sql/03_zone_stations.sql` using BigQuery GIS (`ST_CONTAINS`, `ST_DWITHIN`). **Rows:** 2,499 — 427 inside the official boundary, 441 with the 50 m rule.

**Why a 50 m rule:** the official boundary cuts out the FDR Drive and West Side Highway (not tolled), so riverside stations in lower Manhattan (e.g. West St & Chambers St, South St & Gouverneur Ln) fall just outside it, as do stations on 60th Street itself (which the law includes). All 14 such stations sit 2–44 m from the boundary; the nearest station truly north of 60th St (E 61 St & Madison Ave) is 55 m away. A 50 m buffer captures the first group and excludes the second. The strict label is kept for robustness checks.

| Column | Type | Description |
|---|---|---|
| station_id | STRING | Station ID |
| station_name | STRING | Station name |
| lat, lng | FLOAT | Station coordinates |
| in_zone_strict | BOOL | TRUE if inside the official zone polygon |
| in_zone | BOOL | TRUE if inside the zone or within 50 m of it (**main analysis label**) |
| meters_from_zone | FLOAT | Distance to the zone boundary in meters (0 if inside) |

Note: some stations appear under two IDs after being renumbered (e.g. 3 Ave & E 62 St: 6762.04 and 6830.04).

## `daily_rides`

TODO

## `station_daily`

TODO
