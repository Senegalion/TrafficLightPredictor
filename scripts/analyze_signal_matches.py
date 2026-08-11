import json
from collections import Counter
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent

INPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "signal_road_matches_v2.json"
)


def load_data() -> list[dict]:
    with INPUT_FILE.open("r", encoding="utf-8") as file:
        return json.load(file)


def analyze(data: list[dict]) -> None:

    print("=" * 60)
    print("TRAFFIC SIGNAL MATCH QUALITY ANALYSIS")
    print("=" * 60)

    road_counts = Counter()

    highway_counts = Counter()
    named_road_counts = Counter()

    signals_without_name = []

    for signal in data:

        roads = signal["nearby_roads"]

        road_counts[len(roads)] += 1

        unique_names = set()

        for road in roads:

            highway = road.get("highway")

            if highway:
                highway_counts[highway] += 1

            name = road.get("name")

            if name:
                unique_names.add(name)

        for name in unique_names:
            named_road_counts[name] += 1

        if not unique_names:
            signals_without_name.append(
                signal["signal_id"]
            )

    print("\n" + "-" * 60)
    print("SEGMENTS PER SIGNAL")
    print("-" * 60)

    for count, signals in sorted(road_counts.items()):
        print(
            f"  {count:2d} segments: "
            f"{signals:3d} signals"
        )

    print("\n" + "-" * 60)
    print("HIGHWAY TYPES")
    print("-" * 60)

    for highway, count in highway_counts.most_common():
        print(
            f"  {highway:15s}: {count}"
        )

    print("\n" + "-" * 60)
    print("SIGNALS WITH NO NAMED ROAD")
    print("-" * 60)

    print(
        f"  Count: {len(signals_without_name)}"
    )

    print("\n" + "-" * 60)
    print("MOST COMMON ROAD NAMES")
    print("-" * 60)

    for name, count in named_road_counts.most_common(20):

        print(
            f"  {name}: {count}"
        )

    print("\n" + "-" * 60)
    print("UNIQUE ROAD NAMES PER SIGNAL")
    print("-" * 60)

    unique_name_distribution = Counter()

    for signal in data:

        names = {
            road["name"]
            for road in signal["nearby_roads"]
            if road.get("name")
        }

        unique_name_distribution[len(names)] += 1

    for count, signals in sorted(
        unique_name_distribution.items()
    ):

        print(
            f"  {count:2d} unique names: "
            f"{signals:3d} signals"
        )


def main() -> None:

    data = load_data()

    print(
        f"\nSignals analyzed: {len(data)}"
    )

    analyze(data)


if __name__ == "__main__":
    main()