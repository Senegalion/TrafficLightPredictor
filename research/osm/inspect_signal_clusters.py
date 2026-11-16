import json
import math
from pathlib import Path

from pyproj import Transformer


PROJECT_ROOT = Path(__file__).resolve().parents[2]

INPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "lodz_traffic_signals.json"
)

transformer = Transformer.from_crs(
    "EPSG:4326",
    "EPSG:2180",
    always_xy=True,
)


def load_signals():
    with INPUT_FILE.open("r", encoding="utf-8") as file:
        return json.load(file)["elements"]


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

    components = {}

    for i, signal in enumerate(signals):

        root = find(i)

        components.setdefault(root, [])
        components[root].append(signal)

    return list(components.values())


def cluster_diameter(cluster):

    maximum = 0.0

    for i in range(len(cluster)):

        for j in range(i + 1, len(cluster)):

            d = distance(
                cluster[i],
                cluster[j],
            )

            maximum = max(maximum, d)

    return maximum


def main():

    signals = project_signals(load_signals())

    for radius in [40, 50]:

        components = build_components(
            signals,
            radius,
        )

        components = sorted(
            components,
            key=len,
            reverse=True,
        )

        print("\n" + "=" * 70)
        print(f"TOP CLUSTERS — RADIUS {radius} m")
        print("=" * 70)

        for index, cluster in enumerate(
            components[:20],
            start=1,
        ):

            diameter = cluster_diameter(cluster)

            print(
                f"\nCluster #{index}"
            )

            print(
                f"Signals: {len(cluster)}"
            )

            print(
                f"Diameter: {diameter:.2f} m"
            )

            print(
                "Members:"
            )

            for signal in cluster:

                print(
                    f"  {signal['id']} | "
                    f"{signal['lat']:.7f}, "
                    f"{signal['lon']:.7f}"
                )


if __name__ == "__main__":
    main()