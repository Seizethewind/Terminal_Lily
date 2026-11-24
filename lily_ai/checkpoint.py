"""Saves and loads training progress, so a session that is cut off can carry on."""
import os
from dataclasses import asdict

import torch

from lily_ai.config import ModelConfig


def save(path, model, optimizer, step, best):
    tmp = f"{path}.tmp"   # written aside first, so a crash never leaves half a file
    torch.save({"model": model.state_dict(), "optimizer": optimizer.state_dict(), "step": step,
                "best": best, "config": asdict(model.cfg)}, tmp)
    os.replace(tmp, path)


def load(path, device="cpu"):
    state = torch.load(path, map_location=device, weights_only=True)
    state["config"] = ModelConfig(**state["config"])
    return state
