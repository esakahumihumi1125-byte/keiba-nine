"""Chronological, synthetic-only settlement. Prediction never receives outcomes.

No data download, file writes, network calls, tuning, or paid model requests.
"""
import hashlib
import json
from evaluation_policy import timestamp
from research_planner import plan_race


def _money(value):
    if type(value) is not int or value < 0:
        raise ValueError('Payout must be a nonnegative integer in yen per 100 yen')
    return value


def _settle(race, plan, outcome):
    if outcome is None:
        return {'status': 'pending', 'stake': plan['stake'], 'returned': None, 'hit': None}
    if not isinstance(outcome, dict) or outcome.get('recordType') != 'test':
        raise ValueError('Only synthetic result data is allowed')
    if timestamp(outcome.get('availableAt')) < timestamp(race['offAt']):
        raise ValueError('A result cannot be available before the race')
    if outcome.get('status') == 'cancelled':
        return {'status': 'refunded', 'stake': plan['stake'], 'returned': plan['stake'], 'hit': None}
    if outcome.get('status') != 'final':
        raise ValueError('Unsupported result status')
    if outcome.get('deadHeat') or outcome.get('excludedNumbers'):
        raise ValueError('Dead heats and exclusions need explicit payout/refund support')
    finish = outcome.get('finish')
    field = {h['number'] for h in race['horses']}
    if not isinstance(finish, list) or len(finish) != 3 or any(type(n) is not int or n not in field for n in finish) or len(set(finish)) != 3:
        raise ValueError('Result must contain three different declared horse numbers')
    payout = _money(outcome.get('trifectaPayout'))
    hit = finish in plan['tri']
    return {'status': 'settled', 'stake': plan['stake'], 'returned': payout if hit else 0, 'hit': hit}


def _summary(rows):
    settled = [r for r in rows if r['settlement']['status'] == 'settled']
    stake = sum(r['settlement']['stake'] for r in settled)
    returned = sum(r['settlement']['returned'] for r in settled)
    equity = peak = drawdown = streak = max_streak = 0
    for row in settled:
        gain = row['settlement']['returned'] - row['settlement']['stake']
        equity += gain
        peak = max(peak, equity)
        drawdown = max(drawdown, peak - equity)
        streak = streak + 1 if gain < 0 else 0
        max_streak = max(max_streak, streak)
    return {
        'raceCount': len(rows), 'simulated': sum(r['plan']['researchDecision'] == 'simulate' for r in rows),
        'held': sum(r['plan']['researchDecision'] == 'hold' for r in rows),
        'skipped': sum(r['plan']['researchDecision'] == 'skip' for r in rows),
        'settled': len(settled), 'hits': sum(r['settlement']['hit'] for r in settled),
        'stake': stake, 'returned': returned, 'net': returned - stake,
        'roi': returned / stake * 100 if stake else None,
        'pendingStake': sum(r['settlement']['stake'] for r in rows if r['settlement']['status'] == 'pending'),
        'refundedStake': sum(r['settlement']['stake'] for r in rows if r['settlement']['status'] == 'refunded'),
        'maxDrawdown': drawdown, 'maxConsecutiveLosingRaces': max_streak,
    }


def backtest(races, outcomes, split_at):
    """Fixed policy in chronological partitions; no fitting to either partition."""
    boundary = timestamp(split_at)
    if not isinstance(races, list) or not isinstance(outcomes, dict):
        raise ValueError('Expected a race list and result map')
    ids = [r.get('raceId') if isinstance(r, dict) else None for r in races]
    if any(not isinstance(i, str) or not i for i in ids) or len(set(ids)) != len(ids):
        raise ValueError('Race IDs must be nonempty and unique')
    keys = [(r.get('date'), r.get('track'), r.get('race')) for r in races]
    for date, track, number in keys:
        if not isinstance(date, str) or not isinstance(track, str) or not track.strip() or type(number) is not int or not 1 <= number <= 12:
            raise ValueError('Each race needs a date, track and race number')
    if len(set(keys)) != len(keys):
        raise ValueError('Multiple versions of one race must not be counted twice')
    if set(outcomes) - set(ids):
        raise ValueError('Results contain unknown races')
    rows = []
    for race in sorted(races, key=lambda r: (timestamp(r['offAt']), r['raceId'])):
        # Freeze the prediction before even looking up the result.
        plan = plan_race(race)
        fingerprint = hashlib.sha256(json.dumps(plan, ensure_ascii=False, sort_keys=True).encode()).hexdigest()
        settlement = _settle(race, plan, outcomes.get(race['raceId'])) if plan['researchDecision'] == 'simulate' else {
            'status': 'not_bet', 'stake': 0, 'returned': None, 'hit': None}
        if timestamp(race['offAt']) < boundary:
            partition = 'development'
        elif timestamp(race['asOf']) >= boundary:
            partition = 'validation'
        else:
            raise ValueError('A race crosses the split boundary; use a boundary between prediction windows')
        rows.append({'raceId': race['raceId'], 'partition': partition,
                     'plan': plan, 'predictionHash': fingerprint, 'settlement': settlement})
    return {'recordType': 'test', 'validated': False, 'splitAt': split_at, 'rows': rows,
            'summary': _summary(rows),
            'development': _summary([r for r in rows if r['partition'] == 'development']),
            'validation': _summary([r for r in rows if r['partition'] == 'validation']),
            'note': '架空データの動作検証。実際の予想成績・利益を示すものではありません。'}
