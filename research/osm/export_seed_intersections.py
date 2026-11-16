"""Export a small, curated set of OSM-derived signalised intersections.

The output is used to seed the backend database (see
``backend/src/main/resources/db/migration/V2__seed_sample_intersections.sql``).

Only the *locations* and the OSM node ids of the mapped
``highway=traffic_signals`` nodes come from OpenStreetMap. OpenStreetMap
does not describe which approach a signal head controls or how it is timed,
so all signal timing configurations used by the project are synthetic.

Input:  data/processed/intersections_v2.json  (built by build_intersections_v2.py)
Output: data/processed/seed_intersections.json

Data © OpenStreetMap contributors, available under the ODbL.
"""

import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]

INPUT_FILE = PROJECT_ROOT / "data" / "processed" / "intersections_v2.json"
OUTPUT_FILE = PROJECT_ROOT / "data" / "processed" / "seed_intersections.json"

# Cluster ids produced by build_intersections_v2.py for well-known, central
# signalised intersections. They are pipeline-internal ids, not OSM ids.
SELECTED_CLUSTER_IDS = [3422, 3305, 2386, 4517, 3427, 1290]


def main() -> None:
    with INPUT_FILE.open("r", encoding="utf-8") as file:
        data = json.load(file)

    clusters = {c["intersection_id"]: c for c in data["intersection_clusters"]}

    signals_by_cluster: dict[int, list[int]] = {}
    for assignment in data["signal_assignments"]:
        signals_by_cluster.setdefault(assignment["intersection_id"], []).append(
            assignment["signal_id"]
        )

    seed = []
    for cluster_id in SELECTED_CLUSTER_IDS:
        cluster = clusters[cluster_id]
        seed.append(
            {
                "cluster_id": cluster_id,
                "latitude": round(cluster["latitude"], 7),
                "longitude": round(cluster["longitude"], 7),
                "road_names": cluster["road_names"],
                "osm_signal_node_ids": sorted(signals_by_cluster.get(cluster_id, [])),
            }
        )

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_FILE.open("w", encoding="utf-8") as file:
        json.dump(seed, file, ensure_ascii=False, indent=2)

    for item in seed:
        print(item)
    print(f"\nSaved {len(seed)} intersections to: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
