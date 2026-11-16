# tlp-ml – ML pipeline and prediction service

Python package for the Traffic Light Predictor research prototype. It contains:

| Module | Purpose |
|---|---|
| `tlp_ml.simulation` | Synthetic signal timing plans and simulator (**all output is SIMULATED**) |
| `tlp_ml.data` | Observation dataset schema, validation, supervised sample construction, chronological split |
| `tlp_ml.features` | Feature engineering and the statistical cycle baseline |
| `tlp_ml.models` | Gradient-boosting phase classifier (isotonic calibration) and quantile regressors (conformal intervals) |
| `tlp_ml.evaluation` | Accuracy / precision / recall / F1, MAE / RMSE, calibration (Brier, ECE), selective metrics |
| `tlp_ml.training` | End-to-end training pipeline and report generation |
| `tlp_ml.predictor` | Inference with explicit `OK` / `LOW_CONFIDENCE` / `INSUFFICIENT_DATA` / `UNSUPPORTED_SIGNAL` statuses |
| `tlp_ml.service` | FastAPI service used by the Java backend |
| `tlp_ml.feed` | Simulated observation feed that posts to the backend in the local demo |

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

tlp-ml generate-data      # data/synthetic/observations.csv (synthetic, reproducible)
tlp-ml eda                # reports/eda.md
tlp-ml train              # artifacts/model.joblib + reports/metrics.{json,md}
tlp-ml serve              # http://127.0.0.1:8000/docs
pytest && ruff check src tests
```

See [`../docs/ml-pipeline.md`](../docs/ml-pipeline.md) for the method and [`reports/metrics.md`](reports/metrics.md)
for the latest evaluation on synthetic data.
