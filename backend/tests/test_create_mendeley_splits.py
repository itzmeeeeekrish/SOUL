import sys
from pathlib import Path


DATA_DIRECTORY = Path(__file__).resolve().parents[2] / "data"
if str(DATA_DIRECTORY) not in sys.path:
    sys.path.insert(0, str(DATA_DIRECTORY))

from create_mendeley_splits import (
    create_splits,
    group_model_texts,
    normalise_text,
)


def make_row(record_id, label, text, source_occurrences="1"):
    return {
        "record_id": record_id,
        "label": label,
        "text": text,
        "source_occurrences": source_occurrences,
    }


def test_same_label_masked_texts_collapse_before_splitting():
    rows = [
        make_row("M00001", "legitimate", "same masked text", "2"),
        make_row("M00002", "legitimate", " SAME   MASKED TEXT ", "3"),
    ]

    groups, quarantine, stats = group_model_texts(rows)

    assert len(groups) == 1
    assert quarantine == []
    assert groups[0]["source_occurrences"] == 5
    assert groups[0]["prepared_records_merged"] == 2
    assert stats["prepared_duplicate_records_collapsed"] == 1


def test_cross_label_masked_texts_are_quarantined():
    rows = [
        make_row("M00001", "scam", "same masked text", "1"),
        make_row("M00002", "spam", " SAME MASKED TEXT ", "2"),
    ]

    groups, quarantine, stats = group_model_texts(rows)

    assert groups == []
    assert len(quarantine) == 1
    assert quarantine[0]["reason"] == "same_masked_text_different_labels"
    assert quarantine[0]["prepared_records"] == 2
    assert stats["cross_label_groups_quarantined"] == 1


def test_split_is_stratified_and_each_class_appears_in_every_partition():
    rows = []
    index = 1
    for label in ("legitimate", "scam", "spam"):
        for item in range(20):
            rows.append(
                make_row(
                    f"M{index:05d}",
                    label,
                    f"{label} unique masked template {item}",
                )
            )
            index += 1

    groups, quarantine, _ = group_model_texts(rows)
    splits = create_splits(groups, seed=42)

    assert quarantine == []
    assert len(splits["train"]) == 42
    assert len(splits["validation"]) == 9
    assert len(splits["test"]) == 9

    for split_name in ("train", "validation", "test"):
        labels = {row["label"] for row in splits[split_name]}
        assert labels == {"legitimate", "scam", "spam"}


def test_split_is_deterministic_for_same_seed():
    rows = []
    index = 1
    for label in ("legitimate", "scam", "spam"):
        for item in range(20):
            rows.append(
                make_row(
                    f"M{index:05d}",
                    label,
                    f"{label} distinct example {item}",
                )
            )
            index += 1

    groups, _, _ = group_model_texts(rows)
    first = create_splits(groups, seed=77)
    second = create_splits(groups, seed=77)

    first_ids = {
        name: [row["split_group_id"] for row in values]
        for name, values in first.items()
    }
    second_ids = {
        name: [row["split_group_id"] for row in values]
        for name, values in second.items()
    }
    assert first_ids == second_ids


def test_same_text_never_crosses_partitions():
    rows = []
    index = 1
    for label in ("legitimate", "scam", "spam"):
        for item in range(20):
            rows.append(
                make_row(
                    f"M{index:05d}",
                    label,
                    f"{label} unique template {item}",
                )
            )
            index += 1

    rows.append(make_row("M99999", "legitimate", " legitimate   unique template 0 "))
    groups, _, _ = group_model_texts(rows)
    splits = create_splits(groups, seed=42)

    seen = {}
    for split_name, split_rows in splits.items():
        for row in split_rows:
            key = normalise_text(row["text"])
            assert key not in seen or seen[key] == split_name
            seen[key] = split_name


def test_invalid_label_and_blank_text_are_rejected():
    bad_rows = [
        make_row("M00001", "other", "some text"),
        make_row("M00002", "spam", "   "),
    ]

    try:
        group_model_texts(bad_rows)
    except ValueError:
        pass
    else:
        raise AssertionError("Invalid or blank prepared data must be rejected.")
