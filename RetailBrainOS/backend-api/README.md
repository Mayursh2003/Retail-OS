# Retail Brain OS Backend API

Milestone **0.2** — FastAPI Bootstrap

## Requirements

- Python 3.11+
- pip

## Installation

```bash
python -m venv .venv
```

### Windows

```bash
.venv\Scripts\activate
```

### Linux/macOS

```bash
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

## Run the application

```bash
uvicorn app.main:app --reload
```

The API will start at:

```
http://127.0.0.1:8000
```

## Health Endpoint

```
GET /api/v1/health
```

Example response:

```json
{
  "status": "healthy",
  "service": "backend-api",
  "version": "0.1.0"
}
```

## API Documentation

Swagger UI:

```
http://127.0.0.1:8000/docs
```

ReDoc:

```
http://127.0.0.1:8000/redoc
```

## Current Scope

This milestone intentionally includes only:

- FastAPI application entry point
- Application factory
- API versioning (`/api/v1`)
- Health endpoint

Future milestones will add configuration, logging, middleware, dependency injection, authentication, database integration, Redis, analytics, and Docker support.