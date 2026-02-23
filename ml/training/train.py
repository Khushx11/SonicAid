from __future__ import annotations

import argparse
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict

import torch
import yaml
from torch.utils.data import DataLoader, Subset

from ml.data.asd_therapy_dataset import ASDMockTherapyDataset, ASDMockDatasetConfig
from ml.data.augmentations import WaveformAugmenter
from ml.data.collate import collate_samples
from ml.data.datasets import split_indices
from ml.models.sonicaid_model import SonicAidModel
from ml.training.checkpoint import save_checkpoint
from ml.training.early_stopping import EarlyStopping
from ml.training.losses import LossWeights, MultiTaskLoss
from ml.training.metrics import multitask_metrics, RunningAverages
from ml.training.scheduler import build_scheduler
from ml.training.tensorboard_logger import TBLogger


def _deep_update(dst: Dict[str, Any], src: Dict[str, Any]) -> Dict[str, Any]:
    for k, v in src.items():
        if isinstance(v, dict) and isinstance(dst.get(k), dict):
            dst[k] = _deep_update(dst[k], v)
        else:
            dst[k] = v
    return dst


def load_config(config_path: str) -> Dict[str, Any]:
    cfg = yaml.safe_load(Path(config_path).read_text())
    base = cfg.get("_base")
    if base:
        base_cfg = yaml.safe_load(Path(base).read_text())
        cfg = _deep_update(base_cfg, {k: v for k, v in cfg.items() if k != "_base"})
    return cfg


def set_seed(seed: int) -> None:
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)


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


def run_epoch(
    model: torch.nn.Module,
    loader: DataLoader,
    loss_fn: MultiTaskLoss,
    device: str,
    optimizer: torch.optim.Optimizer | None,
    augmenter: WaveformAugmenter | None,
    feature_extractor,
) -> Dict[str, float]:
    train_mode = optimizer is not None
    model.train(train_mode)

    losses = RunningAverages()
    primary_acc = RunningAverages()
    emotion_acc = RunningAverages()

    for batch in loader:
        wave = batch["waveform"].to(device)
        if augmenter is not None:
            wave = torch.stack([augmenter(w) for w in wave], dim=0)

        # log-mel: (B, n_mels, time) -> (B, 1, n_mels, time)
        mel = torch.stack([feature_extractor(w) for w in wave], dim=0).unsqueeze(1)

        batch = {k: v.to(device) for k, v in batch.items() if k != "waveform"}

        outputs = model(mel)
        loss, _ = loss_fn(outputs, batch)

        if train_mode:
            optimizer.zero_grad(set_to_none=True)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()

        m = multitask_metrics(outputs, batch)
        losses.update(float(loss.item()), n=mel.shape[0])
        primary_acc.update(m["primary_acc"], n=mel.shape[0])
        emotion_acc.update(m["emotion_acc"], n=mel.shape[0])

    return {
        "loss": losses.mean(),
        "primary_acc": primary_acc.mean(),
        "emotion_acc": emotion_acc.mean(),
    }


def train(config_path: str) -> None:
    cfg = load_config(config_path)
    set_seed(int(cfg["seed"]))

    device = cfg["device"]
    artifacts_dir = Path(cfg["paths"]["artifacts_dir"])
    tb_dir = Path(cfg["paths"]["tensorboard_dir"])

    artifacts_dir.mkdir(parents=True, exist_ok=True)
    tb_dir.mkdir(parents=True, exist_ok=True)

    # Dataset
    ds_cfg = ASDMockDatasetConfig(
        sample_rate=int(cfg["data"]["sample_rate"]),
        clip_seconds=float(cfg["data"]["window_seconds"]),
        size=256,
    )
    ds = ASDMockTherapyDataset(ds_cfg)
    train_idx, val_idx = split_indices(len(ds), train_ratio=0.8)
    train_ds = Subset(ds, train_idx.tolist())
    val_ds = Subset(ds, val_idx.tolist())

    loader_args = dict(
        batch_size=int(cfg["data"]["batch_size"]),
        num_workers=int(cfg["data"]["num_workers"]),
        pin_memory=(device == "cuda"),
        collate_fn=collate_samples,
    )
    train_loader = DataLoader(train_ds, shuffle=True, **loader_args)
    val_loader = DataLoader(val_ds, shuffle=False, **loader_args)

    # Model
    model = build_model(cfg).to(device)
    optimizer = torch.optim.AdamW(
        model.parameters(),
        lr=float(cfg["optim"]["lr"]),
        weight_decay=float(cfg["optim"]["weight_decay"]),
    )
    scheduler = build_scheduler(optimizer, max_epochs=int(cfg["training"]["max_epochs"]))

    weights = LossWeights(**cfg["loss_weights"])
    loss_fn = MultiTaskLoss(weights).to(device)

    # Feature extractor (shared with backend)
    from backend.app.ml_inference.feature_extractor import LogMelFeatureExtractor
    from backend.app.ml_inference.audio_config import FeatureConfig

    feature_extractor = LogMelFeatureExtractor(
        FeatureConfig(
            sample_rate=int(cfg["data"]["sample_rate"]),
            n_mels=int(cfg["data"]["n_mels"]),
        )
    )

    augmenter = WaveformAugmenter()
    tb = TBLogger(log_dir=str(tb_dir))
    early = EarlyStopping(patience=int(cfg["training"]["patience"]))

    best_val = float("inf")

    for epoch in range(int(cfg["training"]["max_epochs"])):
        train_stats = run_epoch(
            model=model,
            loader=train_loader,
            loss_fn=loss_fn,
            device=device,
            optimizer=optimizer,
            augmenter=augmenter,
            feature_extractor=feature_extractor,
        )
        val_stats = run_epoch(
            model=model,
            loader=val_loader,
            loss_fn=loss_fn,
            device=device,
            optimizer=None,
            augmenter=None,
            feature_extractor=feature_extractor,
        )

        tb.log_scalars("train", train_stats, epoch)
        tb.log_scalars("val", val_stats, epoch)

        scheduler.step()

        if val_stats["loss"] < best_val:
            best_val = val_stats["loss"]
            save_checkpoint(
                artifacts_dir / "sonicaid_best.pt",
                epoch=epoch,
                model=model,
                optimizer=optimizer,
                best_metric=best_val,
            )

        if early.step(val_stats["loss"]):
            break

    tb.close()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=str, required=True)
    args = parser.parse_args()

    # Ensure project root is on PYTHONPATH for `backend.` and `ml.` imports
    os.environ.setdefault("PYTHONPATH", str(Path(__file__).resolve().parents[2]))
    train(args.config)


if __name__ == "__main__":
    main()

