"""Create a similarity-family-separated development split for the synthetic pilot.

Only the existing train and validation partitions are read. The original
initial holdout test files are deliberately never opened.

Run from repository root:
    python data/create_multilingual_family_splits.py --threshold 0.95
    python data/create_multilingual_family_splits.py --threshold 0.98

Groups are discovered with the already-fitted training-only character TF-IDF
vectorizer. Top-K cosine neighbours above the requested threshold are joined
into undirected connected components. Components, not individual rows, are
then assigned to a new 90/10 train/validation split.
"""

import argparse
import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

import joblib
import numpy as np
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.neighbors import NearestNeighbors

from train_multilingual_baseline import (
    MODEL_PATH,
    SPLIT_DIRECTORY,
    read_split,
)


DATA_DIRECTORY = Path(__file__).resolve().parent
OUTPUT_ROOT = (
    DATA_DIRECTORY
    / "private"
    / "multilingual_candidates"
    / "family_splits"
)
NEIGHBOUR_COUNT = 5
RANDOM_SEED = 42
ALLOWED_THRESHOLDS = (0.95, 0.98)
LABELS = ("ham", "scam")


class UnionFind:
    """Disjoint-set structure used to form similarity-connected families."""

    def __init__(self, size):
        self.parent = list(range(size))
        self.rank = [0] * size

    def find(self, item):
        if self.parent[item] != item:
            self.parent[item] = self.find(self.parent[item])
        return self.parent[item]

    def union(self, left, right):
        root_left = self.find(left)
        root_right = self.find(right)
        if root_left == root_right:
            return
        if self.rank[root_left] < self.rank[root_right]:
            root_left, root_right = root_right, root_left
        self.parent[root_right] = root_left
        if self.rank[root_left] == self.rank[root_right]:
            self.rank[root_left] += 1


def validate_threshold(threshold):
    if threshold not in ALLOWED_THRESHOLDS:
        raise ValueError(
            "threshold must be one of: "
            + ", ".join(f"{value:.2f}" for value in ALLOWED_THRESHOLDS)
        )


def build_similarity_edges(matrix, threshold, neighbour_count=NEIGHBOUR_COUNT):
    """Return undirected top-K cosine-neighbour edges at/above threshold."""
    validate_threshold(threshold)
    row_count = matrix.shape[0]
    if row_count < 2:
        raise ValueError("At least two rows are required for family discovery.")
    if neighbour_count < 1:
        raise ValueError("neighbour_count must be at least one.")

    requested = min(row_count, neighbour_count + 1)
    nearest = NearestNeighbors(
        n_neighbors=requested,
        metric="cosine",
        algorithm="brute",
        n_jobs=1,
    )
    nearest.fit(matrix)
    distances, indices = nearest.kneighbors(matrix)

    edge_scores = {}
    for row_index in range(row_count):
        added = 0
        for distance, neighbour_index in zip(
            distances[row_index], indices[row_index]
        ):
            neighbour_index = int(neighbour_index)
            if neighbour_index == row_index:
                continue
            similarity = float(np.clip(1.0 - distance, 0.0, 1.0))
            if similarity >= threshold:
                edge = tuple(sorted((row_index, neighbour_index)))
                edge_scores[edge] = max(
                    edge_scores.get(edge, 0.0),
                    similarity,
                )
                added += 1
        # The estimator returns at most K non-self neighbours. Keep this
        # assertion as a guard if its neighbour semantics ever change.
        if added > neighbour_count:
            raise RuntimeError("More than K non-self neighbours were returned.")

    return [
        (left, right, similarity)
        for (left, right), similarity in sorted(edge_scores.items())
    ]


def assign_family_ids(rows, edges, threshold):
    """Assign stable component IDs and return aggregate graph statistics."""
    if not rows:
        raise ValueError("Cannot assign families to an empty dataset.")
    validate_threshold(threshold)

    structure = UnionFind(len(rows))
    for left, right, similarity in edges:
        if not (0 <= left < len(rows) and 0 <= right < len(rows)):
            raise ValueError("A similarity edge index is outside the row range.")
        if similarity >= threshold:
            structure.union(left, right)

    components = defaultdict(list)
    for index in range(len(rows)):
        components[structure.find(index)].append(index)

    output = [dict(row) for row in rows]
    family_sizes = []
    mixed_label_families = 0
    mixed_language_families = 0

    for indices in components.values():
        hashes = sorted(output[index]["model_text_sha256"] for index in indices)
        signature = hashlib.sha256("|".join(hashes).encode("utf-8")).hexdigest()
        family_id = f"ML14F{int(threshold * 100):02d}_{signature[:16]}"

        labels = set()
        languages = set()
        for index in indices:
            output[index]["original_exact_group_id"] = output[index]["group_id"]
            output[index]["group_id"] = family_id
            output[index]["family_group_id"] = family_id
            output[index]["similarity_threshold"] = f"{threshold:.2f}"
            labels.add(output[index]["label"])
            languages.add(output[index]["language"])

        family_sizes.append(len(indices))
        mixed_label_families += int(len(labels) > 1)
        mixed_language_families += int(len(languages) > 1)

    non_singleton_sizes = [size for size in family_sizes if size > 1]
    graph_stats = {
        "rows": len(rows),
        "similarity_edges": len(edges),
        "families": len(family_sizes),
        "non_singleton_families": len(non_singleton_sizes),
        "rows_in_non_singleton_families": int(sum(non_singleton_sizes)),
        "fraction_rows_in_non_singleton_families": round(
            sum(non_singleton_sizes) / len(rows), 4
        ),
        "largest_family_size": max(family_sizes, default=0),
        "mixed_label_families": int(mixed_label_families),
        "mixed_language_families": int(mixed_language_families),
    }
    return output, graph_stats


def create_family_holdout(rows, seed=RANDOM_SEED):
    """Create a deterministic 90/10 split while keeping every family intact."""
    if len(rows) < 10:
        raise ValueError("At least 10 rows are required for a family holdout.")

    groups = [row["family_group_id"] for row in rows]
    labels = [row["label"] for row in rows]
    if len(set(groups)) < 10:
        raise ValueError("At least 10 distinct similarity families are required.")
    if set(labels) != set(LABELS):
        raise ValueError("The combined development pool must contain ham and scam.")

    splitter = StratifiedGroupKFold(
        n_splits=10,
        shuffle=True,
        random_state=seed,
    )
    train_indices, validation_indices = next(
        splitter.split(
            X=np.zeros(len(rows), dtype=np.uint8),
            y=labels,
            groups=groups,
        )
    )

    splits = {
        "train": [dict(rows[index]) for index in train_indices],
        "validation": [dict(rows[index]) for index in validation_indices],
    }
    validate_family_holdout(splits)
    return splits


def validate_family_holdout(splits):
    """Reject family/hash overlap, missing partitions or missing global labels."""
    for name in ("train", "validation"):
        if name not in splits or not splits[name]:
            raise ValueError(f"The {name} family split is empty.")
        labels = {row["label"] for row in splits[name]}
        if labels != set(LABELS):
            raise ValueError(f"The {name} split must contain both ham and scam.")

    train_groups = {row["family_group_id"] for row in splits["train"]}
    validation_groups = {
        row["family_group_id"] for row in splits["validation"]
    }
    if train_groups & validation_groups:
        raise ValueError("A similarity family crosses train and validation.")

    train_hashes = {
        row["model_text_sha256"] for row in splits["train"]
    }
    validation_hashes = {
        row["model_text_sha256"] for row in splits["validation"]
    }
    if train_hashes & validation_hashes:
        raise ValueError("Exact model text crosses train and validation.")


def count_language_labels(rows):
    counts = Counter((row["language"], row["label"]) for row in rows)
    return {
        language: {
            label: int(counts.get((language, label), 0))
            for label in LABELS
        }
        for language in sorted({row["language"] for row in rows})
    }


def write_split(path, rows, split_name):
    fields = [
        "record_id",
        "text",
        "source_label",
        "language",
        "split",
        "group_id",
        "model_text_sha256",
        "original_exact_group_id",
        "family_group_id",
        "similarity_threshold",
    ]
    with path.open("w", encoding="utf-8", newline="") as output:
        writer = csv.DictWriter(output, fieldnames=fields)
        writer.writeheader()
        for index, row in enumerate(rows, start=1):
            text_hash = row["model_text_sha256"]
            writer.writerow(
                {
                    "record_id": f"ML14FROW_{text_hash[:20]}",
                    "text": row["text"],
                    "source_label": row["label"],
                    "language": row["language"],
                    "split": split_name,
                    "group_id": row["family_group_id"],
                    "model_text_sha256": text_hash,
                    "original_exact_group_id": row["original_exact_group_id"],
                    "family_group_id": row["family_group_id"],
                    "similarity_threshold": row["similarity_threshold"],
                }
            )


def build_summary(threshold, graph_stats, splits):
    return {
        "experiment": "synthetic_multilingual_similarity_family_holdout",
        "source_dataset": "anmolshrivastav/scam_ham_india_14_languages",
        "source_type": "synthetic",
        "task": "binary scam_vs_ham",
        "similarity_threshold": threshold,
        "neighbours_per_row": NEIGHBOUR_COUNT,
        "source_partitions_read": ["train", "validation"],
        "original_test_partition_read": False,
        "original_test_partition_modified": False,
        "original_multilingual_model_modified": False,
        "graph_method": (
            "undirected connected components from top-K cosine neighbours "
            "using the saved training-only character TF-IDF representation"
        ),
        "graph": graph_stats,
        "split_sizes": {
            name: len(rows) for name, rows in splits.items()
        },
        "split_language_label_counts": {
            name: count_language_labels(rows)
            for name, rows in splits.items()
        },
        "split_integrity": {
            "similarity_families_cross_partitions": False,
            "exact_text_hashes_cross_partitions": False,
        },
        "limitations": [
            "This development pool contains only the original train and validation partitions; the original test partition was not read.",
            "The old validation partition has been used in prior diagnostics, so this is not a fresh independent final evaluation.",
            "The synthetic source does not establish real-world fraud-detection performance.",
            "Top-K connected components are approximate template-family candidates, not verified campaign identities.",
            "Single-link connected components can join rows through similarity chains.",
            "Language subgroup metrics may be low-support or absent after group allocation.",
            "This experiment remains a separate binary ham/scam task and is not merged into SOUL's three-class detector.",
        ],
    }


def main():
    parser = argparse.ArgumentParser(
        description="Build a similarity-family-separated multilingual development split."
    )
    parser.add_argument(
        "--threshold",
        type=float,
        choices=ALLOWED_THRESHOLDS,
        default=0.95,
        help="Cosine similarity threshold for connecting candidate template families.",
    )
    args = parser.parse_args()

    if not MODEL_PATH.is_file():
        raise SystemExit(
            f"Saved multilingual model not found: {MODEL_PATH}. "
            "Train the experimental baseline first."
        )

    try:
        # Deliberately read only train and validation. Never open test.csv here.
        original_train = read_split(SPLIT_DIRECTORY / "train.csv")
        original_validation = read_split(SPLIT_DIRECTORY / "validation.csv")
        rows = original_train + original_validation

        seen_hashes = set()
        for row in rows:
            text_hash = row["model_text_sha256"]
            if text_hash in seen_hashes:
                raise ValueError("Exact model text already overlaps in the input pool.")
            seen_hashes.add(text_hash)

        pipeline = joblib.load(MODEL_PATH)
        vectorizer = pipeline.named_steps["tfidf"]
        matrix = vectorizer.transform([row["text"] for row in rows])
        edges = build_similarity_edges(matrix, args.threshold)
        family_rows, graph_stats = assign_family_ids(
            rows,
            edges,
            args.threshold,
        )
        splits = create_family_holdout(family_rows)
        summary = build_summary(args.threshold, graph_stats, splits)
    except (OSError, ValueError, KeyError, TypeError, RuntimeError) as error:
        raise SystemExit(f"Family split creation failed: {error}") from error

    output_directory = OUTPUT_ROOT / f"threshold_{int(args.threshold * 100):03d}"
    output_directory.mkdir(parents=True, exist_ok=True)
    for name, split_rows in splits.items():
        write_split(output_directory / f"{name}.csv", split_rows, name)

    summary_path = output_directory / "split_summary.json"
    with summary_path.open("w", encoding="utf-8") as output:
        json.dump(summary, output, indent=2, ensure_ascii=False)

    print("SOUL — similarity-family-separated development split")
    print("Threshold:", f"{args.threshold:.2f}")
    print("Input rows (old train + validation):", len(rows))
    print("Original test partition read: no")
    print("Similarity edges:", graph_stats["similarity_edges"])
    print("Families:", graph_stats["families"])
    print("Non-singleton families:", graph_stats["non_singleton_families"])
    print(
        "Rows in non-singleton families:",
        graph_stats["rows_in_non_singleton_families"],
        f"({graph_stats['fraction_rows_in_non_singleton_families']:.1%})",
    )
    print("Largest family:", graph_stats["largest_family_size"])
    print("Mixed-label / mixed-language families:",
          graph_stats["mixed_label_families"], "/",
          graph_stats["mixed_language_families"])

    for name, split_rows in splits.items():
        print(f"\n{name.upper()}: {len(split_rows)} rows")
        print("  labels:", dict(Counter(row["label"] for row in split_rows)))
        print("  language/label counts:", count_language_labels(split_rows))

    print("\nIntegrity:")
    print("  Similarity family crosses partitions: no")
    print("  Exact model text crosses partitions: no")
    print("  Original test partition read or modified: no")
    print("  Original model artifact modified: no")
    print("  Outputs:", output_directory)
    print(
        "\nNote: this is a family-separated development validation, not an "
        "independent final test or real-world evaluation."
    )


if __name__ == "__main__":
    main()
