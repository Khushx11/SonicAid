import torch
import pytest

from backend.app.ml_inference.audio_config import FeatureConfig
from backend.app.ml_inference.feature_extractor import LogMelFeatureExtractor


def test_logmel_feature_extractor_shapes():
    cfg = FeatureConfig(sample_rate=16000, n_mels=80)
    fe = LogMelFeatureExtractor(cfg)
    wav = torch.randn(1, 16000).clamp(-1.0, 1.0)
    mel = fe(wav)
    assert mel.dim() == 2
    assert mel.shape[0] == 80



def test_logmel_accepts_one_dimensional_mono_waveform():
    extractor = LogMelFeatureExtractor(FeatureConfig(sample_rate=16000, n_mels=40))
    result = extractor(torch.zeros(16000))
    assert result.ndim == 2
    assert result.shape[0] == 40


def test_logmel_rejects_multichannel_input():
    extractor = LogMelFeatureExtractor()
    with pytest.raises(ValueError, match="mono"):
        extractor(torch.zeros(2, 16000))
