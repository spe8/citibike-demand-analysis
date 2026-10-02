# Citi Bike Demand Analysis: Weather, Forecasting & Station Rebalancing

> 🚧 In progress

An end-to-end analysis of New York City's Citi Bike system using tens of millions of ride records and NOAA weather data.

## Questions

1. **What drives ridership?** How much do temperature, rain, weekends and holidays change daily rides?
2. **Can we forecast demand?** How accurately can we predict daily ridership 30 days ahead?
3. **Where does the system fall out of balance?** Which stations run out of bikes or overflow, and when?

## Tech stack

| Step | Tools |
|---|---|
| Ingestion & storage | Python, Google BigQuery |
| Cleaning & modeling | SQL (BigQuery) |
| Statistics | R (regression, hypothesis tests), SAS |
| Forecasting | Python (Prophet, XGBoost) |
| Spatial analysis | geopandas |
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
python src/load_to_bigquery.py   # load both into BigQuery
python src/run_sql.py            # build cleaned and summary tables
```

Months are set by `START_MONTH` / `END_MONTH` in `.env`.

## Progress

- [ ] **Phase 1: Data pipeline.** Download 3 months, load to BigQuery, build `trips_clean`
- [ ] **Phase 2: SQL modeling.** `daily_rides`, `stations`, `station_daily`; fill in data dictionary
- [ ] **Phase 3: Statistics.** Regression of daily rides on weather and calendar (R); one hypothesis test; repeat regression in SAS
- [ ] **Phase 4: Forecasting.** Baseline vs. Prophet vs. XGBoost; report MAPE on held-out months
- [ ] **Phase 5: Spatial.** Join stations to NYC neighborhoods with geopandas
- [ ] **Phase 6: Dashboard.** Tableau Public: station map, weather effect, forecast vs. actual
- [ ] **Phase 7: Polish.** Scale to 12 months, GitHub Action for monthly refresh, final report

## Key findings

_Coming soon._

## Data

- Citi Bike System Data: <https://citibikenyc.com/system-data>
- NOAA Global Historical Climatology Network daily summaries, Central Park (USW00094728)

Full column definitions: [docs/data_dictionary.md](docs/data_dictionary.md)
