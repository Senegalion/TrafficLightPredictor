import json
from collections import Counter, defaultdict
from pathlib import Path

import osmium


PROJECT_ROOT = Path(__file__).resolve().parents[2]

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


def load_signals():
    with SIGNALS_FILE.open(
        "r",
        encoding="utf-8",
    ) as file:
        data = json.load(file)

    signals = {}

    for feature in data["features"]:
        properties = feature.get("properties", {})

        signal_id = properties.get("@id")

        if signal_id is None:
            continue

        coordinates = feature["geometry"]["coordinates"]

        lon, lat = coordinates

        signals[int(signal_id)] = {
            "signal_id": int(signal_id),
            "latitude": lat,
            "longitude": lon,
        }

    return signals


class RoadHandler(osmium.SimpleHandler):

    def __init__(self):
        super().__init__()

        self.node_roads = defaultdict(list)

    def way(self, way):

        highway = way.tags.get("highway")

        if highway not in ROAD_TYPES:
            return

        road = {
            "road_id": way.id,
            "name": way.tags.get("name"),
            "highway": highway,
        }

        for node in way.nodes:
            self.node_roads[node.ref].append(road)


def main():

    signals = load_signals()

    print("=" * 60)
    print("SIGNAL → OSM NODE CONTEXT ANALYSIS")
    print("=" * 60)

    print(
        f"\nSignals: {len(signals)}"
    )

    handler = RoadHandler()

    print("\nReading OSM...")

    handler.apply_file(
        str(PBF_FILE),
        locations=False,
    )

    distribution = Counter()

    examples = defaultdict(list)

    for signal_id in signals:

        roads = handler.node_roads.get(
            signal_id,
            [],
        )

        unique_roads = {
            road["road_id"]: road
            for road in roads
        }

        road_count = len(unique_roads)

        names = {
            road["name"]
            for road in unique_roads.values()
            if road["name"]
        }

        distribution[road_count] += 1

        if len(examples[road_count]) < 10:
            examples[road_count].append(
                (
                    signal_id,
                    sorted(names),
                    list(unique_roads.values()),
                )
            )

    print("\nRoads per signal node:")

    for count, amount in sorted(
        distribution.items()
    ):
        print(
            f"  {count} roads: "
            f"{amount} signals"
        )

    print("\nExamples with exactly 1 road:")

    for signal_id, names, roads in examples[1]:

        print("\n" + "-" * 50)

        print(
            f"Signal: {signal_id}"
        )

        print(
            f"Names: "
            f"{', '.join(names) if names else 'NONE'}"
        )

        for road in roads:

            print(
                f"  {road['road_id']} | "
                f"{road['highway']} | "
                f"{road['name']}"
            )

    print("\nExamples with exactly 2 roads:")

    for signal_id, names, roads in examples[2]:

        print("\n" + "-" * 50)

        print(
            f"Signal: {signal_id}"
        )

        print(
            f"Names: "
            f"{', '.join(names)}"
        )

        for road in roads:

            print(
                f"  {road['road_id']} | "
                f"{road['highway']} | "
                f"{road['name']}"
            )


if __name__ == "__main__":
    main()