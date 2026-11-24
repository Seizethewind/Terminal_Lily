"""One transformer block: attention (who looks at whom) and a small feed-forward network."""
import torch.nn as nn
import torch.nn.functional as F


class Attention(nn.Module):
    def __init__(self, cfg):
        super().__init__()
        self.heads = cfg.heads
        self.qkv = nn.Linear(cfg.dim, 3 * cfg.dim, bias=False)   # query, key and value in one step
        self.proj = nn.Linear(cfg.dim, cfg.dim, bias=False)

    def forward(self, x):
        b, t, d = x.shape
        q, k, v = (a.view(b, t, self.heads, d // self.heads).transpose(1, 2) for a in self.qkv(x).split(d, dim=2))
        y = F.scaled_dot_product_attention(q, k, v, is_causal=True)   # a token only sees the ones before it
        return self.proj(y.transpose(1, 2).reshape(b, t, d))


class Block(nn.Module):
    def __init__(self, cfg):
        super().__init__()
        self.norm1, self.norm2 = nn.LayerNorm(cfg.dim), nn.LayerNorm(cfg.dim)
        self.attention = Attention(cfg)
        self.mlp = nn.Sequential(nn.Linear(cfg.dim, 4 * cfg.dim, bias=False), nn.GELU(),
                                 nn.Linear(4 * cfg.dim, cfg.dim, bias=False))

    def forward(self, x):
        x = x + self.attention(self.norm1(x))
        return x + self.mlp(self.norm2(x))
