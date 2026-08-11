# Edge Runtime

The Edge Runtime is an independent microservice responsible for hosting the edge-side runtime of the AI Retail Operating System.

This milestone provides only the production bootstrap.

## Features

- Independent FastAPI application
- Application factory pattern
- Configuration using pydantic-settings
- Centralized logging
- Health endpoint

## Requirements

- Python 3.12+

Install dependencies:

```bash
pip install -r requirements.txt
```

Create a configuration file:

```bash
cp .env.example .env
```

Run the service:

```bash
uvicorn app.main:app --reload
```

Health check:

```
GET /health
```

Response:

```json
{
  "status": "healthy",
  "service": "edge-runtime",
  "version": "0.1.0"
}
```

This milestone intentionally excludes:

- RTSP
- OpenCV
- YOLO
- ByteTrack
- ONNX Runtime
- Camera management
- Redis
- PostgreSQL
- MQTT
- WebSockets
- AI inference
- Business logic