import json
import math
from collections import Counter
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


def load_signals() -> list[dict]:
    with INPUT_FILE.open("r", encoding="utf-8") as file:
        data = json.load(file)

    return data.get("elements", [])


def project_signals(signals: list[dict]) -> list[dict]:

    projected = []

    for signal in signals:

        x, y = transformer.transform(
            signal["lon"],
            signal["lat"],
        )

        projected.append(
            {
                "id": signal["id"],
                "lat": signal["lat"],
                "lon": signal["lon"],
                "x": x,
                "y": y,
            }
        )

    return projected


def distance(a: dict, b: dict) -> float:

    return math.hypot(
        a["x"] - b["x"],
        a["y"] - b["y"],
    )


def build_components(
    signals: list[dict],
    radius: float,
) -> list[list[dict]]:

    parent = list(range(len(signals)))

    def find(x: int) -> int:

        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]

        return x

    def union(a: int, b: int) -> None:

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


def analyze_radius(
    signals: list[dict],
    radius: float,
) -> None:

    components = build_components(
        signals,
        radius,
    )

    sizes = Counter(
        len(component)
        for component in components
    )

    singleton_count = sizes.get(1, 0)

    multi_signal_components = [
        component
        for component in components
        if len(component) > 1
    ]

    largest_component = max(
        len(component)
        for component in components
    )

    print(
        f"\nRadius: {radius:3.0f} m"
    )

    print(
        f"  Components:                 "
        f"{len(components)}"
    )

    print(
        f"  Single-signal components:    "
        f"{singleton_count}"
    )

    print(
        f"  Multi-signal components:      "
        f"{len(multi_signal_components)}"
    )

    print(
        f"  Largest component:            "
        f"{largest_component}"
    )

    print(
        "  Component size distribution:"
    )

    for size, count in sorted(sizes.items()):

        print(
            f"    {size:2d} signals: "
            f"{count:3d} components"
        )


def main() -> None:

    signals = load_signals()

    projected = project_signals(signals)

    print("=" * 60)
    print("TRAFFIC SIGNAL CLUSTERING ANALYSIS")
    print("=" * 60)

    print(
        f"\nSignals: {len(projected)}"
    )

    for radius in [
        20,
        30,
        40,
        50,
        60,
        70,
    ]:

        analyze_radius(
            projected,
            radius,
        )


if __name__ == "__main__":
    main()