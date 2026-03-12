from fastapi import APIRouter, HTTPException, status

from app.schemas.requests import SubmitAnswerRequest
from app.schemas.responses import (
    QuestionResponse,
    StartTestResponse,
    SubmitAnswerResponse,
    ResultResponse,
)
from app.services.session_service import (
    start_new_session,
    get_current_question_for_session,
    submit_answer_for_session,
    get_session_result,
)

router = APIRouter(prefix="/test", tags=["Adaptive Test"])


@router.post("/start-test", response_model=StartTestResponse)
def start_test() -> StartTestResponse:
    try:
        return start_new_session()
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc


@router.get("/next-question/{session_id}", response_model=QuestionResponse)
def next_question(session_id: str) -> QuestionResponse:
    try:
        question = get_current_question_for_session(session_id)
        if question is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found or no current question.",
            )
        return question
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc


@router.post("/submit-answer", response_model=SubmitAnswerResponse)
def submit_answer(payload: SubmitAnswerRequest) -> SubmitAnswerResponse:
    try:
        return submit_answer_for_session(payload)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except PermissionError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc
    except LookupError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc


@router.get("/result/{session_id}", response_model=ResultResponse)
def get_result(session_id: str) -> ResultResponse:
    try:
        return get_session_result(session_id)
    except LookupError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc

