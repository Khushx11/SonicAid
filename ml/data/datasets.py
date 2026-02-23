from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Protocol, Tuple

import torch


@dataclass
class Sample:
    """
    A single multi-task training sample.
    """

    waveform: torch.Tensor  # (1, T) float32 [-1, 1]
    primary_class: torch.Tensor  # () long
    emotion_class: torch.Tensor  # () long
    env_tags: torch.Tensor  # (num_env_tags,) float32 in {0,1}
    noise: torch.Tensor  # () float32
    engagement: torch.Tensor  # () float32


class MultiTaskDataset(Protocol):
    def __len__(self) -> int: ...

    def __getitem__(self, idx: int) -> Sample: ...


def split_indices(n: int, train_ratio: float = 0.8) -> Tuple[torch.Tensor, torch.Tensor]:
    idx = torch.randperm(n)
    k = int(n * train_ratio)
    return idx[:k], idx[k:]


def label_spaces() -> Dict[str, int]:
    """
    Central place for demo label cardinalities. In real use, this should
    come from dataset metadata/config.
    """
    return {"primary": 6, "emotion": 4, "env_tags": 8}

