import json
from pathlib import Path

import requests


OVERPASS_URL = "https://overpass-api.de/api/interpreter"

USER_AGENT = (
    "TrafficLightPredictor/0.1 "
    "(https://github.com/Senegalion/TrafficLightPredictor)"
)

QUERY = """
[out:json][timeout:120];

area["name"="Łódź"]["boundary"="administrative"]["admin_level"="6"]->.searchArea;

node["highway"="traffic_signals"](area.searchArea);

out body;
"""


OUTPUT_FILE = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "raw"
    / "lodz_traffic_signals.json"
)


def download_traffic_signals() -> dict:
    response = requests.post(
        OVERPASS_URL,
        data={"data": QUERY},
        headers={
            "User-Agent": USER_AGENT,
            "Accept-Encoding": "gzip, deflate",
        },
        timeout=180,
    )

    response.raise_for_status()

    return response.json()


def save_data(data: dict) -> None:
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    with OUTPUT_FILE.open("w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)


def main() -> None:
    print("Downloading traffic signals from OpenStreetMap...")
    print(f"Overpass endpoint: {OVERPASS_URL}")

    data = download_traffic_signals()

    elements = data.get("elements", [])

    save_data(data)

    print(f"Traffic signals found: {len(elements)}")
    print(f"Saved to: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()