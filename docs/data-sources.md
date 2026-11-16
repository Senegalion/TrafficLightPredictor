# Data sources

Status as of November 2026. The rule throughout the project: **simulated data is never presented
as real**. Every observation carries `simulated: true|false`, every prediction carries `dataOrigin`
and `trainingDataOrigin`, and the UI shows both.

## OpenStreetMap - used

- **What:** `highway=traffic_signals` nodes and the road network of Łódź, from the Overpass API
  and a Geofabrik extract (`lodzkie-latest.osm.pbf`).
- **How:** the feasibility scripts in [`research/osm/`](../research/osm/README.md) cluster road
  nodes into intersections and assign mapped signal nodes to them. 798 signal nodes were matched to
  intersection clusters. `export_seed_intersections.py` exports six well-known central
  intersections. Their centroid coordinates and OSM signal node ids seed the database
  (`V2__seed_sample_intersections.sql`, `location_source = OPENSTREETMAP`).
- **Limits:** OSM records *where* signals are, not which approach they control, how they are
  grouped or timed. Mapping completeness varies.
- **License:** ODbL. Attribution is shown in the UI map, footer and README.

## Signal group configurations - sample data

The two signal groups per intersection (main road / cross street) and their names are **invented**
(`configuration_source = SAMPLE`, "Sample configuration" badge in the UI). They have not been
verified on site.

## Synthetic observations - used for training and the demo

- **Training:** `tlp-ml generate-data` uses invented timing plans
  (`ml/src/tlp_ml/simulation/signal_plans.json`), with noise and observation sessions. Every record
  has `is_simulated = true` and `source = synthetic-generator`.
- **Live demo:** the `simulator` container (`tlp-ml simulate-feed`) posts observations to the
  backend in real time with `simulated = true` and `source = demo-simulator`. It stands in for a
  real data collector and uses the same public ingestion API.

## Open Data Łódź - investigated, not integrated

Portal: <https://otwarte.miasto.lodz.pl/transport_komunikacja/>. The category page was checked in
November 2026.

| Dataset | Format | Relevance |
|---|---|---|
| GTFS (static schedule) | zip | Stops, routes and schedules of trams and buses |
| GTFS-RT `alerts`, `trip_updates`, `vehicle_positions` | protobuf (`.bin` files, refreshed regularly) | Real-time public transport activity |
| Przystanki autobusowe i tramwajowe, Buspasy, Drogi publiczne, Długość dróg dla rowerów, Pojazdy ogółem, Liczba taksówek | CSV (aggregates from GUS Bank Danych Lokalnych) | Context only |

Findings:

- **No dataset on traffic signal state, signal timing or traffic volumes** is published.
- GTFS-RT describes **vehicles**, not signals. It **must not** be treated as a source of signal
  phases. It could later help as a *feature*: an approaching tram may trigger priority and extend
  a green.
- The portal FAQ says the data is published under an open licence that allows re-use, including
  commercial use, with attribution. No specific licence identifier is shown on the category page.
  Confirm the licence on each dataset page before integrating it.
- Nothing is scraped. The datasets are offered as direct downloads.

Integration is deliberately postponed until real signal observations exist. Without them there is
no way to measure whether public-transport features help.

## Own and crowdsourced observations - planned

The ingestion endpoint `POST /api/v1/intersections/{id}/observations` is ready for real data:

- an observation is "the signal switched to phase P at time t", with an optional duration and
  travel direction;
- `source` identifies the collector (e.g. `manual-app`, `video-2026-12-01`), and `simulated: false`
  must be set explicitly;
- validation rejects future timestamps, implausible durations (> 300 s) and duplicates.

Recording sessions of 5–20 minutes at a few intersections, at different times of day, would give a
first real dataset in the same format the pipeline already consumes.

## Computer vision - future

Detecting phases automatically from roadside or dash-cam video would scale data collection. It has
privacy implications (blurring, retention) that need to be addressed first.
