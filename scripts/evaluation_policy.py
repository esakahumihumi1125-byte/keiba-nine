"""Evidence-based research baseline. No network, paid AI, files or live forecasts.

Inputs are normalized, evidence-backed assessments, NOT raw JRDB fields.
Weights/thresholds are provisional hypotheses, not fitted win probabilities.
"""
from datetime import datetime

POLICY_VERSION = 'research-1'
FACTORS = {
    'training': 20, 'recent': 20, 'course_distance': 20, 'pace': 15,
    'ground': 10, 'pedigree': 5, 'draw_weight': 3, 'jockey_stable': 3,
    'rotation': 2, 'body_condition': 2,
}
CORE = {'training', 'recent', 'course_distance', 'pace', 'ground'}
WIN_FACTORS = {'training', 'recent', 'course_distance', 'pace'}
POINTS = {'S': 3, 'A': 2, 'B': 1, 'C': 0}


def timestamp(value):
    if not isinstance(value, str):
        raise ValueError('Timestamp must be a timezone-aware ISO string')
    try:
        result = datetime.fromisoformat(value.replace('Z', '+00:00'))
    except ValueError:
        raise ValueError('Invalid timestamp') from None
    if result.tzinfo is None:
        raise ValueError('Timestamp needs an explicit timezone')
    return result


def supported(item, cutoff):
    """Require a traceable reason and evidence known by the prediction cutoff."""
    if not isinstance(item, dict) or not isinstance(item.get('reason'), str) or not item['reason'].strip():
        return False
    evidence = item.get('evidence')
    if not isinstance(evidence, list) or not evidence:
        return False
    for source in evidence:
        if not isinstance(source, dict) or not isinstance(source.get('sourceId'), str) or not source['sourceId'].strip():
            return False
        if not isinstance(source.get('reference'), str) or not source['reference'].strip():
            return False
        if timestamp(source.get('availableAt')) > cutoff:
            return False
    return True


def evaluate_race(race):
    """Evaluate synthetic research inputs; never emit a final or purchase signal."""
    if not isinstance(race, dict) or race.get('recordType') != 'test':
        raise ValueError('This unvalidated policy accepts synthetic test races only')
    cutoff, off = timestamp(race.get('asOf')), timestamp(race.get('offAt'))
    if cutoff >= off:
        raise ValueError('Prediction cutoff must precede the race')
    horses = race.get('horses')
    if not isinstance(horses, list) or not 2 <= len(horses) <= 18:
        raise ValueError('Expected 2–18 horses')
    numbers = [h.get('number') if isinstance(h, dict) else None for h in horses]
    if any(type(n) is not int or not 1 <= n <= 18 for n in numbers) or len(set(numbers)) != len(numbers):
        raise ValueError('Horse numbers must be unique integers from 1 to 18')
    evaluated = []
    for horse in horses:
        assessments = horse.get('assessments', {})
        if not isinstance(assessments, dict) or set(assessments) - set(FACTORS):
            raise ValueError('Unknown assessment factor')
        grades, reasons, missing, weighted, coverage = {}, {}, [], 0, 0
        for factor, weight in FACTORS.items():
            item = assessments.get(factor)
            if item is not None and (not isinstance(item, dict) or item.get('grade') not in (*POINTS, '未評価')):
                raise ValueError('Invalid assessment grade')
            if not item or item['grade'] == '未評価' or not supported(item, cutoff):
                grades[factor] = '未評価'
                missing.append(factor)
                continue
            grades[factor] = item['grade']
            reasons[factor] = item['reason']
            weighted += POINTS[item['grade']] * weight
            coverage += weight
        ready = not (CORE & set(missing)) and coverage >= 85
        # No renormalization: missing data can never inflate a score.
        score = weighted / 100 if ready else None
        overall = '未評価' if score is None else 'S' if score >= 2.6 else 'A' if score >= 2 else 'B' if score >= 1 else 'C'
        signals = []
        for factor in sorted(WIN_FACTORS):
            item = assessments.get(factor)
            if grades[factor] in ('S', 'A') and item.get('winSupport') is True:
                signals.append({'factor': factor, 'reason': item['reason']})
        concerns = horse.get('blockingConcerns', [])
        if not isinstance(concerns, list):
            raise ValueError('blockingConcerns must be a list')
        known_concerns = [c['reason'] for c in concerns if supported(c, cutoff)]
        unresolved = len(known_concerns) != len(concerns)
        evaluated.append({
            'number': horse['number'], 'grades': grades, 'reasons': reasons,
            'coverage': coverage, 'score': score, 'overall': overall,
            'missing': missing, 'winSignals': signals,
            'blockingConcerns': known_concerns, 'unverifiedConcerns': unresolved,
            'winReview': ready and len(signals) >= 2 and not known_concerns and not unresolved,
        })
    # Ties share rank: horse number is only a stable display order.
    evaluated.sort(key=lambda h: (h['score'] is None, -(h['score'] or 0), h['number']))
    last_score, last_rank = None, None
    for position, horse in enumerate(evaluated, 1):
        if horse['score'] is None:
            horse['rank'] = None
        else:
            if horse['score'] != last_score:
                last_rank = position
            horse['rank'] = last_rank
            last_score = horse['score']
    candidates = [h['number'] for h in evaluated if h['winReview']]
    if any(h['overall'] == '未評価' or h['unverifiedConcerns'] for h in evaluated):
        review = 'data_incomplete'
    elif len(candidates) > 3:
        review = 'too_many_candidates'
    elif not candidates:
        review = 'no_supported_winner'
    else:
        review = 'review_candidates'
    # Always require review; never silently clip a fourth/fifth-ranked contender.
    return {
        'policyVersion': POLICY_VERSION, 'recordType': 'test', 'status': 'draft',
        'publishable': False, 'validated': False, 'asOf': race['asOf'],
        'horses': evaluated, 'winCandidatesToReview': candidates,
        'candidateLimit': 3, 'reviewState': review,
        'bettingDecision': '保留', 'first': [],
        'note': '仮の評価基準による架空検証。勝率・的中率ではなく、購入推奨ではありません。',
    }
