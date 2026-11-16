"""Evaluation metrics for phase classification, remaining time and calibration."""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    mean_absolute_error,
    precision_recall_fscore_support,
    root_mean_squared_error,
)

CALIBRATION_BINS = 10
ANCHOR_AGE_BUCKETS_S = (0, 60, 180, 420, 900)
P90 = 90


def classification_metrics(y_true, y_pred, labels: list[str]) -> dict:
    precision, recall, f1, support = precision_recall_fscore_support(
        y_true, y_pred, labels=labels, zero_division=0
    )
    macro = precision_recall_fscore_support(
        y_true, y_pred, labels=labels, average="macro", zero_division=0
    )
    return {
        "n": int(len(y_true)),
        "accuracy": float(accuracy_score(y_true, y_pred)) if len(y_true) else None,
        "macro_precision": float(macro[0]),
        "macro_recall": float(macro[1]),
        "macro_f1": float(macro[2]),
        "per_class": {
            label: {
                "precision": float(precision[i]),
                "recall": float(recall[i]),
                "f1": float(f1[i]),
                "support": int(support[i]),
            }
            for i, label in enumerate(labels)
        },
        "confusion_matrix": {
            "labels": labels,
            "matrix": confusion_matrix(y_true, y_pred, labels=labels).tolist(),
        },
    }


def regression_metrics(y_true, y_pred) -> dict:
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    if y_true.size == 0:
        return {"n": 0, "mae_s": None, "rmse_s": None, "median_ae_s": None, "p90_ae_s": None}
    errors = np.abs(y_true - y_pred)
    return {
        "n": int(y_true.size),
        "mae_s": float(mean_absolute_error(y_true, y_pred)),
        "rmse_s": float(root_mean_squared_error(y_true, y_pred)),
        "median_ae_s": float(np.median(errors)),
        "p90_ae_s": float(np.percentile(errors, P90)),
    }


def interval_metrics(y_true, lower, upper) -> dict:
    y_true = np.asarray(y_true, dtype=float)
    covered = (y_true >= lower) & (y_true <= upper)
    return {
        "coverage": float(covered.mean()) if y_true.size else None,
        "mean_width_s": float(np.mean(upper - lower)) if y_true.size else None,
    }


def multiclass_brier(y_true, proba: np.ndarray, classes: list[str]) -> float:
    onehot = (np.asarray(y_true)[:, None] == np.asarray(classes)[None, :]).astype(float)
    return float(np.mean(np.sum((proba - onehot) ** 2, axis=1)))


def expected_calibration_error(y_true, proba: np.ndarray, classes: list[str]) -> float:
    """ECE of the top-class probability with equal-width bins."""
    confidence = proba.max(axis=1)
    predicted = np.asarray(classes)[proba.argmax(axis=1)]
    correct = predicted == np.asarray(y_true)
    edges = np.linspace(0.0, 1.0, CALIBRATION_BINS + 1)
    ece = 0.0
    for low, high in zip(edges[:-1], edges[1:], strict=True):
        mask = (confidence > low) & (confidence <= high)
        if mask.any():
            ece += mask.mean() * abs(correct[mask].mean() - confidence[mask].mean())
    return float(ece)


def reliability_table(y_true, proba: np.ndarray, classes: list[str]) -> list[dict]:
    confidence = proba.max(axis=1)
    correct = np.asarray(classes)[proba.argmax(axis=1)] == np.asarray(y_true)
    edges = np.linspace(0.0, 1.0, CALIBRATION_BINS + 1)
    rows = []
    for low, high in zip(edges[:-1], edges[1:], strict=True):
        mask = (confidence > low) & (confidence <= high)
        if mask.any():
            rows.append(
                {
                    "bin": f"({low:.1f}, {high:.1f}]",
                    "n": int(mask.sum()),
                    "mean_confidence": float(confidence[mask].mean()),
                    "accuracy": float(correct[mask].mean()),
                }
            )
    return rows


def by_anchor_age(
    elapsed_s: np.ndarray,
    y_true_phase,
    y_pred_phase,
    y_true_remaining,
    y_pred_remaining,
    baseline_phase,
) -> list[dict]:
    rows = []
    edges = ANCHOR_AGE_BUCKETS_S
    y_true_phase = np.asarray(y_true_phase)
    for low, high in zip(edges[:-1], edges[1:], strict=True):
        mask = (elapsed_s >= low) & (elapsed_s < high)
        if not mask.any():
            continue
        rows.append(
            {
                "anchor_age_s": f"[{low}, {high})",
                "n": int(mask.sum()),
                "model_accuracy": float(
                    (np.asarray(y_pred_phase)[mask] == y_true_phase[mask]).mean()
                ),
                "baseline_accuracy": float(
                    (np.asarray(baseline_phase)[mask] == y_true_phase[mask]).mean()
                ),
                "model_mae_s": float(
                    np.mean(np.abs(np.asarray(y_true_remaining)[mask] - y_pred_remaining[mask]))
                ),
            }
        )
    return rows


def selective_metrics(
    displayable: np.ndarray, y_true_phase, y_pred_phase, y_true_remaining, y_pred_remaining
) -> dict:
    """Quality of the subset of predictions the system would actually show."""
    displayable = np.asarray(displayable, dtype=bool)
    if not displayable.any():
        return {"display_rate": 0.0, "accuracy_when_displayed": None, "mae_when_displayed_s": None}
    truth = pd.Series(np.asarray(y_true_phase)[displayable])
    pred = pd.Series(np.asarray(y_pred_phase)[displayable])
    errors = np.abs(np.asarray(y_true_remaining)[displayable] - y_pred_remaining[displayable])
    return {
        "display_rate": float(displayable.mean()),
        "accuracy_when_displayed": float((truth.to_numpy() == pred.to_numpy()).mean()),
        "mae_when_displayed_s": float(errors.mean()),
        "p90_ae_when_displayed_s": float(np.percentile(errors, P90)),
    }
