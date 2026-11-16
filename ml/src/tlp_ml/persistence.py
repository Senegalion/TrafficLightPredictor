"""Saving and loading the trained model bundle."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

import joblib

from tlp_ml.features import DurationStats
from tlp_ml.models import TrainedModels

MODEL_FILE = "model.joblib"
METADATA_FILE = "metadata.json"


@dataclass(frozen=True)
class ReliabilityPolicy:
    """When a prediction is considered reliable enough to be displayed.

    ``min_confidence`` applies to the *calibrated* probability of the predicted
    phase. ``max_interval_width_s`` rejects predictions whose remaining-time
    interval is too wide to be useful. ``max_anchor_age_s`` is the oldest
    observation we are willing to extrapolate from.
    """

    min_confidence: float = 0.8
    max_interval_width_s: float = 20.0
    max_anchor_age_s: int = 900


@dataclass
class ModelBundle:
    models: TrainedModels
    stats: DurationStats
    policy: ReliabilityPolicy
    metadata: dict = field(default_factory=dict)

    @property
    def model_version(self) -> str:
        return str(self.metadata.get("model_version", "unknown"))


def save_bundle(bundle: ModelBundle, directory: Path) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / MODEL_FILE
    joblib.dump(bundle, path, compress=3)
    (directory / METADATA_FILE).write_text(json.dumps(bundle.metadata, indent=2), encoding="utf-8")
    return path


def load_bundle(directory: Path) -> ModelBundle:
    path = directory / MODEL_FILE
    if not path.exists():
        raise FileNotFoundError(
            f"Model artifact not found at {path}. Train it first: `tlp-ml train`."
        )
    bundle = joblib.load(path)
    if not isinstance(bundle, ModelBundle):
        raise TypeError(f"{path} does not contain a ModelBundle")
    return bundle
