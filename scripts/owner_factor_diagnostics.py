"""Fixed, non-sensitive reasons for incomplete two-factor assessments."""
TRAINING = {"missing_training_indices", "no_linked_training_record"}
RECENT = {"no_usable_history", "only_one_usable_run", "insufficient_scored_runs", "no_linked_recent_record"}


def missing_reasons(training_grade, recent_grade, training_status=None, recent_status=None):
    reasons = []
    if training_grade == "未評価":
        reasons.append(training_status if training_status in TRAINING else "training_unassessed")
    if recent_grade == "未評価":
        reasons.append(recent_status if recent_status in RECENT else "recent_unassessed")
    return reasons
