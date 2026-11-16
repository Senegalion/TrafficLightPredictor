import numpy as np
import pytest

from tlp_ml.evaluation import (
    classification_metrics,
    expected_calibration_error,
    interval_metrics,
    multiclass_brier,
    regression_metrics,
    selective_metrics,
)
from tlp_ml.models import conformal_margin

LABELS = ["RED", "YELLOW", "GREEN"]


def test_classification_metrics_on_known_input():
    result = classification_metrics(
        ["RED", "RED", "GREEN", "YELLOW"], ["RED", "GREEN", "GREEN", "YELLOW"], LABELS
    )
    assert result["accuracy"] == pytest.approx(0.75)
    assert result["per_class"]["RED"]["recall"] == pytest.approx(0.5)
    assert result["per_class"]["GREEN"]["precision"] == pytest.approx(0.5)
    assert result["confusion_matrix"]["matrix"][0] == [1, 0, 1]


def test_regression_metrics_on_known_input():
    result = regression_metrics([10, 20, 30], [12, 18, 30])
    assert result["mae_s"] == pytest.approx(4 / 3)
    assert result["rmse_s"] == pytest.approx(np.sqrt(8 / 3))
    assert result["median_ae_s"] == pytest.approx(2.0)


def test_regression_metrics_handle_empty_input():
    assert regression_metrics([], [])["mae_s"] is None


def test_interval_metrics():
    result = interval_metrics([5, 15], np.array([0, 0]), np.array([10, 10]))
    assert result == {"coverage": 0.5, "mean_width_s": 10.0}


def test_perfect_probabilities_have_zero_brier_and_ece():
    proba = np.array([[1.0, 0.0, 0.0], [0.0, 0.0, 1.0]])
    assert multiclass_brier(["RED", "GREEN"], proba, LABELS) == 0.0
    assert expected_calibration_error(["RED", "GREEN"], proba, LABELS) == 0.0


def test_overconfident_probabilities_have_positive_ece():
    proba = np.array([[0.95, 0.05, 0.0]] * 4)
    assert expected_calibration_error(["RED", "GREEN", "GREEN", "GREEN"], proba, LABELS) > 0.5


def test_selective_metrics_only_count_displayed_predictions():
    result = selective_metrics(
        np.array([True, False]),
        ["RED", "RED"],
        ["RED", "GREEN"],
        [10.0, 10.0],
        np.array([12.0, 50.0]),
    )
    assert result["display_rate"] == 0.5
    assert result["accuracy_when_displayed"] == 1.0
    assert result["mae_when_displayed_s"] == 2.0


def test_conformal_margin_reaches_target_coverage():
    rng = np.random.default_rng(0)
    y = rng.normal(0, 1, 2000)
    lower, upper = np.full_like(y, -0.5), np.full_like(y, 0.5)
    margin = conformal_margin(y, lower, upper, coverage=0.8)
    coverage = np.mean((y >= lower - margin) & (y <= upper + margin))
    assert coverage >= 0.8
    assert margin > 0
