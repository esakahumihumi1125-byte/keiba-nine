"""Read-only inventory of feed evidence. Never authorizes publication or betting."""
import argparse
import datetime as dt
import json
from pathlib import Path


def valid_record(record, race_date):
    if not isinstance(record, dict):
        return False
    try:
        day = dt.date.fromisoformat(record.get('date', ''))
        cutoff = dt.date.fromisoformat(race_date)
    except (ValueError, TypeError):
        return False
    return day < cutoff and all(isinstance(record.get(k), str) and record[k].strip()
                                for k in ('source', 'detail'))


def inventory(race):
    """Count records, not their truth, adequacy, freshness, or predictive value."""
    card = race.get('raceCard') or {}
    if not isinstance(card, dict):
        card = {}
    runners = card.get('runners')
    horses = race.get('horses', [])
    horses = horses if isinstance(horses, list) else []
    issues, rows = [], []
    if race.get('recordType') != 'live':
        issues.append('実データの区分ではありません')
    if not isinstance(runners, list) or not runners:
        issues.append('全頭出走表がありません')
        runners = []
    if card.get('complete') is not True:
        issues.append('全頭確認が未完了です')
    if any(card.get(k) != race.get(k) for k in ('date', 'track', 'race')):
        issues.append('出走表の開催日・場・Rが一致しません')
    seen = set()
    for runner in runners:
        if not isinstance(runner, dict):
            issues.append('出走馬の形式が不正です')
            continue
        number = runner.get('number')
        if type(number) is not int or not 1 <= number <= 18 or number in seen:
            issues.append('馬番が不正または重複しています')
            continue
        seen.add(number)
        if runner.get('status') in ('scratched', 'excluded'):
            continue
        missing = []
        if runner.get('status') != 'active':
            missing.append('出走状態')
        matches = [h for h in horses if isinstance(h, dict) and h.get('number') == number]
        horse = matches[0] if len(matches) == 1 else {}
        if len(matches) != 1:
            missing.append('馬別資料（未登録または重複）')
        if not runner.get('name') or horse.get('name') != runner.get('name'):
            missing.append('馬名照合')
        counts = {}
        for field, label in [('recentRuns', '近走'), ('workouts', '調教')]:
            records = horse.get(field, [])
            records = records if isinstance(records, list) else []
            counts[field] = sum(valid_record(r, race.get('date')) for r in records)
            if not counts[field]:
                missing.append(label)
        rows.append(dict(number=number, name=runner.get('name', ''), counts=counts, missing=missing))
    return dict(date=race.get('date'), track=race.get('track'), race=race.get('race'),
                issues=issues, horses=rows,
                note='資料の登録状況のみ。出典の真偽・鮮度・予想精度・公開可否は判定しません。')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('feed', type=Path)
    args = parser.parse_args()
    payload = json.loads(args.feed.read_text(encoding='utf-8'))
    if not isinstance(payload, dict) or not isinstance(payload.get('forecasts'), list):
        parser.error('forecasts配列のある配信JSONを指定してください')
    if not all(isinstance(r, dict) for r in payload['forecasts']):
        parser.error('各レースはJSONオブジェクトが必要です')
    print(json.dumps({'raceCount': len(payload['forecasts']),
                      'reports': [inventory(r) for r in payload['forecasts']]}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
