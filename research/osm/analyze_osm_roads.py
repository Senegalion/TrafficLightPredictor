import json
from collections import Counter
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]

INPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "lodzkie_roads.geojson"
)


def load_data() -> dict:
    with INPUT_FILE.open("r", encoding="utf-8") as file:
        return json.load(file)


def analyze_features(features: list[dict]) -> None:
    print("=" * 60)
    print("OSM ROAD NETWORK — DATA QUALITY AUDIT")
    print("=" * 60)

    print(f"\nTotal road features: {len(features)}")

    geometry_types = Counter(
        feature.get("geometry", {}).get("type")
        for feature in features
    )

    print("\nGeometry types:")
    for geometry_type, count in geometry_types.most_common():
        print(f"  {geometry_type}: {count}")

    tag_keys = Counter()

    for feature in features:
        properties = feature.get("properties", {})

        for key in properties:
            tag_keys[key] += 1

    print("\nTag keys:")
    for key, count in tag_keys.most_common():
        print(f"  {key}: {count}")

    print("\n" + "-" * 60)
    print("HIGHWAY CLASS DISTRIBUTION")
    print("-" * 60)

    highway_values = Counter()

    for feature in features:
        highway = feature.get("properties", {}).get("highway")

        if highway:
            highway_values[highway] += 1

    for highway, count in highway_values.most_common():
        print(f"  {highway}: {count}")

    print("\n" + "-" * 60)
    print("ROAD NAME COVERAGE")
    print("-" * 60)

    with_name = 0
    without_name = 0

    for feature in features:
        properties = feature.get("properties", {})

        if properties.get("name"):
            with_name += 1
        else:
            without_name += 1

    print(f"  With name:    {with_name}")
    print(f"  Without name: {without_name}")

    print("\n" + "-" * 60)
    print("IMPORTANT TAG COVERAGE")
    print("-" * 60)

    important_tags = [
        "name",
        "ref",
        "lanes",
        "maxspeed",
        "oneway",
        "junction",
        "surface",
        "bridge",
        "tunnel",
    ]

    for tag in important_tags:
        count = tag_keys[tag]
        percentage = (count / len(features)) * 100

        print(
            f"  {tag:10} {count:6} "
            f"({percentage:6.2f}%)"
        )

    print("\n" + "-" * 60)
    print("SAMPLE ROAD FEATURES")
    print("-" * 60)

    for feature in features[:10]:
        properties = feature.get("properties", {})
        geometry = feature.get("geometry", {})

        print("\n  OSM ID:", properties.get("@id"))
        print("  Geometry:", geometry.get("type"))
        print("  Properties:", properties)


def main() -> None:
    data = load_data()

    features = data.get("features", [])

    analyze_features(features)


if __name__ == "__main__":
    main()