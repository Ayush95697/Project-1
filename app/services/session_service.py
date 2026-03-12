import logging
import uuid
from datetime import datetime
from typing import Any, Dict, Optional

from pymongo.collection import Collection
from pymongo.database import Database
from pymongo.errors import PyMongoError

from app.db import get_database
from app.models.session import AnswerRecord, UserSession, StudyPlan
from app.schemas.requests import SubmitAnswerRequest
from app.schemas.responses import (
    QuestionResponse,
    StartTestResponse,
    SubmitAnswerResponse,
    ResultCore,
    ResultResponse,
    StudyPlanResponse,
)
from app.services.adaptive_engine import (
    update_ability,
    select_next_question,
    compute_session_statistics,
)
from app.services.llm_service import generate_study_plan
from app.services.question_service import (
    get_all_questions,
    get_question_by_id,
    sanitize_question_document,
)

logger = logging.getLogger(__name__)

MAX_QUESTIONS_PER_SESSION = 10


def _sessions_collection(db: Database) -> Collection:
    return db["user_sessions"]


def _load_session(session_id: str, db: Database | None = None) -> UserSession:
    if db is None:
        db = get_database()
    coll = _sessions_collection(db)
    doc = coll.find_one({"_id": session_id})
    if not doc:
        raise LookupError("Session not found.")
    return UserSession.model_validate(doc)


def _save_session(session: UserSession, db: Database | None = None) -> None:
    if db is None:
        db = get_database()
    coll = _sessions_collection(db)
    try:
        coll.replace_one({"_id": session.id}, session.model_dump(by_alias=True), upsert=True)
    except PyMongoError as exc:
        logger.exception("Failed to persist session: %s", exc)
        raise RuntimeError("Failed to persist session") from exc


def _select_initial_question(ability: float, db: Database | None = None) -> Dict[str, Any]:
    questions = get_all_questions(db=db)
    if not questions:
        raise RuntimeError("No questions available in the database.")

    # Pick the question closest to the initial ability (e.g., 0.5).
    questions.sort(key=lambda q: abs(float(q.get("difficulty", 0.5)) - ability))
    return questions[0]


def start_new_session(db: Database | None = None) -> StartTestResponse:
    if db is None:
        db = get_database()
    coll = _sessions_collection(db)

    ability = 0.5
    first_question = _select_initial_question(ability, db=db)
    session_id = str(uuid.uuid4())

    session = UserSession(
        _id=session_id,
        ability_score=ability,
        questions_answered=[],
        current_question_id=first_question["_id"],
        status="in_progress",
        created_at=datetime.utcnow(),
        completed_at=None,
    )

    try:
        coll.insert_one(session.model_dump(by_alias=True))
    except PyMongoError as exc:
        logger.exception("Failed to create session: %s", exc)
        raise RuntimeError("Failed to create session") from exc

    question_payload = QuestionResponse(**sanitize_question_document(first_question))
    return StartTestResponse(
        session_id=session_id,
        ability_score=session.ability_score,
        question=question_payload,
    )


def get_current_question_for_session(session_id: str, db: Database | None = None) -> Optional[QuestionResponse]:
    session = _load_session(session_id, db=db)
    if session.status == "completed":
        raise ValueError("Test already completed for this session.")
    if not session.current_question_id:
        return None
    question_doc = get_question_by_id(session.current_question_id, db=db)
    if not question_doc:
        raise RuntimeError("Current question not found in database.")
    return QuestionResponse(**sanitize_question_document(question_doc))


def _has_answered_question(session: UserSession, question_id: str) -> bool:
    return any(ans.question_id == question_id for ans in session.questions_answered)


def submit_answer_for_session(payload: SubmitAnswerRequest, db: Database | None = None) -> SubmitAnswerResponse:
    session = _load_session(payload.session_id, db=db)
    if session.status == "completed":
        raise PermissionError("Test is already completed for this session.")

    if payload.question_id != session.current_question_id:
        raise ValueError("Submitted question does not match the current question for this session.")

    if _has_answered_question(session, payload.question_id):
        raise PermissionError("This question has already been answered in this session.")

    question_doc = get_question_by_id(payload.question_id, db=db)
    if not question_doc:
        raise LookupError("Question not found.")

    correct_answer = question_doc["correct_answer"]
    is_correct = payload.selected_answer == correct_answer
    difficulty = float(question_doc["difficulty"])
    topic = question_doc["topic"]

    # Update ability using the IRT-based rule.
    new_ability = update_ability(
        theta=session.ability_score,
        difficulty=difficulty,
        is_correct=is_correct,
    )

    answer_record = AnswerRecord(
        question_id=payload.question_id,
        selected_answer=payload.selected_answer,
        is_correct=is_correct,
        difficulty=difficulty,
        topic=topic,
    )
    session.questions_answered.append(answer_record)
    session.ability_score = new_ability

    # Determine whether to continue or complete the test.
    total_answered = len(session.questions_answered)
    next_question_payload: Optional[QuestionResponse] = None
    completed = False
    result_core: Optional[ResultCore] = None

    if total_answered >= MAX_QUESTIONS_PER_SESSION:
        completed = True
    else:
        # Fetch unanswered questions and select the closest difficulty.
        all_questions = get_all_questions(db=db)
        answered_ids = {ans.question_id for ans in session.questions_answered}
        remaining = [q for q in all_questions if q["_id"] not in answered_ids]

        next_question_doc = select_next_question(session.ability_score, remaining)
        if next_question_doc is None:
            completed = True
        else:
            session.current_question_id = next_question_doc["_id"]
            next_question_payload = QuestionResponse(**sanitize_question_document(next_question_doc))

    if completed:
        session.status = "completed"
        session.current_question_id = None
        session.completed_at = datetime.utcnow()

        # Compute statistics for the session.
        accuracy, total, breakdown, highest_difficulty = compute_session_statistics(session.questions_answered)

        # Identify weak topics: those with lowest accuracy and at least one mistake.
        weak_topics: list[str] = []
        for topic, stats in breakdown.items():
            if stats["total"] > 0 and stats["correct"] < stats["total"]:
                weak_topics.append(topic)

        # Generate study plan using LLM (if configured).
        study_plan_raw = generate_study_plan(
            ability=session.ability_score,
            accuracy=accuracy,
            weak_topics=weak_topics,
            max_difficulty=highest_difficulty,
        )
        study_plan_model: Optional[StudyPlan] = None
        study_plan_resp: Optional[StudyPlanResponse] = None
        if study_plan_raw:
            study_plan_model = StudyPlan(**study_plan_raw)
            study_plan_resp = StudyPlanResponse(**study_plan_raw)

        session.study_plan = study_plan_model

        result_core = ResultCore(
            ability_score=session.ability_score,
            accuracy=accuracy,
            total_answered=int(total),
            topic_breakdown=breakdown,
            highest_difficulty=highest_difficulty,
            study_plan=study_plan_resp,
        )

    _save_session(session, db=db)

    return SubmitAnswerResponse(
        session_id=session.id,
        is_correct=is_correct,
        ability_score=session.ability_score,
        next_question=next_question_payload,
        completed=completed,
        result=result_core,
    )


def get_session_result(session_id: str, db: Database | None = None) -> ResultResponse:
    session = _load_session(session_id, db=db)
    if session.status != "completed":
        raise RuntimeError("Session is not yet completed.")

    accuracy, total, breakdown, highest_difficulty = compute_session_statistics(session.questions_answered)

    study_plan_resp: Optional[StudyPlanResponse] = None
    if session.study_plan:
        study_plan_resp = StudyPlanResponse(
            step_1=session.study_plan.step_1,
            step_2=session.study_plan.step_2,
            step_3=session.study_plan.step_3,
        )

    core = ResultCore(
        ability_score=session.ability_score,
        accuracy=accuracy,
        total_answered=int(total),
        topic_breakdown=breakdown,
        highest_difficulty=highest_difficulty,
        study_plan=study_plan_resp,
    )

    return ResultResponse(session_id=session.id, **core.model_dump())

