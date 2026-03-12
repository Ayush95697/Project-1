from pydantic import BaseModel


class SubmitAnswerRequest(BaseModel):
    session_id: str
    question_id: str
    selected_answer: str

