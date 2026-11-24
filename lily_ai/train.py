"""Step 2: python -m lily_ai.train --size test  (reads lily_ai_data, saves lily_ai_data/<size>.pt)."""
import argparse
import random
import time
from pathlib import Path

import torch

from lily_ai import checkpoint, data
from lily_ai.config import SIZES
from lily_ai.model import GPT
from lily_ai.schedule import lr_at
from lily_ai.tokenizer import Tokenizer


def batch(ids, cfg, size, rng, device):
    inputs, targets = data.sample(ids, size, cfg.context, rng)
    return torch.tensor(inputs, device=device), torch.tensor(targets, device=device)


@torch.no_grad()
def check(model, ids, cfg, size, rng, device, rounds=20):
    """Average loss on text the model never trains on. Lower is better."""
    model.eval()
    losses = [model(*batch(ids, cfg, size, rng, device))[1].item() for _ in range(rounds)]
    model.train()
    return sum(losses) / len(losses)


def main(argv=None):
    ask = argparse.ArgumentParser(description=__doc__)
    ask.add_argument("--size", choices=SIZES, default="test")
    ask.add_argument("--data", default="lily_ai_data")
    ask.add_argument("--steps", type=int)
    ask.add_argument("--batch", type=int)
    ask.add_argument("--lr", type=float)
    ask.add_argument("--every", type=int, default=250, help="check and save every N steps")
    args = ask.parse_args(argv)
    cfg, plan = SIZES[args.size]
    steps, size, lr = args.steps or plan["steps"], args.batch or plan["batch"], args.lr or plan["lr"]
    folder = Path(args.data)
    if Tokenizer.load(folder / "tokenizer.json").size > cfg.vocab:
        raise SystemExit(f"the tokenizer is bigger than the '{args.size}' model's vocab ({cfg.vocab}); rerun prepare")
    train_ids, val_ids = data.load(folder / "train.bin"), data.load(folder / "val.bin")
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = GPT(cfg).to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=lr, betas=(0.9, 0.95), weight_decay=0.1)
    path, start, best = folder / f"{args.size}.pt", 0, float("inf")
    if path.exists():
        state = checkpoint.load(path, device)
        model.load_state_dict(state["model"])
        optimizer.load_state_dict(state["optimizer"])
        start, best = state["step"], state["best"]
        print(f"carrying on from step {start}")
    amp = device == "cuda"   # half precision on the GPU: faster and lighter
    scaler = torch.amp.GradScaler("cuda", enabled=amp)
    rng = random.Random(1234 + start)
    print(f"{args.size}: {sum(p.numel() for p in model.parameters()):,} parameters (expected {cfg.parameters():,}) on {device}")
    began = time.time()
    for step in range(start, steps):
        for group in optimizer.param_groups:
            group["lr"] = lr_at(step, steps, lr)
        x, y = batch(train_ids, cfg, size, rng, device)
        with torch.autocast(device_type=device, dtype=torch.float16, enabled=amp):
            _, loss = model(x, y)
        optimizer.zero_grad(set_to_none=True)
        scaler.scale(loss).backward()
        scaler.unscale_(optimizer)
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        scaler.step(optimizer)
        scaler.update()
        if (step + 1) % args.every == 0 or step + 1 == steps:
            seen = check(model, val_ids, cfg, size, rng, device)
            best = min(best, seen)
            checkpoint.save(path, model, optimizer, step + 1, best)
            print(f"step {step + 1}/{steps}  train {loss.item():.3f}  check {seen:.3f}  {time.time() - began:.0f}s")


if __name__ == "__main__":
    main()
