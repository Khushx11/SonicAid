from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import torch
from torch.utils.data import Dataset

from .datasets import Sample, label_spaces


@dataclass
class ASDMockDatasetConfig:
    sample_rate: int = 16000
    clip_seconds: float = 1.0
    size: int = 256


class ASDMockTherapyDataset(Dataset):
    """
    A synthetic dataset for scaffolding the multi-task training pipeline.

    This lets the repo run end-to-end without requiring private ASD therapy data.
    Replace this with a real dataset implementation in future.
    """

    def __init__(self, cfg: Optional[ASDMockDatasetConfig] = None):
        self.cfg = cfg or ASDMockDatasetConfig()
        self.n = self.cfg.size
        self.t = int(self.cfg.sample_rate * self.cfg.clip_seconds)
        spaces = label_spaces()
        self.num_primary = spaces["primary"]
        self.num_emotion = spaces["emotion"]
        self.num_env_tags = spaces["env_tags"]

    def __len__(self) -> int:
        return self.n

    def __getitem__(self, idx: int) -> Sample:
        g = torch.Generator().manual_seed(idx)
        waveform = torch.randn(1, self.t, generator=g).clamp(-1.0, 1.0)

        primary = torch.randint(0, self.num_primary, (1,), generator=g).long().squeeze(0)
        emotion = torch.randint(0, self.num_emotion, (1,), generator=g).long().squeeze(0)

        env_tags = (torch.rand(self.num_env_tags, generator=g) > 0.8).float()
        noise = torch.rand((), generator=g)
        engagement = torch.rand((), generator=g)

        return Sample(
            waveform=waveform,
            primary_class=primary,
            emotion_class=emotion,
            env_tags=env_tags,
            noise=noise,
            engagement=engagement,
        )

