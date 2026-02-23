from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

import torch
import torch.nn as nn


@dataclass
class LossWeights:
    primary: float = 1.0
    emotion: float = 0.7
    env_tags: float = 0.7
    noise: float = 0.5
    engagement: float = 0.5


class MultiTaskLoss(nn.Module):
    def __init__(self, weights: LossWeights):
        super().__init__()
        self.weights = weights
        self.ce = nn.CrossEntropyLoss()
        self.bce = nn.BCEWithLogitsLoss()
        self.mse = nn.MSELoss()

    def forward(self, outputs: Dict[str, torch.Tensor], batch: Dict[str, torch.Tensor]):
        loss_primary = self.ce(outputs["primary"], batch["primary_class"])
        loss_emotion = self.ce(outputs["emotion"], batch["emotion_class"])
        loss_env = self.bce(outputs["env_tags"], batch["env_tags"])
        loss_noise = self.mse(outputs["noise"], batch["noise"])
        loss_engagement = self.mse(outputs["engagement"], batch["engagement"])

        total = (
            self.weights.primary * loss_primary
            + self.weights.emotion * loss_emotion
            + self.weights.env_tags * loss_env
            + self.weights.noise * loss_noise
            + self.weights.engagement * loss_engagement
        )

        return total, {
            "loss_primary": loss_primary.detach(),
            "loss_emotion": loss_emotion.detach(),
            "loss_env_tags": loss_env.detach(),
            "loss_noise": loss_noise.detach(),
            "loss_engagement": loss_engagement.detach(),
            "loss_total": total.detach(),
        }

