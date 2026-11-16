# Exploratory data analysis

> Dataset is 100% SYNTHETIC (simulated observations).

- Rows: 475654 (validation: {'input_rows': 475654, 'valid_rows': 475654, 'dropped_rows': 0, 'dropped_by_reason': {}})
- Intersections: 6, signals: 12
- Time range (UTC): 2026-10-04T00:01:06+00:00 to 2026-10-31T23:59:53+00:00
- Share of simulated rows: 1.000
- Sources: {'synthetic-generator': 475654}
- Phase counts: {'YELLOW': 158590, 'RED': 158540, 'GREEN': 158524}
- Share of observations with known duration: 0.970

## Phase duration (s) by phase and time band

| Phase | Band | n | mean | std | min | median | max |
|---|---|---|---|---|---|---|---|
| GREEN | AM_PEAK | 10451 | 39.81 | 12.92 | 12.0 | 35.0 | 77.0 |
| GREEN | NIGHT | 63275 | 22.88 | 9.52 | 6.0 | 23.0 | 55.0 |
| GREEN | OFF_PEAK | 37851 | 33.41 | 10.14 | 6.0 | 31.0 | 65.0 |
| GREEN | PM_PEAK | 13223 | 41.8 | 13.14 | 13.0 | 38.0 | 79.0 |
| GREEN | WEEKEND | 27649 | 30.68 | 9.41 | 6.0 | 29.0 | 61.0 |
| RED | AM_PEAK | 10353 | 46.83 | 12.92 | 19.0 | 42.0 | 84.0 |
| RED | NIGHT | 62637 | 29.87 | 9.52 | 13.0 | 30.0 | 62.0 |
| RED | OFF_PEAK | 37460 | 40.41 | 10.14 | 13.0 | 38.0 | 72.0 |
| RED | PM_PEAK | 13085 | 48.8 | 13.13 | 20.0 | 45.0 | 86.0 |
| RED | WEEKEND | 27382 | 37.68 | 9.41 | 13.0 | 36.0 | 68.0 |
| YELLOW | AM_PEAK | 10985 | 3.0 | 0.0 | 3.0 | 3.0 | 3.0 |
| YELLOW | NIGHT | 65031 | 3.0 | 0.0 | 3.0 | 3.0 | 3.0 |
| YELLOW | OFF_PEAK | 39466 | 3.0 | 0.0 | 3.0 | 3.0 | 3.0 |
| YELLOW | PM_PEAK | 13947 | 3.0 | 0.0 | 3.0 | 3.0 | 3.0 |
| YELLOW | WEEKEND | 28713 | 3.0 | 0.0 | 3.0 | 3.0 | 3.0 |

## Observations per signal

| Signal | Observations | With duration |
|---|---|---|
| LDZ-BAR-PAB-S1 | 36501 | 0.968 |
| LDZ-BAR-PAB-S2 | 36533 | 0.968 |
| LDZ-KOP-POM-S1 | 34291 | 0.967 |
| LDZ-KOP-POM-S2 | 34313 | 0.966 |
| LDZ-KOS-STR-S1 | 40630 | 0.971 |
| LDZ-KOS-STR-S2 | 40642 | 0.971 |
| LDZ-KOS-ZAM-S1 | 42420 | 0.972 |
| LDZ-KOS-ZAM-S2 | 42398 | 0.972 |
| LDZ-PRZ-LEC-S1 | 38626 | 0.97 |
| LDZ-PRZ-LEC-S2 | 38630 | 0.969 |
| LDZ-SIE-NAR-S1 | 45337 | 0.973 |
| LDZ-SIE-NAR-S2 | 45333 | 0.973 |

## Observations by local hour

| Hour | Observations |
|---|---|
| 0 | 25009 |
| 1 | 23575 |
| 2 | 23859 |
| 3 | 24254 |
| 4 | 26011 |
| 5 | 24770 |
| 6 | 19265 |
| 7 | 17597 |
| 8 | 15447 |
| 9 | 17186 |
| 10 | 17833 |
| 11 | 18893 |
| 12 | 18823 |
| 13 | 18523 |
| 14 | 18509 |
| 15 | 15143 |
| 16 | 16084 |
| 17 | 15437 |
| 18 | 15697 |
| 19 | 17495 |
| 20 | 19394 |
| 21 | 18748 |
| 22 | 23245 |
| 23 | 24857 |
