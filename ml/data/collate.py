from __future__ import annotations

from typing import List, Dict

import torch

from .datasets import Sample


def collate_samples(batch: List[Sample]) -> Dict[str, torch.Tensor]:
    waveforms = torch.stack([s.waveform for s in batch], dim=0)  # (B, 1, T)
    primary = torch.stack([s.primary_class for s in batch], dim=0).long()
    emotion = torch.stack([s.emotion_class for s in batch], dim=0).long()
    env_tags = torch.stack([s.env_tags for s in batch], dim=0).float()
    noise = torch.stack([s.noise for s in batch], dim=0).float().unsqueeze(-1)
    engagement = (
        torch.stack([s.engagement for s in batch], dim=0).float().unsqueeze(-1)
    )

    return {
        "waveform": waveforms,
        "primary_class": primary,
        "emotion_class": emotion,
        "env_tags": env_tags,
        "noise": noise,
        "engagement": engagement,
    }

