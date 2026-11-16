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


class RoadHandler(osmium.SimpleHandler):

    def __init__(self):
        super().__init__()

        self.node_roads = defaultdict(list)

        self.road_count = 0

    def way(self, way):

        highway = way.tags.get("highway")

        if highway not in ROAD_TYPES:
            return

        self.road_count += 1

        road_name = way.tags.get("name")

        for node in way.nodes:

            self.node_roads[node.ref].append(
                {
                    "road_id": way.id,
                    "name": road_name,
                    "highway": highway,
                }
            )


def main():

    handler = RoadHandler()

    print("Reading OSM road network...")

    handler.apply_file(
        str(PBF_FILE),
        locations=False,
    )

    print()
    print("=" * 60)
    print("OSM ROAD NODE ANALYSIS")
    print("=" * 60)

    print(
        f"\nRoad ways: {handler.road_count}"
    )

    node_degree = Counter(
        len(roads)
        for roads in handler.node_roads.values()
    )

    print("\nRoads meeting at node:")

    for degree, count in sorted(
        node_degree.items()
    ):

        print(
            f"  {degree} roads: {count}"
        )

    intersection_nodes = []

    for node_id, roads in handler.node_roads.items():

        road_ids = {
            road["road_id"]
            for road in roads
        }

        if len(road_ids) < 2:
            continue

        names = {
            road["name"]
            for road in roads
            if road["name"]
        }

        intersection_nodes.append(
            {
                "node_id": node_id,
                "road_count": len(road_ids),
                "unique_names": len(names),
                "roads": roads,
            }
        )

    print(
        "\nPotential intersection nodes: "
        f"{len(intersection_nodes)}"
    )

    print(
        "\nNodes with multiple named roads:"
    )

    named = [
        node
        for node in intersection_nodes
        if node["unique_names"] >= 2
    ]

    print(
        f"  {len(named)} nodes"
    )

    print("\nSample nodes:")

    for node in named[:30]:

        names = sorted(
            {
                road["name"]
                for road in node["roads"]
                if road["name"]
            }
        )

        print(
            f"\nNode {node['node_id']}"
        )

        print(
            f"  Roads: {node['road_count']}"
        )

        print(
            f"  Names: {', '.join(names)}"
        )


if __name__ == "__main__":
    main()