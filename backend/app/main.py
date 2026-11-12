"""Entry point for the SOUL FastAPI application."""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from app.config import APP_DEBUG, APP_NAME, APP_VERSION
from app.services.message_detector import analyze_message

app = FastAPI(
    title=APP_NAME,
    version=APP_VERSION,
    debug=APP_DEBUG,
)


class MessageAnalysisRequest(BaseModel):
    """A single message supplied by the user for text-only analysis."""

    text: str = Field(min_length=1, max_length=5000)


@app.get("/health", tags=["Health"])
def health_check():
    """Return a small response to show that the API is running."""
    return {
        "status": "ok",
        "service": APP_NAME,
        "version": APP_VERSION,
    }


@app.post("/v1/messages/analyze", tags=["Message analysis"])
def analyze_message_endpoint(request: MessageAnalysisRequest):
    """Return a provisional text-only suggestion from the local baseline."""
    if not request.text.strip():
        raise HTTPException(
            status_code=422,
            detail="Message text must contain at least one non-space character.",
        )

    try:
        return analyze_message(request.text)
    except FileNotFoundError as error:
        raise HTTPException(
            status_code=503,
            detail="The local message model is not available. Train it before using this endpoint.",
        ) from error
    except RuntimeError as error:
        raise HTTPException(
            status_code=503,
            detail="The local message model is unavailable or incompatible.",
        ) from error
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
