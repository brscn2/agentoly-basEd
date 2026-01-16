from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List, Dict, Any, Literal
from uuid import UUID
from app.api.knowunity_client import KnowunityClient
from app.graph.state import TutoringState
from app.agents.understanding_agent import infer_understanding
from app.agents.tutor_agent import generate_tutoring
from app.utils.logger import logger
from app.models.evaluation import Prediction, PredictionBatch
import uuid

# Create separate routers for tutoring and evaluation endpoints
tutoring_router = APIRouter()
evaluation_router = APIRouter()
api_client = KnowunityClient()


# Request/Response models
class StartTutoringRequest(BaseModel):
    student_id: str
    topic_id: str


class StartTutoringResponse(BaseModel):
    conversation_id: str
    student_id: str
    topic_id: str
    max_turns: int
    conversations_remaining: Optional[int] = None


class InteractRequest(BaseModel):
    conversation_id: str
    tutor_message: Optional[str] = None  # Optional - can auto-generate


class InteractResponse(BaseModel):
    conversation_id: str
    interaction_id: str
    student_response: str
    turn_number: int
    is_complete: bool


class SubmitPredictionsRequest(BaseModel):
    set_type: str
    predictions: List[Dict[str, Any]]  # List of {student_id, topic_id, predicted_level}


class SubmitPredictionsResponse(BaseModel):
    mse_score: float
    submission_info: Dict[str, Any]


class EvaluateTutoringRequest(BaseModel):
    set_type: str


class EvaluateTutoringResponse(BaseModel):
    average_score: float
    evaluation_info: Dict[str, Any]


class AutomatedTutoringRequest(BaseModel):
    set_type: Literal["mini_dev", "dev", "eval"]


class AutomatedTutoringResponse(BaseModel):
    set_type: str
    total_students: int
    total_conversations: int
    conversations: List[Dict[str, Any]]  # List of conversation results
    predictions_submitted: bool
    prediction_submission: Optional[Dict[str, Any]] = None
    tutoring_evaluation: Optional[Dict[str, Any]] = None
    message: str


# In-memory storage for conversation states (in production, use a database)
conversation_states: Dict[str, TutoringState] = {}


@tutoring_router.post("/start", response_model=StartTutoringResponse)
async def start_tutoring(request: StartTutoringRequest):
    """Start a new tutoring conversation with a student on a topic."""
    try:
        # Start conversation with Knowunity API
        start_response = await api_client.start_conversation(
            student_id=request.student_id,
            topic_id=request.topic_id
        )
        
        # Get student and topic info
        students_response = await api_client.get_students()
        student = next((s for s in students_response.students if s.id == request.student_id), None)
        if not student:
            raise HTTPException(status_code=404, detail="Student not found")
        
        topics_response = await api_client.get_topics()
        topic = next((t for t in topics_response.topics if t.id == request.topic_id), None)
        if not topic:
            raise HTTPException(status_code=404, detail="Topic not found")
        
        # Initialize conversation state
        conversation_id = str(start_response.conversation_id)
        initial_state: TutoringState = {
            "conversation_id": UUID(conversation_id),
            "student_id": request.student_id,
            "topic_id": request.topic_id,
            "messages": [],
            "understanding_level": None,
            "understanding_confidence": None,
            "understanding_evidence": None,
            "understanding_level_locked": False,
            "student_profile": {
                "name": student.name,
                "grade_level": student.grade_level
            },
            "topic_info": {
                "name": topic.name,
                "subject_id": topic.subject_id,
                "subject_name": topic.subject_name,
                "grade_level": topic.grade_level
            },
            "turn_count": 0,
            "max_turns": start_response.max_turns,
            "tutor_message": None,
            "student_response": None,
            "conversation_ended": False
        }
        
        # Store state
        conversation_states[conversation_id] = initial_state
        
        return StartTutoringResponse(
            conversation_id=conversation_id,
            student_id=request.student_id,
            topic_id=request.topic_id,
            max_turns=start_response.max_turns,
            conversations_remaining=start_response.conversations_remaining or 0
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error starting conversation: {str(e)}")


@tutoring_router.post("/interact", response_model=InteractResponse)
async def interact_with_student(request: InteractRequest):
    """Send a tutor message and receive a student response."""
    conversation_id = request.conversation_id
    
    # Get conversation state
    if conversation_id not in conversation_states:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    state = conversation_states[conversation_id]
    
    # Check if conversation has ended
    if state.get("conversation_ended", False):
        raise HTTPException(status_code=400, detail="Conversation has ended")
    
    if state.get("turn_count", 0) >= state.get("max_turns", 10):
        raise HTTPException(status_code=400, detail="Maximum turns reached")
    
    try:
        # Generate tutor message if not provided
        tutor_message = request.tutor_message
        if not tutor_message:
            # Generate tutoring message
            tutoring_update = generate_tutoring(state)
            state.update(tutoring_update)
            tutor_message = state.get("tutor_message", "Hello! Let's work on this topic together.")
        
        # Send message to Knowunity API
        interaction_response = await api_client.interact(
            conversation_id=conversation_id,
            tutor_message=tutor_message
        )
        
        # Update state
        messages = state.get("messages", [])
        messages.append({"role": "tutor", "content": tutor_message})
        messages.append({"role": "student", "content": interaction_response.student_response})
        
        state["messages"] = messages
        state["student_response"] = interaction_response.student_response
        state["turn_count"] = interaction_response.turn_number
        state["conversation_ended"] = interaction_response.is_complete
        state["tutor_message"] = tutor_message
        
        # Assess understanding if not locked AND we have at least one student response
        if not state.get("understanding_level_locked", False):
            # Check if we have at least one student response
            student_responses = [msg for msg in state.get("messages", []) if msg.get("role") == "student"]
            if len(student_responses) > 0:
                understanding_update = infer_understanding(state)
                state.update(understanding_update)
                
                # Lock understanding level if agent decides to
                if understanding_update.get("should_lock", False):
                    state["understanding_level_locked"] = True
        
        # Store updated state
        conversation_states[conversation_id] = state
        
        # Log conversation
        logger.log_conversation(
            conversation_id=conversation_id,
            student_id=state["student_id"],
            topic_id=state["topic_id"],
            messages=messages,
            understanding_level=state.get("understanding_level"),
            student_profile=state.get("student_profile"),
            topic_info=state.get("topic_info"),
            metadata={
                "turn_count": state.get("turn_count"),
                "conversation_ended": state.get("conversation_ended")
            }
        )
        
        return InteractResponse(
            conversation_id=conversation_id,
            interaction_id=str(interaction_response.interaction_id),
            student_response=interaction_response.student_response,
            turn_number=interaction_response.turn_number,
            is_complete=interaction_response.is_complete
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error during interaction: {str(e)}")


@evaluation_router.post("/predictions", response_model=SubmitPredictionsResponse)
async def submit_predictions(request: SubmitPredictionsRequest):
    """Submit understanding level predictions and receive MSE score."""
    try:
        # Convert predictions to proper format
        predictions = [
            Prediction(
                student_id=pred["student_id"],
                topic_id=pred["topic_id"],
                predicted_level=pred.get("predicted_level", pred.get("level", 3))  # Support both field names for backward compatibility
            )
            for pred in request.predictions
        ]
        
        # Submit to API
        result = await api_client.submit_predictions(
            set_type=request.set_type,
            predictions=[p.model_dump() for p in predictions]
        )
        
        return SubmitPredictionsResponse(
            mse_score=result.mse_score,
            submission_info={
                "num_predictions": result.num_predictions,
                "submission_number": result.submission_number,
                "submissions_remaining": result.submissions_remaining
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error submitting predictions: {str(e)}")


@evaluation_router.post("/tutoring", response_model=EvaluateTutoringResponse)
async def evaluate_tutoring(request: EvaluateTutoringRequest):
    """Evaluate tutoring quality for a student set."""
    try:
        result = await api_client.evaluate_tutoring(set_type=request.set_type)
        
        return EvaluateTutoringResponse(
            average_score=result.score,
            evaluation_info={
                "num_conversations": result.num_conversations,
                "submission_number": result.submission_number,
                "submissions_remaining": result.submissions_remaining
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error evaluating tutoring: {str(e)}")


async def run_tutoring_conversation(
    student_id: str,
    topic_id: str,
    max_turns: int = 10
) -> Dict[str, Any]:
    """
    Helper function to run a single tutoring conversation.
    Returns conversation result with understanding level.
    """
    # Get student and topic info
    students_response = await api_client.get_students()
    student = next((s for s in students_response.students if s.id == student_id), None)
    if not student:
        raise HTTPException(status_code=404, detail=f"Student {student_id} not found")
    
    topics_response = await api_client.get_topics()
    topic = next((t for t in topics_response.topics if t.id == topic_id), None)
    if not topic:
        raise HTTPException(status_code=404, detail=f"Topic {topic_id} not found")
    
    # Start conversation
    start_response = await api_client.start_conversation(
        student_id=student_id,
        topic_id=topic_id
    )
    conversation_id = str(start_response.conversation_id)
    
    # Initialize conversation state
    initial_state: TutoringState = {
        "conversation_id": UUID(conversation_id),
        "student_id": student_id,
        "topic_id": topic_id,
        "messages": [],
        "understanding_level": None,
        "understanding_confidence": None,
        "understanding_evidence": None,
        "understanding_level_locked": False,
        "student_profile": {
            "name": student.name,
            "grade_level": student.grade_level
        },
        "topic_info": {
            "name": topic.name,
            "subject_id": topic.subject_id,
            "subject_name": topic.subject_name,
            "grade_level": topic.grade_level
        },
        "turn_count": 0,
        "max_turns": start_response.max_turns,
        "tutor_message": None,
        "student_response": None,
        "conversation_ended": False
    }
    
    # Store state
    conversation_states[conversation_id] = initial_state
    
    # Run max_turns of interaction
    turns_completed = 0
    
    for turn in range(max_turns):
        state = conversation_states[conversation_id]
        
        # Check if conversation has ended
        if state.get("conversation_ended", False):
            break
        
        # Check if we've reached max turns
        if state.get("turn_count", 0) >= state.get("max_turns", 10):
            break
        
        # Generate tutoring message
        tutoring_update = generate_tutoring(state)
        state.update(tutoring_update)
        tutor_message = state.get("tutor_message", "Hello! Let's work on this topic together.")
        
        # Send message to Knowunity API
        interaction_response = await api_client.interact(
            conversation_id=conversation_id,
            tutor_message=tutor_message
        )
        
        # Update state
        messages = state.get("messages", [])
        messages.append({"role": "tutor", "content": tutor_message})
        messages.append({"role": "student", "content": interaction_response.student_response})
        
        state["messages"] = messages
        state["student_response"] = interaction_response.student_response
        state["turn_count"] = interaction_response.turn_number
        state["conversation_ended"] = interaction_response.is_complete
        state["tutor_message"] = tutor_message
        
        # Assess understanding if not locked AND we have at least one student response
        if not state.get("understanding_level_locked", False):
            # Check if we have at least one student response
            student_responses = [msg for msg in state.get("messages", []) if msg.get("role") == "student"]
            if len(student_responses) > 0:
                understanding_update = infer_understanding(state)
                state.update(understanding_update)
                
                if understanding_update.get("should_lock", False):
                    state["understanding_level_locked"] = True
        
        # Store updated state
        conversation_states[conversation_id] = state
        
        # Log conversation
        logger.log_conversation(
            conversation_id=conversation_id,
            student_id=state["student_id"],
            topic_id=state["topic_id"],
            messages=messages,
            understanding_level=state.get("understanding_level"),
            student_profile=state.get("student_profile"),
            topic_info=state.get("topic_info"),
            metadata={
                "turn_count": state.get("turn_count"),
                "conversation_ended": state.get("conversation_ended")
            }
        )
        
        turns_completed = interaction_response.turn_number
        
        # Break if conversation ended
        if interaction_response.is_complete:
            break
    
    # Get final understanding level
    final_state = conversation_states.get(conversation_id, initial_state)
    final_understanding_level = final_state.get("understanding_level")
    
    return {
        "student_id": student_id,
        "topic_id": topic_id,
        "conversation_id": conversation_id,
        "turns_completed": turns_completed,
        "understanding_level": final_understanding_level
    }


@tutoring_router.post("/automated", response_model=AutomatedTutoringResponse)
async def automated_tutoring(request: AutomatedTutoringRequest):
    """
    Automated tutoring session for all students in a set: Run conversations, submit predictions, and evaluate.
    
    Takes set_type, automatically:
    1. Gets all students in the set
    2. For each student, gets their topics
    3. Runs 10-turn tutoring conversations for each student-topic pair
    4. Collects all understanding levels
    5. Submits all predictions at once
    6. Calls evaluate_tutoring API
    """
    try:
        # Get all students in the set
        students_response = await api_client.get_students(set_type=request.set_type)
        if not students_response.students:
            raise HTTPException(
                status_code=404,
                detail=f"No students found for set_type {request.set_type}"
            )
        
        # Collect all student-topic pairs and run conversations
        all_predictions = []
        conversation_results = []
        
        for student in students_response.students:
            # Get topics for this student
            student_topics_response = await api_client.get_student_topics(student.id)
            
            for topic in student_topics_response.topics:
                # Run tutoring conversation
                try:
                    result = await run_tutoring_conversation(
                        student_id=student.id,
                        topic_id=topic.id,
                        max_turns=10
                    )
                    conversation_results.append(result)
                    
                    # Add to predictions if we have an understanding level
                    if result["understanding_level"] is not None:
                        all_predictions.append({
                            "student_id": student.id,
                            "topic_id": topic.id,
                            "predicted_level": result["understanding_level"]
                        })
                except Exception as e:
                    print(f"Error running conversation for student {student.id}, topic {topic.id}: {e}")
                    # Continue with other conversations even if one fails
        
        # Submit all predictions at once
        prediction_submission = None
        predictions_submitted = False
        
        if all_predictions:
            try:
                result = await api_client.submit_predictions(
                    set_type=request.set_type,
                    predictions=all_predictions
                )
                prediction_submission = {
                    "mse_score": result.mse_score,
                    "num_predictions": result.num_predictions,
                    "submission_number": result.submission_number,
                    "submissions_remaining": result.submissions_remaining or 0
                }
                predictions_submitted = True
            except Exception as e:
                import traceback
                print(f"Warning: Could not submit predictions: {e}")
                print(f"Number of predictions: {len(all_predictions)}")
                traceback.print_exc()
        
        # Call evaluate_tutoring
        tutoring_evaluation = None
        try:
            eval_result = await api_client.evaluate_tutoring(set_type=request.set_type)
            tutoring_evaluation = {
                "average_score": eval_result.score,
                "num_conversations": eval_result.num_conversations,
                "submission_number": eval_result.submission_number,
                "submissions_remaining": eval_result.submissions_remaining or 0
            }
        except Exception as e:
            print(f"Warning: Could not evaluate tutoring: {e}")
        
        return AutomatedTutoringResponse(
            set_type=request.set_type,
            total_students=len(students_response.students),
            total_conversations=len(conversation_results),
            conversations=conversation_results,
            predictions_submitted=predictions_submitted,
            prediction_submission=prediction_submission,
            tutoring_evaluation=tutoring_evaluation,
            message=f"Completed {len(conversation_results)} conversations for {len(students_response.students)} students. Submitted {len(all_predictions)} predictions."
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error in automated tutoring: {str(e)}")
