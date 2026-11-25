"""Evaluate independent environmental sound datasets on their official folds."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import torch
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score

from ml.real_audio.esc10 import estimator, features, load_audio


@dataclass(frozen=True)
class Dataset:
    metadata: str
    filename: str
    target: str
    category: str
    source: str
    clips: int
    classes: int
    folds: int
    folder_per_fold: bool = False


DATASETS = {
    "esc50": Dataset("meta/esc50.csv", "filename", "target", "category", "src_file", 2000, 50, 5),
    "urbansound8k": Dataset(
        "metadata/UrbanSound8K.csv", "slice_file_name", "classID", "class", "fsID",
        8732, 10, 10, folder_per_fold=True,
    ),
}


@dataclass(frozen=True)
class Clip:
    path: Path
    fold: int
    target: int
    category: str
    source: str


def read_manifest(root: Path, spec: Dataset) -> list[Clip]:
    rows = []
    source_folds = {}
    categories = {}
    with (root / spec.metadata).open(encoding="utf-8-sig", newline="") as stream:
        for row in csv.DictReader(stream):
            filename = row[spec.filename]
            fold = int(row["fold"])
            target = int(row[spec.target])
            category = row[spec.category]
            source = row[spec.source]
            if Path(filename).name != filename or Path(filename).suffix.lower() != ".wav":
                raise ValueError(f"Invalid WAV filename: {filename}")
            if not source or source_folds.setdefault(source, fold) != fold:
                raise ValueError(f"Missing source ID or source crosses folds: {source}")
            if not category or categories.setdefault(target, category) != category:
                raise ValueError(f"Inconsistent category for class {target}")
            folder = root / "audio"
            if spec.folder_per_fold:
                folder /= f"fold{fold}"
            path = folder / filename
            if not path.is_file():
                raise FileNotFoundError(path)
            rows.append(Clip(path, fold, target, category, source))

    if len(rows) != spec.clips or len({clip.path for clip in rows}) != spec.clips:
        raise ValueError(f"Expected {spec.clips} distinct WAV files")
    if set(categories) != set(range(spec.classes)) or len(set(categories.values())) != spec.classes:
        raise ValueError(f"Expected {spec.classes} distinct official classes")
    if {clip.fold for clip in rows} != set(range(1, spec.folds + 1)):
        raise ValueError(f"Expected all {spec.folds} official folds")
    return rows


def evaluate(dataset: str, root: Path) -> dict:
    spec = DATASETS[dataset]
    rows = read_manifest(root, spec)
    torch.set_num_threads(2)
    x = np.stack([features(load_audio(clip.path)) for clip in rows])
    y = np.array([clip.target for clip in rows])
    folds = np.array([clip.fold for clip in rows])
    classes = sorted({clip.target: clip.category for clip in rows}.items())
    labels = [target for target, _ in classes]
    predicted = np.empty_like(y)
    per_fold = []

    for fold in range(1, spec.folds + 1):
        test = folds == fold
        # Probability fitting is unnecessary for offline classification metrics.
        model = estimator().set_params(svc__probability=False)
        model.fit(x[~test], y[~test])
        predicted[test] = model.predict(x[test])
        per_fold.append({
            "fold": fold,
            "test_samples": int(test.sum()),
            "accuracy": accuracy_score(y[test], predicted[test]),
            "macro_f1": f1_score(y[test], predicted[test], labels=labels, average="macro", zero_division=0),
        })

    return {
        "dataset": dataset,
        "metadata_sha256": hashlib.sha256((root / spec.metadata).read_bytes()).hexdigest(),
        "sample_count": len(rows),
        "class_order": [category for _, category in classes],
        "model": "StandardScaler + RBF SVC (C=5)",
        "folds": per_fold,
        "out_of_fold_accuracy": accuracy_score(y, predicted),
        "out_of_fold_macro_f1": f1_score(y, predicted, labels=labels, average="macro", zero_division=0),
        "confusion_matrix": confusion_matrix(y, predicted, labels=labels).tolist(),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dataset", choices=DATASETS)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--metrics", type=Path, required=True)
    args = parser.parse_args()
    report = evaluate(args.dataset, args.root)
    args.metrics.parent.mkdir(parents=True, exist_ok=True)
    args.metrics.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(f"{args.dataset}: {report['sample_count']} clips, "
          f"accuracy={report['out_of_fold_accuracy']:.4f}, "
          f"macro-F1={report['out_of_fold_macro_f1']:.4f}")


if __name__ == "__main__":
    main()
