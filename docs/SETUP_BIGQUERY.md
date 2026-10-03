# BigQuery setup (about 15 minutes, no credit card)

## 1. Create a Google Cloud project

1. Go to <https://console.cloud.google.com> and sign in with any Google account.
2. Accept the terms if asked. At the top of the page, click the project picker, then **New Project**.
3. Name it `citibike-analysis`. Google gives it a **Project ID** (e.g. `citibike-analysis-471203`). Copy the ID, not the name.

## 2. Turn on BigQuery

1. In the console search bar, type **BigQuery** and open it.
2. You'll see a **Sandbox** banner. That's the free mode: no card needed.

Sandbox limits, and how this project handles them:

| Limit | What it means here |
|---|---|
| 10 GB storage | Two years of trips fits (about 5-6 GB) because the raw tables keep only the columns we need and `trips_clean` is a view, not a copy. |
| 1 TB of queries per month | Plenty. `run_sql.py` prints GB scanned per query so you can track it. |
| Tables expire after 60 days | The pipeline is re-runnable: just run it again. To remove this, add a billing account later (you stay in the free tier and aren't charged under the limits). |
| No DELETE / UPDATE / INSERT | That's why each month loads into its own table and SQL uses `CREATE OR REPLACE TABLE`. |

## 3. Install the Google Cloud CLI on your Mac

In Terminal:

```bash
# Download the macOS installer from https://cloud.google.com/sdk/docs/install
# (Apple Silicon for M1-M4 Macs, x86_64 for Intel), then:
cd ~/Downloads
tar -xf google-cloud-cli-*.tar.gz
./google-cloud-sdk/install.sh
```

Say yes to updating your PATH, then close and reopen Terminal. (With Homebrew: `brew install --cask google-cloud-sdk`.)

## 4. Log in so Python can use your account

```bash
gcloud auth login
gcloud config set project YOUR_PROJECT_ID
gcloud auth application-default login
gcloud auth application-default set-quota-project YOUR_PROJECT_ID
```

Each `login` command opens a browser window. Approve it.

## 5. Set up Python

From the repo folder:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

(Or with conda: `conda create -n citibike python=3.11 -y`, `conda activate citibike`, then the same `pip install`.)

## 6. Fill in your settings

```bash
cp .env.example .env
```

Open `.env` and set `GCP_PROJECT_ID` to your project ID.

## 7. Test it

```bash
python src/check_connection.py
```

You should see `BigQuery is connected!`. If you get a permissions or quota-project error, re-run the commands in step 4.
