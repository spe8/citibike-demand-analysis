# Did Congestion Pricing Push New Yorkers onto Bikes?

> **In progress.** Data pipeline, GIS zone labeling, and initial analysis complete. Regression in R and Tableau dashboard in progress.

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
| Statistics | R (difference-in-differences regression), SAS *(in progress)* |
| Forecasting | Python (Prophet, XGBoost) *(planned)* |
| Dashboard | Tableau Public *(planned)* |
| Automation | GitHub Actions *(planned)* |

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

- [x] **Phase 1: Pipeline test.** Load Dec 2024 - Feb 2025 (3 months around the toll start), confirm `trips_clean` works
- [x] **Phase 2: Full data.** Widen to 2024-01 - 2025-12; build `stations`; start the data dictionary
- [x] **Phase 3: Toll zone (GIS).** Get the zone boundary as GeoJSON (search data.ny.gov for the MTA's Central Business District geofence; or draw Manhattan below 60th St at geojson.io and document that), save to `data/raw/zone/`, run `python src/load_to_bigquery.py zone`, build `zone_stations`
- [x] **Phase 4: Analysis tables.** `daily_rides` by trip group; `station_daily`; first 2024 vs. 2025 comparison
- [ ] **Phase 5: Statistics (R).** Difference-in-differences regression with weather and calendar controls; check pre-toll trends are parallel; repeat main model in SAS
- [ ] **Phase 6: Counterfactual forecast (Python).** Train on 2024, predict 2025, measure the gap; report forecast accuracy on held-out 2024 months
- [ ] **Phase 7: Dashboard.** Tableau Public: zone map with station changes, into-zone vs. outside trends, forecast vs. actual
- [ ] **Phase 8: Write-up.** Policy-style summary (1 page) + technical appendix; GitHub Action for monthly refresh

## Key findings

**Data:** 90M+ Citi Bike trips (Jan 2024 – Dec 2025), 2,499 stations, NOAA daily weather. 285K invalid trips (0.3%) removed in cleaning; see the [data dictionary](docs/data_dictionary.md).

**Toll zone:** 441 stations labeled inside the congestion relief zone using BigQuery GIS, with a documented 50 m rule for stations along the excluded FDR Drive / West Side Highway and on 60th Street.

**Initial results (preliminary):**

| Comparison (2024 → 2025) | Into zone | Outside (comparison) | Gap |
|---|---|---|---|
| Jan–Jun, all stations | +2.7% | +7.9% | −5.2 pts |
| Jan–Jun, stations open all 24 months | +0.2% | +5.3% | −5.1 pts |
| Full year, all stations | +1.7% | +3.1% | −1.4 pts |

- Station expansion does **not** explain the gap. It holds when restricted to stations that existed throughout.
- Trips into the zone are strongly seasonal (≈11 per 100 outside trips in winter vs. ≈15 in summer), and the gap is concentrated in **Jan–Feb 2025**, which were ~5°F colder and snowier than Jan–Feb 2024. Jul–Sep 2025 were *above* 2024.
- **So far, there is no clear sustained increase in bike trips into the zone after tolling began.** Next step: a difference-in-differences regression with weather and calendar controls to test this formally.

Full notes: [reports/findings_log.md](reports/findings_log.md)

## Data

- Citi Bike System Data: <https://citibikenyc.com/system-data>
- NOAA daily summaries, Central Park (USW00094728)
- Congestion relief zone boundary: MTA Central Business District Geofence, data.ny.gov (dataset `srxy-5nxn`)

Full column definitions: [docs/data_dictionary.md](docs/data_dictionary.md)
