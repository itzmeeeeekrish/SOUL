"""Load and run SOUL's local text-only message baseline.

The model is a development baseline, not a production fraud verdict. Its
scores are uncalibrated model outputs and must not be presented as probabilities
that a message is fraudulent.
"""

from functools import lru_cache
import math
from pathlib import Path

import joblib

LABEL_ORDER = ("legitimate", "scam", "spam")
MODEL_NAME = "tfidf_logistic_regression_v1"
MAX_MESSAGE_LENGTH = 5000

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
MODEL_PATH = (
    REPOSITORY_ROOT
    / "data"
    / "private"
    / "model_artifacts"
    / "tfidf_logistic_regression.joblib"
)

GUIDANCE = {
    "legitimate": (
        "The text-only model did not identify a strong scam-like pattern. "
        "This does not prove the sender or message is safe. Verify unexpected "
        "requests through the organisation's official app or known contact details."
    ),
    "spam": (
        "The message resembles unsolicited or promotional content. Avoid "
        "interacting with unexpected links or offers; block or report it if unwanted."
    ),
    "scam": (
        "The message resembles a deceptive request. Do not share OTPs, PINs, "
        "passwords or recovery codes, approve unexpected payment requests, "
        "install remote-access apps, or use the message's contact details. "
        "Verify independently through an official channel."
    ),
}

LIMITATIONS = [
    "This experimental baseline analyses message text only.",
    "It does not inspect the sender, URL destination, app context, device, location, or bank records.",
    "Model scores are uncalibrated and are not probabilities of fraud.",
    "Every result is provisional and must not be treated as proof that fraud did or did not occur.",
]


@lru_cache(maxsize=1)
def load_model():
    """Load the locally generated, trusted joblib artifact once per process."""
    if not MODEL_PATH.is_file():
        raise FileNotFoundError(
            "The local message model is missing. Run data/train_text_baseline.py "
            "from the repository root first."
        )

    try:
        model = joblib.load(MODEL_PATH)
    except Exception as error:
        raise RuntimeError("The local message model could not be loaded.") from error

    if not callable(getattr(model, "predict", None)):
        raise RuntimeError("The local model does not provide predict().")
    if not callable(getattr(model, "predict_proba", None)):
        raise RuntimeError("The local model does not provide predict_proba().")

    classes = tuple(str(label) for label in getattr(model, "classes_", ()))
    if set(classes) != set(LABEL_ORDER) or len(classes) != len(LABEL_ORDER):
        raise RuntimeError("The local model has an unexpected label schema.")

    return model


def analyze_message(text, model=None):
    """Return a cautious, provisional text-only classification."""
    cleaned_text = (text or "").strip()
    if not cleaned_text:
        raise ValueError("Message text must not be blank.")
    if len(cleaned_text) > MAX_MESSAGE_LENGTH:
        raise ValueError(
            f"Message text must be at most {MAX_MESSAGE_LENGTH} characters."
        )

    active_model = model if model is not None else load_model()
    classes = [str(label) for label in active_model.classes_]
    if set(classes) != set(LABEL_ORDER) or len(classes) != len(LABEL_ORDER):
        raise RuntimeError("The model has an unexpected label schema.")

    predicted = str(active_model.predict([cleaned_text])[0])
    if predicted not in LABEL_ORDER:
        raise RuntimeError("The model returned an unsupported label.")

    raw_scores = active_model.predict_proba([cleaned_text])[0]
    if len(raw_scores) != len(classes):
        raise RuntimeError("The model returned an invalid score vector.")

    scores = {}
    for label, raw_score in zip(classes, raw_scores):
        score = float(raw_score)
        if not math.isfinite(score) or score < 0.0 or score > 1.0:
            raise RuntimeError("The model returned an invalid score.")
        scores[label] = score

    ranked_scores = sorted(scores.values(), reverse=True)
    top_score = ranked_scores[0]
    second_score = ranked_scores[1]
    score_margin = top_score - second_score

    return {
        "analysis_status": "provisional_model_suggestion",
        "model": MODEL_NAME,
        "candidate_label": predicted,
        "model_scores": scores,
        "top_model_score": top_score,
        "top_two_score_margin": score_margin,
        "low_score_separation": score_margin < 0.10,
        "review_required": True,
        "guidance": GUIDANCE[predicted],
        "limitations": LIMITATIONS,
    }
