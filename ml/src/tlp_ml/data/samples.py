"""Construction of supervised examples from an observation stream.

Labels come only from observations whose duration is known: during
``[observed_at, observed_at + duration)`` the phase of the signal is known.
For each such segment we draw query times inside it and pair each query with
the most recent observation available ``lag`` seconds earlier. Sampling the
lag simulates the realistic case where the latest information is stale.

This works identically on synthetic and on real observation datasets.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from tlp_ml.data.dataset import epoch_seconds

#: Predictions are only attempted when the newest observation is at most this
#: old. Beyond that, accumulated cycle-length noise makes the phase close to
#: unpredictable from a single anchor (see the evaluation by anchor age).
MAX_ANCHOR_AGE_S = 900

SAMPLE_COLUMNS = [
    "signal_code",
    "target_epoch",
    "cutoff_epoch",
    "anchor_phase",
    "anchor_start",
    "anchor_duration",
    "label_phase",
    "label_remaining_s",
    "label_segment_end",
]


def build_samples(
    observations: pd.DataFrame,
    rng: np.random.Generator,
    samples_per_segment: int = 1,
    max_anchor_age_s: int = MAX_ANCHOR_AGE_S,
) -> pd.DataFrame:
    frames = []
    for signal_code, group in observations.groupby("signal_code", sort=True):
        frame = _build_for_signal(
            str(signal_code), group, rng, samples_per_segment, max_anchor_age_s
        )
        if not frame.empty:
            frames.append(frame)
    if not frames:
        return pd.DataFrame(columns=SAMPLE_COLUMNS)
    return pd.concat(frames, ignore_index=True).sort_values("target_epoch").reset_index(drop=True)


def _build_for_signal(
    signal_code: str,
    group: pd.DataFrame,
    rng: np.random.Generator,
    samples_per_segment: int,
    max_anchor_age_s: int,
) -> pd.DataFrame:
    group = group.sort_values("observed_at")
    starts = epoch_seconds(group["observed_at"]).to_numpy()
    phases = group["phase"].astype(str).to_numpy()
    durations = group["phase_duration_s"].astype(float).to_numpy()

    labelled = np.flatnonzero(~np.isnan(durations))
    if labelled.size == 0:
        return pd.DataFrame(columns=SAMPLE_COLUMNS)
    labelled = np.repeat(labelled, samples_per_segment)

    seg_start = starts[labelled]
    seg_end = seg_start + durations[labelled]
    target = seg_start + rng.random(labelled.size) * durations[labelled]
    lag = rng.random(labelled.size) * max_anchor_age_s
    cutoff = target - lag

    anchor = np.searchsorted(starts, cutoff, side="right") - 1
    valid = anchor >= 0
    valid[valid] &= (target[valid] - starts[anchor[valid]]) <= max_anchor_age_s

    anchor = anchor[valid]
    return pd.DataFrame(
        {
            "signal_code": signal_code,
            "target_epoch": target[valid],
            "cutoff_epoch": cutoff[valid],
            "anchor_phase": phases[anchor],
            "anchor_start": starts[anchor],
            "anchor_duration": durations[anchor],
            "label_phase": phases[labelled[valid]],
            "label_remaining_s": seg_end[valid] - target[valid],
            "label_segment_end": seg_end[valid],
        }
    )


@dataclass(frozen=True)
class ChronologicalSplit:
    """Time boundaries (epoch seconds) for train / calibration / test."""

    calibration_start: float
    test_start: float

    @classmethod
    def from_fractions(
        cls, observations: pd.DataFrame, train_fraction: float, calibration_fraction: float
    ) -> ChronologicalSplit:
        if not 0 < train_fraction < 1 or not 0 < calibration_fraction < 1 - train_fraction:
            raise ValueError("Invalid split fractions")
        epoch = epoch_seconds(observations["observed_at"])
        first, last = float(epoch.min()), float(epoch.max())
        span = last - first
        return cls(
            calibration_start=first + span * train_fraction,
            test_start=first + span * (train_fraction + calibration_fraction),
        )

    def observations_before(self, observations: pd.DataFrame, boundary: float) -> pd.DataFrame:
        """Observations whose whole phase is known before ``boundary``."""
        epoch = epoch_seconds(observations["observed_at"])
        end = epoch + observations["phase_duration_s"].astype(float).fillna(0.0)
        return observations[end < boundary]

    def assign(self, samples: pd.DataFrame) -> dict[str, pd.DataFrame]:
        """Split samples by target time; drop samples whose label crosses a boundary."""
        t = samples["target_epoch"]
        end = samples["label_segment_end"]
        train = samples[(end < self.calibration_start)]
        calibration = samples[(t >= self.calibration_start) & (end < self.test_start)]
        test = samples[t >= self.test_start]
        return {"train": train, "calibration": calibration, "test": test}
