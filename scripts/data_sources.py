"""KEIBA NINE BETA 4.3 - data source adapters."""

import json
from pathlib import Path

SCHEMA_VERSION = "4.3"
LIVE_ENABLED = False


def load_source(file_path):
    """Load authorized source data from a local JSON file."""
    path = Path(file_path)
    data = json.loads(path.read_text(encoding="utf-8"))

    if not isinstance(data, dict):
        raise ValueError("Data must be a JSON object")

    required = ("sourceId", "recordType", "rightsNote", "races")
    for key in required:
        if key not in data:
            raise ValueError(f"Missing field: {key}")

    if not isinstance(data["sourceId"], str) or not data["sourceId"].strip():
        raise ValueError("Invalid sourceId")

    if not isinstance(data["rightsNote"], str) or not data["rightsNote"].strip():
        raise ValueError("Missing rights information")

    if data["recordType"] != "test":
        if not LIVE_ENABLED:
            raise ValueError("Live data is disabled pending permission")
        if data["recordType"] != "live":
            raise ValueError("Invalid recordType")

    if not isinstance(data["races"], list):
        raise ValueError("races must be a list")

    for race in data["races"]:
        if not isinstance(race, dict):
            raise ValueError("Invalid race")
        if not race.get("raceId"):
            raise ValueError("Missing raceId")
        if not isinstance(race.get("horses"), list):
            raise ValueError("Missing horses list")

    return {
        "sourceId": data["sourceId"],
        "recordType": data["recordType"],
        "rightsNote": data["rightsNote"],
        "races": data["races"],
    }


def collect_sources(file_paths):
    """Keep each data provider identifiable and separate."""
    sources = [load_source(path) for path in file_paths]
    return {
        "schemaVersion": SCHEMA_VERSION,
        "sources": sources,
    }


if __name__ == "__main__":
    print("KEIBA NINE BETA 4.3 data adapter ready")
