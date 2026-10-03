-- 01_trips_clean.sql
-- Combines every monthly raw table into one cleaned view of trips.
-- This one is written for you as a worked example. Read through it, then
-- write 02-05 yourself using the same patterns.
--
-- It's a VIEW, not a table: it stores no data (two years of trips would blow
-- past the free 10 GB), it just re-runs this query whenever you select from it.
-- The summary tables in 04 and 05 are small, so those are real tables.
--
-- Cleaning rules (document these in docs/data_dictionary.md):
--   1. Remove rides missing a start/end time or a start/end station.
--   2. Remove rides under 1 minute (false starts, re-docks) or over 24 hours (lost/stolen bikes).
--   3. Keep only member / casual rider types.

CREATE OR REPLACE VIEW `{project}.{dataset}.trips_clean` AS

SELECT
  started_at,
  ended_at,
  DATE(started_at)                                   AS ride_date,
  EXTRACT(HOUR FROM started_at)                      AS start_hour,
  FORMAT_DATE('%A', DATE(started_at))                AS day_of_week,
  ROUND(DATETIME_DIFF(ended_at, started_at, SECOND) / 60.0, 2) AS duration_min,
  start_station_id,
  end_station_id,
  rideable_type,
  member_casual,
  -- Congestion pricing started Sunday, January 5, 2025
  DATE(started_at) >= DATE '2025-01-05'              AS is_post_toll
FROM `{project}.{dataset}.raw_trips_*`   -- the * reads every raw_trips_YYYYMM table as one
WHERE started_at IS NOT NULL
  AND ended_at IS NOT NULL
  AND start_station_id IS NOT NULL
  AND end_station_id IS NOT NULL
  AND DATETIME_DIFF(ended_at, started_at, SECOND) BETWEEN 60 AND 86400
  AND member_casual IN ('member', 'casual');
