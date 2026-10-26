"""Provisional synthetic-only trifecta planner; no purchasing or publishing."""
from collections import defaultdict
from evaluation_policy import evaluate_race

PLANNER_VERSION = 'research-plan-1'


def _whole_score_groups(tickets, limit):
    """Do not use horse numbers to break a cutoff tie and choose a bet."""
    groups = defaultdict(list)
    for score, ticket in tickets:
        groups[score].append(ticket)
    selected = []
    for score in sorted(groups, reverse=True):
        group = sorted(groups[score])
        if len(selected) + len(group) > limit:
            break
        selected.extend(group)
    return selected


def plan_race(race):
    evaluation = evaluate_race(race)
    result = {
        'policyVersion': evaluation['policyVersion'], 'plannerVersion': PLANNER_VERSION,
        'recordType': 'test', 'status': 'draft', 'publishable': False,
        'validated': False, 'researchDecision': 'hold', 'reason': '',
        'first': [], 'tri': [], 'points': 0, 'stake': 0, 'unit': 100,
        'evaluation': evaluation,
    }

    def stop(reason, decision='hold'):
        result['reason'] = reason
        result['researchDecision'] = decision
        return result

    state = evaluation['reviewState']
    if state == 'data_incomplete':
        return stop('評価資料不足：未評価・未確認の懸念を解消するまで保留')
    if state == 'too_many_candidates':
        return stop('勝ち切る候補が4頭以上：順位だけで切らず再検討')
    if state == 'no_supported_winner':
        return stop('勝ち切る根拠を備えた候補がいないため見送り', 'skip')
    horses = evaluation['horses']
    by_number = {h['number']: h for h in horses}
    first = evaluation['winCandidatesToReview']
    if len(first) == 1:
        lead = by_number[first[0]]
        runner_score = max(h['score'] for h in horses if h['number'] != first[0])
        if lead['overall'] != 'S' or len(lead['winSignals']) < 3 or lead['score'] - runner_score < .5:
            return stop('候補1頭でも固定の根拠が不足：自動で1頭軸にしない')
    viable = [h for h in horses if not h['blockingConcerns'] and not h['unverifiedConcerns']]
    second = [h['number'] for h in viable if h['overall'] in ('S', 'A') or h['number'] in first]
    third = [h['number'] for h in viable if h['overall'] in ('S', 'A', 'B') or h['number'] in first]
    # Share the cap across every winner candidate; never drop a reviewed first horse.
    per_first = 40 // len(first)
    tickets = []
    for a in first:
        choices = []
        for b in second:
            for c in third:
                if len({a, b, c}) != 3:
                    continue
                score = round((by_number[b]['score'] * 2 + by_number[c]['score']) * 100)
                choices.append((score, [a, b, c]))
        selected = _whole_score_groups(choices, per_first)
        if not selected:
            return stop('相手候補不足、または同評価の候補を点数内で公平に絞れないため保留')
        tickets.extend(selected)
    result.update(researchDecision='simulate', reason='架空検証用。根拠のある候補だけで構成し、点数合わせの追加はしない',
                  first=first[:], tri=tickets, points=len(tickets), stake=len(tickets) * 100)
    return result
