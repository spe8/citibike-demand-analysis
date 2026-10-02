"""Quick test that Python can talk to your BigQuery project."""
from google.cloud import bigquery

from config import LOCATION, require_project_id

project = require_project_id()
client = bigquery.Client(project=project, location=LOCATION)
result = list(client.query("SELECT 'BigQuery is connected!' AS msg").result())
print(result[0].msg)
print("Datasets in project:", [d.dataset_id for d in client.list_datasets()] or "(none yet)")
