from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, ConfigDict


class AnswerRecord(BaseModel):
    question_id: str
    selected_answer: str
    is_correct: bool
    difficulty: float
    topic: str


class StudyPlan(BaseModel):
    step_1: str
    step_2: str
    step_3: str


class UserSession(BaseModel):
    id: str = Field(alias="_id")
    ability_score: float = 0.5
    questions_answered: List[AnswerRecord] = []
    current_question_id: Optional[str] = None
    status: str = "in_progress"  # in_progress | completed
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    study_plan: Optional[StudyPlan] = None

    model_config = ConfigDict(populate_by_name=True)

