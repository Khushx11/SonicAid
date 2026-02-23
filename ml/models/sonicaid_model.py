from __future__ import annotations

import torch
import torch.nn as nn

from .audio_backbone import CnnAudioBackbone
from .audio_transformer import TemporalTransformer
from .multihead_outputs import (
    PrimarySoundHead,
    EmotionHead,
    EnvTagHead,
    NoiseHead,
    EngagementHead,
)


class SonicAidModel(nn.Module):
    def __init__(
        self,
        backbone_cfg: dict,
        transformer_cfg: dict,
        num_primary_classes: int,
        num_emotions: int,
        num_env_tags: int,
    ) -> None:
        super().__init__()
        self.backbone = CnnAudioBackbone(**backbone_cfg)
        self.transformer = TemporalTransformer(**transformer_cfg)

        d_model = transformer_cfg["d_model"]
        self.primary_head = PrimarySoundHead(d_model, num_primary_classes)
        self.emotion_head = EmotionHead(d_model, num_emotions)
        self.env_tag_head = EnvTagHead(d_model, num_env_tags)
        self.noise_head = NoiseHead(d_model)
        self.engagement_head = EngagementHead(d_model)

    def forward(self, x: torch.Tensor):
        # x: (B, 1, n_mels, time)
        feats = self.backbone(x)  # (B, d_model, T')
        feats = feats.transpose(1, 2)  # (B, T', d_model)
        encoded = self.transformer(feats)  # (B, T', d_model)
        pooled = encoded.mean(dim=1)

        return {
            "primary": self.primary_head(pooled),
            "emotion": self.emotion_head(pooled),
            "env_tags": self.env_tag_head(pooled),
            "noise": self.noise_head(pooled),
            "engagement": self.engagement_head(pooled),
        }


def build_sonicaid_demo_model() -> SonicAidModel:
    backbone_cfg = {"n_mels": 80, "d_model": 128}
    transformer_cfg = {"d_model": 128, "nhead": 4, "num_layers": 2, "dim_feedforward": 256, "dropout": 0.1}
    return SonicAidModel(
        backbone_cfg=backbone_cfg,
        transformer_cfg=transformer_cfg,
        num_primary_classes=6,
        num_emotions=4,
        num_env_tags=8,
    )

