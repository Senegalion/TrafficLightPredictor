import json
from collections import defaultdict, Counter
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

OUTPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "signal_node_neighborhood.json"
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

        coordinates = feature["geometry"]["coordinates"]

        signals[int(signal_id)] = {
            "signal_id": int(signal_id),
            "latitude": coordinates[1],
            "longitude": coordinates[0],
        }

    return signals


class RoadNetworkHandler(osmium.SimpleHandler):

    def __init__(self):
        super().__init__()

        self.node_roads = defaultdict(list)
        self.way_nodes = {}
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

        node_ids = []

        for node in way.nodes:

            node_id = node.ref
            node_ids.append(node_id)

            self.node_roads[node_id].append(road)

            if node.location.valid():
                self.node_coordinates[node_id] = (
                    node.location.lat,
                    node.location.lon,
                )

        self.way_nodes[way.id] = node_ids


def haversine_m(lat1, lon1, lat2, lon2):

    from math import radians, sin, cos, sqrt, atan2

    earth_radius = 6_371_000

    phi1 = radians(lat1)
    phi2 = radians(lat2)

    delta_phi = radians(lat2 - lat1)
    delta_lambda = radians(lon2 - lon1)

    a = (
        sin(delta_phi / 2) ** 2
        + cos(phi1)
        * cos(phi2)
        * sin(delta_lambda / 2) ** 2
    )

    return (
        2
        * earth_radius
        * atan2(
            sqrt(a),
            sqrt(1 - a),
        )
    )


def get_neighbors(handler, node_id):

    neighbors = []

    roads = handler.node_roads.get(node_id, [])

    unique_way_ids = {
        road["road_id"]
        for road in roads
    }

    for way_id in unique_way_ids:

        nodes = handler.way_nodes.get(way_id, [])

        try:
            index = nodes.index(node_id)
        except ValueError:
            continue

        candidate_ids = []

        if index > 0:
            candidate_ids.append(nodes[index - 1])

        if index < len(nodes) - 1:
            candidate_ids.append(nodes[index + 1])

        road = next(
            road
            for road in roads
            if road["road_id"] == way_id
        )

        for neighbor_id in candidate_ids:

            if neighbor_id == node_id:
                continue

            coordinates = handler.node_coordinates.get(
                neighbor_id
            )

            if coordinates is None:
                continue

            neighbors.append(
                {
                    "node_id": neighbor_id,
                    "road_id": way_id,
                    "road_name": road["name"],
                    "highway": road["highway"],
                    "latitude": coordinates[0],
                    "longitude": coordinates[1],
                }
            )

    unique_neighbors = {}

    for neighbor in neighbors:

        key = (
            neighbor["node_id"],
            neighbor["road_id"],
        )

        unique_neighbors[key] = neighbor

    return list(unique_neighbors.values())


def main():

    signals = load_signals()

    print("=" * 60)
    print("SIGNAL NODE NEIGHBORHOOD ANALYSIS")
    print("=" * 60)

    print(
        f"\nTraffic signals: {len(signals)}"
    )

    handler = RoadNetworkHandler()

    print("\nReading OSM road network...")

    handler.apply_file(
        str(PBF_FILE),
        locations=True,
    )

    exact_signals = []

    for signal_id, signal in signals.items():

        roads = handler.node_roads.get(
            signal_id,
            [],
        )

        if not roads:
            continue

        unique_roads = {
            road["road_id"]: road
            for road in roads
        }

        neighbors = get_neighbors(
            handler,
            signal_id,
        )

        signal_road_names = {
            road["name"]
            for road in unique_roads.values()
            if road["name"]
        }

        neighborhood_names = {
            neighbor["road_name"]
            for neighbor in neighbors
            if neighbor["road_name"]
        }

        new_names = (
            neighborhood_names
            - signal_road_names
        )

        exact_signals.append(
            {
                "signal_id": signal_id,
                "latitude": signal["latitude"],
                "longitude": signal["longitude"],
                "signal_roads": list(
                    unique_roads.values()
                ),
                "signal_road_names": sorted(
                    signal_road_names
                ),
                "neighbors": neighbors,
                "neighbor_road_names": sorted(
                    neighborhood_names
                ),
                "new_neighborhood_road_names": sorted(
                    new_names
                ),
                "has_new_neighborhood_road": bool(
                    new_names
                ),
            }
        )

    print(
        f"\nExact signal/node matches: "
        f"{len(exact_signals)}"
    )

    distribution = Counter(
        len(
            signal["new_neighborhood_road_names"]
        )
        for signal in exact_signals
    )

    print(
        "\nNew road names discovered in "
        "1-hop neighborhood:"
    )

    for count, amount in sorted(
        distribution.items()
    ):

        print(
            f"  {count} new names: "
            f"{amount} signals"
        )

    signals_with_new_names = [
        signal
        for signal in exact_signals
        if signal[
            "has_new_neighborhood_road"
        ]
    ]

    print(
        "\nSignals with additional road names "
        "in neighborhood: "
        f"{len(signals_with_new_names)}"
    )

    print(
        "\nExamples:"
    )

    for signal in signals_with_new_names[:30]:

        print("\n" + "-" * 60)

        print(
            f"Signal: "
            f"{signal['signal_id']}"
        )

        print(
            f"Location: "
            f"{signal['latitude']}, "
            f"{signal['longitude']}"
        )

        print(
            "Signal road names: "
            + (
                ", ".join(
                    signal["signal_road_names"]
                )
                or "NONE"
            )
        )

        print(
            "Neighborhood road names: "
            + (
                ", ".join(
                    signal[
                        "neighbor_road_names"
                    ]
                )
                or "NONE"
            )
        )

        print(
            "NEW road names: "
            + (
                ", ".join(
                    signal[
                        "new_neighborhood_road_names"
                    ]
                )
                or "NONE"
            )
        )

        print(
            f"Neighbors: "
            f"{len(signal['neighbors'])}"
        )

        for neighbor in signal[
            "neighbors"
        ]:

            distance = haversine_m(
                signal["latitude"],
                signal["longitude"],
                neighbor["latitude"],
                neighbor["longitude"],
            )

            print(
                f"  {neighbor['node_id']} | "
                f"{distance:.2f} m | "
                f"{neighbor['road_name']}"
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