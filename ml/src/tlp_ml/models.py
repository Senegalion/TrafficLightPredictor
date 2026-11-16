"""Model definitions: phase classifier, remaining-time regressors, uncertainty.

* Phase: gradient-boosted trees, probabilities recalibrated with isotonic
  regression on a held-out (chronologically later) calibration split.
* Remaining time: gradient-boosted quantile regressors (10th, 50th, 90th
  percentile). The 10-90 interval is then widened using split-conformal
  calibration (conformalised quantile regression) so that it covers
  approximately ``INTERVAL_COVERAGE`` of calibration examples.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.calibration import CalibratedClassifierCV
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingClassifier, HistGradientBoostingRegressor
from sklearn.frozen import FrozenEstimator
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

from tlp_ml.features import CATEGORICAL_FEATURES, NUMERIC_FEATURES

RANDOM_STATE = 42
LOWER_QUANTILE = 0.1
UPPER_QUANTILE = 0.9
INTERVAL_COVERAGE = UPPER_QUANTILE - LOWER_QUANTILE

# Tree-model hyperparameters. Chosen as reasonable defaults for ~10^5 rows and
# a dozen features; they were not tuned on the test split.
MAX_ITERATIONS = 300
LEARNING_RATE = 0.08
MAX_LEAF_NODES = 31
MIN_SAMPLES_LEAF = 40


def _preprocessor() -> ColumnTransformer:
    return ColumnTransformer(
        [
            (
                "categorical",
                OneHotEncoder(handle_unknown="ignore", sparse_output=False),
                CATEGORICAL_FEATURES,
            ),
            ("numeric", "passthrough", NUMERIC_FEATURES),
        ]
    )


def _tree_params() -> dict:
    return {
        "max_iter": MAX_ITERATIONS,
        "learning_rate": LEARNING_RATE,
        "max_leaf_nodes": MAX_LEAF_NODES,
        "min_samples_leaf": MIN_SAMPLES_LEAF,
        "random_state": RANDOM_STATE,
    }


def build_classifier() -> Pipeline:
    return Pipeline(
        [("features", _preprocessor()), ("model", HistGradientBoostingClassifier(**_tree_params()))]
    )


def build_quantile_regressor(quantile: float) -> Pipeline:
    return Pipeline(
        [
            ("features", _preprocessor()),
            (
                "model",
                HistGradientBoostingRegressor(loss="quantile", quantile=quantile, **_tree_params()),
            ),
        ]
    )


@dataclass
class TrainedModels:
    raw_classifier: Pipeline
    classifier: CalibratedClassifierCV
    lower: Pipeline
    median: Pipeline
    upper: Pipeline
    conformal_margin_s: float

    @property
    def classes(self) -> list[str]:
        return [str(c) for c in self.classifier.classes_]

    def predict_proba(self, features: pd.DataFrame) -> np.ndarray:
        return self.classifier.predict_proba(features)

    def predict_remaining(
        self, features: pd.DataFrame
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Return (point estimate, interval lower, interval upper), seconds, clipped at 0."""
        median = np.clip(self.median.predict(features), 0.0, None)
        lower = np.clip(self.lower.predict(features) - self.conformal_margin_s, 0.0, None)
        upper = np.clip(self.upper.predict(features) + self.conformal_margin_s, 0.0, None)
        # Quantile models are fitted independently and can cross; keep a valid ordering.
        lower = np.minimum(lower, median)
        upper = np.maximum(upper, median)
        return median, lower, upper


def train_models(
    train_x: pd.DataFrame,
    train_phase: pd.Series,
    train_remaining: pd.Series,
    calib_x: pd.DataFrame,
    calib_phase: pd.Series,
    calib_remaining: pd.Series,
) -> TrainedModels:
    raw_classifier = build_classifier().fit(train_x, train_phase)
    calibrated = CalibratedClassifierCV(FrozenEstimator(raw_classifier), method="isotonic")
    calibrated.fit(calib_x, calib_phase)

    lower = build_quantile_regressor(LOWER_QUANTILE).fit(train_x, train_remaining)
    median = build_quantile_regressor(0.5).fit(train_x, train_remaining)
    upper = build_quantile_regressor(UPPER_QUANTILE).fit(train_x, train_remaining)

    margin = conformal_margin(
        calib_remaining.to_numpy(),
        lower.predict(calib_x),
        upper.predict(calib_x),
        INTERVAL_COVERAGE,
    )
    return TrainedModels(raw_classifier, calibrated, lower, median, upper, margin)


def conformal_margin(y: np.ndarray, lower: np.ndarray, upper: np.ndarray, coverage: float) -> float:
    """Split-conformal margin for quantile intervals (Romano et al., 2019)."""
    if len(y) == 0:
        raise ValueError("Calibration set is empty")
    scores = np.maximum(lower - y, y - upper)
    level = min(1.0, np.ceil((len(y) + 1) * coverage) / len(y))
    return float(np.quantile(scores, level, method="higher"))
