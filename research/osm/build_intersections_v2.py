import json
import math
from collections import defaultdict, Counter
from pathlib import Path

import osmium
from pyproj import Transformer


PROJECT_ROOT = Path(__file__).resolve().parents[2]

MIN_LAT = 51.6994795
MAX_LAT = 51.8291963

MIN_LON = 19.3571877
MAX_LON = 19.6120062

PBF_FILE = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "lodz_roads.osm.pbf"
)

SIGNALS_FILE = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "lodzkie_traffic_signals.geojson"
)

OUTPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "intersections_v2.json"
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


# Łódź znajduje się w przybliżeniu w UTM zone 34N.
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


def load_signals():

    with SIGNALS_FILE.open(
        "r",
        encoding="utf-8",
    ) as file:

        data = json.load(file)

    signals = {}

    for feature in data["features"]:

        properties = feature.get(
            "properties",
            {},
        )

        signal_id = properties.get("@id")

        if signal_id is None:
            continue

        coordinates = feature["geometry"]["coordinates"]

        lon, lat = coordinates

        if not (
            MIN_LAT <= lat <= MAX_LAT
            and MIN_LON <= lon <= MAX_LON
        ):
            continue

        signals[int(signal_id)] = {
            "signal_id": int(signal_id),
            "latitude": lat,
            "longitude": lon,
        }

    return signals


class RoadNetworkHandler(osmium.SimpleHandler):

    def __init__(self):

        super().__init__()

        self.node_roads = defaultdict(list)
        self.node_coordinates = {}

    def way(self, way):

        highway = way.tags.get("highway")

        if highway not in ROAD_TYPES:
            return

        name = way.tags.get("name")

        road = {
            "road_id": way.id,
            "name": name,
            "highway": highway,
        }

        for node in way.nodes:

            self.node_roads[node.ref].append(
                road
            )

            if node.location.valid():

                self.node_coordinates[node.ref] = (
                    node.location.lat,
                    node.location.lon,
                )


class UnionFind:

    def __init__(self, values):

        self.parent = {
            value: value
            for value in values
        }

    def find(self, value):

        while self.parent[value] != value:

            self.parent[value] = (
                self.parent[self.parent[value]]
            )

            value = self.parent[value]

        return value

    def union(self, a, b):

        root_a = self.find(a)
        root_b = self.find(b)

        if root_a != root_b:
            self.parent[root_b] = root_a


def build_candidate_nodes(handler):

    candidates = {}

    for node_id, roads in handler.node_roads.items():

        unique_roads = {
            road["road_id"]: road
            for road in roads
        }

        if len(unique_roads) < 2:
            continue

        names = {
            road["name"]
            for road in unique_roads.values()
            if road["name"]
        }

        coordinates = handler.node_coordinates.get(
            node_id
        )

        if coordinates is None:
            continue

        candidates[node_id] = {
            "node_id": node_id,
            "latitude": coordinates[0],
            "longitude": coordinates[1],
            "roads": list(unique_roads.values()),
            "road_names": sorted(names),
        }

    return candidates


def cluster_candidates(
    candidates,
    radius_meters=20,
):

    node_ids = list(candidates.keys())

    union_find = UnionFind(node_ids)

    # Prosty spatial grid.
    # 0.00025 stopnia ~= 17-18 m w Łodzi.
    # Grid trochę większy niż radius.
    grid_size = 0.00035

    grid = defaultdict(list)

    for node_id in node_ids:

        candidate = candidates[node_id]

        lat = candidate["latitude"]
        lon = candidate["longitude"]

        cell = (
            int(lat / grid_size),
            int(lon / grid_size),
        )

        grid[cell].append(node_id)

    for node_id in node_ids:

        candidate = candidates[node_id]

        lat = candidate["latitude"]
        lon = candidate["longitude"]

        cell_x = int(lat / grid_size)
        cell_y = int(lon / grid_size)

        for dx in (-1, 0, 1):

            for dy in (-1, 0, 1):

                neighbour_cell = (
                    cell_x + dx,
                    cell_y + dy,
                )

                for other_id in grid.get(
                    neighbour_cell,
                    [],
                ):

                    if node_id >= other_id:
                        continue

                    other = candidates[other_id]

                    distance = distance_meters(
                        lat,
                        lon,
                        other["latitude"],
                        other["longitude"],
                    )

                    if distance <= radius_meters:

                        union_find.union(
                            node_id,
                            other_id,
                        )

    clusters = defaultdict(list)

    for node_id in node_ids:

        root = union_find.find(node_id)

        clusters[root].append(node_id)

    return clusters


def build_intersections(
    candidates,
    clusters,
):

    intersections = []

    for index, node_ids in enumerate(
        clusters.values(),
        start=1,
    ):

        all_roads = {}

        for node_id in node_ids:

            candidate = candidates[node_id]

            for road in candidate["roads"]:

                all_roads[
                    road["road_id"]
                ] = road

        road_names = {
            road["name"]
            for road in all_roads.values()
            if road["name"]
        }

        coordinates = [
            (
                candidates[node_id]["latitude"],
                candidates[node_id]["longitude"],
            )
            for node_id in node_ids
        ]

        latitude = sum(
            point[0]
            for point in coordinates
        ) / len(coordinates)

        longitude = sum(
            point[1]
            for point in coordinates
        ) / len(coordinates)

        diameter = 0.0

        for i in range(len(coordinates)):

            for j in range(i + 1, len(coordinates)):

                distance = distance_meters(
                    coordinates[i][0],
                    coordinates[i][1],
                    coordinates[j][0],
                    coordinates[j][1],
                )

                diameter = max(
                    diameter,
                    distance,
                )

        intersections.append(
            {
                "intersection_id": index,
                "latitude": latitude,
                "longitude": longitude,
                "diameter_m": round(
                    diameter,
                    2,
                ),
                "osm_nodes": [
                    {
                        "node_id": node_id,
                        "latitude": candidates[node_id]["latitude"],
                        "longitude": candidates[node_id]["longitude"],
                    }
                    for node_id in sorted(node_ids)
                ],
                "road_names": sorted(road_names),
                "road_count": len(road_names),
                "roads": list(
                    all_roads.values()
                ),
            }
        )

    return intersections


def assign_signals(
    signals,
    intersections,
    radius_meters,
):

    assigned = []
    unmatched = []

    for signal in signals.values():

        best_intersection = None
        best_distance = float("inf")

        for intersection in intersections:

            distance = distance_meters(
                signal["latitude"],
                signal["longitude"],
                intersection["latitude"],
                intersection["longitude"],
            )

            if distance < best_distance:

                best_distance = distance
                best_intersection = intersection

        if (
            best_intersection is not None
            and best_distance <= radius_meters
        ):

            assigned.append(
                {
                    "signal_id": signal["signal_id"],
                    "latitude": signal["latitude"],
                    "longitude": signal["longitude"],
                    "intersection_id": (
                        best_intersection[
                            "intersection_id"
                        ]
                    ),
                    "distance_m": round(
                        best_distance,
                        2,
                    ),
                }
            )

        else:

            unmatched.append(
                {
                    **signal,
                    "nearest_distance_m": (
                        round(
                            best_distance,
                            2,
                        )
                        if best_intersection
                        else None
                    ),
                }
            )

    return assigned, unmatched


def main():

    signals = load_signals()

    print("=" * 60)
    print("OSM INTERSECTION BUILDER V2")
    print("=" * 60)

    print(
        f"\nTraffic signals: {len(signals)}"
    )

    handler = RoadNetworkHandler()

    print(
        "\nReading OSM road network..."
    )

    handler.apply_file(
        str(PBF_FILE),
        locations=True,
    )

    print(
        f"Road nodes: "
        f"{len(handler.node_roads)}"
    )

    candidates = build_candidate_nodes(
        handler
    )

    print(
        f"Candidate intersection nodes: "
        f"{len(candidates)}"
    )

    print(
        "\nCandidate road-name distribution:"
    )

    distribution = Counter(
        len(
            candidate["road_names"]
        )
        for candidate in candidates.values()
    )

    for count, amount in sorted(
        distribution.items()
    ):

        print(
            f"  {count} road names: "
            f"{amount} nodes"
        )

    for radius in (
        10,
        15,
        20,
        25,
        30,
    ):

        clusters = cluster_candidates(
            candidates,
            radius_meters=radius,
        )

        intersections = build_intersections(
            candidates,
            clusters,
        )

        assigned, unmatched = assign_signals(
            signals,
            intersections,
            radius_meters=30,
        )

        signalized_ids = {
            item["intersection_id"]
            for item in assigned
        }

        print("\n" + "=" * 60)

        print(
            f"CLUSTER RADIUS: {radius} m"
        )

        print("=" * 60)

        print(
            f"Intersection clusters: "
            f"{len(intersections)}"
        )

        print(
            f"Signal assignments: "
            f"{len(assigned)}"
        )

        print(
            f"Unmatched signals: "
            f"{len(unmatched)}"
        )

        print(
            f"Signalized intersections: "
            f"{len(signalized_ids)}"
        )

        if assigned:

            distances = [
                item["distance_m"]
                for item in assigned
            ]

            print(
                f"Average signal distance: "
                f"{sum(distances) / len(distances):.2f} m"
            )

            print(
                f"Maximum signal distance: "
                f"{max(distances):.2f} m"
            )

            buckets = Counter()

            for distance in distances:

                if distance <= 5:
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

            print(
                "\nSignal → intersection distance:"
            )

            for label in (
                "<= 5 m",
                "<= 10 m",
                "<= 15 m",
                "<= 20 m",
                "<= 30 m",
                "> 30 m",
            ):

                print(
                    f"  {label:>8}: "
                    f"{buckets[label]}"
                )

        if radius == 20:

            OUTPUT_FILE.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

            with OUTPUT_FILE.open(
                "w",
                encoding="utf-8",
            ) as file:

                json.dump(
                    {
                        "intersection_clusters": intersections,
                        "signal_assignments": assigned,
                        "unmatched_signals": unmatched,
                    },
                    file,
                    ensure_ascii=False,
                    indent=2,
                )

            print(
                f"\nSaved diagnostic dataset to:"
                f"\n{OUTPUT_FILE}"
            )


if __name__ == "__main__":
    main()