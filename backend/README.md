# FastAPI Backend Setup

## Prerequisites

- Python 3.8+ installed
- pip package manager

## Installation

1. Navigate to the backend directory:
```bash
cd backend
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Configuration

1. Copy `.env` file and update environment variables as needed:
   - `SUPABASE_URL`: Your Supabase project URL
   - `SUPABASE_SERVICE_ROLE_KEY`: Your Supabase service role key
   - `FRONTEND_URL`: Your frontend URL for CORS configuration
   - `GOOGLE_AI_API_KEY`: Your Google AI Studio API key

## Running the Server

### Development Mode
```bash
python run.py
```

### Production Mode
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## Testing

Run unit tests:
```bash
pytest
```

Run tests with coverage:
```bash
pytest --cov=app
```

## API Endpoints

### Health Check
- `GET /api/health` - Check service health status

## Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application
│   ├── config.py            # Configuration settings
│   ├── routers/
│   │   ├── __init__.py
│   │   └── health.py        # Health check endpoints
│   └── services/
│       ├── __init__.py
│       └── supabase_service.py  # Supabase database operations
├── tests/
│   ├── __init__.py
│   ├── conftest.py          # Test configuration
│   ├── test_supabase_service.py
│   └── test_health_endpoint.py
├── requirements.txt         # Python dependencies
├── pytest.ini             # Pytest configuration
├── run.py                  # Server startup script
└── README.md              # This file
```

## Features Implemented

1. **FastAPI Application**: Main application with proper structure
2. **Configuration Management**: Environment-based configuration using Pydantic
3. **CORS Middleware**: Configured for Next.js frontend communication
4. **Supabase Integration**: Service class for database operations
5. **Health Check Endpoint**: Service health monitoring
6. **Validation Status Updates**: Methods to update validation processing status
7. **Database Operations**: CRUD operations for competitors and feedback
8. **Error Handling**: Comprehensive error handling and logging
9. **Unit Tests**: Complete test suite for all components
10. **Logging**: Structured logging for debugging and monitoring