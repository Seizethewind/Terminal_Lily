"""The language model: token ids in, a score for every possible next token out."""
import torch
import torch.nn as nn
import torch.nn.functional as F

from lily_ai.attention import Block


class GPT(nn.Module):
    def __init__(self, cfg):
        super().__init__()
        self.cfg = cfg
        self.tok = nn.Embedding(cfg.vocab, cfg.dim)       # what each token means
        self.pos = nn.Embedding(cfg.context, cfg.dim)     # where in the text it sits
        self.blocks = nn.ModuleList(Block(cfg) for _ in range(cfg.layers))
        self.norm = nn.LayerNorm(cfg.dim)
        self.head = nn.Linear(cfg.dim, cfg.vocab, bias=False)
        self.head.weight = self.tok.weight                # the output reuses the token table (saves memory)
        self.apply(self._init)

    @staticmethod
    def _init(module):
        if isinstance(module, (nn.Linear, nn.Embedding)):
            nn.init.normal_(module.weight, mean=0.0, std=0.02)

    def forward(self, ids, targets=None):
        x = self.tok(ids) + self.pos(torch.arange(ids.shape[1], device=ids.device))
        for block in self.blocks:
            x = block(x)
        logits = self.head(self.norm(x))
        loss = None
        if targets is not None:
            loss = F.cross_entropy(logits.reshape(-1, logits.size(-1)), targets.reshape(-1))
        return logits, loss

    @torch.no_grad()
    def generate(self, ids, count, temperature=0.8, top_k=40):
        """Add `count` tokens to `ids` (a batch of lists), one at a time."""
        for _ in range(count):
            logits, _ = self(ids[:, -self.cfg.context:])
            logits = logits[:, -1, :] / max(temperature, 1e-5)
            if top_k:
                floor = torch.topk(logits, min(top_k, logits.size(-1))).values[:, -1, None]
                logits = logits.masked_fill(logits < floor, float("-inf"))
            ids = torch.cat([ids, torch.multinomial(F.softmax(logits, dim=-1), 1)], dim=1)
        return ids
