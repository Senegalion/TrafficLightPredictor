"""Core domain vocabulary shared by the simulator, the pipeline and the service."""

from __future__ import annotations

from enum import StrEnum
from zoneinfo import ZoneInfo

LOCAL_TIMEZONE = ZoneInfo("Europe/Warsaw")


class Phase(StrEnum):
    """Simplified signal phases.

    Polish signals also show a short RED+YELLOW phase before GREEN. The
    prototype folds it into RED; see docs/ml-pipeline.md.
    """

    RED = "RED"
    YELLOW = "YELLOW"
    GREEN = "GREEN"


PHASES: tuple[Phase, ...] = (Phase.RED, Phase.YELLOW, Phase.GREEN)

#: Fixed order in which a vehicle signal head cycles through its phases.
NEXT_PHASE: dict[Phase, Phase] = {
    Phase.GREEN: Phase.YELLOW,
    Phase.YELLOW: Phase.RED,
    Phase.RED: Phase.GREEN,
}


class TimeBand(StrEnum):
    """Coarse signal-plan periods. Real controllers switch plans by time of day."""

    NIGHT = "NIGHT"
    AM_PEAK = "AM_PEAK"
    PM_PEAK = "PM_PEAK"
    OFF_PEAK = "OFF_PEAK"
    WEEKEND = "WEEKEND"


NIGHT_START_HOUR = 22
NIGHT_END_HOUR = 6
AM_PEAK_HOURS = range(7, 10)
PM_PEAK_HOURS = range(15, 19)
SATURDAY = 5


def time_band(local_hour: int, local_weekday: int) -> TimeBand:
    """Map a local hour (0-23) and weekday (Monday=0) to a signal-plan band."""
    if local_hour >= NIGHT_START_HOUR or local_hour < NIGHT_END_HOUR:
        return TimeBand.NIGHT
    if local_weekday >= SATURDAY:
        return TimeBand.WEEKEND
    if local_hour in AM_PEAK_HOURS:
        return TimeBand.AM_PEAK
    if local_hour in PM_PEAK_HOURS:
        return TimeBand.PM_PEAK
    return TimeBand.OFF_PEAK
