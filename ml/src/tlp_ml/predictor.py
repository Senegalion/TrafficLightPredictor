"""Inference: turns an anchor observation into a structured prediction."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum

import numpy as np
import pandas as pd

from tlp_ml.domain import Phase
from tlp_ml.features import build_feature_frame
from tlp_ml.persistence import ModelBundle, ReliabilityPolicy


class PredictionStatus(StrEnum):
    OK = "OK"
    LOW_CONFIDENCE = "LOW_CONFIDENCE"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"
    UNSUPPORTED_SIGNAL = "UNSUPPORTED_SIGNAL"


@dataclass(frozen=True)
class PredictionInput:
    signal_code: str
    target_time: datetime
    anchor_phase: Phase | None = None
    anchor_observed_at: datetime | None = None
    anchor_duration_s: float | None = None


@dataclass
class PredictionOutput:
    status: PredictionStatus
    displayable: bool
    model_version: str
    training_data_origin: str
    reasons: list[str] = field(default_factory=list)
    phase: Phase | None = None
    confidence: float | None = None
    phase_probabilities: dict[str, float] | None = None
    remaining_s: float | None = None
    remaining_lower_s: float | None = None
    remaining_upper_s: float | None = None
    baseline_phase: Phase | None = None
    baseline_remaining_s: float | None = None
    anchor_age_s: float | None = None


def decide_displayable(
    confidence: np.ndarray, lower: np.ndarray, upper: np.ndarray, policy: ReliabilityPolicy
) -> np.ndarray:
    return (confidence >= policy.min_confidence) & ((upper - lower) <= policy.max_interval_width_s)


class Predictor:
    def __init__(self, bundle: ModelBundle):
        self._bundle = bundle

    @property
    def bundle(self) -> ModelBundle:
        return self._bundle

    def supports(self, signal_code: str) -> bool:
        return signal_code in self._bundle.stats.signals

    def predict(self, request: PredictionInput) -> PredictionOutput:
        bundle = self._bundle
        policy = bundle.policy
        base = {
            "model_version": bundle.model_version,
            "training_data_origin": str(bundle.metadata.get("training_data_origin", "UNKNOWN")),
        }

        if not self.supports(request.signal_code):
            return PredictionOutput(
                status=PredictionStatus.UNSUPPORTED_SIGNAL,
                displayable=False,
                reasons=[f"Model was not trained on signal {request.signal_code}."],
                **base,
            )
        if request.anchor_phase is None or request.anchor_observed_at is None:
            return PredictionOutput(
                status=PredictionStatus.INSUFFICIENT_DATA,
                displayable=False,
                reasons=["No recent observation of this signal is available."],
                **base,
            )

        target = request.target_time.timestamp()
        anchor_start = request.anchor_observed_at.timestamp()
        age = target - anchor_start
        if age < 0:
            return PredictionOutput(
                status=PredictionStatus.INSUFFICIENT_DATA,
                displayable=False,
                reasons=["The anchor observation is later than the target time."],
                **base,
            )
        if age > policy.max_anchor_age_s:
            return PredictionOutput(
                status=PredictionStatus.INSUFFICIENT_DATA,
                displayable=False,
                anchor_age_s=age,
                reasons=[
                    f"Latest observation is {age:.0f} s old; predictions are only made from "
                    f"observations at most {policy.max_anchor_age_s} s old."
                ],
                **base,
            )

        query = pd.DataFrame(
            {
                "signal_code": [request.signal_code],
                "target_epoch": [target],
                "cutoff_epoch": [target],
                "anchor_phase": [Phase(request.anchor_phase).value],
                "anchor_start": [anchor_start],
                "anchor_duration": [
                    np.nan
                    if request.anchor_duration_s is None
                    else float(request.anchor_duration_s)
                ],
            }
        )
        features = build_feature_frame(query, bundle.stats)
        proba = bundle.models.predict_proba(features)[0]
        classes = bundle.models.classes
        best = int(np.argmax(proba))
        median, lower, upper = bundle.models.predict_remaining(features)
        displayable = bool(decide_displayable(np.array([proba[best]]), lower, upper, policy)[0])

        reasons = []
        if proba[best] < policy.min_confidence:
            reasons.append(
                f"Calibrated confidence {proba[best]:.2f} is below the display threshold "
                f"{policy.min_confidence:.2f}."
            )
        if upper[0] - lower[0] > policy.max_interval_width_s:
            reasons.append(
                f"Remaining-time interval is {upper[0] - lower[0]:.0f} s wide (limit "
                f"{policy.max_interval_width_s:.0f} s)."
            )

        return PredictionOutput(
            status=PredictionStatus.OK if displayable else PredictionStatus.LOW_CONFIDENCE,
            displayable=displayable,
            phase=Phase(classes[best]),
            confidence=float(proba[best]),
            phase_probabilities={c: float(p) for c, p in zip(classes, proba, strict=True)},
            remaining_s=float(median[0]),
            remaining_lower_s=float(lower[0]),
            remaining_upper_s=float(upper[0]),
            baseline_phase=Phase(features["baseline_phase"].iloc[0]),
            baseline_remaining_s=float(features["baseline_remaining_s"].iloc[0]),
            anchor_age_s=float(age),
            reasons=reasons,
            **base,
        )
