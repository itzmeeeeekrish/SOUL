import sys
from pathlib import Path

import pytest
from sklearn.feature_extraction.text import TfidfVectorizer


DATA_DIRECTORY = Path(__file__).resolve().parents[2] / "data"
if str(DATA_DIRECTORY) not in sys.path:
    sys.path.insert(0, str(DATA_DIRECTORY))

from audit_multilingual_baseline import (
    calculate_nearest_train_similarity,
    extract_top_character_cues,
    summarise_scores,
)
from train_multilingual_baseline import build_pipeline, sha256_text


def make_row(text, label, language="english"):
    digest = sha256_text(text)
    return {
        "text": text,
        "label": label,
        "language": language,
        "group_id": f"G_{digest[:12]}",
        "model_text_sha256": digest,
    }


def test_summarise_scores_reports_similarity_thresholds_and_label_agreement():
    result = summarise_scores(
        [0.99, 0.91, 0.72, 0.40],
        ["scam", "ham", "ham", "scam"],
        ["scam", "scam", "ham", "ham"],
    )

    assert result["rows"] == 4
    assert result["mean_max_train_similarity"] == pytest.approx(0.755)
    assert result["nearest_train_label_agreement"] == pytest.approx(0.5)
    assert result["similarity_threshold_counts"]["0.9"]["rows"] == 2
    assert result["similarity_threshold_counts"]["0.95"]["nearest_label_agreement"] == 1.0


def test_summarise_scores_rejects_empty_and_mismatched_inputs():
    with pytest.raises(ValueError, match="empty similarity"):
        summarise_scores([], [], [])
    with pytest.raises(ValueError, match="inconsistent lengths"):
        summarise_scores([0.9], ["ham"], [])


def test_nearest_train_similarity_returns_overall_and_language_metrics():
    train_rows = [
        make_row("normal family reminder message", "ham"),
        make_row("urgent share your otp now", "scam"),
    ]
    validation_rows = [
        make_row("normal family reminder message", "ham", "hindi"),
        make_row("urgent share your otp now", "scam", "tamil"),
    ]
    vectorizer = TfidfVectorizer(analyzer="char", ngram_range=(2, 4))
    vectorizer.fit([row["text"] for row in train_rows])

    result = calculate_nearest_train_similarity(
        train_rows,
        validation_rows,
        vectorizer,
    )

    assert result["overall"]["rows"] == 2
    assert result["overall"]["nearest_train_label_agreement"] == 1.0
    assert set(result["by_language"]) == {"hindi", "tamil"}


def test_nearest_train_similarity_rejects_empty_partitions():
    vectorizer = TfidfVectorizer(analyzer="char", ngram_range=(2, 4))
    with pytest.raises(ValueError, match="must both be non-empty"):
        calculate_nearest_train_similarity([], [], vectorizer)


def test_top_character_cues_only_returns_alphabetic_fragments():
    pipeline = build_pipeline()
    texts = [
        "normal family reminder message",
        "normal family dinner reminder",
        "ordinary school meeting message",
        "share your otp immediately",
        "send the pin to claim reward",
        "urgent bank account otp warning",
        "normal bus arrival reminder",
        "share bank pin for prize",
    ]
    labels = ["ham", "ham", "ham", "scam", "scam", "scam", "ham", "scam"]
    pipeline.fit(texts, labels)

    cues = extract_top_character_cues(pipeline, limit=10)

    assert cues["positive_direction_label"] == "scam"
    assert cues["negative_direction_label"] == "ham"
    assert cues["toward_scam"]
    assert cues["toward_ham"]
    assert all(item["character_ngram"].isalpha() for item in cues["toward_scam"])
    assert all(item["character_ngram"].isalpha() for item in cues["toward_ham"])
