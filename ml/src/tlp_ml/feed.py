"""Simulated observation feed for the local demo.

Plays the role a real data collector (camera, crowdsourcing app, manual
observer) would have: it watches the *simulated* signals in observation
sessions and posts what it saw to the backend ingestion API. Every record is
posted with ``simulated=true`` and ``source=demo-simulator``.
"""

from __future__ import annotations

import logging
import time
from collections.abc import Callable, Iterator
from dataclasses import dataclass, field
from datetime import UTC, datetime

import httpx
import numpy as np

from tlp_ml.simulation.plans import IntersectionPlan
from tlp_ml.simulation.simulator import ObservationSessionConfig, PhaseEvent, iter_phase_events

log = logging.getLogger(__name__)

FEED_SOURCE = "demo-simulator"
HTTP_CONFLICT = 409
#: Denser observation sessions than in the training dataset, so the demo
#: usually has a recent observation to predict from.
DEMO_SESSION_CONFIG = ObservationSessionConfig(
    mean_gap_s=5 * 60, session_min_s=5 * 60, session_max_s=20 * 60
)


@dataclass(frozen=True)
class FeedObservation:
    intersection_code: str
    signal_code: str
    observed_at: int
    phase: str
    phase_duration_s: int | None


@dataclass
class _PlanState:
    plan: IntersectionPlan
    events: Iterator[PhaseEvent]
    pending: PhaseEvent
    open_segments: dict[str, PhaseEvent] = field(default_factory=dict)
    windows: list[tuple[int, int]] = field(default_factory=list)


class SimulatedObserver:
    """Produces observations of simulated signals as simulated time advances."""

    def __init__(
        self,
        plans: list[IntersectionPlan],
        start_epoch: int,
        rng: np.random.Generator,
        session_config: ObservationSessionConfig = DEMO_SESSION_CONFIG,
    ):
        self._rng = rng
        self._config = session_config
        self._states = []
        for plan in plans:
            events = iter_phase_events(plan, start_epoch, rng)
            state = _PlanState(plan=plan, events=events, pending=next(events))
            state.windows.append(self._next_window(start_epoch))
            self._states.append(state)

    def _next_window(self, after: int) -> tuple[int, int]:
        start = after + int(self._rng.exponential(self._config.mean_gap_s))
        length = int(self._rng.integers(self._config.session_min_s, self._config.session_max_s + 1))
        return start, start + length

    def advance(self, now: int) -> list[FeedObservation]:
        """Return observations whose recording became final at or before ``now``."""
        out: list[FeedObservation] = []
        for state in self._states:
            while state.windows[-1][1] <= now:
                state.windows.append(self._next_window(state.windows[-1][1]))
            while state.pending.start <= now:
                event = state.pending
                previous = state.open_segments.get(event.signal_code)
                if previous is not None:
                    observation = self._observe(state, previous, event.start)
                    if observation is not None:
                        out.append(observation)
                state.open_segments[event.signal_code] = event
                state.pending = next(state.events)
            # Keep only windows that can still contain unfinished segments.
            oldest_open = min((e.start for e in state.open_segments.values()), default=now)
            state.windows = [w for w in state.windows if w[1] > oldest_open] or state.windows[-1:]
        out.sort(key=lambda o: o.observed_at)
        return out

    def _observe(self, state: _PlanState, segment: PhaseEvent, end: int) -> FeedObservation | None:
        for window_start, window_end in state.windows:
            if window_start <= segment.start < window_end:
                known = end <= window_end
                return FeedObservation(
                    intersection_code=state.plan.intersection_code,
                    signal_code=segment.signal_code,
                    observed_at=segment.start,
                    phase=segment.phase.value,
                    phase_duration_s=(end - segment.start) if known else None,
                )
        return None


class BackendClient:
    def __init__(self, base_url: str, api_key: str | None, http: httpx.Client | None = None):
        headers = {"X-Api-Key": api_key} if api_key else {}
        self._http = http or httpx.Client(base_url=base_url, headers=headers, timeout=10.0)

    def signal_index(self) -> dict[str, tuple[int, int]]:
        """Map signal code -> (intersection id, signal id)."""
        response = self._http.get("/api/v1/intersections")
        response.raise_for_status()
        index = {}
        for intersection in response.json():
            for signal in intersection.get("signals", []):
                index[signal["code"]] = (intersection["id"], signal["id"])
        return index

    def post(self, intersection_id: int, body: dict) -> int:
        response = self._http.post(
            f"/api/v1/intersections/{intersection_id}/observations", json=body
        )
        if response.status_code != HTTP_CONFLICT:
            response.raise_for_status()
        return response.status_code


def observation_body(observation: FeedObservation, signal_id: int) -> dict:
    return {
        "signalId": signal_id,
        "observedAt": datetime.fromtimestamp(observation.observed_at, UTC).isoformat(),
        "phase": observation.phase,
        "phaseDurationSeconds": observation.phase_duration_s,
        "direction": None,
        "source": FEED_SOURCE,
        "simulated": True,
    }


def wait_for_signal_index(
    client: BackendClient, attempts: int, delay_s: float, sleep: Callable[[float], None]
) -> dict[str, tuple[int, int]]:
    for attempt in range(1, attempts + 1):
        try:
            return client.signal_index()
        except httpx.HTTPError as error:
            log.warning("Backend not ready", extra={"attempt": attempt, "error": str(error)})
            sleep(delay_s)
    raise RuntimeError("Backend did not become available")


def run_feed(
    plans: list[IntersectionPlan],
    client: BackendClient,
    backfill_s: int,
    tick_s: float,
    seed: int,
    max_ticks: int | None = None,
    clock: Callable[[], float] = time.time,
    sleep: Callable[[float], None] = time.sleep,
) -> int:
    index = wait_for_signal_index(client, attempts=30, delay_s=2.0, sleep=sleep)
    known_plans = [p for p in plans if all(code in index for code in p.signal_codes)]
    skipped = sorted(
        {p.intersection_code for p in plans} - {p.intersection_code for p in known_plans}
    )
    if skipped:
        log.warning(
            "Plans without matching backend signals are skipped", extra={"intersections": skipped}
        )

    observer = SimulatedObserver(
        known_plans, int(clock()) - backfill_s, np.random.default_rng(seed)
    )
    posted = 0
    ticks = 0
    while max_ticks is None or ticks < max_ticks:
        for observation in observer.advance(int(clock())):
            intersection_id, signal_id = index[observation.signal_code]
            try:
                client.post(intersection_id, observation_body(observation, signal_id))
                posted += 1
            except httpx.HTTPError as error:
                log.warning("Posting observation failed", extra={"error": str(error)})
        if ticks == 0:
            log.info("Backfill complete", extra={"posted": posted})
        ticks += 1
        sleep(tick_s)
    return posted
