# Evaluation report - `tlp-gbm-20261116-6c78bded`

> **All results below are measured on SYNTHETIC demonstration data** produced by
> the project's simulator. They show that the pipeline works; they say nothing
> about how well real Łódź traffic signals can be predicted.

- Trained at: 2026-11-16T11:01:22.322013+00:00
- Training data origin: SYNTHETIC
- Dataset: `observations.csv` (sha256 `6c78bded96a3`)
- Dataset time range: 2026-10-04T00:01:06+00:00 to 2026-10-31T23:59:53+00:00
- Chronological split: calibration from 2026-10-22T04:48:18.550000+00:00, test from 2026-10-26T09:36:07.600000+00:00
- Samples: {'train': 193417, 'calibration': 45692, 'test': 58568}

## Phase classification (test split)

| Model | Accuracy | Macro precision | Macro recall | Macro F1 |
|---|---|---|---|---|
| Gradient boosting (calibrated) | 0.570 | 0.575 | 0.569 | 0.570 |
| Cycle baseline | 0.469 | 0.507 | 0.474 | 0.427 |
| Persistence (anchor phase) | 0.329 | 0.334 | 0.333 | 0.286 |

## Remaining time in current phase (test split)

| Model | MAE (s) | RMSE (s) | Median AE (s) | P90 AE (s) |
|---|---|---|---|---|
| Gradient boosting (median) | 7.87 | 11.83 | 4.70 | 19.79 |
| ... when phase is correct | 5.71 | 8.75 | 3.14 | 14.82 |
| Cycle baseline | 12.87 | 17.88 | 9.00 | 31.00 |

Conformalised 80% interval: empirical coverage 0.799, mean width 25.7 s.

## Probability calibration (test split)

- Brier score: 0.5196 before, 0.5217 after isotonic calibration
- Expected calibration error: 0.0127 before, 0.0156 after

## Accuracy by anchor age

| Anchor age (s) | n | Model accuracy | Baseline accuracy | Model MAE (s) |
|---|---|---|---|---|
| [0, 60) | 3972 | 0.829 | 0.731 | 4.74 |
| [60, 180) | 10571 | 0.701 | 0.591 | 6.55 |
| [180, 420) | 16604 | 0.593 | 0.479 | 7.81 |
| [420, 900) | 27421 | 0.468 | 0.378 | 8.86 |

## Predictions the system would display

- Display rate: 0.048 of test queries
- Phase accuracy when displayed: 0.961
- Remaining-time MAE when displayed: 3.49 s (P90 7.96 s)
- Policy: {'min_confidence': 0.8, 'max_interval_width_s': 20.0, 'max_anchor_age_s': 900}
