from __future__ import annotations

from typing import Dict

import torch
import torch.nn.functional as F


def multihead_postprocess(
    raw_outputs: Dict[str, torch.Tensor]
) -> Dict[str, Dict[str, float]]:
    """
    Convert raw multi-head model outputs into human-readable predictions.
    """
    primary_logits = raw_outputs["primary"]  # (B, C)
    emotion_logits = raw_outputs["emotion"]  # (B, E)
    env_tag_logits = raw_outputs["env_tags"]  # (B, T)
    noise_pred = raw_outputs["noise"]  # (B, 1)
    engagement_pred = raw_outputs["engagement"]  # (B, 1)

    primary_probs = F.softmax(primary_logits, dim=-1)[0]
    emotion_probs = F.softmax(emotion_logits, dim=-1)[0]
    env_tag_probs = torch.sigmoid(env_tag_logits)[0]

    primary_conf, primary_idx = torch.max(primary_probs, dim=-1)
    emotion_conf, emotion_idx = torch.max(emotion_probs, dim=-1)

    # For a real system, these label lists should come from config / dataset metadata.
    primary_labels = [f"class_{i}" for i in range(primary_probs.shape[0])]
    emotion_labels = [f"emotion_{i}" for i in range(emotion_probs.shape[0])]
    env_tag_labels = [f"tag_{i}" for i in range(env_tag_probs.shape[0])]

    env_tags = [
        (label, float(prob))
        for label, prob in zip(env_tag_labels, env_tag_probs.tolist())
        if prob > 0.5
    ]

    return {
        "primary": {
            "label": primary_labels[int(primary_idx)],
            "confidence": float(primary_conf),
        },
        "emotion": {
            "label": emotion_labels[int(emotion_idx)],
            "confidence": float(emotion_conf),
        },
        "env_tags": {label: score for label, score in env_tags},
        "noise_intensity": float(noise_pred[0, 0]),
        "engagement_score": float(engagement_pred[0, 0]),
    }

