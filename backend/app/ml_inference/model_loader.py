from __future__ import annotations

from pathlib import Path
from typing import Literal

import torch
from loguru import logger


def load_model(model_path: Path, device: Literal["cpu", "cuda"] = "cpu") -> torch.nn.Module:
    """
    Load a SonicAid model checkpoint for inference.

    This assumes the training code saved a state dict or a scripted module.
    """
    model_path = Path(model_path)
    if not model_path.exists():
        logger.warning("Model path %s does not exist, using uninitialized model.", model_path)
        # Lazy import to avoid circular deps at import time
        from ml.models.sonicaid_model import build_sonicaid_demo_model

        model = build_sonicaid_demo_model()
        model.to(device)
        model.eval()
        return model

    logger.info("Loading model from %s", model_path)
    checkpoint = torch.load(model_path, map_location=device)

    if isinstance(checkpoint, torch.nn.Module):
        model = checkpoint
    else:
        from ml.models.sonicaid_model import build_sonicaid_demo_model

        model = build_sonicaid_demo_model()
        model.load_state_dict(checkpoint["model_state"])

    model.to(device)
    model.eval()
    return model

