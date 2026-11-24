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
            waveform: Mono tensor of shape (T,) or (1, T), normalized to [-1, 1].

        Returns:
            Tensor of shape (n_mels, time)
        """
        if waveform.ndim == 1:
            waveform = waveform.unsqueeze(0)
        if waveform.ndim != 2 or waveform.shape[0] != 1:
            raise ValueError("expected mono waveform with shape (T,) or (1, T)")
        spec = self.melspec(waveform)
        logmel = self.amplitude_to_db(spec)
        return logmel.squeeze(0)

