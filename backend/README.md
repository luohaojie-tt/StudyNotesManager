# StudyNotesManager Backend

FastAPI backend for the Study Notes Manager application.

## Features

- FastAPI with async support
- PostgreSQL with pgvector for vector operations
- Redis for caching
- JWT authentication
- Baidu OCR integration
- Aliyun OSS integration
- DeepSeek AI integration
- Comprehensive API documentation

## Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL 15+ with pgvector
- Redis 7+

### Installation

1. Create virtual environment:
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure environment:
```bash
cp .env.example .env
# Edit .env with your configuration
```

4. Run database migrations:
```bash
alembic upgrade head
```

5. Start the server:
```bash
uvicorn app.main:app --reload
```

The API will be available at:
- API: http://localhost:8000
- Documentation: http://localhost:8000/docs
- Alternative docs: http://localhost:8000/redoc

## API Documentation

Once the server is running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Project Structure

```
backend/
├── app/
│   ├── main.py              # FastAPI application entry
│   ├── api/                 # API routes
│   ├── models/              # SQLAlchemy models
│   ├── schemas/             # Pydantic schemas
│   ├── services/            # Business logic
│   ├── core/                # Core configuration
│   └── utils/               # Utility functions
├── tests/                   # Test suite
├── alembic/                 # Database migrations
└── requirements.txt         # Python dependencies
```

## Development

### Run tests
```bash
pytest
```

### Format code
```bash
black app/ tests/
```

### Type checking
```bash
mypy app/
```

### Create new migration
```bash
alembic revision --autogenerate -m "description"
```

### Apply migrations
```bash
alembic upgrade head
```
