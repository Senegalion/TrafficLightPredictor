"""Exploratory data analysis of an observation dataset (text/markdown report)."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from tlp_ml.data.dataset import ValidationReport
from tlp_ml.domain import LOCAL_TIMEZONE
from tlp_ml.features import time_band_series


def summarise(observations: pd.DataFrame, validation: ValidationReport) -> dict:
    df = observations.copy()
    df["time_band"] = time_band_series(df["observed_at"])
    local = df["observed_at"].dt.tz_convert(LOCAL_TIMEZONE)
    with_duration = df[df["phase_duration_s"].notna()].copy()
    with_duration["phase_duration_s"] = with_duration["phase_duration_s"].astype(float)

    durations = (
        with_duration.groupby(["phase", "time_band"])["phase_duration_s"]
        .describe(percentiles=[0.5])
        .round(2)
        .reset_index()
    )
    per_signal = (
        df.groupby("signal_code")
        .agg(
            observations=("phase", "size"),
            share_with_duration=("phase_duration_s", lambda s: float(s.notna().mean())),
        )
        .round(3)
        .reset_index()
    )
    return {
        "validation": validation.to_dict(),
        "rows": int(len(df)),
        "signals": int(df["signal_code"].nunique()),
        "intersections": int(df["intersection_code"].nunique()),
        "time_range": [df["observed_at"].min().isoformat(), df["observed_at"].max().isoformat()],
        "simulated_share": float(df["is_simulated"].mean()),
        "sources": df["source"].value_counts().to_dict(),
        "phase_counts": df["phase"].value_counts().to_dict(),
        "share_with_duration": float(df["phase_duration_s"].notna().mean()),
        "observations_by_local_hour": local.dt.hour.value_counts().sort_index().to_dict(),
        "duration_by_phase_and_band": durations.to_dict(orient="records"),
        "per_signal": per_signal.to_dict(orient="records"),
    }


def render_markdown(summary: dict) -> str:
    synthetic = summary["simulated_share"] >= 1.0
    lines = ["# Exploratory data analysis", ""]
    if synthetic:
        lines += ["> Dataset is 100% SYNTHETIC (simulated observations).", ""]
    lines += [
        f"- Rows: {summary['rows']} (validation: {summary['validation']})",
        f"- Intersections: {summary['intersections']}, signals: {summary['signals']}",
        f"- Time range (UTC): {summary['time_range'][0]} to {summary['time_range'][1]}",
        f"- Share of simulated rows: {summary['simulated_share']:.3f}",
        f"- Sources: {summary['sources']}",
        f"- Phase counts: {summary['phase_counts']}",
        f"- Share of observations with known duration: {summary['share_with_duration']:.3f}",
        "",
        "## Phase duration (s) by phase and time band",
        "",
        "| Phase | Band | n | mean | std | min | median | max |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for r in summary["duration_by_phase_and_band"]:
        lines.append(
            f"| {r['phase']} | {r['time_band']} | {int(r['count'])} | {r['mean']} | "
            f"{r['std']} | {r['min']} | {r['50%']} | {r['max']} |"
        )
    lines += [
        "",
        "## Observations per signal",
        "",
        "| Signal | Observations | With duration |",
        "|---|---|---|",
    ]
    for r in summary["per_signal"]:
        lines.append(f"| {r['signal_code']} | {r['observations']} | {r['share_with_duration']} |")
    lines += ["", "## Observations by local hour", "", "| Hour | Observations |", "|---|---|"]
    for hour, count in summary["observations_by_local_hour"].items():
        lines.append(f"| {hour} | {count} |")
    lines.append("")
    return "\n".join(lines)


def write_eda_report(summary: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_markdown(summary), encoding="utf-8")
