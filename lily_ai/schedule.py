"""The learning rate over time: a short warm-up, then a smooth fall to a tenth of the top value."""
import math


def lr_at(step, total, peak, warmup=100, floor=0.1):
    if step < warmup:
        return peak * (step + 1) / warmup
    if step >= total:
        return peak * floor
    progress = (step - warmup) / max(1, total - warmup)
    return peak * (floor + (1 - floor) * 0.5 * (1 + math.cos(math.pi * progress)))
