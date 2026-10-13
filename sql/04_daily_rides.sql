CREATE OR REPLACE TABLE `{project}.{dataset}.daily_rides` AS
WITH daily AS (
  SELECT
    t.ride_date,
    CASE
      WHEN NOT zs_start.in_zone AND zs_end.in_zone THEN 'into_zone'
      WHEN zs_start.in_zone AND NOT zs_end.in_zone THEN 'out_of_zone'
      WHEN zs_start.in_zone AND zs_end.in_zone THEN 'within_zone'
      ELSE 'outside'
    END AS trip_group,
    COUNT(*) AS rides,
    COUNTIF(t.member_casual = 'member') AS member_rides,
    COUNTIF(t.member_casual = 'casual') AS casual_rides,
    COUNTIF(t.rideable_type = 'electric_bike') AS ebike_rides,
    ROUND(AVG(t.duration_min), 2) AS avg_duration_min
  FROM `{project}.{dataset}.trips_clean` AS t
  JOIN `{project}.{dataset}.zone_stations` AS zs_start
    ON t.start_station_id = zs_start.station_id
  JOIN `{project}.{dataset}.zone_stations` AS zs_end
    ON t.end_station_id = zs_end.station_id
  GROUP BY ride_date, trip_group
)
SELECT
  d.*,
  d.ride_date >= DATE '2025-01-05' AS is_post_toll,
  EXTRACT(DAYOFWEEK FROM d.ride_date) IN (1, 7) AS is_weekend,
  w.tmax_f,
  w.tmin_f,
  w.precip_in,
  w.snow_in,
  w.avg_wind_mph
FROM daily AS d
LEFT JOIN `{project}.{dataset}.weather_daily` AS w
  ON w.date = d.ride_date;