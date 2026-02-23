from dataclasses import dataclass


@dataclass
class FeatureConfig:
    sample_rate: int = 16000
    n_mels: int = 80
    n_fft: int = 400
    win_length: int = 400
    hop_length: int = 160


@dataclass
class StreamingConfig:
    window_seconds: float = 1.0
    hop_seconds: float = 0.5

