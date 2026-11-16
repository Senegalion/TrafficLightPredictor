import json
import math
from pathlib import Path

from pyproj import Transformer


PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATA_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "intersections_v2.json"
)


TRANSFORMER = Transformer.from_crs(
    "EPSG:4326",
    "EPSG:32634",
    always_xy=True,
)


def distance_meters(
    lat1,
    lon1,
    lat2,
    lon2,
):
    x1, y1 = TRANSFORMER.transform(
        lon1,
        lat1,
    )

    x2, y2 = TRANSFORMER.transform(
        lon2,
        lat2,
    )

    return math.hypot(
        x2 - x1,
        y2 - y1,
    )


def main():

    with DATA_FILE.open(
        "r",
        encoding="utf-8",
    ) as file:
        data = json.load(file)

    intersections = data[
        "intersection_clusters"
    ]

    assignments = data[
        "signal_assignments"
    ]

    unmatched = data[
        "unmatched_signals"
    ]

    print("=" * 60)
    print("SIGNAL → INTERSECTION NODE ANALYSIS")
    print("=" * 60)

    print(
        f"\nIntersections: {len(intersections)}"
    )

    print(
        f"Assigned signals: {len(assignments)}"
    )

    print(
        f"Unmatched signals: {len(unmatched)}"
    )

    intersection_by_id = {
        intersection["intersection_id"]: intersection
        for intersection in intersections
    }

    results = []

    for assignment in assignments:

        intersection = intersection_by_id[
            assignment["intersection_id"]
        ]

        signal_lat = assignment["latitude"]
        signal_lon = assignment["longitude"]

        centroid_distance = assignment[
            "distance_m"
        ]

        nearest_node = None
        nearest_node_distance = float("inf")

        exact_node_match = False

        for node in intersection["osm_nodes"]:

            distance = distance_meters(
                signal_lat,
                signal_lon,
                node["latitude"],
                node["longitude"],
            )

            if distance < nearest_node_distance:

                nearest_node_distance = distance
                nearest_node = node

            if node["node_id"] == assignment["signal_id"]:

                exact_node_match = True

        results.append(
            {
                "signal_id": assignment["signal_id"],
                "intersection_id": assignment[
                    "intersection_id"
                ],
                "centroid_distance_m": centroid_distance,
                "nearest_node_distance_m": round(
                    nearest_node_distance,
                    2,
                ),
                "exact_node_match": exact_node_match,
                "nearest_node_id": (
                    nearest_node["node_id"]
                    if nearest_node
                    else None
                ),
                "intersection_diameter_m": intersection[
                    "diameter_m"
                ],
                "road_names": intersection[
                    "road_names"
                ],
            }
        )

    results.sort(
        key=lambda item: item[
            "centroid_distance_m"
        ],
        reverse=True,
    )

    print(
        "\nDistance comparison:"
    )

    buckets = {
        "<= 2 m": 0,
        "<= 5 m": 0,
        "<= 10 m": 0,
        "<= 15 m": 0,
        "<= 20 m": 0,
        "<= 30 m": 0,
        "> 30 m": 0,
    }

    for result in results:

        distance = result[
            "nearest_node_distance_m"
        ]

        if distance <= 2:
            buckets["<= 2 m"] += 1
        elif distance <= 5:
            buckets["<= 5 m"] += 1
        elif distance <= 10:
            buckets["<= 10 m"] += 1
        elif distance <= 15:
            buckets["<= 15 m"] += 1
        elif distance <= 20:
            buckets["<= 20 m"] += 1
        elif distance <= 30:
            buckets["<= 30 m"] += 1
        else:
            buckets["> 30 m"] += 1

    for label, count in buckets.items():

        print(
            f"{label:>8}: "
            f"{count:4d}"
        )

    exact_matches = sum(
        1
        for result in results
        if result["exact_node_match"]
    )

    print(
        f"\nExact signal/node matches "
        f"inside assigned intersections: "
        f"{exact_matches}"
    )

    print(
        "\nWorst centroid → nearest-node differences:"
    )

    for result in results[:30]:

        improvement = (
            result["centroid_distance_m"]
            - result["nearest_node_distance_m"]
        )

        print(
            f"{result['signal_id']} | "
            f"centroid="
            f"{result['centroid_distance_m']:.2f} m | "
            f"nearest node="
            f"{result['nearest_node_distance_m']:.2f} m | "
            f"improvement="
            f"{improvement:.2f} m | "
            f"exact="
            f"{result['exact_node_match']} | "
            f"roads="
            f"{', '.join(result['road_names'])}"
        )

    print(
        "\nAverage distances:"
    )

    average_centroid = (
        sum(
            result["centroid_distance_m"]
            for result in results
        )
        / len(results)
    )

    average_node = (
        sum(
            result["nearest_node_distance_m"]
            for result in results
        )
        / len(results)
    )

    print(
        f"Centroid distance: "
        f"{average_centroid:.2f} m"
    )

    print(
        f"Nearest OSM node distance: "
        f"{average_node:.2f} m"
    )


if __name__ == "__main__":
    main()