from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import JsonOutputParser
from app.graph.state import TutoringState
from app.config import settings
from app.prompts.understanding import get_understanding_prompt
from typing import Dict, Any


# Initialize LLM
llm = ChatOpenAI(
    model=settings.openai_model,
    temperature=0.3,
    api_key=settings.openai_api_key
)


def infer_understanding(state: TutoringState) -> Dict[str, Any]:
    """
    Infer student's INITIAL understanding level (1-5) from conversation history.
    Focuses on early student responses before significant tutoring occurred.
    
    Understanding Levels:
    1 -> Struggling, needs fundamentals
    2 -> Below grade, frequent mistakes
    3 -> At grade, core concepts ok
    4 -> Above grade, occasional gaps
    5 -> Advanced, ready for more
    """
    messages = state.get("messages", [])
    student_profile = state.get("student_profile", {})
    topic_info = state.get("topic_info", {})
    
    # Safety check: don't assess if no student responses yet
    student_responses = [msg for msg in messages if msg.get("role") == "student"]
    if len(student_responses) == 0:
        # Return previous values or None if no previous assessment
        return {
            "understanding_level": state.get("understanding_level"),
            "understanding_confidence": state.get("understanding_confidence"),
            "understanding_evidence": state.get("understanding_evidence", ""),
            "should_lock": False
        }
    
    # Filter messages to only include early student responses (before significant tutoring)
    # Look for the first few student responses and tutor messages before extensive teaching
    filtered_messages = []
    tutor_teaching_count = 0
    student_response_count = 0
    
    for msg in messages:
        role = msg.get("role", "")
        content = msg.get("content", "")
        
        if role == "tutor":
            # Count tutor messages that contain significant teaching (long explanations, examples, etc.)
            if len(content) > 100:  # Significant teaching content
                tutor_teaching_count += 1
            filtered_messages.append(msg)
        elif role == "student":
            student_response_count += 1
            filtered_messages.append(msg)
            # Stop after we have enough student responses or if significant tutoring has started
            if student_response_count >= 3 or tutor_teaching_count >= 2:
                break
    
    # Build conversation history string from filtered messages
    conversation_history = "\n".join([
        f"{msg.get('role', 'unknown').upper()}: {msg.get('content', '')}"
        for msg in filtered_messages
    ])
    
    prompt = get_understanding_prompt()
    
    parser = JsonOutputParser()
    chain = prompt | llm | parser
    
    # Get previous values from state as fallbacks
    previous_level = state.get("understanding_level")
    previous_confidence = state.get("understanding_confidence", 0.5)
    previous_evidence = state.get("understanding_evidence", "")
    
    try:
        result = chain.invoke({
            "student_name": student_profile.get("name", "Unknown"),
            "grade_level": student_profile.get("grade_level", "Unknown"),
            "topic_name": topic_info.get("name", "Unknown"),
            "subject_name": topic_info.get("subject_name", "Unknown"),
            "conversation_history": conversation_history or "No conversation yet."
        })
        
        level = result.get("level")
        confidence = result.get("confidence")
        evidence = result.get("evidence", "")
        should_lock = result.get("should_lock", False)
        
        # Validate level is between 1-5, use previous level if invalid
        if not isinstance(level, int) or level < 1 or level > 5:
            if previous_level is not None:
                level = previous_level
            else:
                # Only default to 3 if we have no previous level
                level = 3
        
        # Use previous confidence if new one is invalid or missing
        if confidence is None or not isinstance(confidence, (int, float)) or confidence < 0.0 or confidence > 1.0:
            confidence = previous_confidence
        
        # Determine should_lock if not provided or invalid
        if not isinstance(should_lock, bool):
            # Auto-determine based on confidence and student responses
            should_lock = (
                confidence >= 0.7 and 
                student_response_count >= 1 and
                tutor_teaching_count < 2  # Lock before significant tutoring
            )
        
        return {
            "understanding_level": level,
            "understanding_confidence": confidence,
            "understanding_evidence": evidence or previous_evidence,
            "should_lock": should_lock
        }
    except Exception as e:
        # Fallback: if LLM fails, use previous values if available
        print(f"Error inferring understanding: {e}")
        
        # Use previous level if available, otherwise default to 3
        fallback_level = previous_level if previous_level is not None else 3
        fallback_confidence = previous_confidence if previous_confidence is not None else 0.3
        
        # If we have a previous level and some student responses, we can lock
        should_lock = (
            previous_level is not None and 
            student_response_count >= 1
        )
        
        return {
            "understanding_level": fallback_level,
            "understanding_confidence": fallback_confidence,
            "understanding_evidence": previous_evidence or "Unable to assess - using previous/default level",
            "should_lock": should_lock
        }
