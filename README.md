# FastAPI Application

A basic FastAPI project structure with organized folders and example endpoints.

## Project Structure

```
.
├── main.py                 # Application entry point
├── app/
│   ├── __init__.py
│   ├── api/
│   │   ├── __init__.py
│   │   └── v1/
│   │       ├── __init__.py
│   │       └── endpoints/
│   │           ├── __init__.py
│   │           └── items.py
│   ├── models/
│   │   ├── __init__.py
│   │   └── item.py
│   └── config.py
├── requirements.txt
├── .env.example
└── README.md
```

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Copy environment file:
```bash
cp .env.example .env
```

## Running the Application

Start the development server:

```bash
uvicorn main:app --reload
```

The API will be available at:
- API: http://localhost:8000
- API Documentation: http://localhost:8000/docs
- Alternative Docs: http://localhost:8000/redoc

## API Endpoints

- `GET /` - Root endpoint
- `GET /health` - Health check
- `GET /api/v1/items` - Get all items
- `GET /api/v1/items/{item_id}` - Get item by ID
- `POST /api/v1/items` - Create new item
- `PUT /api/v1/items/{item_id}` - Update item
- `DELETE /api/v1/items/{item_id}` - Delete item

## Development

This project uses:
- FastAPI for the web framework
- Pydantic for data validation
- Uvicorn as the ASGI server
