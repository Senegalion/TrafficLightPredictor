import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]

INPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "signal_road_matches_v2.json"
)


def load_data() -> list[dict]:
    with INPUT_FILE.open("r", encoding="utf-8") as file:
        return json.load(file)


def get_unique_names(signal: dict) -> list[str]:
    return sorted({
        road["name"]
        for road in signal["nearby_roads"]
        if road.get("name")
    })


def print_signal(signal: dict) -> None:

    names = get_unique_names(signal)

    print("\n" + "=" * 70)

    print(
        f"Signal ID: {signal['signal_id']}"
    )

    print(
        f"Location: "
        f"{signal['latitude']}, "
        f"{signal['longitude']}"
    )

    print(
        f"Unique road names: {len(names)}"
    )

    print(
        "Roads:"
    )

    for name in names:
        print(f"  - {name}")

    print("\nSegments:")

    for road in signal["nearby_roads"]:

        print(
            f"  {road['road_id']} | "
            f"{road.get('highway')} | "
            f"{road.get('name')} | "
            f"lanes={road.get('lanes')} | "
            f"maxspeed={road.get('maxspeed')} | "
            f"distance={road.get('distance_meters', road.get('distance_degrees'))}"
        )


def main() -> None:

    data = load_data()

    # Only signals with exactly 2 unique road names.
    signals_with_two_roads = [
        signal
        for signal in data
        if len(get_unique_names(signal)) == 2
    ]

    print(
        f"Signals with exactly 2 road names: "
        f"{len(signals_with_two_roads)}"
    )

    print(
        "\nShowing first 10 examples:"
    )

    for signal in signals_with_two_roads[:10]:
        print_signal(signal)


if __name__ == "__main__":
    main()