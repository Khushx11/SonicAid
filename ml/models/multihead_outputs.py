from __future__ import annotations

import torch
import torch.nn as nn


class PrimarySoundHead(nn.Module):
    def __init__(self, d_model: int, num_classes: int):
        super().__init__()
        self.fc = nn.Linear(d_model, num_classes)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.fc(x)


class EmotionHead(nn.Module):
    def __init__(self, d_model: int, num_emotions: int):
        super().__init__()
        self.fc = nn.Linear(d_model, num_emotions)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.fc(x)


class EnvTagHead(nn.Module):
    def __init__(self, d_model: int, num_tags: int):
        super().__init__()
        self.fc = nn.Linear(d_model, num_tags)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.fc(x)


class NoiseHead(nn.Module):
    def __init__(self, d_model: int):
        super().__init__()
        self.fc = nn.Linear(d_model, 1)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.fc(x)


class EngagementHead(nn.Module):
    def __init__(self, d_model: int):
        super().__init__()
        self.fc = nn.Linear(d_model, 1)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.fc(x)

