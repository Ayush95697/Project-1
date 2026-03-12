from typing import List, Optional, Dict

from pydantic import BaseModel


class QuestionResponse(BaseModel):
    question_id: str
    question_text: str
    options: List[str]
    difficulty: float
    topic: str


class StartTestResponse(BaseModel):
    session_id: str
    ability_score: float
    question: QuestionResponse


class SubmitAnswerResponse(BaseModel):
    session_id: str
    is_correct: bool
    ability_score: float
    next_question: Optional[QuestionResponse] = None
    completed: bool = False
    result: Optional["ResultCore"] = None


class StudyPlanResponse(BaseModel):
    step_1: str
    step_2: str
    step_3: str


class ResultCore(BaseModel):
    ability_score: float
    accuracy: float
    total_answered: int
    topic_breakdown: Dict[str, Dict[str, float]]
    highest_difficulty: float
    study_plan: Optional[StudyPlanResponse] = None


class ResultResponse(ResultCore):
    session_id: str


SubmitAnswerResponse.model_rebuild()

