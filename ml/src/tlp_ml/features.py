"""Feature engineering and the statistical cycle baseline.

Prediction setting
------------------
For a signal and a target time ``t`` we know the most recent *anchor*
observation: "the signal switched to phase P at time s" (optionally with the
phase duration if the observer saw it end). From that we predict the phase at
``t`` and the seconds remaining in it.

Historical duration statistics are fitted on the training split only, so no
information from the evaluation period leaks into the features.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from tlp_ml.domain import (
    AM_PEAK_HOURS,
    LOCAL_TIMEZONE,
    NEXT_PHASE,
    NIGHT_END_HOUR,
    NIGHT_START_HOUR,
    PHASES,
    PM_PEAK_HOURS,
    SATURDAY,
    Phase,
    TimeBand,
)

CATEGORICAL_FEATURES = ["signal_code", "anchor_phase", "time_band", "baseline_phase"]
NUMERIC_FEATURES = [
    "elapsed_s",
    "hour_sin",
    "hour_cos",
    "day_of_week",
    "is_weekend",
    "median_green_s",
    "median_yellow_s",
    "median_red_s",
    "median_cycle_s",
    "cycle_position",
    "baseline_remaining_s",
]
FEATURE_COLUMNS = CATEGORICAL_FEATURES + NUMERIC_FEATURES

#: Minimum number of completed phases needed before a per-(signal, band)
#: median is trusted; otherwise we fall back to the per-signal median.
MIN_DURATIONS_FOR_BAND_MEDIAN = 5
HOURS_PER_DAY = 24.0

# Duration columns in phase-cycle order for the vehicle head: GREEN, YELLOW, RED.
_DURATION_COLUMNS = {
    Phase.GREEN: "median_green_s",
    Phase.YELLOW: "median_yellow_s",
    Phase.RED: "median_red_s",
}


@dataclass
class DurationStats:
    """Median phase durations per (signal, time band), fitted on training data."""

    table: pd.DataFrame  # index: (signal_code, time_band); columns: median_*_s
    signals: frozenset[str]

    @classmethod
    def fit(cls, observations: pd.DataFrame) -> DurationStats:
        completed = observations[observations["phase_duration_s"].notna()].copy()
        if completed.empty:
            raise ValueError("Cannot fit duration statistics: no observation has a duration")
        completed["time_band"] = time_band_series(completed["observed_at"])
        completed["phase_duration_s"] = completed["phase_duration_s"].astype(float)

        signals = sorted(completed["signal_code"].unique())
        global_median = completed.groupby("phase")["phase_duration_s"].median()
        signal_median = completed.groupby(["signal_code", "phase"])["phase_duration_s"].median()
        band_group = completed.groupby(["signal_code", "time_band", "phase"])["phase_duration_s"]
        band_median = band_group.median()
        band_count = band_group.count()

        rows = []
        for signal in signals:
            for band in TimeBand:
                row = {"signal_code": signal, "time_band": band.value}
                for phase, column in _DURATION_COLUMNS.items():
                    key = (signal, band.value, phase.value)
                    if band_count.get(key, 0) >= MIN_DURATIONS_FOR_BAND_MEDIAN:
                        value = band_median[key]
                    elif (signal, phase.value) in signal_median.index:
                        value = signal_median[(signal, phase.value)]
                    else:
                        value = global_median.get(phase.value, np.nan)
                    row[column] = float(value)
                rows.append(row)
        table = pd.DataFrame(rows).set_index(["signal_code", "time_band"])
        if table.isna().any().any():
            raise ValueError("Duration statistics incomplete: some phases were never observed")
        table["median_cycle_s"] = table[list(_DURATION_COLUMNS.values())].sum(axis=1)
        return cls(table=table, signals=frozenset(signals))


def time_band_series(timestamps: pd.Series) -> pd.Series:
    """Vectorised :func:`tlp_ml.domain.time_band` for UTC timestamps."""
    local = pd.to_datetime(timestamps, utc=True).dt.tz_convert(LOCAL_TIMEZONE)
    hour = local.dt.hour
    weekday = local.dt.day_of_week
    band = np.select(
        [
            (hour >= NIGHT_START_HOUR) | (hour < NIGHT_END_HOUR),
            weekday >= SATURDAY,
            hour.isin(list(AM_PEAK_HOURS)),
            hour.isin(list(PM_PEAK_HOURS)),
        ],
        [
            TimeBand.NIGHT.value,
            TimeBand.WEEKEND.value,
            TimeBand.AM_PEAK.value,
            TimeBand.PM_PEAK.value,
        ],
        default=TimeBand.OFF_PEAK.value,
    )
    return pd.Series(band, index=timestamps.index, dtype="object")


def normalise_anchor(
    anchor_phase: np.ndarray,
    anchor_start: np.ndarray,
    anchor_duration: np.ndarray,
    cutoff: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    """Return the latest phase transition known at ``cutoff``.

    If the anchor phase is known to have ended before the cutoff, the next
    phase in the cycle is known to have started at ``start + duration``.
    A duration that ends after the cutoff is *not* used: the observer could
    not have known it yet (this guards against target leakage).
    """
    duration = np.asarray(anchor_duration, dtype=float)
    ended = ~np.isnan(duration) & (anchor_start + np.nan_to_num(duration) <= cutoff)
    phase = np.asarray(anchor_phase, dtype=object).copy()
    start = np.asarray(anchor_start, dtype=float).copy()
    phase[ended] = [NEXT_PHASE[Phase(p)].value for p in phase[ended]]
    start[ended] = start[ended] + duration[ended]
    return phase, start


def cycle_baseline(
    anchor_phase: np.ndarray,
    elapsed_s: np.ndarray,
    green_s: np.ndarray,
    yellow_s: np.ndarray,
    red_s: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Project the anchor forward assuming median phase durations repeat.

    Returns (predicted phase, remaining seconds, position within the cycle in [0, 1)).
    """
    cycle = green_s + yellow_s + red_s
    offset = np.select(
        [anchor_phase == Phase.GREEN.value, anchor_phase == Phase.YELLOW.value],
        [0.0, green_s],
        default=green_s + yellow_s,
    )
    position = np.mod(offset + elapsed_s, cycle)
    phase = np.select(
        [position < green_s, position < green_s + yellow_s],
        [Phase.GREEN.value, Phase.YELLOW.value],
        default=Phase.RED.value,
    ).astype(object)
    remaining = np.select(
        [position < green_s, position < green_s + yellow_s],
        [green_s - position, green_s + yellow_s - position],
        default=cycle - position,
    )
    return phase, remaining, position / cycle


def build_feature_frame(queries: pd.DataFrame, stats: DurationStats) -> pd.DataFrame:
    """Compute model features.

    ``queries`` needs: signal_code, target_epoch, anchor_phase, anchor_start,
    anchor_duration (NaN if unknown) and cutoff_epoch (when the information
    was available; at serving time this equals target_epoch).
    """
    target = pd.to_datetime(queries["target_epoch"], unit="s", utc=True)
    local = target.dt.tz_convert(LOCAL_TIMEZONE)
    hour = local.dt.hour + local.dt.minute / 60.0 + local.dt.second / 3600.0
    band = time_band_series(target)

    phase, start = normalise_anchor(
        queries["anchor_phase"].to_numpy(dtype=object),
        queries["anchor_start"].to_numpy(dtype=float),
        queries["anchor_duration"].to_numpy(dtype=float),
        queries["cutoff_epoch"].to_numpy(dtype=float),
    )
    elapsed = queries["target_epoch"].to_numpy(dtype=float) - start

    keys = pd.MultiIndex.from_arrays([queries["signal_code"].to_numpy(), band.to_numpy()])
    medians = stats.table.reindex(keys)
    if medians.isna().any().any():
        unknown = sorted(set(queries["signal_code"]) - stats.signals)
        raise ValueError(f"No duration statistics for signals: {unknown}")

    green = medians["median_green_s"].to_numpy()
    yellow = medians["median_yellow_s"].to_numpy()
    red = medians["median_red_s"].to_numpy()
    base_phase, base_remaining, position = cycle_baseline(phase, elapsed, green, yellow, red)

    weekday = local.dt.day_of_week.to_numpy()
    angle = 2 * np.pi * hour.to_numpy() / HOURS_PER_DAY
    return pd.DataFrame(
        {
            "signal_code": queries["signal_code"].to_numpy(),
            "anchor_phase": phase,
            "time_band": band.to_numpy(),
            "baseline_phase": base_phase,
            "elapsed_s": elapsed,
            "hour_sin": np.sin(angle),
            "hour_cos": np.cos(angle),
            "day_of_week": weekday,
            "is_weekend": (weekday >= SATURDAY).astype(int),
            "median_green_s": green,
            "median_yellow_s": yellow,
            "median_red_s": red,
            "median_cycle_s": medians["median_cycle_s"].to_numpy(),
            "cycle_position": position,
            "baseline_remaining_s": base_remaining,
        },
        index=queries.index,
    )


def phase_labels() -> list[str]:
    return [p.value for p in PHASES]
