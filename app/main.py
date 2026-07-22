"""FastAPI application entry point."""

from fastapi import FastAPI

app = FastAPI(title="AOS API")


@app.get("/")
def read_root() -> dict[str, str]:
    """Return basic API information."""
    return {"message": "AOS API"}


@app.get("/health")
def read_health() -> dict[str, str]:
    """Report whether the API process is healthy."""
    return {"status": "ok"}
