from pathlib import Path

import joblib
import numpy as np
import pytest

from ml.real_audio.esc10 import FEATURES, RATE, SECONDS, ESC10Predictor, esc10_manifest, features, estimator


def test_real_audio_features_are_finite_and_have_fixed_shape():
    silent = features(np.zeros(RATE * SECONDS, dtype=np.float32))
    assert silent.shape == (FEATURES,)
    assert np.isfinite(silent).all()
    t = np.arange(RATE * SECONDS, dtype=np.float32) / RATE
    tone = features(0.15 * np.sin(2 * np.pi * 440 * t))
    assert np.isfinite(tone).all()
    assert not np.allclose(silent, tone)


@pytest.mark.parametrize("bad", [[], [[0, 1]], [0, float("nan")], [float("inf")]])
def test_features_reject_bad_audio(bad):
    with pytest.raises(ValueError):
        features(np.asarray(bad))


def test_missing_dataset_has_explicit_failure(tmp_path):
    with pytest.raises(FileNotFoundError, match="ESC-50"):
        esc10_manifest(tmp_path)


def test_only_trusted_versioned_models_are_loaded(tmp_path):
    bad_path = tmp_path / "invalid.joblib"
    joblib.dump({"version": 999}, bad_path)
    with pytest.raises(ValueError, match="version"):
        ESC10Predictor(bad_path)


def test_predictor_uses_saved_class_names(tmp_path):
    rng = np.random.default_rng(9)
    x = rng.normal(size=(12, FEATURES))
    y = np.array([0] * 6 + [1] * 6)
    model = estimator().fit(x, y)
    checkpoint = tmp_path / "esc10.joblib"
    joblib.dump({
        "version": 1, "model": model,
        "labels": {0: "rain", 1: "clock_tick"},
        "sample_rate": RATE, "window_seconds": SECONDS,
        "features": FEATURES,
    }, checkpoint)
    label, confidence = ESC10Predictor(checkpoint).predict(
        np.zeros(RATE * SECONDS, dtype=np.float32)
    )
    assert label in {"rain", "clock_tick"}
    assert 0 <= confidence <= 1
