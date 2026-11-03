"""Private-only fourth-corner positioning observations, not projected pace.

Fourth-corner positions from historic races are not the same as running style
or a reliable pace forecast. Different distances, conditions and field sizes
need later validation. No odds, horse names or paid row values are returned.
"""
from jrdb_coverage import CoverageError

VERSION = "position-observation-1"
LABELS = ("frontObserved", "backObserved", "mixedObserved", "insufficient")


def summarize_position_observations(recent_hints):
    if not isinstance(recent_hints, list) or len(recent_hints) > 120:
        raise CoverageError("Invalid historical race list")
    rows = []
    seen = set()
    for race in recent_hints:
        if not isinstance(race, dict) or not isinstance(race.get("byNumber"), dict):
            raise CoverageError("Invalid historical race")
        track, race_no = race.get("track"), race.get("race")
        if not isinstance(track, str) or type(race_no) is not int:
            raise CoverageError("Invalid race identity")
        key = (track, race_no)
        if key in seen:
            raise CoverageError("Duplicate historic race")
        seen.add(key)
        counts = dict.fromkeys(LABELS, 0)
        for observation in race["byNumber"].values():
            if not isinstance(observation, dict):
                raise CoverageError("Invalid runner observation")
            n = observation.get("fourthObserved")
            front = observation.get("frontAtFourth")
            if (type(n) is not int or type(front) is not int
                    or not 0 <= front <= n <= 3):
                raise CoverageError("Invalid fourth-corner observation counts")
            if n < 2:
                label = "insufficient"
            elif front >= 2:
                label = "frontObserved"
            elif front == 0:
                label = "backObserved"
            else:
                label = "mixedObserved"
            counts[label] += 1
        rows.append({
            "track": track, "race": race_no, "runnerCount": len(race["byNumber"]),
            "observations": counts, "paceForecastAvailable": False,
            "predictionReady": False,
        })
    return {
        "version": VERSION, "races": rows, "paceForecastAvailable": False,
        "predictionReady": False,
        "note": ("過去最大3走の4角位置が2走以上ある馬について、4番手以内の回数から"
                 "位置取りの観測傾向だけを整理。先行力の確定、逃げ馬の特定、"
                 "展開予想・ハイペース予想は行っていません。")
    }
