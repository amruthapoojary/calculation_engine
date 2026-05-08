# Grafana Setup Guide

This file explains how to set up Grafana for this project from start to finish.
Use this after the Docker stack is running.

If you want the full end-to-end run flow, also read [QUICK_REFERENCE.md](QUICK_REFERENCE.md).

## 1) What Grafana does in this project

Grafana reads data from InfluxDB and displays:
- Phase imbalance gauge
- Total power gauge
- Average current gauge
- Load percentage gauge
- Time-series charts
- Overall status panels

Grafana does not calculate the formulas. The formulas stay in `config.yaml` and are processed by Spark.

## 2) Start the Docker services

Open PowerShell in the project root:

```powershell
cd d:\calculation_engine_erp
docker compose up --build -d
docker compose ps
```

Expected services:
- `zookeeper`
- `kafka`
- `influxdb`
- `grafana`
- `producer`
- `spark`
- `frontend`

## 3) Open InfluxDB and create the bucket

Grafana needs a bucket in InfluxDB. This project uses the bucket name `energy`.

### Open InfluxDB

Go to:

```text
http://localhost:8086
```

### Sign in

Use the credentials from `docker-compose.yml`:
- Username: `admin`
- Password: `adminpassword`

### Create or verify the bucket

1. Click **Data** in the left menu.
2. Click **Buckets**.
3. Check whether the bucket `energy` already exists.
4. If it does not exist, click **Create Bucket**.
5. Set the bucket name to `energy`.
6. Keep the organization as `ukshati`.
7. Save the bucket.

Important:
- The bucket name in Grafana must match the bucket in InfluxDB.
- In this project, the expected bucket is `energy`.

## 4) Create an API token in InfluxDB

Grafana uses an InfluxDB token to read data.

### Create the token

1. In InfluxDB, click **Data**.
2. Click **API Tokens**.
3. Click **Generate API Token**.
4. Choose **All Access Token** if you want the simplest setup.
5. Give it a name such as `grafana-token`.
6. Save the token.
7. Copy the token value immediately.

### Put the token in `.env`

Open `.env` in the project root and update:

```powershell
INFLUX_TOKEN=your_new_token_here
```

If you change the token, restart the containers:

```powershell
docker compose up -d --build
```

## 5) Add the Grafana data source

Grafana is available here:

```text
http://localhost:3000
```

Default login:
- Username: `admin`
- Password: `admin123`

### Create the data source

1. Open Grafana.
2. Click **Connections**.
3. Click **Data sources**.
4. Click **Add new data source**.
5. Select **InfluxDB**.

### Configure the data source

Use these values:

```text
Name: InfluxDB
Query language: Flux
URL: http://influxdb:8086
Organization: ukshati
Token: <your InfluxDB token>
Default bucket: energy
```

Important:
- Inside Docker, the InfluxDB URL must be `http://influxdb:8086`.
- Do not use `localhost` in Grafana when Grafana is running inside Docker.
- Make sure query language is **Flux**.

### Save and test

1. Click **Save & test**.
2. If the test fails, re-check the token, bucket name, and URL.

## 6) Import the dashboard JSON file

This project includes a ready-made dashboard file:

```text
grafana_dashboard.json
```

### Import the file manually

1. In Grafana, click **Dashboards**.
2. Click **New** or **Import**.
3. Choose **Import dashboard**.
4. Upload `grafana_dashboard.json` from the project root.
5. Select the InfluxDB data source you created.
6. Click **Import**.

### If Grafana asks for a JSON file

Use the file from this path:

```text
d:\calculation_engine_erp\grafana_dashboard.json
```

## 7) What to expect after import

The dashboard should show:
- 4 gauge panels
- 2 time-series panels
- 1 overall status panel

If the dashboard says **No data**:
- Wait a minute for the producer and Spark to send records.
- Check `docker compose ps`.
- Check logs for `producer` and `spark`.

## 8) Check the data flow if nothing appears

Use these checks in order:

```powershell
docker compose ps
docker compose logs -f producer
docker compose logs -f spark
docker compose logs -f influxdb
docker compose logs -f grafana
```

What each one means:
- `producer` sends simulated motor readings.
- `spark` reads Kafka, calculates metrics, and writes to InfluxDB.
- `influxdb` stores the results.
- `grafana` reads from InfluxDB and draws the charts.

## 9) Where configuration lives

The important project files are:
- [config.yaml](config.yaml) for formulas, thresholds, and Grafana refresh settings
- [.env](.env) for tokens and service URLs
- [docker-compose.yml](docker-compose.yml) for container startup settings
- [grafana_dashboard.json](grafana_dashboard.json) for the dashboard import file

There is no `package.json` needed for Grafana itself.
The frontend has its own `package.json` under `frontend/`.

## 10) Common problems and fixes

### Grafana cannot connect to InfluxDB

Check:
- Data source URL is `http://influxdb:8086`
- Query language is `Flux`
- Token is correct
- Bucket is `energy`

### Dashboard imports but shows no data

Check:
- `producer` is running
- `spark` is running
- Kafka is healthy
- Wait 30 to 60 seconds for data to accumulate

### Bucket name mismatch

If your InfluxDB bucket is different from `energy`, update:
- `config.yaml`
- `.env`
- Grafana data source

## 11) Quick checklist

- Docker stack is running
- InfluxDB bucket exists
- InfluxDB API token is created
- Grafana data source is added
- Dashboard JSON is imported
- Producer and Spark are running
- Charts show data

## 12) Short version

If you only want the minimum steps:

```powershell
cd d:\calculation_engine_erp
docker compose up --build -d
```

Then do these in order:
- Open InfluxDB at `http://localhost:8086`
- Create or confirm bucket `energy`
- Generate an API token
- Open Grafana at `http://localhost:3000`
- Add the InfluxDB data source
- Import `grafana_dashboard.json`

