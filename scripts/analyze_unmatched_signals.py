import json
from pathlib import Path

import osmium
from pyproj import Transformer
from scipy.spatial import cKDTree


PROJECT_ROOT = Path(__file__).resolve().parent.parent

PBF_FILE = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "lodz_roads.osm.pbf"
)

MATCHES_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "signal_road_node_matches.json"
)


# WGS84 → Poland CS92
TRANSFORMER = Transformer.from_crs(
    "EPSG:4326",
    "EPSG:2180",
    always_xy=True,
)


ROAD_TYPES = {
    "motorway",
    "trunk",
    "primary",
    "secondary",
    "tertiary",
    "residential",
    "unclassified",
    "living_street",
}


class RoadNodeHandler(osmium.SimpleHandler):

    def __init__(self):
        super().__init__()

        self.nodes = {}

    def way(self, way):

        highway = way.tags.get("highway")

        if highway not in ROAD_TYPES:
            return

        for node in way.nodes:

            try:
                location = node.location
            except RuntimeError:
                continue

            if not location.valid():
                continue

            self.nodes[node.ref] = (
                location.lon,
                location.lat,
            )


def distance_meters(
    lon1,
    lat1,
    lon2,
    lat2,
):

    x1, y1 = TRANSFORMER.transform(
        lon1,
        lat1,
    )

    x2, y2 = TRANSFORMER.transform(
        lon2,
        lat2,
    )

    dx = x1 - x2
    dy = y1 - y2

    return (dx * dx + dy * dy) ** 0.5


def main():

    with MATCHES_FILE.open(
        "r",
        encoding="utf-8",
    ) as file:

        matches = json.load(file)

    unmatched = matches["unmatched"]

    print("=" * 60)
    print("UNMATCHED TRAFFIC SIGNAL ANALYSIS")
    print("=" * 60)

    print(
        f"\nUnmatched signals: {len(unmatched)}"
    )

    handler = RoadNodeHandler()

    print(
        "\nReading road node coordinates..."
    )

    handler.apply_file(
        str(PBF_FILE),
        locations=True,
    )

    print(
        f"Road nodes: {len(handler.nodes)}"
    )

    node_ids = list(handler.nodes.keys())

    coordinates = []

    for node_id in node_ids:

        lon, lat = handler.nodes[node_id]

        x, y = TRANSFORMER.transform(
            lon,
            lat,
        )

        coordinates.append(
            (x, y)
        )

    tree = cKDTree(coordinates)

    print(
        "\nNearest road-node analysis:"
    )

    results = []

    for signal in unmatched:

        lon = signal["longitude"]
        lat = signal["latitude"]

        x, y = TRANSFORMER.transform(
            lon,
            lat,
        )

        distance, index = tree.query(
            [x, y]
        )

        nearest_node_id = node_ids[index]

        results.append(
            {
                "signal_id": signal["signal_id"],
                "latitude": lat,
                "longitude": lon,
                "nearest_node_id": nearest_node_id,
                "distance_m": float(distance),
            }
        )

    results.sort(
        key=lambda item: item["distance_m"]
    )

    print(
        "\nDistance distribution:"
    )

    buckets = [
        1,
        2,
        5,
        10,
        15,
        20,
        30,
        40,
        50,
        100,
    ]

    for limit in buckets:

        count = sum(
            r["distance_m"] <= limit
            for r in results
        )

        print(
            f"  <= {limit:3d} m: "
            f"{count:3d}"
        )

    print(
        "\nFarthest unmatched signals:"
    )

    for result in results[-20:]:

        print(
            f"{result['distance_m']:8.2f} m | "
            f"{result['signal_id']} -> "
            f"{result['nearest_node_id']}"
        )

    print(
        "\nClosest unmatched signals:"
    )

    for result in results[:30]:

        print(
            f"{result['distance_m']:8.2f} m | "
            f"{result['signal_id']} -> "
            f"{result['nearest_node_id']}"
        )


if __name__ == "__main__":
    main()