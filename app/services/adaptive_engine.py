import math
from collections import Counter
from typing import Iterable, Optional, Tuple, Dict

from app.models.session import AnswerRecord


def probability_correct(theta: float, difficulty: float) -> float:
    """
    Logistic IRT probability model for a 1-parameter (difficulty-only) item.

    P(correct | theta, b) = 1 / (1 + exp(-(theta - b)))

    - theta represents the student's latent ability on [0.1, 1.0]
    - difficulty (b) represents the item difficulty on [0.1, 1.0]
    - When theta == difficulty, P(correct) = 0.5
    - When theta >> difficulty, P(correct) approaches 1
    - When theta << difficulty, P(correct) approaches 0
    """
    return 1 / (1 + math.exp(-(theta - difficulty)))


def update_ability(
    theta: float,
    difficulty: float,
    is_correct: bool,
    learning_rate: float = 0.15,
) -> float:
    """
    Update ability using a stochastic gradient step on the log-likelihood.

    - expected = model probability of correctness for current theta and difficulty
    - actual   = 1 if the student answered correctly, else 0

    The update theta <- theta + lr * (actual - expected)
    moves ability up when the student outperforms expectation
    and down when they underperform, with magnitude scaled by
    how "surprising" the outcome is under the current model.

    This is mathematically grounded and avoids arbitrary +/- constants.
    """
    expected = probability_correct(theta, difficulty)
    actual = 1.0 if is_correct else 0.0
    new_theta = theta + learning_rate * (actual - expected)
    # Clamp to the allowed range and round for stability.
    return max(0.1, min(1.0, round(new_theta, 3)))


def select_next_question(
    ability: float,
    remaining_questions: Iterable[dict],
) -> Optional[dict]:
    """
    Select the question whose difficulty is closest to current ability.

    This minimizes |b - theta|, giving the most information about the
    student's true ability along a 1D scale and concentrates items where
    the model is most uncertain (probability ~ 0.5).
    """
    remaining_list = list(remaining_questions)
    if not remaining_list:
        return None

    remaining_list.sort(key=lambda q: abs(float(q.get("difficulty", 0.5)) - ability))
    return remaining_list[0]


def compute_session_statistics(
    answers: Iterable[AnswerRecord],
) -> Tuple[float, float, Dict[str, Dict[str, float]], float]:
    """
    Compute accuracy, topic breakdown, and highest difficulty reached.

    Returns:
        accuracy (0-1),
        total_answered,
        topic_breakdown: {topic: {accuracy, total, correct}},
        highest_difficulty
    """
    answers_list = list(answers)
    if not answers_list:
        return 0.0, 0, {}, 0.0

    total = len(answers_list)
    correct = sum(1 for a in answers_list if a.is_correct)
    accuracy = correct / total if total else 0.0

    topic_counts: Counter[str] = Counter()
    topic_correct: Counter[str] = Counter()
    highest_difficulty = 0.0

    for ans in answers_list:
        topic_counts[ans.topic] += 1
        if ans.is_correct:
            topic_correct[ans.topic] += 1
        if ans.difficulty > highest_difficulty:
            highest_difficulty = ans.difficulty

    breakdown: Dict[str, Dict[str, float]] = {}
    for topic, count in topic_counts.items():
        correct_for_topic = topic_correct[topic]
        breakdown[topic] = {
            "total": float(count),
            "correct": float(correct_for_topic),
            "accuracy": float(correct_for_topic) / float(count) if count else 0.0,
        }

    return accuracy, float(total), breakdown, highest_difficulty

