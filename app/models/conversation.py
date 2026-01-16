from pydantic import BaseModel
from typing import Optional, Dict, Any
from uuid import UUID


class StartConversationRequest(BaseModel):
    student_id: str
    topic_id: str


class StartConversationResponse(BaseModel):
    conversation_id: UUID
    student_id: UUID
    topic_id: UUID
    max_turns: int
    conversations_remaining: int


class InteractionRequest(BaseModel):
    conversation_id: UUID
    tutor_message: str


class InteractionResponse(BaseModel):
    conversation_id: UUID
    interaction_id: UUID
    student_response: str
    turn_number: int
    is_complete: bool
