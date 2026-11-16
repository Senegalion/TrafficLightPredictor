"""FastAPI prediction service.

The Java backend calls this service; it is not meant to be exposed to end
users directly. It is a separate process because the models are scikit-learn
objects, which the JVM cannot load natively.
"""

from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from pydantic import AwareDatetime, BaseModel, Field

from tlp_ml.domain import Phase
from tlp_ml.persistence import load_bundle
from tlp_ml.predictor import PredictionInput, PredictionStatus, Predictor

log = logging.getLogger(__name__)

DEFAULT_ARTIFACTS_DIR = Path(__file__).resolve().parents[3] / "artifacts"
MAX_PHASE_DURATION_S = 300


class AnchorObservation(BaseModel):
    phase: Phase
    observed_at: AwareDatetime
    phase_duration_s: float | None = Field(default=None, gt=0, le=MAX_PHASE_DURATION_S)


class PredictionRequest(BaseModel):
    signal_code: str = Field(min_length=1, max_length=64)
    target_time: AwareDatetime
    anchor: AnchorObservation | None = None


class PredictionResponse(BaseModel):
    status: PredictionStatus
    displayable: bool
    model_version: str
    training_data_origin: str
    reasons: list[str]
    phase: Phase | None = None
    confidence: float | None = None
    phase_probabilities: dict[str, float] | None = None
    remaining_s: float | None = None
    remaining_lower_s: float | None = None
    remaining_upper_s: float | None = None
    baseline_phase: Phase | None = None
    baseline_remaining_s: float | None = None
    anchor_age_s: float | None = None


def create_app(artifacts_dir: Path | None = None) -> FastAPI:
    directory = artifacts_dir or Path(os.getenv("TLP_ML_ARTIFACTS_DIR", DEFAULT_ARTIFACTS_DIR))

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        try:
            app.state.predictor = Predictor(load_bundle(directory))
            log.info(
                "Model loaded", extra={"model_version": app.state.predictor.bundle.model_version}
            )
        except (FileNotFoundError, TypeError) as error:
            app.state.predictor = None
            log.error("Model could not be loaded", extra={"error": str(error)})
        yield

    app = FastAPI(
        title="Traffic Light Predictor - ML service",
        version="0.1.0",
        description="Internal prediction service. Research prototype; predictions are estimates.",
        lifespan=lifespan,
    )

    def predictor(request: Request) -> Predictor:
        value = request.app.state.predictor
        if value is None:
            raise HTTPException(status_code=503, detail="Model is not loaded")
        return value

    @app.get("/health")
    def health(request: Request) -> dict:
        loaded = request.app.state.predictor is not None
        return {
            "status": "UP" if loaded else "DEGRADED",
            "model_loaded": loaded,
            "model_version": request.app.state.predictor.bundle.model_version if loaded else None,
        }

    @app.get("/v1/model")
    def model_info(request: Request) -> dict:
        meta = predictor(request).bundle.metadata
        keys = [
            "model_version",
            "trained_at",
            "training_data_origin",
            "signals",
            "dataset_time_range",
            "reliability_policy",
            "conformal_margin_s",
        ]
        return {k: meta.get(k) for k in keys}

    @app.post("/v1/predictions", response_model=PredictionResponse)
    def predict(body: PredictionRequest, request: Request) -> PredictionResponse:
        anchor = body.anchor
        result = predictor(request).predict(
            PredictionInput(
                signal_code=body.signal_code,
                target_time=body.target_time,
                anchor_phase=anchor.phase if anchor else None,
                anchor_observed_at=anchor.observed_at if anchor else None,
                anchor_duration_s=anchor.phase_duration_s if anchor else None,
            )
        )
        log.info(
            "Prediction",
            extra={
                "signal_code": body.signal_code,
                "status": result.status.value,
                "confidence": result.confidence,
            },
        )
        return PredictionResponse(**vars(result))

    return app
