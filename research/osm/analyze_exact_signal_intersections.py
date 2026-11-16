import json
from pathlib import Path
from collections import defaultdict


PROJECT_ROOT = Path(__file__).resolve().parents[2]

INTERSECTIONS_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "intersections_v2.json"
)

MATCHES_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "signal_road_node_matches.json"
)


def main():
    print("=" * 70)
    print("EXACT SIGNAL NODE → INTERSECTION ANALYSIS")
    print("=" * 70)

    with INTERSECTIONS_FILE.open("r", encoding="utf-8") as file:
        data = json.load(file)

    with MATCHES_FILE.open("r", encoding="utf-8") as file:
        matches_data = json.load(file)

    intersections = data["intersection_clusters"]
    exact_matches = matches_data["exact_matches"]

    print(f"\nIntersections: {len(intersections)}")
    print(f"Exact signal/node matches: {len(exact_matches)}")

    # ------------------------------------------------------------
    # Build OSM node → intersection mapping
    # ------------------------------------------------------------

    node_to_intersections = defaultdict(list)

    for intersection in intersections:
        intersection_id = intersection["intersection_id"]

        for node in intersection["osm_nodes"]:
            node_to_intersections[node["node_id"]].append(
                intersection_id
            )

    # ------------------------------------------------------------
    # Match exact signal nodes to intersections
    # ------------------------------------------------------------

    matched = []
    unmatched = []
    ambiguous = []

    for signal in exact_matches:
        signal_id = signal["signal_id"]

        intersection_ids = node_to_intersections.get(
            signal_id,
            []
        )

        if not intersection_ids:
            unmatched.append(signal)

        elif len(intersection_ids) == 1:
            matched.append(
                {
                    "signal_id": signal_id,
                    "intersection_id": intersection_ids[0],
                }
            )

        else:
            ambiguous.append(
                {
                    "signal_id": signal_id,
                    "intersection_ids": intersection_ids,
                }
            )

    # ------------------------------------------------------------
    # Results
    # ------------------------------------------------------------

    print("\n" + "-" * 70)
    print("RESULTS")
    print("-" * 70)

    print(
        f"\nExact signals assigned to exactly one intersection: "
        f"{len(matched)}"
    )

    print(
        f"Exact signals not present in any intersection: "
        f"{len(unmatched)}"
    )

    print(
        f"Signals assigned to multiple intersections: "
        f"{len(ambiguous)}"
    )

    if exact_matches:
        rate = len(matched) / len(exact_matches) * 100

        print(
            f"\nExact-node → intersection match rate: "
            f"{rate:.2f}%"
        )

    # ------------------------------------------------------------
    # Intersection coverage
    # ------------------------------------------------------------

    signals_per_intersection = defaultdict(list)

    for match in matched:
        signals_per_intersection[
            match["intersection_id"]
        ].append(
            match["signal_id"]
        )

    signalized_intersections = len(
        signals_per_intersection
    )

    print(
        f"\nIntersections containing exact-matched signals: "
        f"{signalized_intersections}"
    )

    # ------------------------------------------------------------
    # Signal count distribution
    # ------------------------------------------------------------

    distribution = defaultdict(int)

    for signals in signals_per_intersection.values():
        distribution[len(signals)] += 1

    print("\nSignals per signalized intersection:")

    for count, intersection_count in sorted(
        distribution.items()
    ):
        print(
            f"  {count} signals: "
            f"{intersection_count} intersections"
        )

    # ------------------------------------------------------------
    # Sample matches
    # ------------------------------------------------------------

    intersection_by_id = {
        intersection["intersection_id"]: intersection
        for intersection in intersections
    }

    print("\n" + "-" * 70)
    print("SAMPLE EXACT ASSIGNMENTS")
    print("-" * 70)

    for intersection_id, signal_ids in list(
        signals_per_intersection.items()
    )[:20]:

        intersection = intersection_by_id[
            intersection_id
        ]

        print(
            f"\nIntersection #{intersection_id}"
        )

        print(
            f"Location: "
            f"{intersection['latitude']}, "
            f"{intersection['longitude']}"
        )

        print(
            f"Roads: "
            f"{', '.join(intersection['road_names'])}"
        )

        print(
            f"Diameter: "
            f"{intersection['diameter_m']:.2f} m"
        )

        print(
            f"Exact signals: "
            f"{len(signal_ids)}"
        )

        print(
            f"Signal IDs: "
            f"{', '.join(map(str, signal_ids))}"
        )

    # ------------------------------------------------------------
    # Save diagnostic output
    # ------------------------------------------------------------

    output_file = (
        PROJECT_ROOT
        / "data"
        / "processed"
        / "exact_signal_intersection_analysis.json"
    )

    with output_file.open(
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            {
                "exact_signal_count": len(exact_matches),
                "matched": matched,
                "unmatched": unmatched,
                "ambiguous": ambiguous,
                "signals_per_intersection": {
                    str(intersection_id): signals
                    for intersection_id, signals
                    in signals_per_intersection.items()
                },
            },
            file,
            ensure_ascii=False,
            indent=2,
        )

    print(
        f"\nSaved diagnostic analysis to:"
        f"\n{output_file}"
    )


if __name__ == "__main__":
    main()