"""Combine AI-only suggestions with the 31-row blind validation review queue.

This creates a local-only silver-label artifact. It never writes AI labels into
soul_label, review_status, or annotation_note, which remain reserved for
separately adjudicated labels. The source/model key is intentionally not read.

Run from the repository root:
    python data/build_ai_validation_review_dataset.py

Expected local inputs under data/private/model_artifacts/:
    validation_label_review_blind.csv
    validation_label_ai_suggestions_sidecar.csv

Output (Git-ignored):
    validation_label_review_ai_silver.csv
"""

import csv
from collections import Counter
from datetime import date
from pathlib import Path

ARTIFACT_DIRECTORY = (
    Path(__file__).resolve().parent
    / "private"
    / "model_artifacts"
)
BLIND_PATH = ARTIFACT_DIRECTORY / "validation_label_review_blind.csv"
SUGGESTIONS_PATH = ARTIFACT_DIRECTORY / "validation_label_ai_suggestions_sidecar.csv"
OUTPUT_PATH = ARTIFACT_DIRECTORY / "validation_label_review_ai_silver.csv"

SOUL_LABELS = {"legitimate", "scam", "spam"}
AI_LABELS = SOUL_LABELS | {"needs_review"}
BLIND_COLUMNS = {
    "review_id",
    "text",
    "soul_label",
    "review_status",
    "annotation_note",
}
SUGGESTION_COLUMNS = {
    "review_id",
    "ai_provisional_label",
    "ai_review_status",
    "ai_annotation_note",
}
OUTPUT_COLUMNS = [
    "review_id",
    "text",
    "soul_label",
    "review_status",
    "annotation_note",
    "ai_suggested_label",
    "ai_annotation_status",
    "ai_annotation_note",
    "ai_annotator",
    "ai_model",
    "ai_method",
    "ai_created_date",
]


def safe_spreadsheet_value(value):
    """Neutralise formula-like leading characters in CSV text fields."""
    text = str(value or "")
    if text.lstrip().startswith(("=", "+", "-", "@")):
        return "'" + text
    return text


def read_csv(path, required_columns):
    if not path.is_file():
        raise FileNotFoundError(f"Required local input is missing: {path}")

    with path.open("r", encoding="utf-8-sig", newline="") as source:
        reader = csv.DictReader(source)
        missing = required_columns - set(reader.fieldnames or [])
        if missing:
            raise ValueError(
                f"{path.name} is missing columns: " + ", ".join(sorted(missing))
            )
        rows = list(reader)

    if not rows:
        raise ValueError(f"{path.name} contains no data rows.")
    return rows


def index_unique_rows(rows, source_name):
    indexed = {}
    for row in rows:
        review_id = (row.get("review_id") or "").strip()
        if not review_id:
            raise ValueError(f"{source_name} contains a blank review_id.")
        if review_id in indexed:
            raise ValueError(f"{source_name} contains a duplicate review_id.")
        indexed[review_id] = row
    return indexed


def build_ai_review_rows(blind_rows, suggestion_rows, created_date=None):
    """Join AI suggestions without changing official review fields."""
    blind_by_id = index_unique_rows(blind_rows, "Blind review file")
    suggestions_by_id = index_unique_rows(suggestion_rows, "AI suggestion sidecar")

    if set(blind_by_id) != set(suggestions_by_id):
        missing_suggestions = set(blind_by_id) - set(suggestions_by_id)
        extra_suggestions = set(suggestions_by_id) - set(blind_by_id)
        raise ValueError(
            "Review IDs do not match between the blind queue and AI sidecar "
            f"(missing suggestions: {len(missing_suggestions)}, "
            f"extra suggestions: {len(extra_suggestions)})."
        )

    run_date = created_date or date.today().isoformat()
    output_rows = []

    for review_id, blind in blind_by_id.items():
        # The source queue must remain untouched; AI does not fill human fields.
        if (blind.get("soul_label") or "").strip():
            raise ValueError("Blind queue already contains a SOUL label.")
        if (blind.get("review_status") or "").strip().casefold() != "pending":
            raise ValueError("Blind queue is not in pending review state.")
        if (blind.get("annotation_note") or "").strip():
            raise ValueError("Blind queue already contains an annotation note.")

        suggestion = suggestions_by_id[review_id]
        label = (suggestion.get("ai_provisional_label") or "").strip().casefold()
        status = (suggestion.get("ai_review_status") or "").strip().casefold()
        note = (suggestion.get("ai_annotation_note") or "").strip()

        # The sidecar deliberately leaves the class blank when the model abstains.
        # Convert that explicit abstention into the shared needs_review state.
        if not label and status == "needs_more_context":
            label = "needs_review"
        if label not in AI_LABELS:
            raise ValueError(f"AI sidecar contains an unsupported label for {review_id}.")
        if not note:
            raise ValueError(f"AI sidecar has no rationale for {review_id}.")
        if label == "needs_review":
            if status != "needs_more_context":
                raise ValueError("needs_review labels must use needs_more_context status.")
            ai_status = "needs_review"
        else:
            if status != "provisional_suggestion":
                raise ValueError("Definitive AI labels must use provisional_suggestion status.")
            ai_status = "provisional"

        output_rows.append(
            {
                "review_id": review_id,
                "text": safe_spreadsheet_value(blind.get("text", "")),
                "soul_label": "",
                "review_status": "pending",
                "annotation_note": "",
                "ai_suggested_label": label,
                "ai_annotation_status": ai_status,
                "ai_annotation_note": safe_spreadsheet_value(note),
                "ai_annotator": "ChatGPT",
                "ai_model": "GPT-6",
                "ai_method": "text_only_contextual_assessment",
                "ai_created_date": run_date,
            }
        )

    return output_rows


def write_csv(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as destination:
        writer = csv.DictWriter(destination, fieldnames=OUTPUT_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def main():
    try:
        blind_rows = read_csv(BLIND_PATH, BLIND_COLUMNS)
        suggestion_rows = read_csv(SUGGESTIONS_PATH, SUGGESTION_COLUMNS)
        output_rows = build_ai_review_rows(blind_rows, suggestion_rows)
        write_csv(OUTPUT_PATH, output_rows)
    except (OSError, UnicodeError, csv.Error, ValueError) as error:
        raise SystemExit(f"AI validation review build failed: {error}") from error

    counts = Counter(row["ai_suggested_label"] for row in output_rows)
    statuses = Counter(row["ai_annotation_status"] for row in output_rows)

    print("SOUL — AI validation silver-label artifact")
    print("Rows:", len(output_rows))
    print("AI provisional labels:")
    for label in ("legitimate", "scam", "spam", "needs_review"):
        print(f"  {label}: {counts[label]}")
    print("AI annotation statuses:", dict(statuses))
    print("Official SOUL labels written: 0")
    print("Official review states changed: 0")
    print("Source/model key read: no")
    print("Output:", OUTPUT_PATH)
    print("Keep this message-level artifact local/private; do not commit it.")


if __name__ == "__main__":
    main()
