from __future__ import annotations

import torch


def build_scheduler(optimizer: torch.optim.Optimizer, max_epochs: int):
    return torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=max_epochs)

