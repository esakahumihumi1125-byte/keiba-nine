"""Unpurchased 3連単 research from SAME complete, comparable observed factor set.

Only PRESTART, historically held research races may get a second, unsigned
experimental example. Missing recent or other grades remove that factor for
ALL runners: never turn absence into zero, C, or a made-up contribution.
This cannot change original drafts, signed receipts, archived odds, purchases,
ROI, or suggest that JRA has independently verified starters/conditions.
"""
from datetime import datetime, timedelta, timezone
import math
import re

from evaluation_policy import OWNER_FORMAL_FACTORS as WEIGHTS
from jrdb_coverage import CoverageError
from jrdb_owner_auto_draft import VERSION as DRAFT_VERSION
from owner_automatic_factor_scores import VERSION as AUTO_VERSION

VERSION = 'owner-comparable-factor-formation-3'
JST = timezone(timedelta(hours=9))
DAY = re.compile(r'20\d{6}\Z', re.ASCII)
OFF = re.compile(r'(?:[01]\d|2[0-3]):[0-5]\d\Z', re.ASCII)
GRADES = {'S': 3, 'A': 2, 'B': 1, 'C': 0}
AUTO_FACTORS = ('course_distance', 'pace', 'ground', 'jockey_stable', 'rotation')
# The owner's three highest-priority present-condition factors provide 64
# available research points: training 30 + course/distance 17 + pace 17.
# Research-2 required 70/100, so a fully observed core trio could be
# excluded merely because a non-core staff or rotation slot was blank.
# Only this complete trio qualifies for the narrower >=64 research path.
# Missing *any* factor is still omitted race-wide, never imputed as C/zero.
MIN_COMPARABLE_WEIGHT = 64
LEGACY_MIN_WITHOUT_CORE_TRIO = 70
CORE_TRIO = ('training', 'course_distance', 'pace')
assert sum(WEIGHTS[k] for k in CORE_TRIO) == MIN_COMPARABLE_WEIGHT
MAX_RACES = 120
# Fixed aggregate statuses only: no dates, horse IDs, race keys or provider rows.
DIAGNOSTIC_KEYS = (
    'ineligible', 'time_unavailable', 'roster_mismatch',
    'training_missing', 'factor_invalid', 'insufficient_shared_weight',
    'tie_or_point_limit', 'preview',
)


def _grade_points(value, weight):
    return weight * GRADES[value] / 3


def _formation(ranked):
    n = len(ranked)
    def whole(size):
        return 1 <= size <= n and (
            size == n or ranked[size - 1]['units'] > ranked[size]['units'])
    options = []
    for first in (2, 1, 3):
        if not whole(first):
            continue
        for second in range(first + 1, min(n, 8) + 1):
            if not whole(second):
                continue
            for third in range(max(3, second), n + 1):
                if not whole(third):
                    continue
                count = first * (second - 1) * (third - 2)
                if 12 <= count <= 48:
                    options.append((first, second, third, count))
    if not options:
        return None
    # 2 first horses first; 1 only if uniquely clear; equal score tiers
    # are never split by a lower horse number at any cutoff.
    options.sort(key=lambda o: (
        o[0] == 2, 30 <= o[3] <= 40,
        o[0] == 1, -abs(o[3] - 36), o[3]), reverse=True)
    first, second, third, count = options[0]
    return {
        'first': [h['number'] for h in ranked[:first]],
        'second': [h['number'] for h in ranked[:second]],
        'third': [h['number'] for h in ranked[:third]],
        'points': count,
    }


def _candidate(base, automatic, day, now, *, allow_provisional=False):
    # The existing HELD pathway remains the default and is unchanged.
    # A separate, explicitly read-only caller may compare races that
    # already have an issued two-factor provisional draft, without EVER
    # replacing, signing or adding to that draft's original ticket list.
    appropriate = (
        base.get('status') == 'provisional_draft'
        if allow_provisional else
        base.get('status') == 'hold' and base.get('reason') in
        ('missing_factors', 'ambiguous_equal_grade_boundary')
    )
    if (not appropriate
            or automatic.get('status') != 'scored'
            or automatic.get('reason') is not None
            or automatic.get('track') != base.get('track')
            or automatic.get('race') != base.get('race')
            or automatic.get('postTime') != base.get('postTime')):
        return None, 'ineligible'
    off_text = base.get('postTime')
    if not isinstance(off_text, str) or not OFF.fullmatch(off_text):
        return None, 'time_unavailable'
    off = datetime.strptime(day + off_text, '%Y%m%d%H:%M').replace(tzinfo=JST)
    if now >= off or now.date() > off.date():
        return None, 'time_unavailable'
    original, scored = base.get('runners'), automatic.get('horses')
    if (not isinstance(original, list) or not isinstance(scored, list)
            or not 5 <= len(original) <= 18 or len(original) != len(scored)
            or base.get('horseCount') != len(original)):
        return None, 'roster_mismatch'
    runners, source = {}, {}
    for h in original:
        if (not isinstance(h, dict) or type(h.get('number')) is not int
                or not 1 <= h['number'] <= 18
                or h['number'] in runners
                or h.get('training') not in (*GRADES, '未評価')
                or h.get('recent') not in (*GRADES, '未評価')):
            return None, 'roster_mismatch'
        runners[h['number']] = h
    for h in scored:
        if (not isinstance(h, dict) or type(h.get('number')) is not int
                or h['number'] in source or h['number'] not in runners
                or not isinstance(h.get('factors'), dict)):
            return None, 'roster_mismatch'
        source[h['number']] = h['factors']
    if set(source) != set(runners):
        return None, 'roster_mismatch'
    # Training is the owner's dominant source. Without full training
    # coverage there is no research formation, not a lower-grade default.
    if not all(h['training'] in GRADES for h in runners.values()):
        return None, 'training_missing'
    keys = ['training']
    if all(h['recent'] in GRADES for h in runners.values()):
        keys.append('recent')
    for name in AUTO_FACTORS:
        weight = WEIGHTS[name]
        values = [source[number].get(name) for number in runners]
        if any(not isinstance(v, dict) or v.get('weight') != weight
               for v in values):
            return None, 'factor_invalid'
        known = []
        for v in values:
            points, score = v.get('points'), v.get('score')
            if points is None or score is None:
                known.append(False)
                continue
            if (type(points) not in (float, int) or type(score) not in (float, int)
                    or not math.isfinite(points) or not math.isfinite(score)
                    or not 0 <= score <= 100 or not 0 <= points <= weight
                    or abs(points - score * weight / 100) > .0001):
                return None, 'factor_invalid'
            known.append(True)
        # Missing on ANY runner excludes this factor for the WHOLE race.
        if all(known):
            keys.append(name)
    capacity = sum(WEIGHTS[k] for k in keys)
    if (capacity < MIN_COMPARABLE_WEIGHT or
            (capacity < LEGACY_MIN_WITHOUT_CORE_TRIO
             and not all(k in keys for k in CORE_TRIO))):
        # A low 64..69 common-weight total is acceptable ONLY when all
        # horses have each of the three essential observed factors.
        # This does not create a formal 100-point grade or any receipt.
        return None, 'insufficient_shared_weight'
    order = []
    for number, row in runners.items():
        earned = _grade_points(row['training'], WEIGHTS['training'])
        if 'recent' in keys:
            earned += _grade_points(row['recent'], WEIGHTS['recent'])
        for name in AUTO_FACTORS:
            if name in keys:
                earned += source[number][name]['points']
        order.append({'number': number, 'units': round(earned * 10000)})
    order.sort(key=lambda h: (-h['units'], h['number']))
    formation = _formation(order)
    if not formation:
        return None, 'tie_or_point_limit'
    return {
        'track': base['track'], 'race': base['race'],
        'postTime': off_text, 'status': ('provisional_comparable_research_only'
                                       if allow_provisional else 'comparable_research_only'),
        **formation,
        'comparedKeys': keys, 'comparedWeight': capacity,
        'excludedKeys': [k for k in ('training', 'recent', *AUTO_FACTORS)
                         if k not in keys],
        'tiesNeverSplit': True, 'missingNeverImputed': True,
        'officialJraVerified': False, 'formalScoreReady': False,
        'bettingReady': False, 'receiptIssued': False, 'actualPurchase': False,
    }, 'preview'


def preview_comparable_factor_holds(report, automatic, day, *, now):
    if (not isinstance(now, datetime) or now.tzinfo is None
            or now.utcoffset() is None or
            type(day) is not str or not DAY.fullmatch(day)
            or not isinstance(report, dict) or not isinstance(automatic, dict)
            or report.get('version') != DRAFT_VERSION
            or automatic.get('version') != AUTO_VERSION
            or report.get('date') != day or automatic.get('date') != day
            or report.get('researchOnly') is not True
            or report.get('privateOwnerOnly') is not True
            or any(report.get(k) is not False for k in
                   ('officialJraVerified', 'overallPredictionReady', 'bettingReady', 'autoPurchase'))
            or automatic.get('officialJraVerified') is not False
            or automatic.get('overallPredictionReady') is not False
            or automatic.get('modelCalibrated') is not False
            or automatic.get('newProviderRequests') != 0
            or type(automatic.get('maximumPoints')) is not int
            or automatic['maximumPoints'] != sum(WEIGHTS[k] for k in AUTO_FACTORS)
            or automatic.get('factorKeys') !=
            ['pace', 'jockey_stable', 'rotation', 'course_distance', 'ground']
            or not isinstance(report.get('races'), list)
            or not isinstance(automatic.get('races'), list)
            or len(report['races']) > MAX_RACES
            or len(report['races']) != len(automatic['races'])
            or report.get('raceCount') != len(report['races'])):
        raise CoverageError('Invalid comparable research snapshot')
    original, seen = {}, set()
    for race in report['races']:
        if not isinstance(race, dict):
            raise CoverageError('Invalid held race')
        coord = race.get('track'), race.get('race')
        if coord in original:
            raise CoverageError('Duplicate held race')
        original[coord] = race
    rows = []
    reviewed = 0
    diagnostics = {key: 0 for key in DIAGNOSTIC_KEYS}
    now_jst = now.astimezone(JST)
    for row in automatic['races']:
        if not isinstance(row, dict):
            raise CoverageError('Invalid score race')
        coord = row.get('track'), row.get('race')
        if coord in seen or coord not in original:
            raise CoverageError('Missing or duplicated score race')
        seen.add(coord)
        base = original[coord]
        if (base.get('status') != 'hold'
                or base.get('reason') not in
                ('missing_factors', 'ambiguous_equal_grade_boundary')):
            continue
        reviewed += 1
        candidate, reason = _candidate(base, row, day, now_jst)
        diagnostics[reason] += 1
        if candidate:
            rows.append(candidate)
    return {
        'version': VERSION, 'date': day, 'raceCount': len(original),
        'reviewedHeldRaces': reviewed, 'unsignedReferenceCount': len(rows),
        'diagnostics': diagnostics, 'minimumComparableWeight': MIN_COMPARABLE_WEIGHT,
        'races': rows, 'researchOnly': True, 'privateOwnerOnly': True,
        'officialJraVerified': False, 'formalTenFactorReady': False,
        'predictionReady': False, 'bettingReady': False,
        'ticketsIssued': 0, 'newProviderRequests': 0,
        'changesExistingDrafts': False, 'changesExistingReceipts': False,
        'changesExistingRoi': False,
        'note': '比較可能な暫定項目のみ。未確認項目は全頭一律で集計対象外。正式100点予想や購入推奨ではありません。',
    }
