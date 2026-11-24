"""Turns text files into one long list of token ids (2 bytes each) and draws training batches."""
from array import array
from pathlib import Path

from lily_ai.tokenizer import END

LINES = 50_000   # lines encoded at a time, so a huge file never sits in memory whole


def chunks(path):
    with open(path, encoding="utf-8", errors="replace") as handle:
        group = []
        for line in handle:
            group.append(line)
            if len(group) >= LINES:
                yield "".join(group)
                group = []
        if group:
            yield "".join(group)


def encode_files(paths, tokenizer):
    ids = array("H")
    for path in paths:
        for text in chunks(path):
            ids.extend(tokenizer.encode(text))
        ids.append(END)
    return ids


def save(ids, path):
    with open(path, "wb") as handle:
        ids.tofile(handle)


def load(path):
    ids = array("H")
    with open(path, "rb") as handle:
        ids.fromfile(handle, Path(path).stat().st_size // ids.itemsize)
    return ids


def split(ids, fraction=0.01):
    """(training part, validation part): the last bit is kept aside to check the model on unseen text."""
    cut = max(1, int(len(ids) * fraction))
    return ids[:-cut], ids[-cut:]


def sample(ids, batch, context, rng):
    """Random windows: inputs and, shifted by one token, the targets. Lists of lists of ids."""
    if len(ids) < context + 2:
        raise ValueError(f"only {len(ids)} tokens: too little text for a context of {context}")
    starts = [rng.randrange(len(ids) - context - 1) for _ in range(batch)]
    return ([ids[i:i + context].tolist() for i in starts],
            [ids[i + 1:i + context + 1].tolist() for i in starts])
