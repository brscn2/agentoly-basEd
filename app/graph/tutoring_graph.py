from langgraph.graph import StateGraph, START, END
from app.graph.state import TutoringState
from app.agents.understanding_agent import infer_understanding
from app.agents.tutor_agent import generate_tutoring
from app.config import settings
from typing import Literal


def should_continue(state: TutoringState) -> Literal["infer_understanding", "generate_tutoring", "end"]:
    """Decide next step based on conversation state."""
    turn_count = state.get("turn_count", 0)
    max_turns = state.get("max_turns", 10)
    understanding_level = state.get("understanding_level")
    conversation_ended = state.get("conversation_ended", False)
    
    # End if conversation is ended or max turns reached
    if conversation_ended or turn_count >= max_turns:
        return "end"
    
    # If we don't have an understanding level yet, or it's early in conversation, infer
    if understanding_level is None or turn_count <= 2:
        return "infer_understanding"
    
    # Otherwise, generate tutoring
    return "generate_tutoring"


def should_infer_understanding(state: TutoringState) -> Literal["infer_understanding", "generate_tutoring"]:
    """Decide if we should infer understanding or go straight to tutoring."""
    understanding_level = state.get("understanding_level")
    turn_count = state.get("turn_count", 0)
    
    # Infer understanding if we don't have it, or every few turns to update
    if understanding_level is None or turn_count % 3 == 0:
        return "infer_understanding"
    return "generate_tutoring"


# Create the graph
workflow = StateGraph(TutoringState)

# Add nodes
workflow.add_node("infer_understanding", infer_understanding)
workflow.add_node("generate_tutoring", generate_tutoring)

# Set entry point - start with understanding inference
workflow.set_entry_point("infer_understanding")

# Add conditional edges
workflow.add_conditional_edges(
    "infer_understanding",
    should_infer_understanding,
    {
        "infer_understanding": "infer_understanding",  # Loop if needed
        "generate_tutoring": "generate_tutoring"
    }
)
workflow.add_conditional_edges(
    "generate_tutoring",
    should_continue,
    {
        "infer_understanding": "infer_understanding",
        "generate_tutoring": "generate_tutoring",
        "end": END
    }
)

# Compile the graph
tutoring_graph = workflow.compile()
