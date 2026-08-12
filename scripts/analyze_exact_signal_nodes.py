import json
from collections import defaultdict, Counter
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
    / "exact_signal_node_topology.json"
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
    with SIGNALS_FILE.open("r", encoding="utf-8") as file:
        data = json.load(file)

    signals = {}

    for feature in data["features"]:
        properties = feature.get("properties", {})
        signal_id = properties.get("@id")

        if signal_id is None:
            continue

        signals[int(signal_id)] = {
            "signal_id": int(signal_id),
            "latitude": feature["geometry"]["coordinates"][1],
            "longitude": feature["geometry"]["coordinates"][0],
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

        road = {
            "road_id": way.id,
            "name": way.tags.get("name"),
            "highway": highway,
        }

        for node in way.nodes:
            self.node_roads[node.ref].append(road)

            if node.location.valid():
                self.node_coordinates[node.ref] = (
                    node.location.lat,
                    node.location.lon,
                )


def main():

    signals = load_signals()

    print("=" * 60)
    print("EXACT SIGNAL NODE TOPOLOGY ANALYSIS")
    print("=" * 60)

    print(f"\nTraffic signals: {len(signals)}")

    handler = RoadNetworkHandler()

    print("\nReading OSM road network...")

    handler.apply_file(
        str(PBF_FILE),
        locations=True,
    )

    exact_signals = []

    for signal_id, signal in signals.items():

        roads = handler.node_roads.get(signal_id, [])

        if not roads:
            continue

        unique_roads = {
            road["road_id"]: road
            for road in roads
        }

        exact_signals.append(
            {
                "signal_id": signal_id,
                "latitude": signal["latitude"],
                "longitude": signal["longitude"],
                "roads": list(unique_roads.values()),
            }
        )

    print(
        f"\nExact signal/node matches: "
        f"{len(exact_signals)}"
    )

    distribution = Counter()

    for signal in exact_signals:

        names = {
            road["name"]
            for road in signal["roads"]
            if road["name"]
        }

        distribution[len(names)] += 1

    print("\nLogical road-name distribution:")

    for count, amount in sorted(distribution.items()):
        print(
            f"  {count} road names: "
            f"{amount} signals"
        )

    print("\nExamples:")

    for signal in exact_signals[:30]:

        names = sorted(
            {
                road["name"]
                for road in signal["roads"]
                if road["name"]
            }
        )

        print("\n" + "-" * 60)

        print(
            f"Signal: {signal['signal_id']}"
        )

        print(
            f"Location: "
            f"{signal['latitude']}, "
            f"{signal['longitude']}"
        )

        print(
            f"Road names: "
            f"{', '.join(names) if names else 'NONE'}"
        )

        print(
            f"OSM ways: "
            f"{len(signal['roads'])}"
        )

        for road in signal["roads"]:

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
            exact_signals,
            file,
            ensure_ascii=False,
            indent=2,
        )

    print(
        f"\nSaved to: {OUTPUT_FILE}"
    )


if __name__ == "__main__":
    main()