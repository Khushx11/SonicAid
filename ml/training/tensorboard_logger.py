from __future__ import annotations

from pathlib import Path
from typing import Dict

from torch.utils.tensorboard import SummaryWriter


class TBLogger:
    def __init__(self, log_dir: str):
        Path(log_dir).mkdir(parents=True, exist_ok=True)
        self.writer = SummaryWriter(log_dir=log_dir)

    def log_scalars(self, prefix: str, scalars: Dict[str, float], step: int) -> None:
        for k, v in scalars.items():
            self.writer.add_scalar(f"{prefix}/{k}", v, step)

    def close(self) -> None:
        self.writer.close()

