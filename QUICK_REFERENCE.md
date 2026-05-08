# Quick Reference

## Prerequisites

- Docker Desktop installed and running

---

## 1) Edit `.env` and `docker-compose.yml`

Edit `.env` in the project root:

```

INFLUX_TOKEN=your_influxdb_token_here
```

Now create it in InfluxDB and paste it here later.

In `docker-compose.yml`, there's a token placeholder in the InfluxDB sections, you'll update it after creating the token.
---

## 2) Start the stack

```powershell
docker compose up --build 
```

---

## 3) Check if services are healthy

```powershell
docker compose ps
```

All services should show `healthy` or `running`. If not:

```powershell
docker compose down
docker compose up --build 
```

Then check again.
## 4) Create InfluxDB API token

Open InfluxDB UI: `http://localhost:8086`

Login (admin credentials from `docker-compose.yml`, default: `admin`/`adminpassword`).

Go: **Data** → **API Tokens** → **Generate API Token** → copy the token.

---

## 5) Paste the token

- Open `.env` and set: `INFLUX_TOKEN=your_token_here`
- In `docker-compose.yml`, also update it locally .

---

## 6) Restart services

```powershell
docker compose down
docker compose up
```

---

## 7) Configure Grafana and import dashboard

Open Grafana: `http://localhost:3000` (admin/admin123)

Add InfluxDB data source:
- Type: InfluxDB (Flux)
- URL: `http://influxdb:8086`
- Organization: `ukshati`
- Token: (paste your token)
- Default bucket: `energy`
- Click **Save & test**

Import dashboard:
- Go: **Dashboards** → **Import** → upload `grafana_dashboard.json` from repo root
- Select the InfluxDB data source and import

---

## 8) Open the dashboard

Frontend: `http://localhost:3001`  
Grafana: `http://localhost:3000`

---

## Useful commands

Check services:
```powershell
docker compose ps
```

Tail logs:
```powershell
docker compose logs -f grafana
docker compose logs -f influxdb
docker compose logs -f spark
docker compose logs -f producer
```

Stop everything:
```powershell
docker compose down
```