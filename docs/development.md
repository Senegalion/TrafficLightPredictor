# Development guide

## Prerequisites

| Tool | Version | Needed for |
|---|---|---|
| Docker + Compose v2 | recent | Full stack; backend tests (Testcontainers) |
| JDK | 21+ (tested with 21 in Docker and 25 locally) | Backend |
| Maven | 3.9+ | Backend |
| Python | 3.12+ | ML |
| Node.js | 22+ (24 used) | Frontend |

## Repository layout

```text
.
├── backend/                 Spring Boot API (Maven)
│   ├── src/main/java/io/github/senegalion/tlp/{intersection,observation,prediction,common}
│   ├── src/main/resources/db/migration/   Flyway migrations (schema + sample seed)
│   └── src/test/java/...    unit, slice (MockMvc), repository and integration tests
├── ml/                      Python package `tlp_ml` (pipeline, FastAPI service, simulator)
│   ├── src/tlp_ml/
│   ├── tests/
│   └── reports/             EDA and evaluation reports (committed)
├── frontend/                React + TypeScript + Vite SPA, nginx config
├── research/osm/            OpenStreetMap feasibility scripts (research history)
├── docs/                    Architecture, ML, data, API and this guide
├── docker-compose.yml       Full local stack
├── .env.example             Local configuration template
├── Makefile                 Convenience targets
└── .github/workflows/ci.yml CI: backend, ML, frontend, Docker build
```

Generated and ignored: `ml/artifacts/`, `ml/data/`, `data/` (OSM downloads), `frontend/dist/`,
`node_modules/`, `.env`.

## Configuration

Backend (`backend/src/main/resources/application.yml`, all overridable by environment):

| Variable | Default | Purpose |
|---|---|---|
| `TLP_DB_URL` | `jdbc:postgresql://localhost:5432/traffic_light_predictor` | JDBC URL |
| `TLP_DB_USER` / `TLP_DB_PASSWORD` | `tlp` / *(empty)* | DB credentials |
| `TLP_ML_BASE_URL` | `http://localhost:8000` | ML service |
| `TLP_INGEST_API_KEY` | *(empty: ingestion open, a warning is logged)* | Key for `POST .../observations` |
| `TLP_CORS_ALLOWED_ORIGINS` | `http://localhost:5173` | Browser origins |
| `LOGGING_STRUCTURED_FORMAT_CONSOLE` | *(unset)* | `ecs` for JSON logs |

Further tunables under `tlp.*`: `tlp.predictions.max-anchor-age` (PT15M, keep in sync with the ML
policy), `max-future-target`, `max-past-target`, `tlp.observations.max-clock-skew`,
`tlp.ml.connect-timeout` and `read-timeout`.

ML: `TLP_ML_ARTIFACTS_DIR`, `TLP_ML_HOST`, `TLP_ML_PORT`, `TLP_LOG_FORMAT` (`json`|`text`),
`TLP_LOG_LEVEL`. Feed: `TLP_BACKEND_URL`, `TLP_INGEST_API_KEY`, `TLP_FEED_BACKFILL_MINUTES`.

Compose reads `.env` (copy from `.env.example`). It fails fast if required variables are missing.
No secrets are committed.

## Running parts locally

```bash
cp .env.example .env
docker compose up -d db                       # PostGIS on localhost:5433

# ML
make ml-train                                 # venv + synthetic data + EDA + model
ml/.venv/bin/tlp-ml serve                     # :8000

# Backend
cd backend
TLP_DB_URL=jdbc:postgresql://localhost:5433/traffic_light_predictor \
TLP_DB_PASSWORD=change-me-local-only TLP_INGEST_API_KEY=change-me-local-only \
  mvn spring-boot:run                         # :8080, Flyway migrates on start

# Simulated feed (optional, from repo root)
TLP_INGEST_API_KEY=change-me-local-only ml/.venv/bin/tlp-ml simulate-feed

# Frontend
cd frontend && npm install && npm run dev     # :5173, proxies /api to :8080
```

## Tests

```bash
make test-backend    # mvn verify: 46 tests (unit, MockMvc slices, PostGIS repository + integration via Testcontainers)
make test-ml         # ruff + pytest: 67 tests (validation, features, leakage guards, training, evaluation, API, feed)
make test-frontend   # vitest: 16 tests + production build
```

Backend tests need a running Docker daemon. The PostGIS test image is set in `pom.xml`
(`postgis.test.image`). Override it with `mvn verify -Dpostgis.test.image=postgis/postgis:17-3.5`
on x86 machines if preferred.

## Adding a real observation source

1. Create a collector that posts to `POST /api/v1/intersections/{id}/observations` with
   `simulated: false` and a descriptive `source`.
2. Disable the simulator: `docker compose up --scale simulator=0`, or remove the service.
3. Export observations to the ML CSV schema and retrain (see
   [ml-pipeline.md](ml-pipeline.md#10-using-real-data-later)).

## Adding an intersection

Add a Flyway migration (`V3__...sql`) inserting into `intersections` and `traffic_signals`. Mark
`location_source` and `configuration_source` honestly. A signal is only predictable once the model
has been trained with observations of its `code`. Until then predictions return
`UNSUPPORTED_SIGNAL`.

## Code style

- Java: feature packages, constructor injection, records for DTOs, problem details for errors, no
  Lombok.
- Python: `ruff check` and `ruff format` (line length 100), type hints, dataclasses.
- TypeScript: `strict` mode, function components, no global state library.
