# Did Congestion Pricing Push New Yorkers onto Bikes?

> 🚧 In progress

On January 5, 2025, New York City began charging most vehicles a toll to enter Manhattan at or below 60th Street, the first congestion pricing program in the U.S. This project measures whether the toll changed how people use Citi Bike, using two years of ride records (2024 vs. 2025), NOAA weather data, and a geographic definition of the toll zone.

## Questions

1. **Did Citi Bike trips into the toll zone increase after tolling began**, beyond what weather, season, and overall system growth explain?
2. **Who changed?** Members vs. casual riders, e-bikes vs. classic bikes, weekdays vs. weekends, rush hour vs. off-peak.
3. **Where?** Which zone stations gained the most arrivals, and are they now filling up at rush hour?
4. **How big is the effect?** Forecast what ridership would have been without the toll and compare it to what actually happened.

## Approach

| Step | Method |
|---|---|
| Define the toll zone | Point-in-polygon test (BigQuery GIS) labels each station inside/outside the zone |
| Group trips | Into the zone, out of the zone, within the zone, and outside-only (comparison group) |
| Main estimate | **Difference-in-differences**: change in into-zone trips (2024 → 2025) minus change in outside-only trips. The comparison group absorbs system-wide growth, pricing changes, and economic conditions |
| Controls | Regression with temperature, precipitation, snow, weekends, holidays |
| Counterfactual | Train a forecast on 2024 only, predict 2025, compare to actual |

### Known limitations (to discuss in the write-up)

- Citi Bike kept adding stations and e-bikes during 2024-2025, so system growth isn't the same everywhere.
- Trips "outside" the zone could also be affected (spillover), which would make the estimate conservative.
- Other 2025 changes (transit, return-to-office policies) could overlap with the toll's start date.

## Tech stack

| Step | Tools |
|---|---|
| Ingestion & storage | Python, Google BigQuery |
| Cleaning & modeling | SQL (BigQuery), BigQuery GIS |
| Statistics | R (difference-in-differences regression), SAS |
| Forecasting | Python (Prophet, XGBoost) |
| Dashboard | Tableau Public |
| Automation | GitHub Actions |

## Repo structure

```
src/          Python pipeline: download, load to BigQuery, run SQL
sql/          BigQuery SQL, run in order (01_, 02_, ...)
notebooks/    Python analysis and forecasting
r/            R statistical analysis
sas/          SAS version of the regression
dashboards/   Tableau workbook and screenshots
reports/      Final write-up
docs/         Setup guide and data dictionary
```

## How to run

First-time setup: see [docs/SETUP_BIGQUERY.md](docs/SETUP_BIGQUERY.md).

```bash
python src/download_trips.py     # trip files -> data/raw/trips/
python src/download_weather.py   # NOAA weather -> data/raw/weather/
python src/load_to_bigquery.py   # load everything into BigQuery
python src/run_sql.py            # build cleaned and summary tables
```

Months are set by `START_MONTH` / `END_MONTH` in `.env`. The full study window is 2024-01 to 2025-12.

## Progress

- [ ] **Phase 1: Pipeline test.** Load Dec 2024 - Feb 2025 (3 months around the toll start), confirm `trips_clean` works
- [ ] **Phase 2: Full data.** Widen to 2024-01 - 2025-12; build `stations`; start the data dictionary
- [ ] **Phase 3: Toll zone (GIS).** Get the zone boundary as GeoJSON (search data.ny.gov for the MTA's Central Business District geofence; or draw Manhattan below 60th St at geojson.io and document that), save to `data/raw/zone/`, run `python src/load_to_bigquery.py zone`, build `zone_stations`
- [ ] **Phase 4: Analysis tables.** `daily_rides` by trip group; `station_daily`; first 2024 vs. 2025 comparison
- [ ] **Phase 5: Statistics (R).** Difference-in-differences regression with weather and calendar controls; check pre-toll trends are parallel; repeat main model in SAS
- [ ] **Phase 6: Counterfactual forecast (Python).** Train on 2024, predict 2025, measure the gap; report forecast accuracy on held-out 2024 months
- [ ] **Phase 7: Dashboard.** Tableau Public: zone map with station changes, into-zone vs. outside trends, forecast vs. actual
- [ ] **Phase 8: Write-up.** Policy-style summary (1 page) + technical appendix; GitHub Action for monthly refresh

## Key findings

_Coming soon._

## Data

- Citi Bike System Data: <https://citibikenyc.com/system-data>
- NOAA daily summaries, Central Park (USW00094728)
- Congestion relief zone boundary: TBD (Phase 3)

Full column definitions: [docs/data_dictionary.md](docs/data_dictionary.md)
