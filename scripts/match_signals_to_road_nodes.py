import json
from collections import defaultdict
from pathlib import Path

import osmium


PROJECT_ROOT = Path(__file__).resolve().parent.parent

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
    / "signal_road_node_matches.json"
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
            "tags": properties,
        }

    return signals


class RoadNodeHandler(osmium.SimpleHandler):

    def __init__(self):
        super().__init__()

        self.road_nodes = defaultdict(list)

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

            self.road_nodes[node.ref].append(
                road
            )


def main():

    signals = load_signals()

    print("=" * 60)
    print("TRAFFIC SIGNAL → OSM ROAD NODE MATCHING")
    print("=" * 60)

    print(
        f"\nTraffic signals: {len(signals)}"
    )

    handler = RoadNodeHandler()

    print(
        "\nReading road network..."
    )

    handler.apply_file(
        str(PBF_FILE),
        locations=False,
    )

    exact_matches = []

    unmatched = []

    for signal_id, signal in signals.items():

        roads = handler.road_nodes.get(
            signal_id,
            []
        )

        if roads:

            road_ids = {
                road["road_id"]
                for road in roads
            }

            names = sorted(
                {
                    road["name"]
                    for road in roads
                    if road["name"]
                }
            )

            exact_matches.append(
                {
                    "signal_id": signal_id,
                    "latitude": signal["latitude"],
                    "longitude": signal["longitude"],
                    "road_node_id": signal_id,
                    "roads": [
                        {
                            "road_id": road["road_id"],
                            "name": road["name"],
                            "highway": road["highway"],
                        }
                        for road in {
                            road["road_id"]: road
                            for road in roads
                        }.values()
                    ],
                    "road_count": len(road_ids),
                    "unique_road_names": len(names),
                }
            )

        else:

            unmatched.append(signal)

    print("\n" + "-" * 60)
    print("MATCHING RESULTS")
    print("-" * 60)

    print(
        f"\nExact signal/node matches: "
        f"{len(exact_matches)}"
    )

    print(
        f"Signals without exact node match: "
        f"{len(unmatched)}"
    )

    if signals:

        percentage = (
            len(exact_matches)
            / len(signals)
            * 100
        )

        print(
            f"\nExact match rate: "
            f"{percentage:.2f}%"
        )

    print(
        "\nRoads per exact-match node:"
    )

    distribution = defaultdict(int)

    for match in exact_matches:

        distribution[
            match["road_count"]
        ] += 1

    for count, signals_count in sorted(
        distribution.items()
    ):

        print(
            f"  {count} roads: "
            f"{signals_count} signals"
        )

    print(
        "\nExamples of exact matches:"
    )

    for match in exact_matches[:20]:

        print(
            f"\nSignal {match['signal_id']}"
        )

        print(
            f"  Location: "
            f"{match['latitude']}, "
            f"{match['longitude']}"
        )

        print(
            f"  Roads: "
            f"{match['road_count']}"
        )

        for road in match["roads"]:

            print(
                f"    {road['road_id']} | "
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
            {
                "exact_matches": exact_matches,
                "unmatched": unmatched,
            },
            file,
            ensure_ascii=False,
            indent=2,
        )

    print(
        f"\nSaved to: {OUTPUT_FILE}"
    )


if __name__ == "__main__":
    main()