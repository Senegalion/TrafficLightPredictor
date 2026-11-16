import json
from pathlib import Path

from pyproj import Transformer
from shapely.geometry import Point, shape
from shapely.strtree import STRtree


PROJECT_ROOT = Path(__file__).resolve().parents[2]

SIGNALS_FILE = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "lodz_traffic_signals.json"
)

ROADS_FILE = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "lodz_roads.geojson"
)

OUTPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "signal_road_matches_v2.json"
)

MATCH_RADIUS_METERS = 40


# WGS84 -> PUWG 1992
TRANSFORMER = Transformer.from_crs(
    "EPSG:4326",
    "EPSG:2180",
    always_xy=True,
)


def load_signals() -> list[dict]:
    with SIGNALS_FILE.open("r", encoding="utf-8") as file:
        data = json.load(file)

    return data.get("elements", [])


def load_roads() -> list[dict]:
    with ROADS_FILE.open("r", encoding="utf-8") as file:
        data = json.load(file)

    return data.get("features", [])


def project_point(lon: float, lat: float) -> Point:
    x, y = TRANSFORMER.transform(lon, lat)

    return Point(x, y)


def build_road_index(
    roads: list[dict],
) -> tuple[list, STRtree]:

    geometries = []

    for road in roads:
        geometry = shape(road["geometry"])

        projected_geometry = geometry.__class__(
            [
                TRANSFORMER.transform(lon, lat)
                for lon, lat in geometry.coords
            ]
        )

        geometries.append(projected_geometry)

    tree = STRtree(geometries)

    return geometries, tree


def find_nearby_roads(
    signal: dict,
    roads: list[dict],
    geometries: list,
    tree: STRtree,
) -> list[dict]:

    point = project_point(
        signal["lon"],
        signal["lat"],
    )

    candidates = tree.query(
        point.buffer(MATCH_RADIUS_METERS)
    )

    matches = []

    for candidate_index in candidates:

        road_geometry = geometries[candidate_index]

        distance = point.distance(road_geometry)

        if distance <= MATCH_RADIUS_METERS:

            road = roads[candidate_index]

            matches.append(
                {
                    "road_id": road["properties"].get("@id"),
                    "highway": road["properties"].get("highway"),
                    "name": road["properties"].get("name"),
                    "lanes": road["properties"].get("lanes"),
                    "maxspeed": road["properties"].get("maxspeed"),
                    "oneway": road["properties"].get("oneway"),
                    "distance_meters": round(
                        distance,
                        2,
                    ),
                }
            )

    matches.sort(
        key=lambda match: match["distance_meters"]
    )

    return matches


def save_results(results: list[dict]) -> None:

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with OUTPUT_FILE.open(
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            results,
            file,
            ensure_ascii=False,
            indent=2,
        )


def main() -> None:

    print("=" * 60)
    print("TRAFFIC SIGNAL → ROAD SPATIAL MATCHING V2")
    print("=" * 60)

    print(
        f"\nMatching radius: "
        f"{MATCH_RADIUS_METERS} meters"
    )

    signals = load_signals()
    roads = load_roads()

    print(
        f"Traffic signals: {len(signals)}"
    )

    print(
        f"Road features:   {len(roads)}"
    )

    print(
        "\nBuilding spatial index..."
    )

    geometries, tree = build_road_index(
        roads
    )

    results = []

    for index, signal in enumerate(
        signals,
        start=1,
    ):

        matches = find_nearby_roads(
            signal,
            roads,
            geometries,
            tree,
        )

        results.append(
            {
                "signal_id": signal["id"],
                "latitude": signal["lat"],
                "longitude": signal["lon"],
                "tags": signal.get("tags", {}),
                "nearby_roads": matches,
            }
        )

        if index % 100 == 0:

            print(
                f"Processed signals: "
                f"{index}/{len(signals)}"
            )

    save_results(results)

    signals_with_roads = sum(
        1
        for result in results
        if result["nearby_roads"]
    )

    signals_without_roads = (
        len(results)
        - signals_with_roads
    )

    total_matches = sum(
        len(result["nearby_roads"])
        for result in results
    )

    print("\n" + "-" * 60)
    print("MATCHING RESULTS")
    print("-" * 60)

    print(
        f"Signals with nearby roads: "
        f"{signals_with_roads}"
    )

    print(
        f"Signals without nearby roads: "
        f"{signals_without_roads}"
    )

    print(
        f"Total signal-road matches: "
        f"{total_matches}"
    )

    print(
        f"\nSaved to: {OUTPUT_FILE}"
    )


if __name__ == "__main__":
    main()