from datetime import UTC, datetime, timedelta

import httpx
import numpy as np
import pytest
from fastapi.testclient import TestClient

from tlp_ml.feed import BackendClient, SimulatedObserver, observation_body, run_feed
from tlp_ml.service.api import create_app

NOW = datetime(2026, 10, 6, 12, 0, tzinfo=UTC)


@pytest.fixture
def client(trained):
    config, _, _ = trained
    with TestClient(create_app(config.artifacts_dir)) as test_client:
        yield test_client


def test_health_reports_loaded_model(client):
    body = client.get("/health").json()
    assert body["status"] == "UP" and body["model_loaded"] is True


def test_model_info_exposes_data_origin(client):
    body = client.get("/v1/model").json()
    assert body["training_data_origin"] == "SYNTHETIC"
    assert body["signals"]


def test_prediction_endpoint_returns_structured_result(client, trained):
    signal = trained[2].metadata["signals"][0]
    response = client.post(
        "/v1/predictions",
        json={
            "signal_code": signal,
            "target_time": NOW.isoformat(),
            "anchor": {"phase": "RED", "observed_at": (NOW - timedelta(seconds=10)).isoformat()},
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] in ("OK", "LOW_CONFIDENCE")
    assert body["phase"] in ("RED", "YELLOW", "GREEN")
    assert body["model_version"].startswith("tlp-gbm-")


def test_prediction_without_anchor_is_insufficient_data(client, trained):
    signal = trained[2].metadata["signals"][0]
    body = client.post(
        "/v1/predictions", json={"signal_code": signal, "target_time": NOW.isoformat()}
    ).json()
    assert body["status"] == "INSUFFICIENT_DATA"
    assert body["phase"] is None


@pytest.mark.parametrize(
    "payload",
    [
        {"signal_code": "", "target_time": NOW.isoformat()},
        {"signal_code": "S", "target_time": "2026-10-06T12:00:00"},  # naive timestamp
        {
            "signal_code": "S",
            "target_time": NOW.isoformat(),
            "anchor": {"phase": "BLUE", "observed_at": NOW.isoformat()},
        },
    ],
)
def test_invalid_requests_are_rejected(client, payload):
    assert client.post("/v1/predictions", json=payload).status_code == 422


def test_service_without_model_is_degraded(tmp_path):
    with TestClient(create_app(tmp_path)) as test_client:
        assert test_client.get("/health").json()["status"] == "DEGRADED"
        response = test_client.post(
            "/v1/predictions", json={"signal_code": "S", "target_time": NOW.isoformat()}
        )
        assert response.status_code == 503


def test_simulated_observer_reports_ordered_simulated_observations(plans):
    start = int(NOW.timestamp())
    observer = SimulatedObserver(plans, start, np.random.default_rng(0))
    observations = observer.advance(start + 6 * 3600)
    assert observations, "six hours of dense sessions should produce observations"
    times = [o.observed_at for o in observations]
    assert times == sorted(times)
    assert all(o.observed_at <= start + 6 * 3600 for o in observations)
    assert any(o.phase_duration_s is not None for o in observations)
    # advancing again does not repeat earlier observations
    later = observer.advance(start + 7 * 3600)
    keys = {(o.signal_code, o.observed_at) for o in observations}
    assert later and not keys & {(o.signal_code, o.observed_at) for o in later}


def test_observation_body_marks_data_as_simulated(plans):
    observer = SimulatedObserver(plans, int(NOW.timestamp()), np.random.default_rng(1))
    first = observer.advance(int(NOW.timestamp()) + 3 * 3600)[0]
    body = observation_body(first, signal_id=7)
    assert body["simulated"] is True
    assert body["source"] == "demo-simulator"
    assert body["signalId"] == 7


def test_run_feed_posts_to_backend(plans):
    posted = []
    intersections = [
        {
            "id": i + 1,
            "signals": [
                {"id": 10 * (i + 1) + j, "code": code} for j, code in enumerate(plan.signal_codes)
            ],
        }
        for i, plan in enumerate(plans)
    ]

    def handler(request: httpx.Request) -> httpx.Response:
        if request.method == "GET":
            return httpx.Response(200, json=intersections)
        posted.append(request)
        return httpx.Response(201, json={})

    http = httpx.Client(base_url="http://backend", transport=httpx.MockTransport(handler))
    count = run_feed(
        plans,
        BackendClient("http://backend", None, http=http),
        backfill_s=3600,
        tick_s=0,
        seed=1,
        max_ticks=1,
        clock=lambda: NOW.timestamp(),
        sleep=lambda _: None,
    )
    assert count == len(posted) > 0
    assert all(r.url.path.startswith("/api/v1/intersections/") for r in posted)
