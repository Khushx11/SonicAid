from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

import torch


@dataclass
class RunningAverages:
    total: float = 0.0
    count: int = 0

    def update(self, value: float, n: int = 1) -> None:
        self.total += value * n
        self.count += n

    def mean(self) -> float:
        return self.total / max(1, self.count)


def accuracy_from_logits(logits: torch.Tensor, targets: torch.Tensor) -> float:
    preds = torch.argmax(logits, dim=-1)
    return float((preds == targets).float().mean().item())


def multitask_metrics(outputs: Dict[str, torch.Tensor], batch: Dict[str, torch.Tensor]) -> Dict[str, float]:
    return {
        "primary_acc": accuracy_from_logits(outputs["primary"], batch["primary_class"]),
        "emotion_acc": accuracy_from_logits(outputs["emotion"], batch["emotion_class"]),
    }

