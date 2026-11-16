import json
from datetime import UTC, datetime, timedelta

import pytest

from tlp_ml.data.dataset import save_observations
from tlp_ml.domain import Phase
from tlp_ml.persistence import METADATA_FILE, MODEL_FILE
from tlp_ml.predictor import PredictionInput, PredictionStatus, Predictor
from tlp_ml.training import InsufficientDataError, TrainingConfig, run_training

NOW = datetime(2026, 10, 6, 12, 0, tzinfo=UTC)


def test_training_writes_artifacts_and_reports(trained):
    config, report, _ = trained
    assert (config.artifacts_dir / MODEL_FILE).exists()
    metadata = json.loads((config.artifacts_dir / METADATA_FILE).read_text())
    assert metadata["training_data_origin"] == "SYNTHETIC"
    assert metadata["model_version"].startswith("tlp-gbm-")
    assert (config.reports_dir / "metrics.json").exists()
    assert "SYNTHETIC" in (config.reports_dir / "metrics.md").read_text()
    assert report["metadata"]["samples"]["test"] > 0


def test_evaluation_reports_required_metrics(trained):
    _, report, _ = trained
    metrics = report["metrics"]
    model = metrics["phase_classification"]["model"]
    for key in ("accuracy", "macro_precision", "macro_recall", "macro_f1"):
        assert 0.0 <= model[key] <= 1.0
    assert metrics["remaining_time"]["model"]["mae_s"] > 0
    assert (
        metrics["remaining_time"]["model"]["rmse_s"] >= metrics["remaining_time"]["model"]["mae_s"]
    )
    assert 0.0 <= metrics["selective"]["display_rate"] <= 1.0


def test_model_beats_persistence_baseline(trained):
    _, report, _ = trained
    classification = report["metrics"]["phase_classification"]
    assert classification["model"]["accuracy"] > classification["persistence_baseline"]["accuracy"]


def test_training_refuses_insufficient_data(raw_dataset, tmp_path):
    path = tmp_path / "tiny.csv"
    save_observations(raw_dataset.head(300), path)
    with pytest.raises(InsufficientDataError):
        run_training(TrainingConfig(path, tmp_path / "a", tmp_path / "r"))


@pytest.fixture
def predictor(trained):
    return Predictor(trained[2])


@pytest.fixture
def signal(trained):
    return trained[2].metadata["signals"][0]


def test_unknown_signal_is_unsupported(predictor):
    result = predictor.predict(PredictionInput("NOPE", NOW, Phase.GREEN, NOW))
    assert result.status == PredictionStatus.UNSUPPORTED_SIGNAL
    assert not result.displayable and result.phase is None


def test_missing_anchor_is_insufficient_data(predictor, signal):
    result = predictor.predict(PredictionInput(signal, NOW))
    assert result.status == PredictionStatus.INSUFFICIENT_DATA


def test_stale_anchor_is_insufficient_data(predictor, signal):
    result = predictor.predict(PredictionInput(signal, NOW, Phase.GREEN, NOW - timedelta(hours=1)))
    assert result.status == PredictionStatus.INSUFFICIENT_DATA
    assert result.anchor_age_s == pytest.approx(3600)


def test_anchor_after_target_is_insufficient_data(predictor, signal):
    result = predictor.predict(
        PredictionInput(signal, NOW, Phase.GREEN, NOW + timedelta(seconds=5))
    )
    assert result.status == PredictionStatus.INSUFFICIENT_DATA


def test_fresh_anchor_produces_structured_prediction(predictor, signal):
    result = predictor.predict(
        PredictionInput(signal, NOW, Phase.GREEN, NOW - timedelta(seconds=3))
    )
    assert result.status in (PredictionStatus.OK, PredictionStatus.LOW_CONFIDENCE)
    assert result.phase is not None
    assert sum(result.phase_probabilities.values()) == pytest.approx(1.0)
    assert result.confidence == pytest.approx(max(result.phase_probabilities.values()))
    assert 0 <= result.remaining_lower_s <= result.remaining_s <= result.remaining_upper_s
    assert result.training_data_origin == "SYNTHETIC"
    assert result.displayable == (result.status == PredictionStatus.OK)


def test_just_started_green_is_predicted_green(predictor, signal):
    result = predictor.predict(
        PredictionInput(signal, NOW, Phase.GREEN, NOW - timedelta(seconds=2))
    )
    assert result.phase == Phase.GREEN


def test_completed_anchor_phase_shifts_to_next_phase(predictor, signal):
    # GREEN lasted 30 s and ended 1 s ago -> YELLOW just started.
    result = predictor.predict(
        PredictionInput(signal, NOW, Phase.GREEN, NOW - timedelta(seconds=31), anchor_duration_s=30)
    )
    assert result.baseline_phase == Phase.YELLOW


def test_low_confidence_predictions_explain_why(predictor, signal):
    results = [
        predictor.predict(PredictionInput(signal, NOW, Phase.RED, NOW - timedelta(seconds=s)))
        for s in range(300, 900, 60)
    ]
    low = [r for r in results if r.status == PredictionStatus.LOW_CONFIDENCE]
    assert low, "stale anchors should produce at least one low-confidence prediction"
    assert all(r.reasons for r in low)


def test_metrics_report_does_not_contain_absolute_paths(trained):
    config, _, _ = trained
    assert str(config.data_path.parent) not in (config.artifacts_dir / METADATA_FILE).read_text()


def test_prediction_is_deterministic(predictor, signal):
    first = predictor.predict(PredictionInput(signal, NOW, Phase.RED, NOW - timedelta(seconds=20)))
    second = predictor.predict(PredictionInput(signal, NOW, Phase.RED, NOW - timedelta(seconds=20)))
    assert first.confidence == second.confidence
    assert first.remaining_s == second.remaining_s
