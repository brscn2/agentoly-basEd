import httpx
from typing import Optional, List
from app.config import settings
from app.models.student import StudentListResponse
from app.models.topic import TopicListResponse, SubjectListResponse
from app.models.conversation import (
    StartConversationRequest,
    StartConversationResponse,
    InteractionRequest,
    InteractionResponse
)
from app.models.evaluation import Prediction, PredictionBatch, MSEResult, TutoringEvaluationRequest, TutoringEvaluationResult


class KnowunityClient:
    """Client for interacting with the Knowunity API."""
    
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        self.api_key = api_key or settings.knowunity_api_key
        self.base_url = base_url or settings.knowunity_api_base
        self._headers = {
            "X-Api-Key": self.api_key,
            "Content-Type": "application/json"
        }
    
    async def get_students(self, set_type: Optional[str] = None) -> StudentListResponse:
        """List available students, optionally filtered by set type."""
        params = {}
        if set_type:
            params["set_type"] = set_type
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/students",
                headers=self._headers,
                params=params,
                timeout=30.0
            )
            response.raise_for_status()
            return StudentListResponse(**response.json())
    
    async def get_student_topics(self, student_id: str) -> TopicListResponse:
        """Get topics that a specific student has understanding levels for."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/students/{student_id}/topics",
                headers=self._headers,
                timeout=30.0
            )
            response.raise_for_status()
            return TopicListResponse(**response.json())
    
    async def get_subjects(self) -> SubjectListResponse:
        """List all available subjects."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/subjects",
                headers=self._headers,
                timeout=30.0
            )
            response.raise_for_status()
            return SubjectListResponse(**response.json())
    
    async def get_topics(self, subject_id: Optional[str] = None) -> TopicListResponse:
        """List all available topics, optionally filtered by subject."""
        params = {}
        if subject_id:
            params["subject_id"] = subject_id
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/topics",
                headers=self._headers,
                params=params,
                timeout=30.0
            )
            response.raise_for_status()
            return TopicListResponse(**response.json())
    
    async def start_conversation(
        self, 
        student_id: str, 
        topic_id: str
    ) -> StartConversationResponse:
        """Start a new conversation with a student on a topic."""
        request_data = StartConversationRequest(
            student_id=student_id,
            topic_id=topic_id
        )
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/interact/start",
                headers=self._headers,
                json=request_data.model_dump(),
                timeout=30.0
            )
            response.raise_for_status()
            return StartConversationResponse(**response.json())
    
    async def interact(
        self,
        conversation_id: str,
        tutor_message: str
    ) -> InteractionResponse:
        """Send a tutor message and receive a student response."""
        from uuid import UUID
        # Convert string to UUID for the model
        conv_uuid = UUID(conversation_id) if isinstance(conversation_id, str) else conversation_id
        
        request_data = InteractionRequest(
            conversation_id=conv_uuid,
            tutor_message=tutor_message
        )
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/interact",
                headers=self._headers,
                json=request_data.model_dump(mode="json"),
                timeout=30.0
            )
            response.raise_for_status()
            return InteractionResponse(**response.json())
    
    async def submit_predictions(
        self,
        set_type: str,
        predictions: List[dict]
    ) -> MSEResult:
        """Submit understanding level predictions and receive MSE score."""
        # Convert dict predictions to Prediction objects
        prediction_objects = [
            Prediction(**pred) if isinstance(pred, dict) else pred
            for pred in predictions
        ]
        
        batch = PredictionBatch(
            set_type=set_type,
            predictions=prediction_objects
        )
        
        async with httpx.AsyncClient() as client:
            # Serialize to JSON format expected by API
            request_data = batch.model_dump(mode="json")
            response = await client.post(
                f"{self.base_url}/evaluate/mse",
                headers=self._headers,
                json=request_data,
                timeout=60.0
            )
            if response.status_code != 200:
                # Log the error response for debugging
                error_detail = response.text
                print(f"API Error {response.status_code}: {error_detail}")
                print(f"Request data: {request_data}")
            response.raise_for_status()
            response_json = response.json()
            return MSEResult(**response_json)
    
    async def evaluate_tutoring(
        self,
        set_type: str
    ) -> TutoringEvaluationResult:
        """Evaluate tutoring quality for a student set."""
        request_data = TutoringEvaluationRequest(set_type=set_type)
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/evaluate/tutoring",
                headers=self._headers,
                json=request_data.model_dump(),
                timeout=60.0
            )
            response.raise_for_status()
            return TutoringEvaluationResult(**response.json())
