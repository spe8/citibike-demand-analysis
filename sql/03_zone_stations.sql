CREATE OR REPLACE TABLE `{project}.{dataset}.zone_stations` AS
WITH zone AS (
  SELECT ST_UNION_AGG(ST_GEOGFROMGEOJSON(geojson, make_valid => TRUE)) AS geom
  FROM `{project}.{dataset}.crz_boundary`
)
SELECT
  s.station_id,
  s.station_name,
  s.lat,
  s.lng,
  ST_CONTAINS(z.geom, ST_GEOGPOINT(s.lng, s.lat)) AS in_zone_strict,
  ST_DWITHIN(z.geom, ST_GEOGPOINT(s.lng, s.lat), 50) AS in_zone,
  ROUND(ST_DISTANCE(z.geom, ST_GEOGPOINT(s.lng, s.lat))) AS meters_from_zone
FROM `{project}.{dataset}.stations` AS s, zone AS z;
