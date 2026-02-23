import torch

from backend.app.ml_inference.audio_config import FeatureConfig
from backend.app.ml_inference.feature_extractor import LogMelFeatureExtractor


def test_logmel_feature_extractor_shapes():
    cfg = FeatureConfig(sample_rate=16000, n_mels=80)
    fe = LogMelFeatureExtractor(cfg)
    wav = torch.randn(1, 16000).clamp(-1.0, 1.0)
    mel = fe(wav)
    assert mel.dim() == 2
    assert mel.shape[0] == 80

