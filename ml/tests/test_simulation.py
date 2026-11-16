from datetime import UTC, datetime

import numpy as np
import pandas as pd
import pytest

from tlp_ml.domain import NEXT_PHASE, Phase, TimeBand, time_band
from tlp_ml.simulation.plans import load_plans
from tlp_ml.simulation.simulator import (
    generate_observation_dataset,
    observe_segments,
    simulate_segments,
)

START = int(datetime(2026, 10, 5, 12, tzinfo=UTC).timestamp())
HOUR = 3600


@pytest.mark.parametrize(
    ("hour", "weekday", "expected"),
    [
        (23, 0, TimeBand.NIGHT),
        (3, 6, TimeBand.NIGHT),
        (8, 1, TimeBand.AM_PEAK),
        (16, 4, TimeBand.PM_PEAK),
        (12, 2, TimeBand.OFF_PEAK),
        (12, 5, TimeBand.WEEKEND),
    ],
)
def test_time_band(hour, weekday, expected):
    assert time_band(hour, weekday) == expected


def test_packaged_plans_define_every_band():
    plans = load_plans()
    assert len(plans) == 6
    for plan in plans:
        assert set(plan.greens) == set(TimeBand)
        assert plan.main_signal != plan.cross_signal


def test_segments_are_contiguous_and_follow_phase_order(plans):
    segments = simulate_segments(plans[0], START, START + HOUR, np.random.default_rng(1))
    for _, group in segments.groupby("signal_code"):
        starts = group["start"].to_numpy()
        ends = starts + group["duration_s"].to_numpy()
        assert np.array_equal(ends[:-1], starts[1:])
        phases = group["phase"].tolist()
        for current, following in zip(phases, phases[1:], strict=False):
            assert NEXT_PHASE[Phase(current)] == Phase(following)


def test_signal_groups_never_show_green_simultaneously(plans):
    segments = simulate_segments(plans[0], START, START + HOUR, np.random.default_rng(2))
    greens = segments[segments["phase"] == "GREEN"]
    main = greens[greens["signal_code"] == plans[0].main_signal]
    cross = greens[greens["signal_code"] == plans[0].cross_signal]
    for _, m in main.iterrows():
        overlap = (cross["start"] < m["start"] + m["duration_s"]) & (
            cross["start"] + cross["duration_s"] > m["start"]
        )
        assert not overlap.any()


def test_observe_segments_records_duration_only_if_phase_ended_inside_window():
    segments = pd.DataFrame(
        {
            "intersection_code": "X",
            "signal_code": "X-S1",
            "phase": ["GREEN", "YELLOW", "RED"],
            "start": [100, 130, 133],
            "duration_s": [30, 3, 40],
        }
    )
    observed = observe_segments(segments, [(90, 150)])
    assert observed["start"].tolist() == [100, 130, 133]
    assert observed["observed_duration_s"].tolist()[:2] == [30, 3]
    assert pd.isna(observed["observed_duration_s"].iloc[2])


def test_observe_segments_skips_segment_that_started_before_window():
    segments = pd.DataFrame(
        {
            "intersection_code": "X",
            "signal_code": "X-S1",
            "phase": ["GREEN"],
            "start": [100],
            "duration_s": [30],
        }
    )
    assert observe_segments(segments, [(110, 200)]).empty


def test_generated_dataset_is_reproducible_and_labelled_simulated(plans):
    end = datetime(2026, 10, 5, tzinfo=UTC)
    first = generate_observation_dataset(plans, end, 1, seed=3)
    second = generate_observation_dataset(plans, end, 1, seed=3)
    pd.testing.assert_frame_equal(first, second)
    assert first["is_simulated"].all()
    assert (first["source"] == "synthetic-generator").all()
