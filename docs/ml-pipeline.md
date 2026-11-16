# ML pipeline

All code is in `ml/src/tlp_ml`. Run it with `tlp-ml generate-data && tlp-ml eda && tlp-ml train`
(or `make ml-train`).

> All metrics in this repository are computed on **synthetic** data. See
> [Evaluation](#evaluation) for what they do and do not show.

## 1. Problem formulation

Real signal state is not published, so the system only ever knows **observations** of the form:

> signal *S* was seen switching to phase *P* at time *s*; optionally, the phase lasted *d* seconds.

Given the most recent such observation (the **anchor**) and a target time *t* (0–15 min later),
predict:

1. the phase at *t* (classification: RED / YELLOW / GREEN);
2. the seconds remaining in that phase at *t* (regression);
3. an uncertainty measure for both;
4. whether the prediction is reliable enough to display.

Phases are simplified to three. The Polish RED+YELLOW transition is counted as RED.

## 2. Data

### Schema

The observation CSV schema (`tlp_ml/data/dataset.py`) is identical for synthetic and real data:
`intersection_code, signal_code, observed_at, phase, phase_duration_s, direction, source,
is_simulated`. Real data exported from the backend's `observations` table maps 1:1.

### Validation

`validate_observations` raises on missing columns. It drops and **counts by reason** any rows with
a missing signal code, an unparseable timestamp, an unknown phase, an implausible duration (<1 s or
>300 s), duplicates `(signal_code, observed_at)`, or an invalid `is_simulated`.

### Synthetic data generator

Because no real observations exist yet, `tlp_ml/simulation` generates a clearly labelled synthetic
dataset:

- **Timing plans** (`signal_plans.json`): six intersections, each with two alternating signal
  groups (main road, cross street), per-band green times (NIGHT, AM_PEAK, PM_PEAK, OFF_PEAK,
  WEEKEND), 3 s yellow, 2 s all-red. **The values are invented.**
- **Actuation-like noise**: each green gets Gaussian jitter (2–4 s) and, with probability 8–20%,
  an extension of 8–10 s (to mimic e.g. tram priority).
- **Observation sessions**: observers watch an intersection in sessions of 5–20 min separated by
  exponential gaps (mean 20 min for training data). Inside a session every phase change is
  recorded. The phase still running at the end of a session has no duration.
- Default: 28 days ending 2026-11-01 00:00 UTC, seed 42. This gives ~476k observations.

## 3. Supervised samples (`data/samples.py`)

Labels come only from observations with a known duration: during `[s, s + d)` the phase is known.

For each such segment:

1. draw a query time *t* uniformly inside the segment;
2. draw a lag *L* ~ U(0, 900 s) and set the information cut-off *c = t − L*;
3. the anchor is the latest observation with `observed_at ≤ c`;
4. discard samples whose anchor is older than 900 s (at serving time these are `INSUFFICIENT_DATA`).

Labels: the phase of the segment, and `s + d − t` as the remaining time. Sampling the lag teaches
the model how uncertainty grows with stale information. The procedure works unchanged on real
observation streams.

## 4. Features (`features.py`)

| Feature | Description |
|---|---|
| `signal_code` | One-hot signal identifier (implies the intersection) |
| `anchor_phase`, `elapsed_s` | Latest *known* phase transition and seconds since then (see below) |
| `hour_sin`, `hour_cos`, `day_of_week`, `is_weekend`, `time_band` | Local (Europe/Warsaw) time context |
| `median_{green,yellow,red}_s`, `median_cycle_s` | Historical medians for the signal and time band; fall back to the signal median if a band has < 5 samples |
| `baseline_phase`, `baseline_remaining_s`, `cycle_position` | Output of the statistical cycle baseline |

**Anchor normalisation and leakage.** If the anchor's duration is known *and* the phase ended
before the cut-off *c*, then the next phase is known to have started at `s + d`. That transition
is used as the effective anchor. A duration that ends after *c* is ignored, because the observer
could not have known it yet. Unit tests cover this (`test_normalise_anchor_...`).

**Statistical cycle baseline.** Assume the median durations repeat: position = (offset of the
anchor phase in the cycle + elapsed) mod median cycle. The predicted phase and remaining time
follow directly. It is explainable and serves both as a benchmark and as an input feature.

Direction of travel is part of the observation schema but is not a feature: the simulator does
not produce it and signal groups already encode the approach.

## 5. Split (`ChronologicalSplit`)

The observation time range is split chronologically: 65% train, 15% calibration, 20% test.

- Samples are assigned by query time.
- Samples whose label segment crosses a boundary are dropped.
- Duration statistics are fitted only on phases that **ended before the calibration period**.

There is no random shuffling, so no future information is used for training.

## 6. Models (`models.py`)

| Target | Model | Uncertainty |
|---|---|---|
| Phase | `HistGradientBoostingClassifier` (300 iterations, lr 0.08, 31 leaves, min 40 samples/leaf) | Isotonic calibration (`CalibratedClassifierCV` on a frozen model) fitted on the calibration split |
| Remaining time | Three `HistGradientBoostingRegressor`s with quantile loss (q = 0.1, 0.5, 0.9) | Split-conformal widening of the 10–90% interval on the calibration split (Romano et al., 2019). Target coverage 80% |

Hyperparameters are reasonable defaults. They were **not** tuned on the test split.

## 7. Reliability policy (`ReliabilityPolicy`)

A prediction is `OK` (displayable) only if:

- the calibrated probability of the predicted phase is ≥ 0.80;
- the remaining-time interval is ≤ 20 s wide;
- the anchor is ≤ 900 s old (otherwise `INSUFFICIENT_DATA`).

Otherwise the status is `LOW_CONFIDENCE` and `reasons` explains why. Unknown signals return
`UNSUPPORTED_SIGNAL`. The thresholds are product choices and are documented in the model metadata.

**What "confidence" means.** It is the model's probability for its predicted phase, recalibrated
so that, *on held-out data from the same distribution*, predictions with confidence ≈ *p* are
correct ≈ *p* of the time (see the reliability table in `metrics.json`). On the synthetic demo
data this holds (ECE ≈ 0.016). It is **not** validated on real signals and must not be read as a
safety guarantee.

## 8. Evaluation

Reported on the chronologically last 20% (`ml/reports/metrics.md`):

- classification: accuracy, macro precision/recall/F1, per-class metrics, confusion matrix;
- remaining time: MAE, RMSE, median and P90 absolute error, plus MAE when the phase is correct;
- uncertainty: interval coverage and width, Brier score and ECE before and after calibration, and
  a reliability table;
- by anchor age (0–1, 1–3, 3–7, 7–15 min);
- selective metrics: share of predictions that would be displayed, and their accuracy and MAE;
- baselines: statistical cycle baseline and persistence ("the anchor phase continues").

Latest results (synthetic data, 58,568 test queries):

| | Model | Cycle baseline | Persistence |
|---|---|---|---|
| Phase accuracy | 0.570 | 0.469 | 0.329 |
| Macro F1 | 0.570 | 0.427 | 0.286 |
| Remaining-time MAE | 7.87 s | 12.87 s | – |
| Remaining-time RMSE | 11.83 s | 17.88 s | – |

The 80% conformal interval achieved 79.9% coverage with a mean width of 25.7 s. 4.8% of queries
pass the reliability gate; on those, accuracy is 96.1% and MAE is 3.5 s.

Interpretation:

- The model improves on the explainable baseline mainly because it learns how uncertainty grows
  with elapsed time and handles phase boundaries better.
- Accuracy decays quickly with anchor age. With noisy cycle lengths, an observation a few cycles
  old says little about the current phase. Frequent observations matter more than model capacity.
- Isotonic calibration did not improve calibration on this data (ECE 0.013 → 0.016). The raw
  boosted-tree probabilities were already well calibrated on synthetic data. Re-evaluate on real data.
- Synthetic data follows the simulator's assumptions by construction, so real-world performance
  will be lower.

## 9. Persistence and serving

`tlp-ml train` writes `artifacts/model.joblib` (models, duration statistics, policy, metadata) and
`artifacts/metadata.json`. The metadata holds the model version, training-data origin
(`SYNTHETIC` / `REAL` / `MIXED`), dataset SHA-256, time range, split boundaries, sample counts and
scikit-learn version. The model version is `tlp-gbm-<date>-<dataset hash>`.

`tlp-ml serve` loads the bundle at start-up. If it is missing, `/health` reports `DEGRADED` and
predictions return 503. The Docker image trains the model at build time, so the image is
self-contained and reproducible.

## 10. Using real data later

1. Export observations from the database to the CSV schema above with `is_simulated=false`.
2. `tlp-ml eda --data real.csv` and inspect validation drops and coverage.
3. `tlp-ml train --data real.csv`. The pipeline refuses to train with fewer than 200 samples per
   split (`InsufficientDataError`).
4. The metadata then says `training_data_origin: REAL`, which the API and UI display.
