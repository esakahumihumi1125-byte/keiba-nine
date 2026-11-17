"""Owner-only rule scores from the already fetched /tky and /tze snapshot.

Versioned, uncalibrated model rules, NOT provider grades or win probabilities.
No odds/marks, extra fetch, result data, ticket mutation, or missing-value fill.
"""
from datetime import datetime, timedelta, timezone
import math

from evaluation_policy import OWNER_FORMAL_FACTORS, OWNER_FORMAL_POLICY_VERSION
from jrdb_coverage import CoverageError
from jrdb_evidence_readiness import audit_evidence_coverage, _missing_previous_date

VERSION = 'owner-automatic-factor-scores-3'
FACTORS = ('pace', 'jockey_stable', 'rotation', 'course_distance', 'ground')
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


def _ground_condition_research(race, entry, context):
    """Study muddy-going codes only when the same-race /tka going is present.

    A good-going race receives no synthetic ground score; JRDB heavy-ground
    aptitude is not evidence of performance on a fast, dry or firm track.
    """
    if not isinstance(context, dict) or context.get('conditionProviderFetchStatus') != 'received':
        return None, 'ground_going_unknown'
    if (context.get('track') != race.get('track')
            or context.get('race') != race.get('race')
            or context.get('surface') != race.get('surface')
            or context.get('surface') not in ('芝', 'ダート')
            or context.get('conditionSnapshotPresent') is not True
            or context.get('goingAvailable') is not True):
        return None, 'ground_going_unknown'
    if context.get('conditionUpdateCutoffStatus') == 'after_cutoff':
        return None, 'ground_source_after_cutoff'
    going = context.get('going')
    if going == '良':
        return None, 'ground_good_not_scored'
    if going not in ('稍重', '重', '不良'):
        return None, 'ground_going_unknown'
    mudder = entry.get('mudder_cd')
    if type(mudder) is not str or mudder not in ('1', '2', '3'):
        return None, 'ground_mudder_code_missing'
    # Provisional 0-100 rule, NOT provider ability points or a win chance.
    table = {'稍重': {'1': 80, '2': 65, '3': 45},
             '重': {'1': 90, '2': 70, '3': 35},
             '不良': {'1': 90, '2': 70, '3': 35}}
    return table[going][mudder], 'ground_soft_mudder_' + mudder


def automatic_factor_scores(programme, entries, recent, day, *, now, race_context=None):
    if not isinstance(now, datetime) or now.tzinfo is None or now.utcoffset() is None:
        raise CoverageError('Server clock must include timezone')
    audit_evidence_coverage(programme, entries, [], recent, day)
    target = datetime.strptime(day, '%Y%m%d').date()
    # Optional normalized, already-fetched /tka context: no new provider read.
    going_by_race = {}
    if (isinstance(race_context, dict)
            and race_context.get('version') == 'race-context-1'
            # A track/R repeats weekly; reject another date's /tka context.
            # Missing date is unverified, NEVER implicitly today's going.
            and race_context.get('date') == day
            and race_context.get('conditionProviderFetchStatus') == 'received'
            and type(race_context.get('raceCount')) is int
            and isinstance(race_context.get('races'), list)
            and race_context['raceCount'] == len(race_context['races'])
            and len(race_context['races']) <= 120):
        for ctx in race_context['races']:
            if not isinstance(ctx, dict):
                going_by_race = {}
                break
            coordinate = ctx.get('track'), ctx.get('race')
            if coordinate in going_by_race:
                going_by_race = {}
                break
            going_by_race[coordinate] = {**ctx, 'conditionProviderFetchStatus': 'received'}
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
            # The optional /tze beta feed can contain a zero-dated,
            # entirely blank historical slot. Missing history cannot
            # imply that the runner had a previous race or deserves C/0.
            # Nonempty malformed dates are rejected in the shared audit.
            gap = (None if _missing_previous_date(prior)
                   else (target - datetime.strptime(prior, '%Y%m%d').date()).days)
            rotation = None if gap is None else (80 if 14 <= gap <= 56 else
                        65 if 7 <= gap <= 90 else 50)
            staff = ((_percentile(jockeys[i], jockeys) + _percentile(stables[i], stables)) / 2
                     if staff_complete else None)
            distance_score, distance_reason = _distance_aptitude_only(race, entry)
            ground_score, ground_reason = _ground_condition_research(
                race, entry, going_by_race.get((race['track'], race['race'])))
            slots = {
                'course_distance': _slot('course_distance', distance_score, distance_reason),
                'ground': _slot('ground', ground_score, ground_reason),
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
