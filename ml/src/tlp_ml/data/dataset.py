"""Observation dataset schema, loading and validation.

The CSV schema is deliberately the same for synthetic and real observations,
so real data exported from the backend can replace the synthetic dataset
without code changes:

=================  ========================================================
column             meaning
=================  ========================================================
intersection_code  external intersection code, e.g. ``LDZ-KOS-STR``
signal_code        external signal code, e.g. ``LDZ-KOS-STR-S1``
observed_at        ISO-8601 timestamp (UTC) at which the signal was
                   observed switching to ``phase``
phase              RED, YELLOW or GREEN
phase_duration_s   how long that phase lasted, if the observer saw it end
direction          optional travel direction (NORTHBOUND, ...)
source             free-text data source identifier
is_simulated       true for synthetic/simulated records
=================  ========================================================
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd

from tlp_ml.domain import PHASES

REQUIRED_COLUMNS = (
    "intersection_code",
    "signal_code",
    "observed_at",
    "phase",
    "phase_duration_s",
    "direction",
    "source",
    "is_simulated",
)

#: Longest plausible duration of a single phase. Longer values are treated
#: as recording errors (e.g. an observer who forgot to stop the timer).
MAX_PLAUSIBLE_PHASE_DURATION_S = 300
MIN_PHASE_DURATION_S = 1


class DatasetValidationError(ValueError):
    """Raised when a dataset is structurally unusable."""


@dataclass
class ValidationReport:
    input_rows: int
    valid_rows: int
    dropped: dict[str, int] = field(default_factory=dict)

    @property
    def dropped_rows(self) -> int:
        return self.input_rows - self.valid_rows

    def to_dict(self) -> dict:
        return {
            "input_rows": self.input_rows,
            "valid_rows": self.valid_rows,
            "dropped_rows": self.dropped_rows,
            "dropped_by_reason": self.dropped,
        }


def validate_observations(frame: pd.DataFrame) -> tuple[pd.DataFrame, ValidationReport]:
    """Return a cleaned copy of ``frame`` and a report of dropped rows.

    Structural problems (missing columns) raise :class:`DatasetValidationError`;
    row-level problems drop the offending rows and are counted in the report.
    """
    missing = [c for c in REQUIRED_COLUMNS if c not in frame.columns]
    if missing:
        raise DatasetValidationError(f"Missing required columns: {missing}")

    df = frame.loc[:, list(REQUIRED_COLUMNS)].copy()
    report = ValidationReport(input_rows=len(df), valid_rows=0)

    def drop(mask: pd.Series, reason: str) -> None:
        nonlocal df
        count = int(mask.sum())
        if count:
            report.dropped[reason] = report.dropped.get(reason, 0) + count
            df = df[~mask]

    drop(
        df["signal_code"].isna() | (df["signal_code"].astype("string").str.strip() == ""),
        "missing_signal_code",
    )

    df["observed_at"] = pd.to_datetime(df["observed_at"], utc=True, errors="coerce", format="mixed")
    drop(df["observed_at"].isna(), "invalid_timestamp")

    df["phase"] = df["phase"].astype("string").str.upper().str.strip()
    drop(~df["phase"].isin([p.value for p in PHASES]), "invalid_phase")

    df["phase_duration_s"] = pd.to_numeric(df["phase_duration_s"], errors="coerce")
    duration = df["phase_duration_s"]
    implausible = duration.notna() & (
        (duration < MIN_PHASE_DURATION_S) | (duration > MAX_PLAUSIBLE_PHASE_DURATION_S)
    )
    drop(implausible, "implausible_duration")

    drop(df.duplicated(subset=["signal_code", "observed_at"], keep="first"), "duplicate")

    df["is_simulated"] = df["is_simulated"].map(_parse_bool)
    drop(df["is_simulated"].isna(), "invalid_is_simulated")

    df["phase_duration_s"] = df["phase_duration_s"].astype("Float64")
    df["is_simulated"] = df["is_simulated"].astype(bool)
    df = df.sort_values(["signal_code", "observed_at"]).reset_index(drop=True)
    report.valid_rows = len(df)
    return df, report


def epoch_seconds(timestamps: pd.Series) -> pd.Series:
    """UTC timestamps as float seconds since the Unix epoch."""
    return pd.to_datetime(timestamps, utc=True).dt.as_unit("ns").astype("int64") / 1e9


def _parse_bool(value: object) -> bool | None:
    if isinstance(value, bool):
        return value
    text = str(value).strip().lower()
    if text in {"true", "1", "yes"}:
        return True
    if text in {"false", "0", "no"}:
        return False
    return None


def load_observations(path: Path) -> tuple[pd.DataFrame, ValidationReport]:
    if not path.exists():
        raise FileNotFoundError(f"Observation dataset not found: {path}")
    raw = pd.read_csv(path, dtype={"signal_code": "string", "intersection_code": "string"})
    return validate_observations(raw)


def save_observations(frame: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    out = frame.copy()
    out["observed_at"] = pd.to_datetime(out["observed_at"], utc=True).dt.strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )
    out.to_csv(path, index=False)
