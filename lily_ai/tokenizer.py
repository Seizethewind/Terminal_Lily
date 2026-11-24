"""A byte-level BPE tokenizer: any text can be encoded, nothing is 'unknown'."""
import json
import re
from pathlib import Path

PRETOKEN = re.compile(r" ?\w+| ?[^\w\s]+|\s+")   # words keep their leading space; covers every character
END = 256     # marks the end of a text
FIRST = 257   # ids 0-255 are bytes, 256 is END, learned merges follow
CACHE_MAX = 500_000


def merge(ids, pair, new):
    """Replace every adjacent `pair` in `ids` by the id `new`."""
    out, i = [], 0
    while i < len(ids):
        if i + 1 < len(ids) and (ids[i], ids[i + 1]) == pair:
            out.append(new)
            i += 2
        else:
            out.append(ids[i])
            i += 1
    return out


class Tokenizer:
    def __init__(self, merges):
        self.merges = [tuple(pair) for pair in merges]
        self.rank = {pair: n for n, pair in enumerate(self.merges)}
        self.cache = {}
        self.pieces = [bytes([i]) for i in range(256)] + [b""]
        for a, b in self.merges:
            self.pieces.append(self.pieces[a] + self.pieces[b])

    @property
    def size(self):
        return len(self.pieces)

    def _word(self, word):
        ids = self.cache.get(word)
        if ids is None:
            ids = list(word.encode("utf-8"))
            while len(ids) > 1:
                pair = min(zip(ids, ids[1:]), key=lambda p: self.rank.get(p, len(self.rank)))
                if pair not in self.rank:
                    break
                ids = merge(ids, pair, FIRST + self.rank[pair])
            if len(self.cache) >= CACHE_MAX:
                self.cache.clear()
            self.cache[word] = ids
        return ids

    def encode(self, text):
        ids = []
        for word in PRETOKEN.findall(text):
            ids.extend(self._word(word))
        return ids

    def decode(self, ids):
        return b"".join(self.pieces[i] for i in ids).decode("utf-8", errors="replace")

    def save(self, path):
        Path(path).write_text(json.dumps({"merges": self.merges}), encoding="utf-8")

    @classmethod
    def load(cls, path):
        return cls(json.loads(Path(path).read_text(encoding="utf-8"))["merges"])
