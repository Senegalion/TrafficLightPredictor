import json
from collections import defaultdict
from pathlib import Path

import osmium


PROJECT_ROOT = Path(__file__).resolve().parent.parent

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
    / "intersections_raw.json"
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


def load_traffic_signals() -> set[int]:
    with SIGNALS_FILE.open(
        "r",
        encoding="utf-8",
    ) as file:
        data = json.load(file)

    signal_ids = set()

    for feature in data["features"]:
        properties = feature.get("properties", {})

        signal_id = properties.get("@id")

        if signal_id is not None:
            signal_ids.add(int(signal_id))

    return signal_ids


class RoadNetworkHandler(osmium.SimpleHandler):

    def __init__(self):
        super().__init__()

        self.nodes = {}
        self.node_roads = defaultdict(list)

    def way(self, way):

        highway = way.tags.get("highway")

        if highway not in ROAD_TYPES:
            return

        road = {
            "road_id": way.id,
            "name": way.tags.get("name"),
            "highway": highway,
            "lanes": way.tags.get("lanes"),
            "maxspeed": way.tags.get("maxspeed"),
            "oneway": way.tags.get("oneway"),
            "surface": way.tags.get("surface"),
        }

        for node in way.nodes:

            self.nodes[node.ref] = {
                "latitude": node.lat,
                "longitude": node.lon,
            }

            self.node_roads[node.ref].append(road)


def build_intersection(
    node_id: int,
    roads: list[dict],
    coordinates: dict,
    signal_ids: set[int],
) -> dict:

    unique_roads = {}

    for road in roads:
        unique_roads[road["road_id"]] = road

    roads = list(unique_roads.values())

    named_roads = {
        road["name"]
        for road in roads
        if road["name"]
    }

    unnamed_roads = [
        road
        for road in roads
        if not road["name"]
    ]

    # A named road represents one logical road even if
    # OSM split it into multiple ways.
    logical_road_count = (
        len(named_roads)
        + len(unnamed_roads)
    )

    is_signalized = node_id in signal_ids

    return {
        "intersection_id": node_id,
        "latitude": coordinates["latitude"],
        "longitude": coordinates["longitude"],
        "road_count": len(roads),
        "logical_road_count": logical_road_count,
        "unique_road_names": sorted(named_roads),
        "has_traffic_signal": is_signalized,
        "traffic_signal_count": 1 if is_signalized else 0,
        "roads": [
            {
                "road_id": road["road_id"],
                "name": road["name"],
                "highway": road["highway"],
                "lanes": road["lanes"],
                "maxspeed": road["maxspeed"],
                "oneway": road["oneway"],
                "surface": road["surface"],
            }
            for road in roads
        ],
    }


def is_intersection(
    roads: list[dict],
) -> bool:

    unique_roads = {
        road["road_id"]: road
        for road in roads
    }

    roads = list(unique_roads.values())

    named_roads = {
        road["name"]
        for road in roads
        if road["name"]
    }

    unnamed_road_count = sum(
        1
        for road in roads
        if not road["name"]
    )

    logical_road_count = (
        len(named_roads)
        + unnamed_road_count
    )

    # At least two logically different roads.
    if logical_road_count >= 2:
        return True

    # Also keep nodes where one logical road is split
    # into 3+ OSM ways. These are useful candidates for
    # later inspection, especially at complex junctions.
    return len(roads) >= 3


def main():

    print("=" * 60)
    print("OSM INTERSECTION BUILDER")
    print("=" * 60)

    signal_ids = load_traffic_signals()

    print(
        f"\nTraffic signals loaded: "
        f"{len(signal_ids)}"
    )

    handler = RoadNetworkHandler()

    print("\nReading OSM road network...")

    handler.apply_file(
        str(PBF_FILE),
        locations=True,
    )

    print(
        f"Road nodes: "
        f"{len(handler.nodes)}"
    )

    print(
        f"Road-node associations: "
        f"{len(handler.node_roads)}"
    )

    intersections = []

    for node_id, roads in handler.node_roads.items():

        if node_id not in handler.nodes:
            continue

        if not is_intersection(roads):
            continue

        intersection = build_intersection(
            node_id=node_id,
            roads=roads,
            coordinates=handler.nodes[node_id],
            signal_ids=signal_ids,
        )

        intersections.append(intersection)

    intersections.sort(
        key=lambda x: x["intersection_id"]
    )

    signalized = [
        intersection
        for intersection in intersections
        if intersection["has_traffic_signal"]
    ]

    non_signalized = [
        intersection
        for intersection in intersections
        if not intersection["has_traffic_signal"]
    ]

    distribution = defaultdict(int)

    for intersection in intersections:
        distribution[
            intersection["logical_road_count"]
        ] += 1

    print("\n" + "-" * 60)
    print("INTERSECTION RESULTS")
    print("-" * 60)

    print(
        f"\nTotal intersections: "
        f"{len(intersections)}"
    )

    print(
        f"With traffic signals: "
        f"{len(signalized)}"
    )

    print(
        f"Without traffic signals: "
        f"{len(non_signalized)}"
    )

    print("\nLogical roads per intersection:")

    for count, amount in sorted(
        distribution.items()
    ):
        print(
            f"  {count} roads: "
            f"{amount} intersections"
        )

    print("\nSample signalized intersections:")

    for intersection in signalized[:10]:

        print("\n" + "-" * 40)

        print(
            f"Intersection: "
            f"{intersection['intersection_id']}"
        )

        print(
            f"Location: "
            f"{intersection['latitude']}, "
            f"{intersection['longitude']}"
        )

        print(
            f"Logical roads: "
            f"{intersection['logical_road_count']}"
        )

        print(
            f"Road names: "
            f"{', '.join(intersection['unique_road_names'])}"
        )

        for road in intersection["roads"]:
            print(
                f"  {road['road_id']} | "
                f"{road['highway']} | "
                f"{road['name']}"
            )

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with OUTPUT_FILE.open(
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            intersections,
            file,
            ensure_ascii=False,
            indent=2,
        )

    print(
        f"\nSaved to: {OUTPUT_FILE}"
    )


if __name__ == "__main__":
    main()