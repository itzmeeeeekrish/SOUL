"""Entry point for the SOUL FastAPI application."""

from fastapi import FastAPI

from app.config import APP_DEBUG, APP_NAME, APP_VERSION

app = FastAPI(
    title=APP_NAME,
    version=APP_VERSION,
    debug=APP_DEBUG,
)


@app.get("/health", tags=["Health"])
def health_check():
    """Return a small response to show that the API is running."""
    return {
        "status": "ok",
        "service": APP_NAME,
        "version": APP_VERSION,
    }
