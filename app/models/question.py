from typing import List

from pydantic import BaseModel, Field, field_validator, ConfigDict


class Question(BaseModel):
    id: str = Field(alias="_id")
    question_text: str
    options: List[str]
    correct_answer: str
    difficulty: float = Field(ge=0.1, le=1.0)
    topic: str
    tags: List[str] = []

    @field_validator("difficulty")
    @classmethod
    def validate_difficulty(cls, v: float) -> float:  # noqa: B902
        if not 0.1 <= v <= 1.0:
            raise ValueError("difficulty must be between 0.1 and 1.0")
        return v

    model_config = ConfigDict(populate_by_name=True)

