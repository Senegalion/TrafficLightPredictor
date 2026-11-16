-- Traffic Light Predictor - core schema.

CREATE EXTENSION IF NOT EXISTS postgis;

CREATE TABLE intersections (
    id              BIGSERIAL PRIMARY KEY,
    code            VARCHAR(32)      NOT NULL UNIQUE,
    name            VARCHAR(200)     NOT NULL,
    city            VARCHAR(100)     NOT NULL,
    description     TEXT,
    latitude        DOUBLE PRECISION NOT NULL CHECK (latitude BETWEEN -90 AND 90),
    longitude       DOUBLE PRECISION NOT NULL CHECK (longitude BETWEEN -180 AND 180),
    -- Derived geography point used for radius queries (ST_DWithin).
    location        GEOGRAPHY(POINT, 4326) GENERATED ALWAYS AS (
                        ST_SetSRID(ST_MakePoint(longitude, latitude), 4326)::geography
                    ) STORED,
    location_source VARCHAR(32)      NOT NULL CHECK (location_source IN ('OPENSTREETMAP', 'SAMPLE')),
    osm_reference   TEXT,
    created_at      TIMESTAMPTZ      NOT NULL DEFAULT now()
);

CREATE INDEX idx_intersections_location ON intersections USING GIST (location);

CREATE TABLE traffic_signals (
    id                   BIGSERIAL PRIMARY KEY,
    intersection_id      BIGINT       NOT NULL REFERENCES intersections (id) ON DELETE CASCADE,
    code                 VARCHAR(48)  NOT NULL UNIQUE,
    name                 VARCHAR(200) NOT NULL,
    description          TEXT,
    approach             VARCHAR(200),
    configuration_source VARCHAR(32)  NOT NULL CHECK (configuration_source IN ('SAMPLE', 'VERIFIED')),
    -- Enables the composite foreign keys below (signal must belong to the intersection).
    UNIQUE (id, intersection_id)
);

CREATE INDEX idx_traffic_signals_intersection ON traffic_signals (intersection_id);

CREATE TABLE observations (
    id                     BIGSERIAL PRIMARY KEY,
    intersection_id        BIGINT      NOT NULL,
    signal_id              BIGINT      NOT NULL,
    observed_at            TIMESTAMPTZ NOT NULL,
    phase                  VARCHAR(8)  NOT NULL CHECK (phase IN ('RED', 'YELLOW', 'GREEN')),
    phase_duration_seconds INTEGER CHECK (phase_duration_seconds BETWEEN 1 AND 300),
    direction              VARCHAR(16) CHECK (direction IN ('NORTHBOUND', 'SOUTHBOUND', 'EASTBOUND', 'WESTBOUND')),
    source                 VARCHAR(64) NOT NULL CHECK (length(trim(source)) > 0),
    simulated              BOOLEAN     NOT NULL,
    created_at             TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT fk_observations_signal FOREIGN KEY (signal_id, intersection_id)
        REFERENCES traffic_signals (id, intersection_id) ON DELETE CASCADE,
    CONSTRAINT uq_observations_signal_time UNIQUE (signal_id, observed_at)
);

CREATE INDEX idx_observations_intersection_time ON observations (intersection_id, observed_at DESC);

CREATE TABLE predictions (
    id                       UUID PRIMARY KEY,
    intersection_id          BIGINT       NOT NULL,
    signal_id                BIGINT       NOT NULL,
    created_at               TIMESTAMPTZ  NOT NULL,
    target_time              TIMESTAMPTZ  NOT NULL,
    status                   VARCHAR(32)  NOT NULL CHECK (status IN
                                 ('OK', 'LOW_CONFIDENCE', 'INSUFFICIENT_DATA', 'UNSUPPORTED_SIGNAL', 'MODEL_UNAVAILABLE')),
    displayable              BOOLEAN      NOT NULL,
    predicted_phase          VARCHAR(8) CHECK (predicted_phase IN ('RED', 'YELLOW', 'GREEN')),
    confidence               DOUBLE PRECISION CHECK (confidence BETWEEN 0 AND 1),
    probability_red          DOUBLE PRECISION CHECK (probability_red BETWEEN 0 AND 1),
    probability_yellow       DOUBLE PRECISION CHECK (probability_yellow BETWEEN 0 AND 1),
    probability_green        DOUBLE PRECISION CHECK (probability_green BETWEEN 0 AND 1),
    remaining_seconds        DOUBLE PRECISION CHECK (remaining_seconds >= 0),
    remaining_seconds_lower  DOUBLE PRECISION CHECK (remaining_seconds_lower >= 0),
    remaining_seconds_upper  DOUBLE PRECISION CHECK (remaining_seconds_upper >= 0),
    model_version            VARCHAR(64),
    training_data_origin     VARCHAR(16),
    data_origin              VARCHAR(16)  NOT NULL CHECK (data_origin IN ('REAL', 'SIMULATED', 'NONE')),
    anchor_observation_id    BIGINT REFERENCES observations (id) ON DELETE SET NULL,
    anchor_age_seconds       DOUBLE PRECISION,
    message                  TEXT,
    CONSTRAINT fk_predictions_signal FOREIGN KEY (signal_id, intersection_id)
        REFERENCES traffic_signals (id, intersection_id) ON DELETE CASCADE,
    CONSTRAINT ck_predictions_ok_has_phase CHECK (status NOT IN ('OK', 'LOW_CONFIDENCE') OR predicted_phase IS NOT NULL)
);

CREATE INDEX idx_predictions_signal_time ON predictions (signal_id, created_at DESC);
