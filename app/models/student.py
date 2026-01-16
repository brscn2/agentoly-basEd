from pydantic import BaseModel
from typing import List


class Student(BaseModel):
    id: str
    name: str
    grade_level: int


class StudentListResponse(BaseModel):
    students: List[Student]
