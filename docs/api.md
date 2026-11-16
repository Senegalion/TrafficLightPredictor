# REST API

Interactive documentation is at `http://localhost:8080/swagger-ui.html` and the OpenAPI JSON at
`/v3/api-docs`. Base path: `/api/v1`. All timestamps are ISO-8601 in UTC.

## Conventions

- Errors are [RFC 9457](https://www.rfc-editor.org/rfc/rfc9457) problem details
  (`application/problem+json`) with `title`, `status` and `detail`. Validation errors add an
  `errors` array of `{field, message}`.
- Status codes: `200` OK, `201` created (with `Location`), `400` invalid input or business rule,
  `401` missing or invalid ingestion key, `404` unknown resource, `409` duplicate or conflicting
  data, `503` ML service unavailable (`/model` only).
- CORS is allowed for origins in `TLP_CORS_ALLOWED_ORIGINS`.

## Intersections

### `GET /intersections`

```json
[
  {
    "id": 1, "code": "LDZ-KOS-STR", "name": "Al. Kościuszki / Struga", "city": "Łódź",
    "description": "...", "latitude": 51.765294, "longitude": 19.4543812,
    "locationSource": "OPENSTREETMAP",
    "osmReference": "traffic_signals nodes: 1537900461, 9588437613, 9588437614",
    "signals": [
      {"id": 5, "code": "LDZ-KOS-STR-S1", "name": "Main road signal group",
       "description": "...", "approach": "Al. Tadeusza Kościuszki", "configurationSource": "SAMPLE"}
    ]
  }
]
```

### `GET /intersections/{id}`

Returns one intersection, or `404`.

### `GET /intersections/nearby`

| Parameter | Required | Constraints |
|---|---|---|
| `latitude` | yes | −90..90 |
| `longitude` | yes | −180..180 |
| `radiusMeters` | no (1000) | 1..20000 |
| `limit` | no (10) | 1..50 |

Returns `[{"distanceMeters": 12.4, "intersection": {...}}]`, nearest first. Uses PostGIS
`ST_DWithin` and `ST_Distance` on a `geography` column.

## Observations

### `GET /intersections/{id}/observations`

Query: `signalId`, `from`, `to` (ISO-8601, inclusive), `page` (≥ 0), `size` (1..200, default 50).
Results are newest first.

```json
{
  "content": [
    {"id": 2415, "intersectionId": 1, "signalId": 5, "signalCode": "LDZ-KOS-STR-S1",
     "observedAt": "2026-11-16T10:47:14Z", "phase": "GREEN", "phaseDurationSeconds": 41,
     "direction": null, "source": "demo-simulator", "simulated": true}
  ],
  "page": 0, "size": 50, "totalElements": 208, "totalPages": 5
}
```

### `GET /intersections/{id}/observations/{observationId}`

### `POST /intersections/{id}/observations`

Header `X-Api-Key: <TLP_INGEST_API_KEY>` is required when a key is configured (always in Docker
Compose).

```json
{
  "signalId": 5,
  "observedAt": "2026-11-16T10:47:14Z",
  "phase": "GREEN",
  "phaseDurationSeconds": 41,
  "direction": "NORTHBOUND",
  "source": "manual-app",
  "simulated": false
}
```

| Field | Rules |
|---|---|
| `signalId` | required; must belong to the intersection in the path (else `404`) |
| `observedAt` | required; when the signal was seen **switching to** `phase`; at most 1 min in the future |
| `phase` | required; `RED`, `YELLOW`, `GREEN` |
| `phaseDurationSeconds` | optional; 1..300; only if the end of the phase was observed |
| `direction` | optional; `NORTHBOUND`, `SOUTHBOUND`, `EASTBOUND`, `WESTBOUND` |
| `source` | required; ≤ 64 chars |
| `simulated` | **required**; there is no default, so every record is explicitly labelled |

Responses: `201` with `Location`, `400`, `401`, `404`, or `409` if an observation of that signal
at that instant already exists.

## Predictions

### `POST /predictions`

```json
{"intersectionId": 5, "signalId": 9, "targetTime": "2026-11-16T11:00:00Z"}
```

`targetTime` is optional and defaults to now. It may be at most 2 min in the future and 7 days in
the past (past targets are useful for back-testing). The response is always `201` with a stored
prediction. The outcome is in `status`:

| `status` | Meaning | `displayable` |
|---|---|---|
| `OK` | Meets the reliability policy | `true` |
| `LOW_CONFIDENCE` | Model output exists but confidence < 0.80 or interval > 20 s; see `message` | `false` |
| `INSUFFICIENT_DATA` | No observation at or before `targetTime`, or the latest is > 15 min old | `false` |
| `UNSUPPORTED_SIGNAL` | The model was not trained for this signal | `false` |
| `MODEL_UNAVAILABLE` | ML service unreachable or returned an invalid response | `false` |

Clients **must not** present a prediction with `displayable: false` as an estimate.

```json
{
  "id": "1f0e...", "intersectionId": 5, "intersectionName": "Przybyszewskiego / Łęczycka",
  "signalId": 9, "signalCode": "LDZ-PRZ-LEC-S1",
  "status": "OK", "displayable": true,
  "predictedPhase": "GREEN", "confidence": 0.95,
  "phaseProbabilities": {"RED": 0.03, "YELLOW": 0.02, "GREEN": 0.95},
  "remainingSeconds": 29.4, "remainingSecondsLower": 21.0, "remainingSecondsUpper": 36.8,
  "targetTime": "2026-11-16T11:00:00Z", "createdAt": "2026-11-16T11:00:00.120Z",
  "modelVersion": "tlp-gbm-20261116-6c78bded", "trainingDataOrigin": "SYNTHETIC",
  "dataOrigin": "SIMULATED",
  "anchorObservation": {"id": 3100, "phase": "GREEN", "observedAt": "2026-11-16T10:59:15Z",
                        "phaseDurationSeconds": null, "ageSeconds": 45.0,
                        "source": "demo-simulator", "simulated": true},
  "message": null,
  "disclaimer": "Experimental estimate, not a guarantee. Not connected to any traffic signal controller. Always obey the actual traffic signal. Input observation is SIMULATED. Model trained on SYNTHETIC data."
}
```

- `confidence`: calibrated probability of `predictedPhase` on held-out data from the training
  distribution. See [ml-pipeline.md](ml-pipeline.md#7-reliability-policy-reliabilitypolicy).
- `remainingSecondsLower` / `remainingSecondsUpper`: conformalised interval with ≈80% coverage on
  held-out data.

### `GET /predictions/{id}`

Returns a stored prediction, `404` if unknown, `400` if the id is not a UUID.

## Model

### `GET /model`

Proxies the ML service's metadata: `model_version`, `trained_at`, `training_data_origin`,
`signals`, `dataset_time_range`, `reliability_policy`, `conformal_margin_s`. Returns `503` if the
ML service is unreachable.

## ML service (internal)

FastAPI on port 8000; docs at `/docs`.

| Method | Path | Description |
|---|---|---|
| GET | `/health` | `{"status": "UP"/"DEGRADED", "model_loaded": bool, "model_version": ...}` |
| GET | `/v1/model` | Model metadata |
| POST | `/v1/predictions` | `{"signal_code", "target_time", "anchor": {"phase", "observed_at", "phase_duration_s"}}` |

## Health

`GET /actuator/health`, `/actuator/health/liveness`, `/actuator/health/readiness`.
