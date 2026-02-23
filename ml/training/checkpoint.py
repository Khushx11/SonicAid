from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional

import torch


@dataclass
class CheckpointState:
    epoch: int
    model_state: Dict[str, Any]
    optim_state: Dict[str, Any]
    best_metric: float


def save_checkpoint(
    path: Path,
    epoch: int,
    model: torch.nn.Module,
    optimizer: torch.optim.Optimizer,
    best_metric: float,
) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    torch.save(
        {
            "epoch": epoch,
            "model_state": model.state_dict(),
            "optim_state": optimizer.state_dict(),
            "best_metric": best_metric,
        },
        path,
    )


def load_checkpoint(
    path: Path,
    model: torch.nn.Module,
    optimizer: Optional[torch.optim.Optimizer] = None,
    map_location: str = "cpu",
) -> Optional[CheckpointState]:
    path = Path(path)
    if not path.exists():
        return None
    ckpt = torch.load(path, map_location=map_location)
    model.load_state_dict(ckpt["model_state"])
    if optimizer is not None:
        optimizer.load_state_dict(ckpt["optim_state"])
    return CheckpointState(
        epoch=int(ckpt["epoch"]),
        model_state=ckpt["model_state"],
        optim_state=ckpt["optim_state"],
        best_metric=float(ckpt.get("best_metric", 0.0)),
    )

