from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import torch


@dataclass
class AugmentationConfig:
    noise_std: float = 0.01
    gain_min: float = 0.8
    gain_max: float = 1.2


class WaveformAugmenter:
    def __init__(self, cfg: Optional[AugmentationConfig] = None):
        self.cfg = cfg or AugmentationConfig()

    def __call__(self, waveform: torch.Tensor) -> torch.Tensor:
        """
        waveform: (1, T)
        """
        # Random gain
        gain = torch.empty((), device=waveform.device).uniform_(
            self.cfg.gain_min, self.cfg.gain_max
        )
        x = waveform * gain

        # Additive white noise
        if self.cfg.noise_std > 0:
            x = x + torch.randn_like(x) * self.cfg.noise_std

        return x.clamp(-1.0, 1.0)

