from langchain_openai import ChatOpenAI
from app.graph.state import TutoringState
from app.config import settings
from app.prompts.tutoring import get_tutoring_prompt, get_teaching_style_guidance
from typing import Dict, Any


# Initialize LLM
llm = ChatOpenAI(
    model=settings.openai_model,
    temperature=0.7,
    api_key=settings.openai_api_key
)


def generate_tutoring(state: TutoringState) -> Dict[str, Any]:
    """
    Generate personalized tutoring message based on understanding level and conversation.
    """
    messages = state.get("messages", [])
    understanding_level = state.get("understanding_level", 3)
    student_profile = state.get("student_profile", {})
    topic_info = state.get("topic_info", {})
    student_response = state.get("student_response", "")
    
    # Build conversation history
    conversation_history = "\n".join([
        f"{msg.get('role', 'unknown').upper()}: {msg.get('content', '')}"
        for msg in messages
    ])
    
    teaching_style = get_teaching_style_guidance(understanding_level)
    prompt = get_tutoring_prompt()
    
    # Determine context for latest response
    if student_response:
        latest_response_context = f"Student's Latest Response: {student_response}\n\nAnalyze this response and provide appropriate feedback or continue teaching."
    else:
        latest_response_context = "This is the start of the conversation. Begin by introducing the topic and assessing the student's prior knowledge."
    
    chain = prompt | llm
    
    try:
        response = chain.invoke({
            "teaching_style": teaching_style,
            "student_name": student_profile.get("name", "Student"),
            "grade_level": student_profile.get("grade_level", "Unknown"),
            "topic_name": topic_info.get("name", "the topic"),
            "subject_name": topic_info.get("subject_name", "the subject"),
            "understanding_level": understanding_level,
            "conversation_history": conversation_history or "No previous conversation.",
            "latest_response_context": latest_response_context
        })
        
        tutor_message = response.content if hasattr(response, 'content') else str(response)
        
        return {
            "tutor_message": tutor_message
        }
    except Exception as e:
        print(f"Error generating tutoring message: {e}")
        # Fallback message
        return {
            "tutor_message": f"Hello! Let's work on {topic_info.get('name', 'this topic')} together. Can you tell me what you already know about it?"
        }
