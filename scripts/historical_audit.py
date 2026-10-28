"""Audit real historical input without generating or settling predictions.

Result facts never enter the synthetic research predictor. No network or paid calls.
"""
import argparse
import json
from datetime import datetime

REQUIRED = ('racecard', 'recentRuns', 'workouts', 'courseDistance', 'pace', 'ground')


def stamp(value):
    if not isinstance(value, str):
        raise ValueError('Timestamp required')
    result = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if result.tzinfo is None:
        raise ValueError('Timezone required')
    return result


def audit(record):
    if not isinstance(record, dict) or record.get('recordType') != 'historical':
        raise ValueError('Expected a historical record')
    if not isinstance(record.get('raceId'), str) or not record['raceId'].strip():
        raise ValueError('Race ID required')
    off = stamp(record.get('offAt'))
    cutoff = stamp(record.get('asOf'))
    if cutoff >= off:
        raise ValueError('Prediction cutoff must precede the race')
    field = record.get('declaredNumbers')
    if not isinstance(field, list) or not 3 <= len(field) <= 18 or any(type(n) is not int or not 1 <= n <= 18 for n in field) or len(set(field)) != len(field):
        raise ValueError('Invalid declared numbers')
    evidence = record.get('evidence', [])
    if not isinstance(evidence, list):
        raise ValueError('Evidence must be a list')
    accepted, rejected = [], []
    for index, item in enumerate(evidence):
        reason = None
        if not isinstance(item, dict):
            reason = 'invalid_record'
        elif item.get('kind') not in REQUIRED:
            reason = 'not_prediction_input'
        elif item.get('horseNumber') not in field or type(item.get('horseNumber')) is not int:
            reason = 'unknown_horse'
        elif not all(isinstance(item.get(k), str) and item[k].strip() for k in ('source', 'reference', 'detail')):
            reason = 'missing_provenance_or_detail'
        elif item.get('stage') != 'pre_race':
            reason = 'not_pre_race'
        else:
            try:
                available = stamp(item.get('availableAt'))
                retrieved = stamp(item.get('retrievedAt'))
                if available > retrieved:
                    reason = 'invalid_provenance_time'
                elif available > cutoff:
                    reason = 'after_prediction_cutoff'
            except (ValueError, TypeError):
                reason = 'unknown_availability'
        if reason:
            rejected.append({'index': index, 'reason': reason})
        else:
            accepted.append(item)
    missing = {str(n): [k for k in REQUIRED if not any(e['horseNumber'] == n and e['kind'] == k for e in accepted)] for n in field}
    missing = {n: kinds for n, kinds in missing.items() if kinds}
    result = record.get('result')
    result_status = 'missing'
    if result is not None:
        if not isinstance(result, dict) or result.get('raceId') != record['raceId']:
            raise ValueError('Result race mismatch')
        finish = result.get('finish')
        if not isinstance(finish, list) or len(finish) != 3 or any(type(n) is not int or n not in field for n in finish) or len(set(finish)) != 3:
            raise ValueError('Invalid finishing order')
        if type(result.get('trifectaPayout')) is not int or result['trifectaPayout'] < 0:
            raise ValueError('Invalid payout per 100 yen')
        if not isinstance(result.get('source'), str) or not result['source'].strip() or stamp(result.get('retrievedAt')) < off:
            raise ValueError('Invalid result provenance')
        if result.get('deadHeat') or result.get('excludedNumbers'):
            raise ValueError('Complex settlements are unsupported')
        result_status = 'recorded_not_independently_verified'
    return {'raceId': record['raceId'], 'recordType': 'historical_audit',
            'acceptedEvidence': len(accepted), 'rejectedEvidence': rejected,
            'missingByHorse': missing, 'inputComplete': not missing,
            'resultStatus': result_status, 'predictionStatus': 'not_generated',
            'publishable': False, 'hit': None, 'roi': None,
            'note': '入力の形式・時刻の検査です。情報の真偽や利用許諾、予想精度の保証ではありません。'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', help='Historical JSON file')
    args = parser.parse_args()
    with open(args.input, encoding='utf-8') as f:
        print(json.dumps(audit(json.load(f)), ensure_ascii=False, indent=2))
