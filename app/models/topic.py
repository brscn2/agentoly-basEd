from pydantic import BaseModel
from typing import List, Optional


class Subject(BaseModel):
    id: str
    name: str


class SubjectListResponse(BaseModel):
    subjects: List[Subject]


class Topic(BaseModel):
    id: str
    subject_id: str
    subject_name: Optional[str] = None
    name: str
    grade_level: int


class TopicListResponse(BaseModel):
    topics: List[Topic]
