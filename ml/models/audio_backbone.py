from __future__ import annotations

import torch
import torch.nn as nn


class DepthwiseSeparableConv(nn.Module):
    def __init__(self, in_channels: int, out_channels: int, stride: int = 1):
        super().__init__()
        self.depthwise = nn.Conv2d(
            in_channels,
            in_channels,
            kernel_size=3,
            stride=stride,
            padding=1,
            groups=in_channels,
            bias=False,
        )
        self.pointwise = nn.Conv2d(
            in_channels, out_channels, kernel_size=1, stride=1, bias=False
        )
        self.bn = nn.BatchNorm2d(out_channels)
        self.act = nn.SiLU()

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = self.depthwise(x)
        x = self.pointwise(x)
        x = self.bn(x)
        x = self.act(x)
        return x


class CnnAudioBackbone(nn.Module):
    """
    Lightweight CNN backbone inspired by MobileNet-like depthwise separable convs.
    Input: (B, 1, n_mels, time)
    Output: (B, d_model, T')
    """

    def __init__(self, n_mels: int = 80, d_model: int = 128):
        super().__init__()
        self.stem = nn.Sequential(
            nn.Conv2d(1, 32, kernel_size=3, stride=2, padding=1, bias=False),
            nn.BatchNorm2d(32),
            nn.SiLU(),
        )
        self.block1 = DepthwiseSeparableConv(32, 64, stride=2)
        self.block2 = DepthwiseSeparableConv(64, d_model, stride=2)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = self.stem(x)
        x = self.block1(x)
        x = self.block2(x)  # (B, d_model, F', T')

        # Collapse frequency dimension into channels to get (B, d_model, T')
        b, c, f, t = x.shape
        x = x.view(b, c * f, t)
        # Optionally project back to d_model if needed
        return x

