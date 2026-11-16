import pandas as pd
import pytest

from tlp_ml.data.dataset import (
    DatasetValidationError,
    load_observations,
    save_observations,
    validate_observations,
)


def _row(**overrides):
    row = {
        "intersection_code": "LDZ-KOS-STR",
        "signal_code": "LDZ-KOS-STR-S1",
        "observed_at": "2026-10-01T10:00:00Z",
        "phase": "GREEN",
        "phase_duration_s": 40,
        "direction": None,
        "source": "test",
        "is_simulated": True,
    }
    row.update(overrides)
    return row


def test_valid_rows_are_kept_and_sorted():
    frame = pd.DataFrame([_row(observed_at="2026-10-01T10:01:00Z"), _row()])
    clean, report = validate_observations(frame)
    assert report.valid_rows == 2
    assert clean["observed_at"].is_monotonic_increasing
    assert str(clean["observed_at"].dt.tz) == "UTC"


@pytest.mark.parametrize(
    ("overrides", "reason"),
    [
        ({"phase": "BLUE"}, "invalid_phase"),
        ({"observed_at": "not-a-date"}, "invalid_timestamp"),
        ({"phase_duration_s": 0}, "implausible_duration"),
        ({"phase_duration_s": 10_000}, "implausible_duration"),
        ({"signal_code": None}, "missing_signal_code"),
        ({"is_simulated": "maybe"}, "invalid_is_simulated"),
    ],
)
def test_invalid_rows_are_dropped_with_reason(overrides, reason):
    frame = pd.DataFrame([_row(observed_at="2026-10-01T09:00:00Z"), _row(**overrides)])
    clean, report = validate_observations(frame)
    assert report.valid_rows == 1
    assert report.dropped == {reason: 1}


def test_duplicates_are_dropped():
    clean, report = validate_observations(pd.DataFrame([_row(), _row()]))
    assert len(clean) == 1
    assert report.dropped == {"duplicate": 1}


def test_missing_duration_is_allowed():
    clean, _ = validate_observations(pd.DataFrame([_row(phase_duration_s=None)]))
    assert clean["phase_duration_s"].isna().all()


def test_lowercase_phase_is_normalised():
    clean, _ = validate_observations(pd.DataFrame([_row(phase="green")]))
    assert clean["phase"].iloc[0] == "GREEN"


def test_missing_columns_raise():
    with pytest.raises(DatasetValidationError, match="phase"):
        validate_observations(pd.DataFrame([_row()]).drop(columns=["phase"]))


def test_save_and_load_round_trip(tmp_path, raw_dataset):
    path = tmp_path / "obs.csv"
    save_observations(raw_dataset.head(100), path)
    loaded, report = load_observations(path)
    assert report.valid_rows == 100
    assert loaded["is_simulated"].all()


def test_load_missing_file_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_observations(tmp_path / "missing.csv")
