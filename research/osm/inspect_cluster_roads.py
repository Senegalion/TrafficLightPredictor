import json
import math
from pathlib import Path
from collections import defaultdict

from pyproj import Transformer


PROJECT_ROOT = Path(__file__).resolve().parents[2]

SIGNALS_FILE = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "lodz_traffic_signals.json"
)

MATCHES_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "signal_road_matches_v2.json"
)


transformer = Transformer.from_crs(
    "EPSG:4326",
    "EPSG:2180",
    always_xy=True,
)


def load_signals():

    with SIGNALS_FILE.open(
        "r",
        encoding="utf-8",
    ) as file:

        return json.load(file)["elements"]


def load_matches():

    with MATCHES_FILE.open(
        "r",
        encoding="utf-8",
    ) as file:

        return json.load(file)


def project_signals(signals):

    result = []

    for signal in signals:

        x, y = transformer.transform(
            signal["lon"],
            signal["lat"],
        )

        result.append(
            {
                "id": signal["id"],
                "lat": signal["lat"],
                "lon": signal["lon"],
                "x": x,
                "y": y,
            }
        )

    return result


def distance(a, b):

    return math.hypot(
        a["x"] - b["x"],
        a["y"] - b["y"],
    )


def build_components(signals, radius):

    parent = list(range(len(signals)))

    def find(x):

        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]

        return x

    def union(a, b):

        root_a = find(a)
        root_b = find(b)

        if root_a != root_b:
            parent[root_b] = root_a

    for i in range(len(signals)):

        for j in range(i + 1, len(signals)):

            if distance(signals[i], signals[j]) <= radius:
                union(i, j)

    components = defaultdict(list)

    for i, signal in enumerate(signals):

        components[find(i)].append(signal)

    return list(components.values())


def cluster_diameter(cluster):

    maximum = 0.0

    for i in range(len(cluster)):

        for j in range(i + 1, len(cluster)):

            maximum = max(
                maximum,
                distance(cluster[i], cluster[j]),
            )

    return maximum


def main():

    signals = project_signals(load_signals())
    matches = load_matches()

    matches_by_signal = {
        item["signal_id"]: item
        for item in matches
    }

    components = build_components(
        signals,
        radius=40,
    )

    components = sorted(
        components,
        key=len,
        reverse=True,
    )

    print("=" * 70)
    print("CLUSTER → ROAD CONTEXT ANALYSIS")
    print("=" * 70)

    for index, cluster in enumerate(
        components[:20],
        start=1,
    ):

        print("\n" + "-" * 70)

        print(
            f"Cluster #{index}"
        )

        print(
            f"Signals: {len(cluster)}"
        )

        print(
            f"Diameter: "
            f"{cluster_diameter(cluster):.2f} m"
        )

        road_names = defaultdict(set)

        for signal in cluster:

            match = matches_by_signal.get(
                signal["id"]
            )

            if not match:
                continue

            for road in match["nearby_roads"]:

                name = road.get("name")

                if name:

                    road_names[name].add(
                        road["road_id"]
                    )

        print("\nRoad names:")

        for name, road_ids in sorted(
            road_names.items()
        ):

            print(
                f"  {name} "
                f"({len(road_ids)} segments)"
            )

        print("\nSignals:")

        for signal in cluster:

            print(
                f"  {signal['id']} | "
                f"{signal['lat']:.7f}, "
                f"{signal['lon']:.7f}"
            )


if __name__ == "__main__":
    main()