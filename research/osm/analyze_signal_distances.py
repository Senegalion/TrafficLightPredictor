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


# WGS84 -> Poland CS92
transformer = Transformer.from_crs(
    "EPSG:4326",
    "EPSG:2180",
    always_xy=True,
)


def load_signals() -> list[dict]:
    with INPUT_FILE.open("r", encoding="utf-8") as file:
        data = json.load(file)

    return data.get("elements", [])


def distance_meters(a: dict, b: dict) -> float:

    x1, y1 = transformer.transform(
        a["lon"],
        a["lat"],
    )

    x2, y2 = transformer.transform(
        b["lon"],
        b["lat"],
    )

    return math.hypot(
        x2 - x1,
        y2 - y1,
    )


def main() -> None:

    signals = load_signals()

    print("=" * 60)
    print("TRAFFIC SIGNAL DISTANCE ANALYSIS")
    print("=" * 60)

    distances = []

    for i, signal in enumerate(signals):

        nearest_distance = None
        nearest_signal = None

        for j, other in enumerate(signals):

            if i == j:
                continue

            distance = distance_meters(
                signal,
                other,
            )

            if (
                nearest_distance is None
                or distance < nearest_distance
            ):
                nearest_distance = distance
                nearest_signal = other

        if nearest_distance is not None:
            distances.append(
                (
                    nearest_distance,
                    signal["id"],
                    nearest_signal["id"],
                )
            )

    distances.sort()

    print("\nNearest-neighbour distance distribution:")

    thresholds = [
        5,
        10,
        15,
        20,
        25,
        30,
        35,
        40,
        45,
        50,
        60,
        75,
        100,
    ]

    for threshold in thresholds:

        count = sum(
            distance <= threshold
            for distance, _, _ in distances
        )

        percentage = (
            count / len(distances) * 100
        )

        print(
            f"  <= {threshold:3d} m: "
            f"{count:4d} "
            f"({percentage:5.1f}%)"
        )

    print("\nSelected nearest-neighbour examples:")

    for distance, signal_id, nearest_id in distances[:30]:

        print(
            f"  {distance:6.2f} m | "
            f"{signal_id} -> {nearest_id}"
        )


if __name__ == "__main__":
    main()