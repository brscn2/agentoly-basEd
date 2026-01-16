from typing import TypedDict, List, Dict, Optional, Any
from uuid import UUID


class TutoringState(TypedDict):
    """State for the tutoring conversation graph."""
    conversation_id: Optional[UUID]
    student_id: str
    topic_id: str
    messages: List[Dict[str, Any]]  # Conversation history with role and content
    understanding_level: Optional[int]  # 1-5, inferred from conversation
    understanding_confidence: Optional[float]  # Confidence in understanding assessment (0.0-1.0)
    understanding_evidence: Optional[str]  # Evidence supporting the understanding level assessment
    student_profile: Dict[str, Any]  # name, grade_level, etc.
    topic_info: Dict[str, Any]  # topic name, subject, etc.
    turn_count: int
    max_turns: int
    tutor_message: Optional[str]  # Generated tutor message
    student_response: Optional[str]  # Latest student response
    conversation_ended: bool
