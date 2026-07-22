# Architecture

## Current structure

The application is a single FastAPI service running on Python 3.11. The ASGI
application is defined in `app/main.py` and served by Uvicorn.

No database, cache, message broker, agent, or RAG component is part of the current
architecture.
