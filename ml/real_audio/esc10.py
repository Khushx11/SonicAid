"""Reproducible environmental-sound baseline on the official ESC-10 subset.

Dataset: Karol J. Piczak's ESC-50 collection, using only esc10=True clips.
Official folds are held out in turn; source recordings never cross folds.
This model predicts sound categories, not emotion or therapeutic engagement.

Run:
  python -m ml.real_audio.esc10 train --dataset data/ESC-50
  python -m ml.real_audio.esc10 predict --model ml/artifacts/esc10.joblib --audio example.wav

Only load checkpoint files created locally by this script: joblib uses pickle.
"""
from __future__ import annotations

import argparse
import csv
import json
from functools import lru_cache
from pathlib import Path

import joblib
import numpy as np
import torch
import torchaudio
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC


RATE = 16000
SECONDS = 5
N_MELS = 64
FEATURES = 2 * N_MELS + 2
VERSION = 1


@lru_cache(maxsize=1)
def mel_transform():
    return torchaudio.transforms.MelSpectrogram(
        sample_rate=RATE, n_fft=1024, win_length=1024,
        hop_length=320, n_mels=N_MELS,
    )


def features(samples: np.ndarray) -> np.ndarray:
    """Return 130 finite float32 features from 5 seconds of 16k mono PCM."""
    waveform = np.asarray(samples, dtype=np.float32)
    if waveform.ndim != 1 or waveform.size == 0:
        raise ValueError("expected non-empty mono audio vector")
    if not np.isfinite(waveform).all():
        raise ValueError("audio samples must be finite")
    if waveform.size < RATE * SECONDS:
        waveform = np.pad(waveform, (0, RATE * SECONDS - waveform.size))
    else:
        waveform = waveform[: RATE * SECONDS]
    x = torch.from_numpy(waveform).unsqueeze(0)
    with torch.no_grad():
        mel = torch.log1p(mel_transform()(x)).squeeze(0)
        spectral = torch.cat((mel.mean(dim=-1), mel.std(dim=-1))).numpy()
    rms = np.sqrt(np.mean(np.square(waveform, dtype=np.float64)))
    zcr = np.mean(np.diff(np.signbit(waveform)).astype(np.float32))
    output = np.concatenate((spectral, [rms, zcr])).astype(np.float32)
    if output.shape != (FEATURES,) or not np.isfinite(output).all():
        raise ValueError("invalid extracted audio features")
    return output


def load_audio(path: Path) -> np.ndarray:
    waveform, sample_rate = torchaudio.load(str(path))
    if waveform.ndim != 2 or sample_rate <= 0:
        raise ValueError(f"bad audio file: {path}")
    mono = waveform.mean(dim=0, keepdim=True)
    if sample_rate != RATE:
        mono = torchaudio.functional.resample(mono, sample_rate, RATE)
    return mono.squeeze(0).numpy()


def esc10_manifest(root: Path) -> list[dict]:
    manifest = root / "meta" / "esc50.csv"
    if not manifest.is_file():
        raise FileNotFoundError(f"Missing {manifest}. Download the official ESC-50 dataset.")
    with manifest.open(encoding="utf-8", newline="") as stream:
        rows = [
            {"filename": row["filename"], "fold": int(row["fold"]),
             "target": int(row["target"]), "category": row["category"]}
            for row in csv.DictReader(stream)
            if row["esc10"].lower() == "true"
        ]
    if len(rows) != 400:
        raise ValueError(f"Expected 400 ESC-10 clips, got {len(rows)}")
    if set(row["fold"] for row in rows) != set(range(1, 6)):
        raise ValueError("ESC-10 official 5 folds are missing")
    if len({row["filename"] for row in rows}) != 400:
        raise ValueError("Duplicate filenames in ESC-10 metadata")
    if len({row["target"] for row in rows}) != 10:
        raise ValueError("Expected 10 environmental sound classes")
    for row in rows:
        if Path(row["filename"]).name != row["filename"]:
            raise ValueError("Invalid ESC-10 audio filename")
        if not (root / "audio" / row["filename"]).is_file():
            raise FileNotFoundError(root / "audio" / row["filename"])
    return rows


def estimator():
    # Fixed baseline configuration, not tuned using held-out fold scores.
    return make_pipeline(
        StandardScaler(),
        SVC(kernel="rbf", C=5.0, gamma="scale", probability=True, random_state=42),
    )


def train(root: Path, model_path: Path, metrics_path: Path) -> dict:
    torch.set_num_threads(2)
    rows = esc10_manifest(root)
    x = np.stack([features(load_audio(root / "audio" / row["filename"])) for row in rows])
    y = np.array([row["target"] for row in rows])
    folds = np.array([row["fold"] for row in rows])
    labels = sorted({row["target"] for row in rows})
    label_names = {row["target"]: row["category"] for row in rows}
    predictions = np.empty_like(y)
    fold_metrics = []
    for fold in sorted(set(folds)):
        tr, te = folds != fold, folds == fold
        model = estimator()
        model.fit(x[tr], y[tr])
        predicted = model.predict(x[te])
        predictions[te] = predicted
        fold_metrics.append({
            "fold": int(fold), "test_samples": int(np.sum(te)),
            "accuracy": float(accuracy_score(y[te], predicted)),
            "macro_f1": float(f1_score(y[te], predicted, average="macro", zero_division=0)),
        })
    summary = {
        "dataset": "ESC-10 (subset of ESC-50)",
        "dataset_url": "https://github.com/karolpiczak/ESC-50",
        "sample_count": int(len(rows)),
        "folds": fold_metrics,
        "out_of_fold_accuracy": float(accuracy_score(y, predictions)),
        "out_of_fold_macro_f1": float(f1_score(y, predictions, average="macro", zero_division=0)),
        "labels": {str(key): label_names[key] for key in labels},
        "confusion_matrix": confusion_matrix(y, predictions, labels=labels).tolist(),
        "class_order": labels,
        "model": "StandardScaler + SVC(C=5, RBF, probability=True)",
        "feature": "64-band log1p-mel mean/std, RMS, zero-crossing rate; 5 s, 16 kHz",
        "limitation": "Environmental sound labels only; no clinical/emotion/engagement ground truth",
    }
    final_model = estimator().fit(x, y)
    model_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump({
        "version": VERSION, "model": final_model, "labels": label_names,
        "sample_rate": RATE, "window_seconds": SECONDS,
        "features": FEATURES, "dataset": summary["dataset"],
    }, model_path)
    metrics_path.parent.mkdir(parents=True, exist_ok=True)
    metrics_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    return summary


class ESC10Predictor:
    def __init__(self, checkpoint: Path):
        if not checkpoint.is_file():
            raise FileNotFoundError(checkpoint)
        # Security: only load locally generated, trusted checkpoints.
        payload = joblib.load(checkpoint)
        if not isinstance(payload, dict) or payload.get("version") != VERSION:
            raise ValueError("Unknown ESC-10 model artifact version")
        if payload.get("features") != FEATURES or payload.get("sample_rate") != RATE:
            raise ValueError("Incompatible ESC-10 model feature specification")
        self.model = payload["model"]
        self.labels = {int(k): v for k, v in payload["labels"].items()}

    def predict(self, pcm: np.ndarray) -> tuple[str, float]:
        probabilities = self.model.predict_proba(features(pcm).reshape(1, -1))[0]
        index = int(np.argmax(probabilities))
        target = int(self.model.classes_[index])
        return self.labels[target], float(probabilities[index])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="operation", required=True)
    training = sub.add_parser("train")
    training.add_argument("--dataset", type=Path, required=True)
    training.add_argument("--model", type=Path, default=Path("ml/artifacts/esc10.joblib"))
    training.add_argument("--metrics", type=Path, default=Path("ml/artifacts/esc10_metrics.json"))
    inference = sub.add_parser("predict")
    inference.add_argument("--model", type=Path, required=True)
    inference.add_argument("--audio", type=Path, required=True)
    args = parser.parse_args()
    if args.operation == "train":
        print(json.dumps(train(args.dataset, args.model, args.metrics), indent=2))
    else:
        result = ESC10Predictor(args.model).predict(load_audio(args.audio))
        print(json.dumps({"category": result[0], "confidence": result[1]}))


if __name__ == "__main__":
    main()
