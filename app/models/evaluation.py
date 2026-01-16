from pydantic import BaseModel
from typing import List, Literal, Optional


class Prediction(BaseModel):
    student_id: str
    topic_id: str
    predicted_level: int  # 1-5


class PredictionBatch(BaseModel):
    set_type: Literal["mini_dev", "dev", "eval"]
    predictions: List[Prediction]


class MSEResult(BaseModel):
    mse_score: float
    num_predictions: int
    submission_number: int
    submissions_remaining: Optional[int] = None


class TutoringEvaluationRequest(BaseModel):
    set_type: Literal["mini_dev", "dev", "eval"]


class TutoringEvaluationResult(BaseModel):
    score: float
    num_conversations: int
    submission_number: int
    submissions_remaining: Optional[int] = None
