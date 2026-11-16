"""Synthetic traffic signal simulator and observation sampler.

Everything produced here is SIMULATED. The simulator exists so that the
pipeline, service and UI can be developed and demonstrated before real
observations are collected. Records it produces are always labelled
``is_simulated=True``.
"""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from datetime import UTC, datetime

import numpy as np
import pandas as pd

from tlp_ml.domain import LOCAL_TIMEZONE, Phase, time_band
from tlp_ml.simulation.plans import IntersectionPlan

SYNTHETIC_SOURCE = "synthetic-generator"


@dataclass(frozen=True)
class PhaseEvent:
    """A signal switched to ``phase`` at ``start`` (UTC epoch seconds)."""

    signal_code: str
    phase: Phase
    start: int


def _draw_green(base_s: int, plan: IntersectionPlan, rng: np.random.Generator) -> int:
    green = base_s + rng.normal(0.0, plan.green_jitter_s)
    if rng.random() < plan.extension_probability:
        # Models e.g. public transport priority or demand-based extension.
        green += plan.extension_s
    return max(plan.min_green_s, int(round(green)))


def iter_phase_events(
    plan: IntersectionPlan, start_epoch: int, rng: np.random.Generator
) -> Iterator[PhaseEvent]:
    """Yield phase-start events of both signal groups, in time order, forever."""
    t = start_epoch
    while True:
        local = datetime.fromtimestamp(t, LOCAL_TIMEZONE)
        main_base, cross_base = plan.greens[time_band(local.hour, local.weekday())]
        main_green = _draw_green(main_base, plan, rng)
        cross_green = _draw_green(cross_base, plan, rng)

        main_yellow_at = t + main_green
        main_red_at = main_yellow_at + plan.yellow_s
        cross_green_at = main_red_at + plan.all_red_s
        cross_yellow_at = cross_green_at + cross_green
        cross_red_at = cross_yellow_at + plan.yellow_s
        cycle_end = cross_red_at + plan.all_red_s

        yield PhaseEvent(plan.main_signal, Phase.GREEN, t)
        yield PhaseEvent(plan.main_signal, Phase.YELLOW, main_yellow_at)
        yield PhaseEvent(plan.main_signal, Phase.RED, main_red_at)
        yield PhaseEvent(plan.cross_signal, Phase.GREEN, cross_green_at)
        yield PhaseEvent(plan.cross_signal, Phase.YELLOW, cross_yellow_at)
        yield PhaseEvent(plan.cross_signal, Phase.RED, cross_red_at)
        t = cycle_end


def simulate_segments(
    plan: IntersectionPlan, start_epoch: int, end_epoch: int, rng: np.random.Generator
) -> pd.DataFrame:
    """Ground-truth phase segments (with exact durations) in ``[start, end)``.

    Segments that are still running at ``end_epoch`` are dropped because their
    duration is unknown.
    """
    rows: list[tuple[str, str, int, int]] = []
    open_segment: dict[str, PhaseEvent] = {}
    for event in iter_phase_events(plan, start_epoch, rng):
        previous = open_segment.get(event.signal_code)
        if previous is not None:
            rows.append(
                (
                    previous.signal_code,
                    previous.phase.value,
                    previous.start,
                    event.start - previous.start,
                )
            )
        open_segment[event.signal_code] = event
        # Stop once every signal's open segment starts at or after the end.
        if event.start >= end_epoch and all(e.start >= end_epoch for e in open_segment.values()):
            break

    frame = pd.DataFrame(rows, columns=["signal_code", "phase", "start", "duration_s"])
    frame = frame[
        (frame["start"] >= start_epoch) & (frame["start"] + frame["duration_s"] <= end_epoch)
    ]
    frame.insert(0, "intersection_code", plan.intersection_code)
    return frame.sort_values(["start", "signal_code"]).reset_index(drop=True)


@dataclass(frozen=True)
class ObservationSessionConfig:
    """How often someone (or a camera) is watching an intersection.

    Observers record every phase change while a session lasts. The phase in
    progress when a session ends is recorded without a duration.
    """

    mean_gap_s: float = 20 * 60
    session_min_s: int = 5 * 60
    session_max_s: int = 20 * 60


def sample_session_windows(
    start_epoch: int, end_epoch: int, config: ObservationSessionConfig, rng: np.random.Generator
) -> list[tuple[int, int]]:
    windows = []
    t = start_epoch + int(rng.exponential(config.mean_gap_s))
    while t < end_epoch:
        length = int(rng.integers(config.session_min_s, config.session_max_s + 1))
        windows.append((t, min(t + length, end_epoch)))
        t += length + int(rng.exponential(config.mean_gap_s))
    return windows


def observe_segments(segments: pd.DataFrame, windows: list[tuple[int, int]]) -> pd.DataFrame:
    """Turn ground-truth segments into what observers would have recorded.

    A segment is recorded if its start falls inside a session window. Its
    duration is recorded only if it also ended before the window closed.
    """
    if segments.empty or not windows:
        return segments.iloc[0:0].assign(observed_duration_s=pd.Series(dtype="Int64"))

    starts = segments["start"].to_numpy()
    ends = starts + segments["duration_s"].to_numpy()
    window_starts = np.array([w[0] for w in windows])
    window_ends = np.array([w[1] for w in windows])

    idx = np.searchsorted(window_starts, starts, side="right") - 1
    valid = idx >= 0
    inside = np.zeros(len(starts), dtype=bool)
    inside[valid] = starts[valid] < window_ends[idx[valid]]
    duration_known = np.zeros(len(starts), dtype=bool)
    duration_known[inside] = ends[inside] <= window_ends[idx[inside]]

    observed = segments[inside].copy()
    observed["observed_duration_s"] = pd.array(
        np.where(duration_known[inside], observed["duration_s"], 0), dtype="Int64"
    )
    observed.loc[~duration_known[inside], "observed_duration_s"] = pd.NA
    return observed


def to_observation_records(observed: pd.DataFrame, source: str = SYNTHETIC_SOURCE) -> pd.DataFrame:
    """Convert observed segments into the public observation dataset schema."""
    return pd.DataFrame(
        {
            "intersection_code": observed["intersection_code"].to_numpy(),
            "signal_code": observed["signal_code"].to_numpy(),
            "observed_at": pd.to_datetime(observed["start"].to_numpy(), unit="s", utc=True),
            "phase": observed["phase"].to_numpy(),
            "phase_duration_s": observed["observed_duration_s"].to_numpy(),
            "direction": pd.NA,
            "source": source,
            "is_simulated": True,
        }
    )


def generate_observation_dataset(
    plans: list[IntersectionPlan],
    end: datetime,
    days: int,
    seed: int,
    session_config: ObservationSessionConfig | None = None,
) -> pd.DataFrame:
    """Generate a reproducible synthetic observation dataset ending at ``end``."""
    session_config = session_config or ObservationSessionConfig()
    end_epoch = int(end.astimezone(UTC).timestamp())
    start_epoch = end_epoch - days * 24 * 3600
    rng = np.random.default_rng(seed)

    frames = []
    for plan in plans:
        segments = simulate_segments(plan, start_epoch, end_epoch, rng)
        windows = sample_session_windows(start_epoch, end_epoch, session_config, rng)
        frames.append(to_observation_records(observe_segments(segments, windows)))

    dataset = pd.concat(frames, ignore_index=True)
    return dataset.sort_values(["observed_at", "signal_code"]).reset_index(drop=True)
