"""HTTP-level tests for the message-analysis endpoint."""

from fastapi.testclient import TestClient

import app.main as main_module
from app.main import app

client = TestClient(app)


def test_message_analysis_endpoint_returns_model_suggestion(monkeypatch):
    expected = {
        "analysis_status": "provisional_model_suggestion",
        "model": "tfidf_logistic_regression_v1",
        "candidate_label": "scam",
        "model_scores": {"legitimate": 0.1, "scam": 0.8, "spam": 0.1},
        "top_model_score": 0.8,
        "top_two_score_margin": 0.7,
        "low_score_separation": False,
        "review_required": True,
        "guidance": "Verify independently.",
        "limitations": ["Text only."],
    }
    monkeypatch.setattr(main_module, "analyze_message", lambda text: expected)

    response = client.post(
        "/v1/messages/analyze",
        json={"text": "Please share your OTP."},
    )

    assert response.status_code == 200
    assert response.json() == expected


def test_message_analysis_endpoint_rejects_blank_text():
    response = client.post("/v1/messages/analyze", json={"text": "   "})

    assert response.status_code == 422


def test_message_analysis_endpoint_rejects_oversized_text():
    response = client.post(
        "/v1/messages/analyze",
        json={"text": "x" * 5001},
    )

    assert response.status_code == 422


def test_message_analysis_endpoint_reports_missing_model(monkeypatch):
    def missing_model(_text):
        raise FileNotFoundError("Local model missing")

    monkeypatch.setattr(main_module, "analyze_message", missing_model)

    response = client.post(
        "/v1/messages/analyze",
        json={"text": "A normal message"},
    )

    assert response.status_code == 503
    assert "not available" in response.json()["detail"]
