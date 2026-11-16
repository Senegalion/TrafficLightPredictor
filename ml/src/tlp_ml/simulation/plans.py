"""Loading of the synthetic signal timing plans (see signal_plans.json)."""

from __future__ import annotations

import json
from dataclasses import dataclass
from importlib import resources
from pathlib import Path

from tlp_ml.domain import TimeBand


@dataclass(frozen=True)
class IntersectionPlan:
    """Synthetic two-group fixed-time plan with random actuation-like noise.

    The main and cross signal groups alternate: main GREEN -> YELLOW ->
    all-red clearance -> cross GREEN -> YELLOW -> all-red clearance.
    """

    intersection_code: str
    main_signal: str
    cross_signal: str
    greens: dict[TimeBand, tuple[int, int]]
    yellow_s: int
    all_red_s: int
    green_jitter_s: float
    extension_probability: float
    extension_s: int
    min_green_s: int

    @property
    def signal_codes(self) -> tuple[str, str]:
        return self.main_signal, self.cross_signal


def load_plans(path: Path | None = None) -> list[IntersectionPlan]:
    """Load plans from ``path`` or from the packaged default file."""
    if path is None:
        raw = resources.files("tlp_ml.simulation").joinpath("signal_plans.json").read_text("utf-8")
    else:
        raw = path.read_text("utf-8")
    document = json.loads(raw)
    defaults = document["defaults"]

    plans = []
    for item in document["intersections"]:
        merged = {**defaults, **item}
        greens = {TimeBand(band): (int(v[0]), int(v[1])) for band, v in merged["greens"].items()}
        missing = set(TimeBand) - set(greens)
        if missing:
            raise ValueError(f"{item['intersection_code']}: missing time bands {sorted(missing)}")
        plans.append(
            IntersectionPlan(
                intersection_code=merged["intersection_code"],
                main_signal=merged["main_signal"],
                cross_signal=merged["cross_signal"],
                greens=greens,
                yellow_s=int(merged["yellow_s"]),
                all_red_s=int(merged["all_red_s"]),
                green_jitter_s=float(merged["green_jitter_s"]),
                extension_probability=float(merged["extension_probability"]),
                extension_s=int(merged["extension_s"]),
                min_green_s=int(merged["min_green_s"]),
            )
        )
    return plans
