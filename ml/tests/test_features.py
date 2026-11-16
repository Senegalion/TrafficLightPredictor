import numpy as np
import pandas as pd
import pytest

from tlp_ml.data.samples import ChronologicalSplit, build_samples
from tlp_ml.features import (
    FEATURE_COLUMNS,
    DurationStats,
    build_feature_frame,
    cycle_baseline,
    normalise_anchor,
)


def test_normalise_anchor_uses_duration_only_if_phase_ended_before_cutoff():
    phase, start = normalise_anchor(
        np.array(["GREEN", "GREEN", "RED"], dtype=object),
        np.array([100.0, 100.0, 100.0]),
        np.array([30.0, 30.0, np.nan]),
        cutoff=np.array([200.0, 120.0, 200.0]),
    )
    # ended before cutoff -> next phase known to start at 130
    assert phase[0] == "YELLOW" and start[0] == 130.0
    # phase end (130) is after the cutoff (120): must not leak the future
    assert phase[1] == "GREEN" and start[1] == 100.0
    # unknown duration
    assert phase[2] == "RED" and start[2] == 100.0


def test_cycle_baseline_projects_median_cycle():
    green, yellow, red = np.array([40.0]), np.array([3.0]), np.array([47.0])  # cycle 90
    cases = [
        ("GREEN", 10.0, "GREEN", 30.0),
        ("GREEN", 41.0, "YELLOW", 2.0),
        ("GREEN", 50.0, "RED", 40.0),
        ("RED", 50.0, "GREEN", 37.0),  # RED starts at 43 in cycle; 43+50=93 -> 3 into next GREEN
        ("YELLOW", 0.0, "YELLOW", 3.0),
    ]
    for anchor, elapsed, expected_phase, expected_remaining in cases:
        phase, remaining, position = cycle_baseline(
            np.array([anchor], dtype=object), np.array([elapsed]), green, yellow, red
        )
        assert phase[0] == expected_phase
        assert remaining[0] == pytest.approx(expected_remaining)
        assert 0.0 <= position[0] < 1.0


def test_duration_stats_fall_back_to_signal_median_for_sparse_bands():
    observations = pd.DataFrame(
        {
            "signal_code": ["S1"] * 6,
            "observed_at": pd.to_datetime(
                ["2026-10-05T10:00:00Z"] * 2
                + ["2026-10-05T10:01:00Z"] * 2
                + ["2026-10-05T10:02:00Z"] * 2,
                utc=True,
            )
            + pd.to_timedelta(range(6), unit="s"),
            "phase": ["GREEN", "YELLOW", "RED", "GREEN", "YELLOW", "RED"],
            "phase_duration_s": [40.0, 3.0, 50.0, 44.0, 3.0, 46.0],
        }
    )
    stats = DurationStats.fit(observations)
    row = stats.table.loc[("S1", "NIGHT")]  # no NIGHT data -> signal-level median
    assert row["median_green_s"] == 42.0
    assert row["median_cycle_s"] == 42.0 + 3.0 + 48.0


def test_feature_frame_has_expected_columns(observations):
    stats = DurationStats.fit(observations)
    samples = build_samples(observations, np.random.default_rng(0))
    features = build_feature_frame(samples.head(50), stats)
    assert list(features.columns) == FEATURE_COLUMNS
    assert not features.isna().any().any()
    assert (features["elapsed_s"] >= 0).all()


def test_feature_frame_rejects_unknown_signal(observations):
    stats = DurationStats.fit(observations)
    query = pd.DataFrame(
        {
            "signal_code": ["UNKNOWN"],
            "target_epoch": [1.79e9],
            "cutoff_epoch": [1.79e9],
            "anchor_phase": ["GREEN"],
            "anchor_start": [1.79e9 - 10],
            "anchor_duration": [np.nan],
        }
    )
    with pytest.raises(ValueError, match="UNKNOWN"):
        build_feature_frame(query, stats)


def test_samples_have_consistent_labels(observations):
    samples = build_samples(observations, np.random.default_rng(1), max_anchor_age_s=600)
    assert len(samples) > 0
    assert (samples["label_remaining_s"] > 0).all()
    assert (samples["anchor_start"] <= samples["cutoff_epoch"]).all()
    assert (samples["cutoff_epoch"] <= samples["target_epoch"]).all()
    assert (samples["target_epoch"] - samples["anchor_start"] <= 600).all()


def test_chronological_split_does_not_overlap(observations):
    samples = build_samples(observations, np.random.default_rng(2))
    split = ChronologicalSplit.from_fractions(observations, 0.6, 0.2)
    parts = split.assign(samples)
    assert parts["train"]["label_segment_end"].max() < split.calibration_start
    assert parts["calibration"]["target_epoch"].min() >= split.calibration_start
    assert parts["calibration"]["label_segment_end"].max() < split.test_start
    assert parts["test"]["target_epoch"].min() >= split.test_start


def test_history_for_stats_excludes_later_phases(observations):
    split = ChronologicalSplit.from_fractions(observations, 0.6, 0.2)
    history = split.observations_before(observations, split.calibration_start)
    end = history["observed_at"].astype("int64") / 1e9 + history["phase_duration_s"].fillna(0)
    assert (end < split.calibration_start).all()


def test_invalid_split_fractions_raise(observations):
    with pytest.raises(ValueError):
        ChronologicalSplit.from_fractions(observations, 0.9, 0.2)
