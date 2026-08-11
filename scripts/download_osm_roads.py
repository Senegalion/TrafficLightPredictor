import json
from pathlib import Path

import requests


OVERPASS_URL = "https://overpass-api.de/api/interpreter"

USER_AGENT = (
    "TrafficLightPredictor/0.1 "
    "(https://github.com/Senegalion/TrafficLightPredictor)"
)

QUERY = """
[out:json][timeout:180];

area["name"="Łódź"]["boundary"="administrative"]["admin_level"="6"]->.searchArea;

way["highway"](area.searchArea);

out body;
>;
out skel qt;
"""


OUTPUT_FILE = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "raw"
    / "lodz_roads.json"
)


def download_roads() -> dict:
    response = requests.post(
        OVERPASS_URL,
        data={"data": QUERY},
        headers={
            "User-Agent": USER_AGENT,
            "Accept-Encoding": "gzip, deflate",
        },
        timeout=240,
    )

    response.raise_for_status()

    return response.json()


def save_data(data: dict) -> None:
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    with OUTPUT_FILE.open("w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)


def main() -> None:
    print("Downloading road network from OpenStreetMap...")
    print(f"Overpass endpoint: {OVERPASS_URL}")

    data = download_roads()

    elements = data.get("elements", [])

    ways = [
        element
        for element in elements
        if element.get("type") == "way"
    ]

    nodes = [
        element
        for element in elements
        if element.get("type") == "node"
    ]

    save_data(data)

    print(f"Road ways found: {len(ways)}")
    print(f"Road nodes found: {len(nodes)}")
    print(f"Total OSM elements: {len(elements)}")
    print(f"Saved to: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()