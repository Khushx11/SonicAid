from __future__ import annotations

from typing import Optional

import torch
import torchaudio

from .audio_config import FeatureConfig


class LogMelFeatureExtractor:
    def __init__(self, cfg: Optional[FeatureConfig] = None) -> None:
        self.cfg = cfg or FeatureConfig()
        self.melspec = torchaudio.transforms.MelSpectrogram(
            sample_rate=self.cfg.sample_rate,
            n_fft=self.cfg.n_fft,
            win_length=self.cfg.win_length,
            hop_length=self.cfg.hop_length,
            n_mels=self.cfg.n_mels,
        )
        self.amplitude_to_db = torchaudio.transforms.AmplitudeToDB(top_db=80.0)

    def __call__(self, waveform: torch.Tensor) -> torch.Tensor:
        """
        Convert a waveform into a log-mel spectrogram.

        Args:
            waveform: Tensor of shape (1, T) in float32, normalized to [-1, 1].

        Returns:
            Tensor of shape (n_mels, time)
        """
        spec = self.melspec(waveform)
        logmel = self.amplitude_to_db(spec)
        return logmel

