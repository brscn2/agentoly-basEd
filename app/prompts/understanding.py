"""Prompts for the understanding agent that infers student understanding levels."""

from langchain_core.prompts import ChatPromptTemplate


UNDERSTANDING_SYSTEM_PROMPT = """You are an expert educational assessor. Your task is to analyze a conversation 
between a tutor and a student to determine the student's understanding level on a specific topic.

Understanding Levels:
1 - Struggling: Student needs fundamentals, shows significant gaps, struggles with basic concepts
2 - Below grade: Student is below grade level, makes frequent mistakes, needs extra support
3 - At grade: Student is at grade level, understands core concepts, occasional minor gaps
4 - Above grade: Student is above grade level, grasps concepts well, occasional minor gaps
5 - Advanced: Student is advanced, ready for more challenging material, demonstrates strong understanding

Analyze the conversation carefully and provide:
1. The understanding level (1-5)
2. Confidence level (0.0-1.0)
3. Key evidence from the conversation that supports this assessment

Respond with a JSON object containing: "level" (int 1-5), "confidence" (float 0.0-1.0), and "evidence" (string)."""

UNDERSTANDING_HUMAN_PROMPT = """Student Profile:
- Name: {student_name}
- Grade Level: {grade_level}

Topic: {topic_name}
Subject: {subject_name}

Conversation History:
{conversation_history}

Based on this conversation, assess the student's understanding level."""


def get_understanding_prompt() -> ChatPromptTemplate:
    """Get the prompt template for understanding assessment."""
    return ChatPromptTemplate.from_messages([
        ("system", UNDERSTANDING_SYSTEM_PROMPT),
        ("human", UNDERSTANDING_HUMAN_PROMPT)
    ])
