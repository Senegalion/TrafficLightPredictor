import json
import math
from pathlib import Path
from collections import defaultdict

import osmium


PROJECT_ROOT = Path(__file__).resolve().parents[2]

PBF_FILE = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "lodz_roads.osm.pbf"
)

SIGNALS_FILE = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "lodzkie_traffic_signals.geojson"
)

INTERSECTIONS_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "intersections_v2.json"
)

OUTPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "signal_intersection_map_matching.json"
)


ROAD_TYPES = {
    "motorway",
    "trunk",
    "primary",
    "secondary",
    "tertiary",
    "residential",
    "unclassified",
    "living_street",
}


MAX_SIGNAL_TO_ROAD_DISTANCE_M = 50.0
MAX_SIGNAL_TO_INTERSECTION_DISTANCE_M = 150.0


def haversine_m(lat1, lon1, lat2, lon2):
    r = 6371000.0

    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)

    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)

    a = (
        math.sin(dphi / 2) ** 2
        + math.cos(phi1)
        * math.cos(phi2)
        * math.sin(dlambda / 2) ** 2
    )

    return 2 * r * math.asin(math.sqrt(a))


def project_to_local_xy(lat, lon, ref_lat, ref_lon):
    """
    Convert lat/lon to local metric coordinates.
    Good enough for small areas such as Łódź.
    """

    meters_per_degree_lat = 111320.0
    meters_per_degree_lon = (
        111320.0 * math.cos(math.radians(ref_lat))
    )

    x = (lon - ref_lon) * meters_per_degree_lon
    y = (lat - ref_lat) * meters_per_degree_lat

    return x, y


def point_to_segment_distance(
    px,
    py,
    ax,
    ay,
    bx,
    by,
):
    dx = bx - ax
    dy = by - ay

    length_sq = dx * dx + dy * dy

    if length_sq == 0:
        return math.hypot(px - ax, py - ay)

    t = (
        (px - ax) * dx
        + (py - ay) * dy
    ) / length_sq

    t = max(0.0, min(1.0, t))

    cx = ax + t * dx
    cy = ay + t * dy

    return math.hypot(px - cx, py - cy)


def point_to_polyline_distance(
    lat,
    lon,
    coordinates,
):
    if not coordinates:
        return float("inf")

    ref_lat = lat
    ref_lon = lon

    px, py = project_to_local_xy(
        lat,
        lon,
        ref_lat,
        ref_lon,
    )

    best = float("inf")

    for i in range(len(coordinates) - 1):
        lat1, lon1 = coordinates[i]
        lat2, lon2 = coordinates[i + 1]

        ax, ay = project_to_local_xy(
            lat1,
            lon1,
            ref_lat,
            ref_lon,
        )

        bx, by = project_to_local_xy(
            lat2,
            lon2,
            ref_lat,
            ref_lon,
        )

        distance = point_to_segment_distance(
            px,
            py,
            ax,
            ay,
            bx,
            by,
        )

        best = min(best, distance)

    if len(coordinates) == 1:
        lat2, lon2 = coordinates[0]

        return haversine_m(
            lat,
            lon,
            lat2,
            lon2,
        )

    return best


def load_signals():
    with SIGNALS_FILE.open(
        "r",
        encoding="utf-8",
    ) as file:
        data = json.load(file)

    signals = []

    for feature in data["features"]:
        properties = feature.get(
            "properties",
            {},
        )

        signal_id = properties.get("@id")

        if signal_id is None:
            continue

        coordinates = feature["geometry"]["coordinates"]

        lon, lat = coordinates

        signals.append(
            {
                "signal_id": int(signal_id),
                "latitude": lat,
                "longitude": lon,
            }
        )

    return signals


class RoadGeometryHandler(osmium.SimpleHandler):

    def __init__(self):
        super().__init__()

        self.roads = []

    def way(self, way):

        highway = way.tags.get("highway")

        if highway not in ROAD_TYPES:
            return

        coordinates = []

        try:
            for node in way.nodes:
                if not node.location.valid():
                    continue

                coordinates.append(
                    (
                        node.location.lat,
                        node.location.lon,
                    )
                )
        except Exception:
            return

        if len(coordinates) < 2:
            return

        self.roads.append(
            {
                "road_id": way.id,
                "name": way.tags.get("name"),
                "highway": highway,
                "coordinates": coordinates,
            }
        )


def load_intersections():

    with INTERSECTIONS_FILE.open(
        "r",
        encoding="utf-8",
    ) as file:
        data = json.load(file)

    intersections = data[
        "intersection_clusters"
    ]

    return intersections


def build_road_to_intersections(
    intersections,
):

    mapping = defaultdict(set)

    for intersection in intersections:

        intersection_id = intersection[
            "intersection_id"
        ]

        for road in intersection.get(
            "roads",
            [],
        ):
            road_id = road["road_id"]

            mapping[road_id].add(
                intersection_id
            )

    return mapping


def build_intersection_index(
    intersections,
):

    return {
        intersection[
            "intersection_id"
        ]: intersection
        for intersection in intersections
    }


def find_nearest_roads(
    signal,
    roads,
    limit=5,
):
    candidates = []

    for road in roads:

        distance = point_to_polyline_distance(
            signal["latitude"],
            signal["longitude"],
            road["coordinates"],
        )

        if distance <= MAX_SIGNAL_TO_ROAD_DISTANCE_M:

            candidates.append(
                (
                    distance,
                    road,
                )
            )

    candidates.sort(
        key=lambda x: x[0]
    )

    return candidates[:limit]


def intersection_distance(
    signal,
    intersection,
):
    """
    Use the closest actual OSM node belonging
    to the intersection, not the centroid.
    """

    best = float("inf")

    for node in intersection.get(
        "osm_nodes",
        [],
    ):

        distance = haversine_m(
            signal["latitude"],
            signal["longitude"],
            node["latitude"],
            node["longitude"],
        )

        best = min(
            best,
            distance,
        )

    return best


def score_candidate(
    road_distance,
    intersection_distance,
):
    """
    Lower is better.

    Road proximity is important because it tells us
    which approach the signal belongs to.

    Intersection distance determines which intersection
    on that road is the most plausible.
    """

    return (
        intersection_distance
        + road_distance * 2.0
    )


def main():

    print("=" * 60)
    print("SIGNAL → ROAD → INTERSECTION MAP MATCHING")
    print("=" * 60)

    signals = load_signals()

    print(
        f"\nTraffic signals: {len(signals)}"
    )

    intersections = load_intersections()

    print(
        f"Intersections: {len(intersections)}"
    )

    road_to_intersections = (
        build_road_to_intersections(
            intersections
        )
    )

    intersection_index = (
        build_intersection_index(
            intersections
        )
    )

    handler = RoadGeometryHandler()

    print(
        "\nReading OSM road geometry..."
    )

    handler.apply_file(
        str(PBF_FILE),
        locations=True,
    )

    roads = handler.roads

    print(
        f"Road geometries: {len(roads)}"
    )

    results = []

    unmatched = []

    print(
        "\nMatching signals..."
    )

    for index, signal in enumerate(
        signals,
        start=1,
    ):

        nearest_roads = find_nearest_roads(
            signal,
            roads,
        )

        candidates = []

        for road_distance, road in (
            nearest_roads
        ):

            intersection_ids = (
                road_to_intersections.get(
                    road["road_id"],
                    set(),
                )
            )

            for intersection_id in (
                intersection_ids
            ):

                intersection = (
                    intersection_index[
                        intersection_id
                    ]
                )

                distance = (
                    intersection_distance(
                        signal,
                        intersection,
                    )
                )

                if (
                    distance
                    > MAX_SIGNAL_TO_INTERSECTION_DISTANCE_M
                ):
                    continue

                score = score_candidate(
                    road_distance,
                    distance,
                )

                candidates.append(
                    {
                        "intersection_id":
                            intersection_id,
                        "road_id":
                            road["road_id"],
                        "road_name":
                            road["name"],
                        "road_type":
                            road["highway"],
                        "signal_to_road_m":
                            round(
                                road_distance,
                                2,
                            ),
                        "signal_to_intersection_m":
                            round(
                                distance,
                                2,
                            ),
                        "score":
                            round(
                                score,
                                2,
                            ),
                    }
                )

        candidates.sort(
            key=lambda x: x["score"]
        )

        if not candidates:

            unmatched.append(signal)
            continue

        best = candidates[0]

        intersection = (
            intersection_index[
                best["intersection_id"]
            ]
        )

        result = {
            "signal_id":
                signal["signal_id"],

            "signal_latitude":
                signal["latitude"],

            "signal_longitude":
                signal["longitude"],

            "intersection_id":
                best["intersection_id"],

            "intersection_latitude":
                intersection["latitude"],

            "intersection_longitude":
                intersection["longitude"],

            "road_names":
                intersection["road_names"],

            "road_count":
                intersection["road_count"],

            "signal_to_road_m":
                best["signal_to_road_m"],

            "signal_to_intersection_m":
                best[
                    "signal_to_intersection_m"
                ],

            "matched_road":
                best["road_name"],

            "matched_road_id":
                best["road_id"],

            "candidate_count":
                len(candidates),

            "candidates":
                candidates[:5],
        }

        results.append(result)

        if index % 100 == 0:
            print(
                f"Processed {index}/"
                f"{len(signals)}"
            )

    print("\n" + "=" * 60)
    print("RESULTS")
    print("=" * 60)

    print(
        f"\nMatched signals: {len(results)}"
    )

    print(
        f"Unmatched signals: {len(unmatched)}"
    )

    if results:

        distances = [
            result[
                "signal_to_intersection_m"
            ]
            for result in results
        ]

        print(
            "\nSignal → intersection distance:"
        )

        for threshold in (
            5,
            10,
            15,
            20,
            30,
            50,
            100,
        ):
            count = sum(
                d <= threshold
                for d in distances
            )

            print(
                f"<= {threshold:3} m:"
                f" {count:4}"
            )

        print(
            f"\nAverage:"
            f" {sum(distances) / len(distances):.2f} m"
        )

        print(
            f"Maximum:"
            f" {max(distances):.2f} m"
        )

    print(
        "\nExamples:"
    )

    for result in results[:20]:

        print("\n---")

        print(
            f"Signal:"
            f" {result['signal_id']}"
        )

        print(
            f"Matched intersection:"
            f" {result['intersection_id']}"
        )

        print(
            f"Roads:"
            f" {', '.join(result['road_names'])}"
        )

        print(
            f"Matched road:"
            f" {result['matched_road']}"
        )

        print(
            f"Signal → road:"
            f" {result['signal_to_road_m']:.2f} m"
        )

        print(
            f"Signal → intersection:"
            f" {result['signal_to_intersection_m']:.2f} m"
        )

        print(
            f"Candidates:"
            f" {result['candidate_count']}"
        )

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with OUTPUT_FILE.open(
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            {
                "results": results,
                "unmatched": unmatched,
            },
            file,
            ensure_ascii=False,
            indent=2,
        )

    print(
        f"\nSaved to:"
        f" {OUTPUT_FILE}"
    )


if __name__ == "__main__":
    main()