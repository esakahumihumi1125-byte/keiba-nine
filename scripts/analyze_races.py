"""KEIBA NINE BETA 4.3 - synthetic race AI analysis."""

import json
import os
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from data_sources import load_source


HERE = Path(__file__).resolve().parent
INPUT_FILE = HERE / "test_race_data.json"
OUTPUT_FILE = HERE / "race_analysis_test.json"
MODEL = "gpt-4o-mini"


def analyze():
    source = load_source(INPUT_FILE)

    if source["recordType"] != "test":
        raise ValueError("Only synthetic test data is allowed")

    if source["sourceId"] != "keiba-nine-synthetic-test":
        raise ValueError("Unexpected data source")

    races = source["races"]
    if len(races) != 1:
        raise ValueError("Expected one synthetic test race")

    race = races[0]
    horses = race["horses"]
    horse_numbers = [h["horseNumber"] for h in horses]

    if len(horse_numbers) != len(set(horse_numbers)):
        raise ValueError("Duplicate horse numbers")

    print("Synthetic race data validated.")
    print("Horses:", len(horses))

    if os.getenv("RUN_PAID_AI_TEST") != "yes":
        print("AI call disabled. Set RUN_PAID_AI_TEST=yes to test.")
        return

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY is missing")

    system_message = (
        "You are the KEIBA NINE experimental racing analyst. "
        "All supplied racing data is synthetic. "
        "Never invent facts or treat it as a real race. "
        "Rank only the supplied horses. "
        "Consider workouts, past runs, course suitability, "
        "running style and pedigree where provided. "
        "Missing information must be described as unverified. "
        "Return a JSON object with a 'ranking' array. "
        "Each entry must contain horseNumber (integer), "
        "overallGrade (S, A, B or C), and reason (Japanese). "
        "Include each horse exactly once, best first. "
        "Add a Japanese 'summary' explaining the exercise. "
        "Do not claim the ranking has proven predictive accuracy."
    )

    body = {
        "model": MODEL,
        "temperature": 0.2,
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": system_message},
            {
                "role": "user",
                "content": json.dumps(race, ensure_ascii=False),
            },
        ],
    }

    request = urllib.request.Request(
        "https://api.openai.com/v1/chat/completions",
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Authorization": "Bearer " + api_key,
            "Content-Type": "application/json",
        },
        method="POST",
    )

    with urllib.request.urlopen(request, timeout=60) as response:
        api_result = json.load(response)

    content = api_result["choices"][0]["message"]["content"]
    analysis = json.loads(content)
    ranking = analysis.get("ranking")

    if not isinstance(ranking, list):
        raise ValueError("AI ranking is not a list")

    returned_numbers = [
        entry["horseNumber"] for entry in ranking
    ]

    if (
        len(returned_numbers) != len(horse_numbers)
        or set(returned_numbers) != set(horse_numbers)
    ):
        raise ValueError("AI ranking does not match input horses")

    for entry in ranking:
        if entry.get("overallGrade") not in ("S", "A", "B", "C"):
            raise ValueError("Invalid overall grade")
        if not isinstance(entry.get("reason"), str):
            raise ValueError("Missing evaluation reason")

    output = {
        "schemaVersion": "4.3",
        "testOnly": True,
        "recordType": "test",
        "publishable": False,
        "sourceId": source["sourceId"],
        "raceId": race["raceId"],
        "model": MODEL,
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "analysis": analysis,
        "disclaimer": "Synthetic test only. Not a real prediction.",
    }

    OUTPUT_FILE.write_text(
        json.dumps(output, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print("BETA 4.3 AI ANALYSIS TEST PASSED")
    print("Ranking:", returned_numbers)
    print("Test result saved:", OUTPUT_FILE.name)


if __name__ == "__main__":
    analyze()
