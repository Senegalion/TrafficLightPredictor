import json
from pathlib import Path
from collections import Counter


PROJECT_ROOT = Path(__file__).resolve().parents[2]

INPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "signal_intersection_map_matching.json"
)


def main():

    with INPUT_FILE.open(
        "r",
        encoding="utf-8",
    ) as file:
        data = json.load(file)

    results = data["results"]

    print("=" * 60)
    print("MAP MATCHING CONFIDENCE ANALYSIS")
    print("=" * 60)

    print(
        f"\nMatched signals: {len(results)}"
    )

    analyses = []

    for result in results:

        candidates_by_intersection = {}

        for candidate in result["candidates"]:

            intersection_id = candidate[
                "intersection_id"
            ]

            current = candidates_by_intersection.get(
                intersection_id
            )

            if (
                current is None
                or candidate["score"] < current["score"]
            ):
                candidates_by_intersection[
                    intersection_id
                ] = candidate

        candidates = sorted(
            candidates_by_intersection.values(),
            key=lambda x: x["score"],
        )

        if not candidates:
            continue

        best = candidates[0]

        second = (
            candidates[1]
            if len(candidates) > 1
            else None
        )

        best_score = best["score"]

        second_score = (
            second["score"]
            if second is not None
            else None
        )

        if second_score is None:
            gap = None
        else:
            gap = second_score - best_score

        analyses.append(
            {
                "signal_id":
                    result["signal_id"],

                "intersection_id":
                    best["intersection_id"],

                "road_names":
                    result["road_names"],

                "distance":
                    result[
                        "signal_to_intersection_m"
                    ],

                "score":
                    best_score,

                "second_score":
                    second_score,

                "gap":
                    gap,

                "candidate_count":
                    len(candidates),
            }
        )

    print(
        f"\nSignals analyzed: {len(analyses)}"
    )

    # --------------------------------------------------
    # Candidate count
    # --------------------------------------------------

    print(
        "\nUnique candidate intersections:"
    )

    distribution = Counter(
        item["candidate_count"]
        for item in analyses
    )

    for count, number in sorted(
        distribution.items()
    ):
        print(
            f"{count:2} candidates:"
            f" {number:4}"
        )

    # --------------------------------------------------
    # Score gap
    # --------------------------------------------------

    gaps = [
        item["gap"]
        for item in analyses
        if item["gap"] is not None
    ]

    print(
        "\nScore gap distribution:"
    )

    for threshold in (
        0,
        1,
        2,
        5,
        10,
        20,
        50,
    ):
        count = sum(
            gap <= threshold
            for gap in gaps
        )

        print(
            f"gap <= {threshold:2}:"
            f" {count:4}"
        )

    # --------------------------------------------------
    # Distance distribution
    # --------------------------------------------------

    print(
        "\nBest intersection distance:"
    )

    distances = [
        item["distance"]
        for item in analyses
    ]

    for threshold in (
        5,
        10,
        15,
        20,
        30,
        40,
        50,
        75,
        100,
    ):
        count = sum(
            distance <= threshold
            for distance in distances
        )

        print(
            f"<= {threshold:3} m:"
            f" {count:4}"
        )

    # --------------------------------------------------
    # Confidence categories
    # --------------------------------------------------

    high = []
    medium = []
    low = []

    for item in analyses:

        gap = item["gap"]
        distance = item["distance"]

        if gap is None:

            high.append(item)

        elif (
            gap >= 15
            and distance <= 30
        ):

            high.append(item)

        elif (
            gap >= 5
            and distance <= 40
        ):

            medium.append(item)

        else:

            low.append(item)

    print(
        "\nPreliminary confidence:"
    )

    print(
        f"HIGH:   {len(high):4}"
    )

    print(
        f"MEDIUM: {len(medium):4}"
    )

    print(
        f"LOW:    {len(low):4}"
    )

    # --------------------------------------------------
    # Most ambiguous
    # --------------------------------------------------

    ambiguous = [
        item
        for item in analyses
        if item["gap"] is not None
    ]

    ambiguous.sort(
        key=lambda x: x["gap"]
    )

    print(
        "\nMOST AMBIGUOUS MATCHES"
    )

    for item in ambiguous[:30]:

        print("\n---")

        print(
            f"Signal:"
            f" {item['signal_id']}"
        )

        print(
            f"Intersection:"
            f" {item['intersection_id']}"
        )

        print(
            f"Roads:"
            f" {', '.join(item['road_names'])}"
        )

        print(
            f"Distance:"
            f" {item['distance']:.2f} m"
        )

        print(
            f"Best score:"
            f" {item['score']:.2f}"
        )

        print(
            f"Second score:"
            f" {item['second_score']:.2f}"
        )

        print(
            f"Gap:"
            f" {item['gap']:.2f}"
        )

    # --------------------------------------------------
    # Worst distances
    # --------------------------------------------------

    print(
        "\nWORST DISTANCE MATCHES"
    )

    worst = sorted(
        analyses,
        key=lambda x: x["distance"],
        reverse=True,
    )

    for item in worst[:30]:

        print("\n---")

        print(
            f"Signal:"
            f" {item['signal_id']}"
        )

        print(
            f"Intersection:"
            f" {item['intersection_id']}"
        )

        print(
            f"Roads:"
            f" {', '.join(item['road_names'])}"
        )

        print(
            f"Distance:"
            f" {item['distance']:.2f} m"
        )

        print(
            f"Gap:"
            f" {item['gap']}"
        )


if __name__ == "__main__":
    main()