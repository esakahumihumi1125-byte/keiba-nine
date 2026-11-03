"""Deterministic pre-start source-age diagnostic, never JRA official verification.

No network, credentials, wagers or predictions. Inject a timezone-aware clock
instead of trusting a client-supplied timestamp. Only private race-level
aggregates escape; actual condition update timestamps stay server-side.
"""
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from jrdb_race_context import audit_race_context
from jrdb_program_preview import TRACKS

VERSION = "prestart-freshness-1"
JST = ZoneInfo("Asia/Tokyo")
MAX_REVIEW_MINUTES = 120
RECENT_SOURCE_MINUTES = 60


class FreshnessError(ValueError):
    """Invalid or conflicting source timing; never includes provider text."""


def _aware(when):
    if not isinstance(when, str) or len(when) > 40:
        raise FreshnessError("Expected an offset-aware timestamp")
    try:
        timestamp = datetime.fromisoformat(when.replace("Z", "+00:00"))
    except ValueError:
        raise FreshnessError("Invalid timestamp") from None
    if timestamp.tzinfo is None or timestamp.utcoffset() is None:
        raise FreshnessError("Timezone offset is required")
    return timestamp


def audit_prestart_freshness(programme, holding_rows, requested_date, checked_at):
    """Show age of reported source snapshots, never claim official/race readiness.

    checked_at must be generated on the authenticated private server.
    updated_at is taken only from bounded /tka records validated by
    audit_race_context; a new fetch is not proof that source data is recent.
    """
    now = _aware(checked_at).astimezone(JST)
    context = audit_race_context(programme, holding_rows, requested_date)
    if not 2000 <= now.year <= 2100:
        raise FreshnessError("Date outside supported range")
    venue_timestamp = {}
    for row in holding_rows:
        track = TRACKS[row["holdingkey"][:2]]
        value = row.get("updated_at")
        venue_timestamp[track] = (
            None if not value else _aware(value).astimezone(JST)
        )
    context_by_key = {(r["track"], r["race"]): r for r in context["races"]}
    if len(context_by_key) != len(context["races"]):
        raise FreshnessError("Duplicate race in normalized context")
    results = []
    date_today = requested_date == now.strftime("%Y%m%d")
    for race in programme:
        key = (race["track"], race["race"])
        data = context_by_key[key]
        raw_post = race.get("post_time")
        if raw_post is None:
            minutes = None
            window = "post_time_unknown"
        elif (not isinstance(raw_post, str) or len(raw_post) != 5
              or raw_post[2] != ":" or not raw_post[:2].isdigit()
              or not raw_post[3:].isdigit()
              or not 0 <= int(raw_post[:2]) < 24
              or not 0 <= int(raw_post[3:]) < 60):
            raise FreshnessError("Unrecognized programme post time")
        else:
            post_time = datetime.strptime(
                requested_date + raw_post.replace(":", ""), "%Y%m%d%H%M"
            ).replace(tzinfo=JST)
            minutes = int((post_time - now).total_seconds() // 60)
            if not date_today:
                window = "other_date"
            elif post_time <= now:
                window = "post_time_passed"
            elif post_time <= now + timedelta(minutes=MAX_REVIEW_MINUTES):
                window = "within_two_hours"
            else:
                window = "more_than_two_hours"
        updated = venue_timestamp.get(race["track"])
        if not data["goingAvailable"]:
            age = None
            source_status = "no_going_report"
        elif updated is None:
            age = None
            source_status = "no_update_timestamp"
        elif updated > now:
            age = None
            source_status = "timestamp_in_future"
        else:
            age = int((now - updated).total_seconds() // 60)
            source_status = ("recent_reported" if date_today
                             and age <= RECENT_SOURCE_MINUTES
                             else "old_or_other_date_reported")
        # A current source timestamp alone never proves a final official
        # race-card change, or that any horse is eligible to run.
        results.append({
            "track": key[0],
            "race": key[1],
            "listedPostTime": raw_post,
            "minutesUntilListedPost": minutes,
            "prestartWindow": window,
            "sourceGoing": data["going"],
            "sourceGoingUpdateAgeMinutes": age,
            "sourceGoingAgeStatus": source_status,
            "candidateForManualJraReview": (
                window == "within_two_hours" and
                source_status == "recent_reported"
            ),
            "jraOfficialDataFetched": False,
            "jraScratchesVerified": False,
            "jraGoingVerified": False,
            "jraPostTimeVerified": False,
            "finalRaceReady": False,
            "predictionReady": False,
            "bettingReady": False,
        })
    if len(results) != context["raceCount"]:
        raise FreshnessError("Programme and context differ")
    return {
        "version": VERSION,
        "checkedAtJapan": now.strftime("%Y-%m-%d %H:%M JST"),
        "raceCount": len(results),
        "racesWithinTwoHours": sum(
            r["prestartWindow"] == "within_two_hours" for r in results
        ),
        "racesWithRecentlyReportedGoing": sum(
            r["sourceGoingAgeStatus"] == "recent_reported" for r in results
        ),
        "manualJraReviewCandidates": sum(
            r["candidateForManualJraReview"] for r in results
        ),
        "officiallyVerifiedRaces": 0,
        "predictionReady": False,
        "bettingReady": False,
        "races": results,
        "note": (
            "開催日・発走予定時刻までの時間と、提供元に記録された馬場更新時刻"
            "の経過時間だけを確認。60分以内は画面上の整理基準で、"
            "馬場・出走取消・発走時刻の公式確定やデータ品質を証明しない。"
            "JRA公式と照合する自動取得は未実装。"
            "発走時刻が過ぎた後の購入・WIN5変更はできません。"
        ),
    }
