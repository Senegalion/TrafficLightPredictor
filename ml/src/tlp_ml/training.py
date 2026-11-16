"""End-to-end training pipeline: load -> split -> features -> train -> evaluate -> save."""

from __future__ import annotations

import hashlib
import json
import logging
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pandas as pd
import sklearn

from tlp_ml.data.dataset import ValidationReport, load_observations
from tlp_ml.data.samples import MAX_ANCHOR_AGE_S, ChronologicalSplit, build_samples
from tlp_ml.evaluation import (
    by_anchor_age,
    classification_metrics,
    expected_calibration_error,
    interval_metrics,
    multiclass_brier,
    regression_metrics,
    reliability_table,
    selective_metrics,
)
from tlp_ml.features import FEATURE_COLUMNS, DurationStats, build_feature_frame, phase_labels
from tlp_ml.models import TrainedModels, train_models
from tlp_ml.persistence import ModelBundle, ReliabilityPolicy, save_bundle
from tlp_ml.predictor import decide_displayable

log = logging.getLogger(__name__)

#: Minimum examples per split. Below this the metrics would be meaningless and
#: training is refused rather than producing a misleading model.
MIN_SAMPLES_PER_SPLIT = 200


@dataclass(frozen=True)
class TrainingConfig:
    data_path: Path
    artifacts_dir: Path
    reports_dir: Path
    train_fraction: float = 0.65
    calibration_fraction: float = 0.15
    samples_per_segment: int = 1
    seed: int = 42
    max_anchor_age_s: int = MAX_ANCHOR_AGE_S


class InsufficientDataError(RuntimeError):
    pass


def run_training(config: TrainingConfig) -> dict:
    observations, validation = load_observations(config.data_path)
    log.info(
        "Loaded %d valid observations (%d dropped)", validation.valid_rows, validation.dropped_rows
    )
    simulated_share = float(observations["is_simulated"].mean()) if len(observations) else 0.0
    data_origin = _data_origin(simulated_share)

    split = ChronologicalSplit.from_fractions(
        observations, config.train_fraction, config.calibration_fraction
    )
    rng = np.random.default_rng(config.seed)
    samples = build_samples(observations, rng, config.samples_per_segment, config.max_anchor_age_s)
    parts = split.assign(samples)
    for name, part in parts.items():
        if len(part) < MIN_SAMPLES_PER_SPLIT:
            raise InsufficientDataError(
                f"Only {len(part)} {name} samples (need {MIN_SAMPLES_PER_SPLIT}). "
                "Collect more observations with known phase durations."
            )

    # Statistics are fitted on phases that finished before the calibration period.
    stats = DurationStats.fit(split.observations_before(observations, split.calibration_start))
    x = {name: build_feature_frame(part, stats) for name, part in parts.items()}

    models = train_models(
        x["train"],
        parts["train"]["label_phase"],
        parts["train"]["label_remaining_s"],
        x["calibration"],
        parts["calibration"]["label_phase"],
        parts["calibration"]["label_remaining_s"],
    )
    policy = ReliabilityPolicy(max_anchor_age_s=config.max_anchor_age_s)
    metrics = evaluate(models, x["test"], parts["test"], policy)

    dataset_hash = _sha256(config.data_path)
    trained_at = datetime.now(UTC)
    metadata = {
        "model_version": f"tlp-gbm-{trained_at:%Y%m%d}-{dataset_hash[:8]}",
        "trained_at": trained_at.isoformat(),
        "training_data_origin": data_origin,
        "simulated_share": simulated_share,
        "dataset_file": config.data_path.name,
        "dataset_sha256": dataset_hash,
        "dataset_time_range": [
            observations["observed_at"].min().isoformat(),
            observations["observed_at"].max().isoformat(),
        ],
        "split_boundaries_utc": {
            "calibration_start": _iso(split.calibration_start),
            "test_start": _iso(split.test_start),
        },
        "samples": {name: len(part) for name, part in parts.items()},
        "signals": sorted(stats.signals),
        "feature_columns": FEATURE_COLUMNS,
        "sklearn_version": sklearn.__version__,
        "conformal_margin_s": models.conformal_margin_s,
        "reliability_policy": asdict(policy),
        "config": {k: v for k, v in asdict(config).items() if not isinstance(v, Path)},
    }
    bundle = ModelBundle(models=models, stats=stats, policy=policy, metadata=metadata)
    save_bundle(bundle, config.artifacts_dir)

    report = {"metadata": metadata, "validation": validation.to_dict(), "metrics": metrics}
    write_reports(report, validation, config.reports_dir)
    return report


def evaluate(
    models: TrainedModels, test_x: pd.DataFrame, test: pd.DataFrame, policy: ReliabilityPolicy
) -> dict:
    labels = phase_labels()
    true_phase = test["label_phase"].to_numpy()
    true_remaining = test["label_remaining_s"].to_numpy()

    proba = models.predict_proba(test_x)
    raw_proba = models.raw_classifier.predict_proba(test_x)
    classes = models.classes
    predicted = np.asarray(classes)[proba.argmax(axis=1)]
    median, lower, upper = models.predict_remaining(test_x)
    baseline_phase = test_x["baseline_phase"].to_numpy()
    baseline_remaining = test_x["baseline_remaining_s"].to_numpy()
    persistence_phase = test_x["anchor_phase"].to_numpy()

    correct = predicted == true_phase
    displayable = decide_displayable(proba.max(axis=1), lower, upper, policy)
    return {
        "test_samples": int(len(test)),
        "phase_classification": {
            "model": classification_metrics(true_phase, predicted, labels),
            "cycle_baseline": classification_metrics(true_phase, baseline_phase, labels),
            "persistence_baseline": classification_metrics(true_phase, persistence_phase, labels),
        },
        "remaining_time": {
            "model": regression_metrics(true_remaining, median),
            "model_when_phase_correct": regression_metrics(
                true_remaining[correct], median[correct]
            ),
            "cycle_baseline": regression_metrics(true_remaining, baseline_remaining),
            "interval": interval_metrics(true_remaining, lower, upper),
        },
        "calibration": {
            "brier_uncalibrated": multiclass_brier(true_phase, raw_proba, classes),
            "brier_calibrated": multiclass_brier(true_phase, proba, classes),
            "ece_uncalibrated": expected_calibration_error(true_phase, raw_proba, classes),
            "ece_calibrated": expected_calibration_error(true_phase, proba, classes),
            "reliability_table": reliability_table(true_phase, proba, classes),
        },
        "by_anchor_age": by_anchor_age(
            test_x["elapsed_s"].to_numpy(),
            true_phase,
            predicted,
            true_remaining,
            median,
            baseline_phase,
        ),
        "selective": selective_metrics(displayable, true_phase, predicted, true_remaining, median),
    }


def write_reports(report: dict, validation: ValidationReport, reports_dir: Path) -> None:
    reports_dir.mkdir(parents=True, exist_ok=True)
    (reports_dir / "metrics.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    (reports_dir / "metrics.md").write_text(render_markdown(report), encoding="utf-8")


def render_markdown(report: dict) -> str:
    meta, m = report["metadata"], report["metrics"]
    synthetic = meta["training_data_origin"] != "REAL"
    boundaries = meta["split_boundaries_utc"]
    lines = [f"# Evaluation report - `{meta['model_version']}`", ""]
    if synthetic:
        lines += [
            "> **All results below are measured on SYNTHETIC demonstration data** produced by",
            "> the project's simulator. They show that the pipeline works; they say nothing",
            "> about how well real Łódź traffic signals can be predicted.",
            "",
        ]
    lines += [
        f"- Trained at: {meta['trained_at']}",
        f"- Training data origin: {meta['training_data_origin']}",
        f"- Dataset: `{meta['dataset_file']}` (sha256 `{meta['dataset_sha256'][:12]}`)",
        f"- Dataset time range: {meta['dataset_time_range'][0]} to {meta['dataset_time_range'][1]}",
        f"- Chronological split: calibration from {boundaries['calibration_start']},"
        f" test from {boundaries['test_start']}",
        f"- Samples: {meta['samples']}",
        "",
        "## Phase classification (test split)",
        "",
        "| Model | Accuracy | Macro precision | Macro recall | Macro F1 |",
        "|---|---|---|---|---|",
    ]
    names = {
        "model": "Gradient boosting (calibrated)",
        "cycle_baseline": "Cycle baseline",
        "persistence_baseline": "Persistence (anchor phase)",
    }
    for key, label in names.items():
        c = m["phase_classification"][key]
        lines.append(
            f"| {label} | {c['accuracy']:.3f} | {c['macro_precision']:.3f} | "
            f"{c['macro_recall']:.3f} | {c['macro_f1']:.3f} |"
        )
    lines += [
        "",
        "## Remaining time in current phase (test split)",
        "",
        "| Model | MAE (s) | RMSE (s) | Median AE (s) | P90 AE (s) |",
        "|---|---|---|---|---|",
    ]
    for key, label in [
        ("model", "Gradient boosting (median)"),
        ("model_when_phase_correct", "... when phase is correct"),
        ("cycle_baseline", "Cycle baseline"),
    ]:
        r = m["remaining_time"][key]
        lines.append(
            f"| {label} | {r['mae_s']:.2f} | {r['rmse_s']:.2f} | {r['median_ae_s']:.2f} | "
            f"{r['p90_ae_s']:.2f} |"
        )
    interval = m["remaining_time"]["interval"]
    cal = m["calibration"]
    sel = m["selective"]
    lines += [
        "",
        f"Conformalised 80% interval: empirical coverage {interval['coverage']:.3f}, "
        f"mean width {interval['mean_width_s']:.1f} s.",
        "",
        "## Probability calibration (test split)",
        "",
        f"- Brier score: {cal['brier_uncalibrated']:.4f} before, "
        f"{cal['brier_calibrated']:.4f} after isotonic calibration",
        f"- Expected calibration error: {cal['ece_uncalibrated']:.4f} before, "
        f"{cal['ece_calibrated']:.4f} after",
        "",
        "## Accuracy by anchor age",
        "",
        "| Anchor age (s) | n | Model accuracy | Baseline accuracy | Model MAE (s) |",
        "|---|---|---|---|---|",
    ]
    for row in m["by_anchor_age"]:
        lines.append(
            f"| {row['anchor_age_s']} | {row['n']} | {row['model_accuracy']:.3f} | "
            f"{row['baseline_accuracy']:.3f} | {row['model_mae_s']:.2f} |"
        )
    policy = meta.get("reliability_policy") or {}
    lines += [
        "",
        "## Predictions the system would display",
        "",
        f"- Display rate: {sel['display_rate']:.3f} of test queries",
    ]
    if sel.get("accuracy_when_displayed") is not None:
        lines += [
            f"- Phase accuracy when displayed: {sel['accuracy_when_displayed']:.3f}",
            f"- Remaining-time MAE when displayed: {sel['mae_when_displayed_s']:.2f} s "
            f"(P90 {sel['p90_ae_when_displayed_s']:.2f} s)",
        ]
    if policy:
        lines.append(f"- Policy: {policy}")
    lines.append("")
    return "\n".join(lines)


def _data_origin(simulated_share: float) -> str:
    if simulated_share >= 1.0:
        return "SYNTHETIC"
    if simulated_share <= 0.0:
        return "REAL"
    return "MIXED"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _iso(epoch: float) -> str:
    return datetime.fromtimestamp(epoch, UTC).isoformat()
