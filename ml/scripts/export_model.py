from __future__ import annotations

import argparse
from pathlib import Path

import torch

from ml.models.sonicaid_model import build_sonicaid_demo_model


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=str, default="ml/artifacts/sonicaid_scripted.pt")
    args = parser.parse_args()

    model = build_sonicaid_demo_model().eval()
    scripted = torch.jit.script(model)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    scripted.save(str(out))
    print(f"Saved scripted model to {out}")


if __name__ == "__main__":
    main()

