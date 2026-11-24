"""Model sizes. A size is five numbers, and the parameter count is plain arithmetic."""
from dataclasses import dataclass


@dataclass(frozen=True)
class ModelConfig:
    vocab: int      # how many different tokens (pieces of text) it knows
    dim: int        # width of every layer
    layers: int     # how many transformer blocks
    heads: int      # attention heads (dim must divide by it)
    context: int    # how many tokens it reads at once

    def __post_init__(self):
        if self.dim % self.heads or self.vocab > 32767:
            raise ValueError("dim must divide evenly by heads, and vocab must be 32767 or less")

    def parameters(self):
        """Exact count for lily_ai.model.GPT: embeddings (shared with the output), blocks, final norm."""
        block = 12 * self.dim ** 2 + 4 * self.dim   # attention 4d*d, feed-forward 8d*d, two norms
        return (self.vocab + self.context) * self.dim + self.layers * block + 2 * self.dim


# name -> (model, training: steps, batch size, top learning rate)
SIZES = {
    "test": (ModelConfig(1024, 128, 4, 4, 128), dict(steps=300, batch=16, lr=3e-3)),     # about 0.9M: checks the code
    "small": (ModelConfig(4096, 384, 6, 6, 256), dict(steps=15000, batch=64, lr=1e-3)),  # about 12M: Lily_Ai 0.1
    "medium": (ModelConfig(4096, 512, 8, 8, 256), dict(steps=25000, batch=64, lr=6e-4)),  # about 27M
}


def describe():
    return "\n".join(f"{name:<7}{cfg.parameters() / 1e6:5.1f}M parameters, {cfg.layers} layers, "
                     f"{cfg.dim} wide, reads {cfg.context} tokens" for name, (cfg, _) in SIZES.items())
