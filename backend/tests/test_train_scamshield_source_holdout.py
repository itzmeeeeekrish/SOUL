import hashlib
import sys
from pathlib import Path

import pytest

DATA_DIRECTORY = Path(__file__).resolve().parents[2] / "data"
if str(DATA_DIRECTORY) not in sys.path:
    sys.path.insert(0, str(DATA_DIRECTORY))

from split_scamshield_candidate import DEFAULT_HELDOUT_SOURCE
from train_scamshield_baseline import LABEL_ORDER
from train_scamshield_source_holdout import partition_source_holdout


def make_rows(per_class=12, holdout_per_class=5, include_overlap=True):
    rows = []
    index = 0
    phrases = {
        "legitimate": "Appointment confirmation normal update",
        "spam": "Promotional discount offer buy now",
        "scam": "Urgent fake KYC OTP account blocked",
    }

    for label in LABEL_ORDER:
        for _ in range(per_class):
            index += 1
            text = f"{phrases[label]} record {index}"
            rows.append({
                "model_row_id": f"SS_{index:05d}",
                "text": text,
                "label": label,
                "masked_text_sha256": hashlib.sha256(
                    " ".join(text.casefold().split()).encode("utf-8")
                ).hexdigest(),
                "_language": "english",
                "_sources": ["Source_A"],
            })

    for label in LABEL_ORDER:
        for _ in range(holdout_per_class):
            index += 1
            text = f"{phrases[label]} heldout {index}"
            rows.append({
                "model_row_id": f"SS_{index:05d}",
                "text": text,
                "label": label,
                "masked_text_sha256": hashlib.sha256(
                    " ".join(text.casefold().split()).encode("utf-8")
                ).hexdigest(),
                "_language": "english",
                "_sources": [DEFAULT_HELDOUT_SOURCE],
            })

    if include_overlap:
        for label in LABEL_ORDER:
            index += 1
            text = f"{phrases[label]} cross source {index}"
            rows.append({
                "model_row_id": f"SS_{index:05d}",
                "text": text,
                "label": label,
                "masked_text_sha256": hashlib.sha256(
                    " ".join(text.casefold().split()).encode("utf-8")
                ).hexdigest(),
                "_language": "english",
                "_sources": [DEFAULT_HELDOUT_SOURCE, "Source_A"],
            })

    return rows


def test_source_holdout_keeps_selected_source_out_of_training_and_validation():
    splits, summary = partition_source_holdout(make_rows())

    assert all(
        DEFAULT_HELDOUT_SOURCE not in row["_sources"]
        for row in splits["train"] + splits["validation"]
    )
    assert all(
        row["_sources"] == [DEFAULT_HELDOUT_SOURCE]
        for row in splits["test"]
    )
    assert summary["heldout_source"] == DEFAULT_HELDOUT_SOURCE


def test_source_holdout_excludes_cross_source_duplicates_touching_test_source():
    splits, summary = partition_source_holdout(make_rows())

    assert summary["cross_source_rows_excluded"] == len(LABEL_ORDER)
    assert sum(map(len, splits.values())) == (
        len(make_rows()) - len(LABEL_ORDER)
    )


def test_source_holdout_preserves_all_classes_in_each_partition():
    splits, _ = partition_source_holdout(make_rows())

    for rows in splits.values():
        assert {row["label"] for row in rows} == set(LABEL_ORDER)


def test_source_holdout_has_no_exact_masked_text_overlap():
    splits, _ = partition_source_holdout(make_rows())
    hashes = {
        name: {row["masked_text_sha256"] for row in rows}
        for name, rows in splits.items()
    }

    assert hashes["train"].isdisjoint(hashes["validation"])
    assert hashes["train"].isdisjoint(hashes["test"])
    assert hashes["validation"].isdisjoint(hashes["test"])


def test_source_holdout_is_deterministic_for_same_seed():
    rows = make_rows()
    first, _ = partition_source_holdout(rows, seed=21)
    second, _ = partition_source_holdout(rows, seed=21)

    assert [
        row["model_row_id"] for row in first["train"]
    ] == [
        row["model_row_id"] for row in second["train"]
    ]


def test_source_holdout_changes_development_split_for_different_seed():
    rows = make_rows()
    first, _ = partition_source_holdout(rows, seed=21)
    second, _ = partition_source_holdout(rows, seed=22)

    assert {
        row["model_row_id"] for row in first["train"]
    } != {
        row["model_row_id"] for row in second["train"]
    }


def test_source_holdout_rejects_missing_selected_source():
    rows = [
        row for row in make_rows()
        if DEFAULT_HELDOUT_SOURCE not in row["_sources"]
    ]

    with pytest.raises(ValueError, match="No single-source rows"):
        partition_source_holdout(rows)


def test_source_holdout_rejects_heldout_source_missing_a_class():
    rows = [
        row for row in make_rows()
        if not (
            DEFAULT_HELDOUT_SOURCE in row["_sources"]
            and row["label"] == "scam"
        )
    ]

    with pytest.raises(ValueError, match="Held-out source must contain all three classes"):
        partition_source_holdout(rows)


def test_source_holdout_rejects_development_pool_missing_a_class():
    rows = [
        row for row in make_rows()
        if not (
            DEFAULT_HELDOUT_SOURCE not in row["_sources"]
            and row["label"] == "scam"
        )
    ]

    with pytest.raises(ValueError, match="Remaining development sources must contain all three classes"):
        partition_source_holdout(rows)


def test_source_holdout_rejects_invalid_validation_fraction():
    with pytest.raises(ValueError, match="validation_fraction must be"):
        partition_source_holdout(make_rows(), validation_fraction=0.8)


def test_source_holdout_rejects_blank_source_name():
    with pytest.raises(ValueError, match="heldout_source cannot be blank"):
        partition_source_holdout(make_rows(), heldout_source=" ")
