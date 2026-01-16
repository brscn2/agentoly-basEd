# Multi-Agent Tutoring System

An AI-powered multi-agent tutoring system that infers student understanding levels (1-5) through conversation and provides personalized adaptive teaching. Built with FastAPI, LangGraph, and OpenAI.

## Features

- **Understanding Inference**: Analyzes student conversations to determine understanding level (1-5)
- **Adaptive Tutoring**: Generates personalized teaching messages based on student's understanding level
- **Multi-Agent Architecture**: Uses LangGraph to coordinate between understanding and tutor agents
- **Knowunity API Integration**: Seamlessly interacts with the Knowunity tutoring challenge API
- **Conversation Logging**: Logs all conversations to JSONL files for analysis and improvement

## Project Structure

```
.
├── main.py                    # Application entry point
├── app/
│   ├── api/
│   │   ├── knowunity_client.py    # Knowunity API client
│   │   └── v1/endpoints/
│   │       └── tutoring.py        # Tutoring API endpoints
│   ├── agents/
│   │   ├── understanding_agent.py # Infers student understanding level
│   │   └── tutor_agent.py          # Generates tutoring messages
│   ├── graph/
│   │   ├── state.py                # TutoringState TypedDict
│   │   └── tutoring_graph.py      # LangGraph workflow
│   ├── models/                     # Pydantic models for API
│   ├── prompts/                    # LLM prompts (maintainable)
│   ├── utils/
│   │   └── logger.py               # Conversation logger
│   └── config.py                   # Application configuration
├── logs/                          # Conversation logs (JSONL)
├── requirements.txt
└── README.md
```

## Installation

1. **Install dependencies:**
```bash
pip install -r requirements.txt
```

2. **Set up environment variables:**
```bash
cp .env.example .env
```

Edit `.env` and add your API keys:
```env
# Knowunity API
KNOWUNITY_API_KEY=your_knowunity_api_key_here
KNOWUNITY_API_BASE=https://knowunity-agent-olympics-2026-api.vercel.app

# OpenAI API
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4o-mini

# Optional: Application settings
LOG_DIR=logs
MAX_CONVERSATION_TURNS=10
```

## Running the Application

Start the development server:

```bash
uvicorn main:app --reload
```

The API will be available at:
- **API**: http://localhost:8000
- **Interactive API Documentation**: http://localhost:8000/docs
- **Alternative Docs**: http://localhost:8000/redoc

## API Endpoints

### Tutoring Endpoints

#### 1. Start a Conversation
```http
POST /api/v1/tutor/start
Content-Type: application/json

{
  "student_id": "student-uuid",
  "topic_id": "topic-uuid"
}
```

**Response:**
```json
{
  "conversation_id": "conversation-uuid",
  "student_info": {
    "id": "student-uuid",
    "name": "Student Name",
    "grade_level": 10
  },
  "topic_info": {
    "id": "topic-uuid",
    "name": "Topic Name",
    "subject_id": "subject-uuid",
    "subject_name": "Mathematics",
    "grade_level": 10
  },
  "limits": {
    "conversations_remaining": 4,
    "max_turns": 10
  }
}
```

#### 2. Interact with Student
```http
POST /api/v1/tutor/interact
Content-Type: application/json

{
  "conversation_id": "conversation-uuid",
  "tutor_message": "Optional custom message (auto-generated if omitted)"
}
```

**Response:**
```json
{
  "student_response": "Student's response text",
  "turn_count": 2,
  "understanding_level": 3,
  "conversation_history": [
    {"role": "tutor", "content": "Hello! Let's work on..."},
    {"role": "student", "content": "Okay, I understand..."}
  ],
  "conversation_ended": false,
  "tutor_message": "Generated tutor message"
}
```

### Evaluation Endpoints

#### 3. Submit Predictions
```http
POST /api/v1/evaluate/predictions
Content-Type: application/json

{
  "set_type": "dev",
  "predictions": [
    {
      "student_id": "student-uuid",
      "topic_id": "topic-uuid",
      "predicted_level": 3
    }
  ]
}
```

**Response:**
```json
{
  "mse_score": 0.5,
  "submission_info": {
    "num_predictions": 10,
    "submission_number": 1,
    "submissions_remaining": 99
  }
}
```

#### 4. Evaluate Tutoring Quality
```http
POST /api/v1/evaluate/tutoring
Content-Type: application/json

{
  "set_type": "dev"
}
```

**Response:**
```json
{
  "average_score": 0.85,
  "evaluation_info": {
    "num_conversations": 10,
    "submission_number": 1,
    "submissions_remaining": 99
  }
}
```

## Usage Examples

### Python Example

```python
import httpx

BASE_URL = "http://localhost:8000"

# Start a conversation
response = httpx.post(
    f"{BASE_URL}/api/v1/tutor/start",
    json={
        "student_id": "student-uuid",
        "topic_id": "topic-uuid"
    }
)
conversation = response.json()
conversation_id = conversation["conversation_id"]

# Interact with student (auto-generate tutor message)
response = httpx.post(
    f"{BASE_URL}/api/v1/tutor/interact",
    json={"conversation_id": conversation_id}
)
interaction = response.json()
print(f"Student: {interaction['student_response']}")
print(f"Understanding Level: {interaction['understanding_level']}")

# Continue conversation
for turn in range(5):
    response = httpx.post(
        f"{BASE_URL}/api/v1/tutor/interact",
        json={"conversation_id": conversation_id}
    )
    interaction = response.json()
    print(f"Turn {interaction['turn_count']}: {interaction['student_response']}")
    
    if interaction["conversation_ended"]:
        break
```

### cURL Example

```bash
# Start conversation
CONV_ID=$(curl -X POST "http://localhost:8000/api/v1/tutor/start" \
  -H "Content-Type: application/json" \
  -d '{"student_id":"student-uuid","topic_id":"topic-uuid"}' \
  | jq -r '.conversation_id')

# Interact
curl -X POST "http://localhost:8000/api/v1/tutor/interact" \
  -H "Content-Type: application/json" \
  -d "{\"conversation_id\":\"$CONV_ID\"}"
```

## Understanding Levels

The system infers student understanding on a scale of 1-5:

1. **Struggling** - Needs fundamentals, shows significant gaps
2. **Below Grade** - Below grade level, makes frequent mistakes
3. **At Grade** - At grade level, understands core concepts
4. **Above Grade** - Above grade level, grasps concepts well
5. **Advanced** - Advanced, ready for more challenging material

## Conversation Logging

All conversations are automatically logged to `logs/conversations.jsonl` in JSONL format. Each entry includes:
- Timestamp
- Conversation ID
- Student and topic information
- Full conversation history
- Understanding level and confidence
- Metadata (turn count, etc.)

You can review these logs to analyze and improve the tutoring system.

## Configuration

Key settings in `app/config.py`:
- `knowunity_api_key`: Your Knowunity API key
- `openai_model`: OpenAI model to use (default: `gpt-4o-mini`)
- `max_conversation_turns`: Maximum turns per conversation (default: 10)
- `log_dir`: Directory for conversation logs (default: `logs`)

## Development

This project uses:
- **FastAPI** - Web framework
- **LangGraph** - Multi-agent orchestration
- **LangChain** - LLM integration
- **OpenAI** - Language model
- **Pydantic** - Data validation
- **httpx** - Async HTTP client

## Troubleshooting

1. **API Key Errors**: Make sure your `.env` file has valid API keys
2. **Import Errors**: Ensure all dependencies are installed: `pip install -r requirements.txt`
3. **Port Already in Use**: Change the port: `uvicorn main:app --port 8001`
4. **Logs Directory**: The `logs/` directory is created automatically on first run

## Next Steps

1. Review conversation logs in `logs/conversations.jsonl`
2. Adjust prompts in `app/prompts/` to improve tutoring quality
3. Experiment with different OpenAI models
4. Submit predictions and evaluate tutoring quality via the evaluation endpoints
