-- 02_stations.sql
-- One row per station across 2024-2025: most recent name, ride-weighted
-- average coordinates, total trip endpoints, and first/last month seen.

CREATE OR REPLACE TABLE `{project}.{dataset}.stations` AS
SELECT
  station_id,
  ARRAY_AGG(station_name ORDER BY _TABLE_SUFFIX DESC LIMIT 1)[OFFSET(0)] AS station_name,
  SUM(lat * trip_endpoints) / SUM(trip_endpoints) AS lat,
  SUM(lng * trip_endpoints) / SUM(trip_endpoints) AS lng,
  SUM(trip_endpoints)  AS trip_endpoints,
  MIN(_TABLE_SUFFIX)   AS first_month,
  MAX(_TABLE_SUFFIX)   AS last_month
FROM `{project}.{dataset}.raw_stations_*`
GROUP BY station_id;