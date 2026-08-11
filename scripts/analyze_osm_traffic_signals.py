import json
from collections import Counter, defaultdict
from pathlib import Path


INPUT_FILE = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "raw"
    / "lodz_traffic_signals.json"
)


def load_data() -> dict:
    with INPUT_FILE.open("r", encoding="utf-8") as file:
        return json.load(file)


def analyze_elements(elements: list[dict]) -> None:
    print("=" * 60)
    print("OSM TRAFFIC SIGNALS — DATA QUALITY AUDIT")
    print("=" * 60)

    print(f"\nTotal traffic signals: {len(elements)}")

    signals_with_tags = [
        element
        for element in elements
        if element.get("tags")
    ]

    print(f"Signals with tags: {len(signals_with_tags)}")

    tag_keys = Counter()

    for element in elements:
        tags = element.get("tags", {})

        for key in tags:
            tag_keys[key] += 1

    print("\nTag keys:")

    for key, count in tag_keys.most_common():
        print(f"  {key}: {count}")

    print("\n" + "-" * 60)
    print("SIGNALS WITH ADDITIONAL METADATA")
    print("-" * 60)

    for key, count in tag_keys.most_common():
        if key != "highway":
            print(f"  {key}: {count}")

    coordinates = [
        (element["lat"], element["lon"])
        for element in elements
        if "lat" in element and "lon" in element
    ]

    if coordinates:
        latitudes = [lat for lat, _ in coordinates]
        longitudes = [lon for _, lon in coordinates]

        print("\n" + "-" * 60)
        print("GEOGRAPHIC RANGE")
        print("-" * 60)

        print(f"  Latitude : {min(latitudes)} - {max(latitudes)}")
        print(f"  Longitude: {min(longitudes)} - {max(longitudes)}")

    print("\n" + "-" * 60)
    print("SAMPLE SIGNALS WITH ADDITIONAL TAGS")
    print("-" * 60)

    samples = []

    for element in elements:
        tags = element.get("tags", {})

        additional_tags = {
            key: value
            for key, value in tags.items()
            if key != "highway"
        }

        if additional_tags:
            samples.append(element)

        if len(samples) >= 10:
            break

    if not samples:
        print("  No signals with additional tags found.")
    else:
        for element in samples:
            print(f"\n  OSM ID: {element['id']}")
            print(f"  Location: {element['lat']}, {element['lon']}")
            print(f"  Tags: {element.get('tags', {})}")


def analyze_tag_values(elements: list[dict]) -> None:
    print("\n" + "-" * 60)
    print("TAG VALUE DISTRIBUTION")
    print("-" * 60)

    tag_values = defaultdict(Counter)

    for element in elements:
        tags = element.get("tags", {})

        for key, value in tags.items():
            tag_values[key][value] += 1

    for key, values in tag_values.items():
        if key == "highway":
            continue

        print(f"\n{key}:")

        for value, count in values.most_common():
            print(f"  {value}: {count}")


def main() -> None:
    data = load_data()

    elements = data.get("elements", [])

    analyze_elements(elements)
    analyze_tag_values(elements)


if __name__ == "__main__":
    main()