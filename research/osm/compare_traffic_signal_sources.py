import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]

OVERPASS_FILE = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "lodz_traffic_signals.json"
)

GEOJSON_FILE = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "lodzkie_traffic_signals.geojson"
)


MIN_LAT = 51.6994795
MAX_LAT = 51.8291963

MIN_LON = 19.3571877
MAX_LON = 19.6120062


def load_overpass_data() -> list[dict]:
    with OVERPASS_FILE.open("r", encoding="utf-8") as file:
        data = json.load(file)

    return data.get("elements", [])


def load_geojson_data() -> list[dict]:
    with GEOJSON_FILE.open("r", encoding="utf-8") as file:
        data = json.load(file)

    return data.get("features", [])


def is_inside_lodz_bbox(lat: float, lon: float) -> bool:
    return (
        MIN_LAT <= lat <= MAX_LAT
        and MIN_LON <= lon <= MAX_LON
    )


def main() -> None:
    overpass_elements = load_overpass_data()
    geojson_features = load_geojson_data()

    overpass_ids = {
        element["id"]
        for element in overpass_elements
    }

    geofabrik_features = []

    for feature in geojson_features:
        geometry = feature.get("geometry")

        if not geometry:
            continue

        coordinates = geometry.get("coordinates")

        if not coordinates or len(coordinates) < 2:
            continue

        lon, lat = coordinates

        if is_inside_lodz_bbox(lat, lon):
            geofabrik_features.append(feature)

    geofabrik_ids = {
        feature["properties"]["@id"]
        for feature in geofabrik_features
        if feature.get("properties", {}).get("@id") is not None
    }

    common_ids = overpass_ids & geofabrik_ids

    only_overpass = overpass_ids - geofabrik_ids
    only_geofabrik = geofabrik_ids - overpass_ids

    print("=" * 60)
    print("TRAFFIC SIGNAL SOURCE COMPARISON")
    print("=" * 60)

    print(f"\nOverpass signals:              {len(overpass_ids)}")
    print(f"Geofabrik signals in bbox:    {len(geofabrik_ids)}")

    print(f"\nSignals present in both:       {len(common_ids)}")
    print(f"Only in Overpass:              {len(only_overpass)}")
    print(f"Only in Geofabrik:             {len(only_geofabrik)}")

    if overpass_ids:
        overlap_percentage = (
            len(common_ids) / len(overpass_ids)
        ) * 100

        print(
            f"\nOverpass → Geofabrik overlap: "
            f"{overlap_percentage:.2f}%"
        )

    print("\n" + "-" * 60)
    print("SAMPLE IDs ONLY IN OVERPASS")
    print("-" * 60)

    for osm_id in sorted(only_overpass)[:10]:
        print(osm_id)

    print("\n" + "-" * 60)
    print("SAMPLE IDs ONLY IN GEOFABRIK")
    print("-" * 60)

    for osm_id in sorted(only_geofabrik)[:10]:
        print(osm_id)


if __name__ == "__main__":
    main()