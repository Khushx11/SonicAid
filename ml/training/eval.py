from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any, Dict

import torch
import yaml
from torch.utils.data import DataLoader

from ml.data.asd_therapy_dataset import ASDMockTherapyDataset, ASDMockDatasetConfig
from ml.data.collate import collate_samples
from ml.models.sonicaid_model import SonicAidModel
from ml.training.checkpoint import load_checkpoint
from ml.training.losses import LossWeights, MultiTaskLoss
from ml.training.metrics import multitask_metrics, RunningAverages


def load_config(config_path: str) -> Dict[str, Any]:
    cfg = yaml.safe_load(Path(config_path).read_text())
    base = cfg.get("_base")
    if base:
        base_cfg = yaml.safe_load(Path(base).read_text())
        base_cfg.update({k: v for k, v in cfg.items() if k != "_base"})
        return base_cfg
    return cfg


def build_model(cfg: Dict[str, Any]) -> SonicAidModel:
    model_cfg = cfg["model"]
    heads = model_cfg["heads"]
    return SonicAidModel(
        backbone_cfg=model_cfg["backbone"],
        transformer_cfg=model_cfg["transformer"],
        num_primary_classes=heads["num_primary_classes"],
        num_emotions=heads["num_emotions"],
        num_env_tags=heads["num_env_tags"],
    )


@torch.no_grad()
def evaluate(model: torch.nn.Module, loader: DataLoader, loss_fn: MultiTaskLoss, device: str, feature_extractor):
    model.eval()
    losses = RunningAverages()
    primary_acc = RunningAverages()
    emotion_acc = RunningAverages()

    for batch in loader:
        wave = batch["waveform"].to(device)
        mel = torch.stack([feature_extractor(w) for w in wave], dim=0).unsqueeze(1)
        labels = {k: v.to(device) for k, v in batch.items() if k != "waveform"}
        outputs = model(mel)
        loss, _ = loss_fn(outputs, labels)
        m = multitask_metrics(outputs, labels)

        losses.update(float(loss.item()), n=mel.shape[0])
        primary_acc.update(m["primary_acc"], n=mel.shape[0])
        emotion_acc.update(m["emotion_acc"], n=mel.shape[0])

    return {"loss": losses.mean(), "primary_acc": primary_acc.mean(), "emotion_acc": emotion_acc.mean()}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=str, required=True)
    parser.add_argument("--checkpoint", type=str, default="ml/artifacts/sonicaid_best.pt")
    args = parser.parse_args()

    cfg = load_config(args.config)
    device = cfg["device"]

    ds_cfg = ASDMockDatasetConfig(
        sample_rate=int(cfg["data"]["sample_rate"]),
        clip_seconds=float(cfg["data"]["window_seconds"]),
        size=128,
    )
    ds = ASDMockTherapyDataset(ds_cfg)
    loader = DataLoader(
        ds,
        batch_size=int(cfg["data"]["batch_size"]),
        num_workers=int(cfg["data"]["num_workers"]),
        shuffle=False,
        collate_fn=collate_samples,
    )

    model = build_model(cfg).to(device)
    ckpt = load_checkpoint(Path(args.checkpoint), model=model, optimizer=None, map_location=device)
    if ckpt is None:
        raise FileNotFoundError(f"Checkpoint not found: {args.checkpoint}")

    weights = LossWeights(**cfg["loss_weights"])
    loss_fn = MultiTaskLoss(weights).to(device)

    from backend.app.ml_inference.feature_extractor import LogMelFeatureExtractor
    from backend.app.ml_inference.audio_config import FeatureConfig

    feature_extractor = LogMelFeatureExtractor(
        FeatureConfig(
            sample_rate=int(cfg["data"]["sample_rate"]),
            n_mels=int(cfg["data"]["n_mels"]),
        )
    )

    stats = evaluate(model, loader, loss_fn, device=device, feature_extractor=feature_extractor)
    print(stats)


if __name__ == "__main__":
    main()

