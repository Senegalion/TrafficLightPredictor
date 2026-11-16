# Architecture

## Overview

The MVP is a small modular system: one Java backend, one Python ML service, one static frontend and
PostgreSQL/PostGIS. There is no message broker and no microservice mesh. The only reason for a
second backend process is that the models are scikit-learn objects, which the JVM cannot load.

```mermaid
flowchart TB
    subgraph Browser
        UI[React SPA]
    end
    subgraph frontend [frontend container]
        NGINX[nginx<br/>static files + /api proxy]
    end
    subgraph backend [backend container - Spring Boot]
        IC[IntersectionController] --> IS[IntersectionService]
        OC[ObservationController] --> OS[ObservationService]
        PC[PredictionController] --> PS[PredictionService]
        PS --> IS
        PS --> OS
        PS --> MLC[MlPredictionClient<br/>RestClient]
        IS & OS & PS --> REPO[Spring Data JPA repositories]
    end
    subgraph ml [ml-service container - FastAPI]
        API[/v1/predictions/] --> PRED[Predictor]
        PRED --> BUNDLE[(model.joblib<br/>+ duration stats<br/>+ reliability policy)]
    end
    subgraph sim [simulator container]
        FEED[SimulatedObserver + BackendClient]
    end
    DB[(PostgreSQL + PostGIS)]

    UI --> NGINX --> IC & OC & PC
    REPO --> DB
    MLC -- HTTP JSON --> API
    FEED -- POST observations<br/>X-Api-Key, simulated=true --> OC
```

## Prediction flow

```mermaid
sequenceDiagram
    participant UI
    participant BE as Backend
    participant DB as PostgreSQL
    participant ML as ML service
    UI->>BE: POST /api/v1/predictions {intersectionId, signalId}
    BE->>DB: signal belongs to intersection?
    alt not found
        BE-->>UI: 404 problem+json
    end
    BE->>DB: latest observation of signal at or before target time
    alt none, or older than 15 min
        BE->>DB: store prediction (INSUFFICIENT_DATA)
        BE-->>UI: 201 {status: INSUFFICIENT_DATA, displayable: false}
    else fresh observation
        BE->>ML: POST /v1/predictions {signal_code, target_time, anchor}
        alt ML unreachable / error
            BE->>DB: store prediction (MODEL_UNAVAILABLE)
        else
            ML-->>BE: phase, probabilities, remaining time + interval, status
            BE->>DB: store prediction (OK / LOW_CONFIDENCE / UNSUPPORTED_SIGNAL)
        end
        BE-->>UI: 201 PredictionResponse (+ data origin + disclaimer)
    end
```

## Backend module structure

Packages are organised **by feature**, not by layer:

| Package | Contents |
|---|---|
| `intersection` | `Intersection`, `TrafficSignal` entities, repositories (incl. native PostGIS `findNearby`), service, controller, DTOs |
| `observation` | `Observation` entity, repository (anchor lookup, paging), service (validation rules), controller, DTOs |
| `prediction` | `PredictionRecord` entity, service (data-sufficiency rules and orchestration), controllers, DTOs |
| `prediction.ml` | `MlPredictionClient` port, HTTP adapter, request/response contracts, configuration |
| `common` | Problem-detail exception handler, API-key interceptor, CORS, OpenAPI config, shared enums |

## Database

Managed by Flyway (`backend/src/main/resources/db/migration`). Hibernate only validates the schema.

```mermaid
erDiagram
    intersections ||--o{ traffic_signals : has
    traffic_signals ||--o{ observations : "observed in"
    traffic_signals ||--o{ predictions : "predicted for"
    observations |o--o{ predictions : "anchor of"
    intersections {
        bigint id PK
        varchar code UK
        varchar name
        double latitude
        double longitude
        geography location "generated, GiST index"
        varchar location_source "OPENSTREETMAP | SAMPLE"
    }
    traffic_signals {
        bigint id PK
        bigint intersection_id FK
        varchar code UK
        varchar configuration_source "SAMPLE | VERIFIED"
    }
    observations {
        bigint id PK
        bigint intersection_id
        bigint signal_id
        timestamptz observed_at
        varchar phase
        int phase_duration_seconds "1..300, nullable"
        varchar direction
        varchar source
        boolean simulated
    }
    predictions {
        uuid id PK
        varchar status
        boolean displayable
        varchar predicted_phase
        double confidence
        double remaining_seconds
        varchar data_origin "REAL | SIMULATED | NONE"
    }
```

Integrity is enforced in the database, not only in Java:

- a composite foreign key `(signal_id, intersection_id)` guarantees that an observation or
  prediction refers to a signal of *that* intersection;
- `UNIQUE (signal_id, observed_at)` prevents duplicate observations;
- `CHECK` constraints restrict phases, directions, statuses, probabilities and durations;
- `location` is a stored generated `geography(Point, 4326)` column, so it always matches lat/lon.

## Key design decisions

| Decision | Rationale |
|---|---|
| Separate Python ML service instead of exporting the model to the JVM | Keeps one ML codebase (training and serving share feature code, avoiding training/serving skew). ONNX/PMML export of the full pipeline (calibration, conformal margin, history statistics) would add complexity. |
| Backend owns data-sufficiency rules; ML service repeats them | The backend avoids a network call when there is no usable observation. The ML service stays safe to call directly. |
| Store every prediction | Traceability, and the basis for evaluating predictions against real observations later. |
| `simulated` is a required input field | Every record must be explicitly labelled real or simulated; there is no default. |
| Observation = "phase started at time t" (+ optional duration) | Matches what a human or camera can record, and lets labels be derived from real data in the same way as from synthetic data. |
| Shared API key for ingestion, no Spring Security | There are no user accounts. A full security setup would add complexity without benefit at this stage. |
| No ML health dependency for backend readiness | The backend degrades gracefully (`MODEL_UNAVAILABLE`) instead of going down with the ML service. |
| Multi-arch PostGIS image (`imresamu/postgis`) by default | The official `postgis/postgis` image is amd64-only. The image is configurable via `POSTGIS_IMAGE`. |

## Observability

- Health: `GET /actuator/health` (readiness and liveness probes enabled) for the backend,
  `GET /health` for the ML service (reports `DEGRADED` if no model is loaded). Docker health checks
  use both.
- Logs: the backend logs ECS JSON in Docker (`LOGGING_STRUCTURED_FORMAT_CONSOLE=ecs`). The Python
  services log JSON lines (`TLP_LOG_FORMAT=json`, or `text` for local use).
