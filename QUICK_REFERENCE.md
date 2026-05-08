# Full Run Guide - Docker-Only Workflow

This is the only guide you need to run the full program end to end.
All services run inside Docker:
- ZooKeeper
- Kafka
- InfluxDB
- Grafana
- Python producer
- Spark processing job
- Next.js frontend

## 1) What you need installed

Only install these on your Windows machine:
- Docker Desktop
- Git or a way to open the project folder

Do not install Python, Node.js, or Java locally for normal use. They run inside containers.

## 2) Open the project

```powershell
cd d:\calculation_engine_erp
```

## 3) Check the environment file

Make sure `.env` exists in the project root and contains values like these:

```powershell
INFLUX_URL=http://influxdb:8086
INFLUX_ORG=ukshati
INFLUX_BUCKET=energy
INFLUX_TOKEN=my_super_secret_token_123456789
KAFKA_BOOTSTRAP_SERVERS=kafka:9092
KAFKA_TOPIC=energy-meter
PRODUCER_INTERVAL=1
```

Important:
- Use service names like `influxdb` and `kafka` inside Docker, not `localhost`.
- If you change the token, update both `.env` and the InfluxDB admin token in `docker-compose.yml`.

## 4) If image pulls are slow, pull one by one

If `docker compose up --build` fails with a TLS timeout, run these individually:

```powershell
docker pull confluentinc/cp-zookeeper:7.5.0
docker pull confluentinc/cp-kafka:7.5.0
docker pull influxdb:2.7.0
docker pull grafana/grafana:10.2.0
```

If Grafana times out once, run just this again:

```powershell
docker pull grafana/grafana:10.2.0
```

Docker will resume from cached layers.

## 5) Start the full stack

```powershell
docker compose up --build -d
```

What this starts:
- `zookeeper`
- `kafka`
- `influxdb`
- `grafana`
- `producer`
- `spark`
- `frontend`

## 6) Verify everything is running

```powershell
docker compose ps
```

Expected result:
- Zookeeper healthy
- Kafka healthy
- InfluxDB healthy
- Grafana healthy
- Producer running
- Spark running
- Frontend healthy

## 7) Open the apps

- Grafana: http://localhost:3000
- InfluxDB UI: http://localhost:8086
- Next.js frontend: http://localhost:3001

Note:
- Grafana uses port 3000 on the host.
- The frontend is mapped to 3001 so it does not conflict with Grafana.

## 8) Watch logs

Use these if something looks wrong:

```powershell
docker compose logs -f zookeeper
docker compose logs -f kafka
docker compose logs -f influxdb
docker compose logs -f grafana
docker compose logs -f producer
docker compose logs -f spark
docker compose logs -f frontend
```

## 9) Data flow

```text
Producer -> Kafka -> Spark -> InfluxDB -> Grafana -> Next.js frontend
```

## 10) How to change formulas or alerts

Edit `config.yaml`.

Examples:

```yaml
calculations:
  imbalance:
    formula: "abs(I_R - I_Y) / ((I_R + I_Y + I_B) / 3) * 100"
```

```yaml
alerts:
  imbalance:
    alert: 5
    warning: 10
    alarm: 20
```

Then rebuild the affected containers:

```powershell
docker compose up -d --build spark producer
```

If you changed frontend code:

```powershell
docker compose up -d --build frontend
```

## 11) How to restart cleanly

```powershell
docker compose restart
```

If you need a full rebuild:

```powershell
docker compose down
docker compose up --build -d
```

If you want to remove volumes too:

```powershell
docker compose down -v
docker compose up --build -d
```

## 12) Common checks

Kafka:
```powershell
docker compose logs -f kafka
```

Spark:
```powershell
docker compose logs -f spark
```

Producer:
```powershell
docker compose logs -f producer
```

Frontend:
```powershell
docker compose logs -f frontend
```

## 13) Stop everything

```powershell
docker compose down
```

## 14) One-line recovery order

If you just want the shortest working path:

```powershell
cd d:\calculation_engine_erp
docker pull confluentinc/cp-zookeeper:7.5.0
docker pull confluentinc/cp-kafka:7.5.0
docker pull influxdb:2.7.0
docker pull grafana/grafana:10.2.0
docker compose up --build -d
docker compose ps
```
