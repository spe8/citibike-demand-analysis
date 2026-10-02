"""Run the SQL files in sql/ in order (01_, 02_, ...) against BigQuery.

{project} and {dataset} in each file are filled in from .env.
Files that are still only comments (not written yet) are skipped.

Usage:
    python src/run_sql.py                 # run every file
    python src/run_sql.py 02_daily_rides  # run files whose name contains this text
"""
import sys

from google.cloud import bigquery

from config import DATASET, LOCATION, SQL_DIR, require_project_id


def has_sql(text: str) -> bool:
    lines = [l.strip() for l in text.splitlines()]
    return any(l and not l.startswith("--") for l in lines)


def main() -> None:
    project = require_project_id()
    client = bigquery.Client(project=project, location=LOCATION)
    match = sys.argv[1] if len(sys.argv) > 1 else ""

    for path in sorted(SQL_DIR.glob("*.sql")):
        if match not in path.stem:
            continue
        text = path.read_text()
        if not has_sql(text):
            print(f"{path.name}: skipped (not written yet)")
            continue
        query = text.replace("{project}", project).replace("{dataset}", DATASET)
        job = client.query(query)
        job.result()
        gb = (job.total_bytes_processed or 0) / 1e9
        print(f"{path.name}: done ({gb:.2f} GB scanned)")


if __name__ == "__main__":
    main()
