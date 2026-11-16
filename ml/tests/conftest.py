from datetime import UTC, datetime
from pathlib import Path

import pytest

from tlp_ml.data.dataset import save_observations, validate_observations
from tlp_ml.persistence import load_bundle
from tlp_ml.simulation.plans import load_plans
from tlp_ml.simulation.simulator import generate_observation_dataset
from tlp_ml.training import TrainingConfig, run_training

DATASET_END = datetime(2026, 10, 5, tzinfo=UTC)  # a Monday
SMALL_DATASET_DAYS = 4


@pytest.fixture(scope="session")
def plans():
    return load_plans()[:2]


@pytest.fixture(scope="session")
def raw_dataset(plans):
    return generate_observation_dataset(plans, DATASET_END, SMALL_DATASET_DAYS, seed=7)


@pytest.fixture(scope="session")
def observations(raw_dataset):
    frame, _ = validate_observations(raw_dataset)
    return frame


@pytest.fixture(scope="session")
def dataset_csv(raw_dataset, tmp_path_factory) -> Path:
    path = tmp_path_factory.mktemp("data") / "observations.csv"
    save_observations(raw_dataset, path)
    return path


@pytest.fixture(scope="session")
def trained(dataset_csv, tmp_path_factory):
    root = tmp_path_factory.mktemp("model")
    config = TrainingConfig(
        data_path=dataset_csv, artifacts_dir=root / "artifacts", reports_dir=root / "reports"
    )
    report = run_training(config)
    return config, report, load_bundle(config.artifacts_dir)
