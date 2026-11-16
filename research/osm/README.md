# OpenStreetMap research scripts

Exploratory scripts from the data-feasibility phase of the project. They download OpenStreetMap
road and `highway=traffic_signals` data for Łódź and investigate how mapped signal nodes relate to
road intersections (clustering, map matching, node topology).

They are kept as research history. Only two outputs are used by the application:

| Script | Output | Used for |
|---|---|---|
| `build_intersections_v2.py` | `data/processed/intersections_v2.json` | intersection clusters with assigned OSM signal nodes |
| `export_seed_intersections.py` | `data/processed/seed_intersections.json` | coordinates + OSM node ids in `backend/.../V2__seed_sample_intersections.sql` |

Raw and processed data are not committed (see `.gitignore`); regenerate them with the download
scripts. Some scripts read `data/external/lodzkie-latest.osm.pbf` (Geofabrik extract, downloaded manually).

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r research/osm/requirements.txt
python research/osm/download_osm_traffic_signals.py     # Overpass API
python research/osm/download_osm_roads.py
python research/osm/build_intersections_v2.py
python research/osm/export_seed_intersections.py
```

Please respect the [Overpass API usage policy](https://dev.overpass-api.de/overpass-doc/en/preface/commons.html)
when re-running downloads. Data © OpenStreetMap contributors, ODbL.

Note: `test_signal_clustering.py` is an experiment script, not a unit test.
