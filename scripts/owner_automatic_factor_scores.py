"""Owner-only rule scores from the already fetched /tky and /tze snapshot.

Versioned, uncalibrated model rules, NOT provider grades or win probabilities.
No odds/marks, extra fetch, result data, ticket mutation, or missing-value fill.
"""
from datetime import datetime, timedelta, timezone
import math

from evaluation_policy import OWNER_FORMAL_FACTORS, OWNER_FORMAL_POLICY_VERSION
from jrdb_coverage import CoverageError
from jrdb_evidence_readiness import audit_evidence_coverage

VERSION = 'owner-automatic-factor-scores-2'
FACTORS = ('pace', 'jockey_stable', 'rotation', 'course_distance')
JST = timezone(timedelta(hours=9))


def _number(value):
    if type(value) not in (str, int, float) or len(str(value)) > 24:
        return None
    try:
        n = float(value)
    except (ValueError, OverflowError):
        return None
    return n if math.isfinite(n) and -10000 <= n <= 10000 else None


def _percentile(value, values):
    # Midrank: identical observations ALWAYS receive identical scores.
    # All-equal fields carry no separation and give the neutral midpoint.
    lower = sum(x < value for x in values)
    equal = sum(x == value for x in values)
    return 100 * (lower + (equal - 1) / 2) / (len(values) - 1)


def _slot(key, value, reason):
    weight = OWNER_FORMAL_FACTORS[key]
    if value is None:
        return {'score': None, 'points': None, 'weight': weight,
                'grade': '未評価', 'reason': reason}
    score = round(value, 4)
    grade = 'S' if score >= 85 else 'A' if score >= 70 else 'B' if score >= 55 else 'C'
    return {'score': score, 'points': round(score * weight / 100, 4),
            'weight': weight, 'grade': grade, 'reason': reason}


def _distance_aptitude_only(race, entry):
    """Uncalibrated distance-only research, not proof of course suitability."""
    distance = race.get('distance_m')
    if (race.get('surface') not in ('芝', 'ダート') or type(distance) is not int
            or not 800 <= distance <= 3600):
        return None, 'course_context_missing'
    code = entry.get('distance_aptitude_cd1')
    bands = ('1', '5', '2', '3')
    if type(code) is not str or code not in (*bands, '6'):
        return None, 'distance_code_missing'
    if code == '6':
        return 75, 'distance_only_versatile'
    target = ('1' if distance <= 1400 else '5' if distance <= 1800 else
              '2' if distance <= 2400 else '3')
    gap = abs(bands.index(code) - bands.index(target))
    return ((85, 'distance_only_match') if gap == 0 else
            (65, 'distance_only_adjacent') if gap == 1 else
            (40, 'distance_only_far'))


def automatic_factor_scores(programme, entries, recent, day, *, now):
    if not isinstance(now, datetime) or now.tzinfo is None or now.utcoffset() is None:
        raise CoverageError('Server clock must include timezone')
    audit_evidence_coverage(programme, entries, [], recent, day)
    target = datetime.strptime(day, '%Y%m%d').date()
    by_number = {(e['racekey'], e['horse_number']): e for e in entries}
    by_id = {(e['racekey'], e['horse_id']): e for e in entries if e.get('horse_id')}
    history = {}
    for row in recent:
        entry = by_id.get((row['racekey'], row.get('horse_id')))
        if entry is None:
            entry = by_number.get((row['racekey'], row.get('horse_number')))
        if entry is None:
            continue
        key = entry['racekey'], entry['horse_number']
        if key in history:
            raise CoverageError('Duplicate recent source')
        history[key] = row
    races = []
    for race in programme:
        key = race['racekey']
        rows = [e for e in entries if e['racekey'] == key]
        reason = None
        if race.get('headcount') != len(rows) or not 4 <= len(rows) <= 18:
            reason = 'roster_incomplete'
        if any(e.get('withdrawn_flag') not in ('0', '1') for e in rows):
            reason = 'withdrawal_unknown'
        active = [e for e in rows if e.get('withdrawn_flag') == '0']
        if len(active) < 4:
            reason = reason or 'too_few_active'
        try:
            off = datetime.fromisoformat(target.isoformat() + 'T' + race['post_time'] + ':00+09:00')
        except (ValueError, KeyError, TypeError):
            off = None
        if off is None:
            reason = 'post_time_unknown'
        elif now >= off:
            reason = 'after_start'
        # Current snapshots must never masquerade as historical predictions.
        if target < now.astimezone(JST).date():
            reason = 'after_start'
        result = {'track': race['track'], 'race': race['race'],
                  'status': 'held' if reason else 'scored', 'reason': reason,
                  'postTime': race.get('post_time'), 'horses': []}
        if reason:
            races.append(result)
            continue
        styles = [e.get('foottype_cd') for e in active]
        known_styles = all(type(s) is str and s in ('1', '2', '3', '4', '5', '6') for s in styles)
        front_fraction = sum(s in ('1', '2') for s in styles) / len(active)
        scenario = 'fast' if front_fraction >= .5 else 'slow' if front_fraction <= .25 else 'balanced'
        # Transparent model assumption: more early runners increase pressure.
        pace_values = {'fast': {'1': 40, '2': 55, '3': 85, '4': 75, '5': 80, '6': 75},
                       'slow': {'1': 85, '2': 80, '3': 55, '4': 40, '5': 70, '6': 75},
                       'balanced': {'1': 60, '2': 70, '3': 70, '4': 60, '5': 75, '6': 75}}
        jockeys = [_number(e.get('jockey_index')) for e in active]
        stables = [_number(e.get('stable_index')) for e in active]
        staff_complete = None not in jockeys and None not in stables
        for i, entry in enumerate(active):
            past = history.get((key, entry['horse_number']), {})
            prior = past.get('race_back_1_racedate')
            gap = (target - datetime.strptime(prior, '%Y%m%d').date()).days if prior else None
            rotation = None if gap is None else (80 if 14 <= gap <= 56 else
                        65 if 7 <= gap <= 90 else 50)
            staff = ((_percentile(jockeys[i], jockeys) + _percentile(stables[i], stables)) / 2
                     if staff_complete else None)
            distance_score, distance_reason = _distance_aptitude_only(race, entry)
            slots = {
                'course_distance': _slot('course_distance', distance_score, distance_reason),
                'pace': _slot('pace', pace_values[scenario][styles[i]] if known_styles else None,
                              'pace_' + scenario if known_styles else 'styles_missing'),
                'jockey_stable': _slot('jockey_stable', staff,
                                     'staff_relative_midrank' if staff_complete else 'staff_missing'),
                'rotation': _slot('rotation', rotation,
                                 'rotation_14_56' if gap is not None and 14 <= gap <= 56 else
                                 'rotation_7_90' if gap is not None and 7 <= gap <= 90 else
                                 'rotation_outside' if gap is not None else 'previous_date_missing'),
            }
            result['horses'].append({'number': int(entry['horse_number']), 'factors': slots})
        races.append(result)
    return {'version': VERSION, 'policyVersion': OWNER_FORMAL_POLICY_VERSION,
            'date': day, 'capturedAt': now.isoformat(), 'races': races,
            'factorKeys': list(FACTORS), 'maximumPoints': sum(OWNER_FORMAL_FACTORS[k] for k in FACTORS),
            'modelCalibrated': False, 'officialJraVerified': False,
            'overallPredictionReady': False, 'newProviderRequests': 0}
