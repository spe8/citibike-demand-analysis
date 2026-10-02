-- 01_trips_clean.sql
-- Combines every monthly raw table into one cleaned trips table.
-- This one is written for you as a worked example. Read through it, then
-- write 02-04 yourself using the same patterns.
--
-- Cleaning rules (document these in docs/data_dictionary.md):
--   1. Remove duplicate ride_ids (keep the first one).
--   2. Remove rides missing a start/end time or a start/end station.
--   3. Remove rides under 1 minute (false starts, re-docks) or over 24 hours (lost/stolen bikes).
--   4. Keep only member / casual rider types.

CREATE OR REPLACE TABLE `{project}.{dataset}.trips_clean` AS

WITH all_months AS (
  -- The * wildcard reads raw_trips_202501, raw_trips_202502, ... as one table
  SELECT * FROM `{project}.{dataset}.raw_trips_*`
),

deduped AS (
  SELECT *
  FROM all_months
  WHERE TRUE  -- BigQuery requires a WHERE (or GROUP BY/HAVING) before QUALIFY
  QUALIFY ROW_NUMBER() OVER (PARTITION BY ride_id ORDER BY started_at) = 1
)

SELECT
  ride_id,
  rideable_type,
  member_casual,
  started_at,
  ended_at,
  DATE(started_at)                                   AS ride_date,
  EXTRACT(HOUR FROM started_at)                      AS start_hour,
  FORMAT_DATE('%A', DATE(started_at))                AS day_of_week,
  ROUND(DATETIME_DIFF(ended_at, started_at, SECOND) / 60.0, 2) AS duration_min,
  start_station_id,
  start_station_name,
  end_station_id,
  end_station_name,
  start_lat,
  start_lng,
  end_lat,
  end_lng
FROM deduped
WHERE started_at IS NOT NULL
  AND ended_at IS NOT NULL
  AND start_station_id IS NOT NULL
  AND end_station_id IS NOT NULL
  AND DATETIME_DIFF(ended_at, started_at, SECOND) BETWEEN 60 AND 86400
  AND member_casual IN ('member', 'casual');
