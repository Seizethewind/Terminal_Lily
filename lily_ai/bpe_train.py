"""Learns the merges of a Tokenizer from text: always join the most common neighbouring pair."""
from collections import Counter, defaultdict

from lily_ai.tokenizer import FIRST, PRETOKEN, Tokenizer, merge


def _pairs(ids):
    return zip(ids, ids[1:])


def train(text, vocab_size):
    """A Tokenizer with up to `vocab_size` tokens (fewer if the text has nothing left to join)."""
    counts = Counter(PRETOKEN.findall(text))
    words = [list(word.encode("utf-8")) for word in counts]
    freqs = list(counts.values())
    pairs, where = Counter(), defaultdict(set)   # pair -> how often, pair -> which words hold it
    for n, ids in enumerate(words):
        for pair in _pairs(ids):
            pairs[pair] += freqs[n]
            where[pair].add(n)
    merges = []
    while len(merges) < vocab_size - FIRST and pairs:
        best = max(pairs, key=lambda pair: (pairs[pair], pair))
        new = FIRST + len(merges)
        merges.append(best)
        for n in where.pop(best):
            if best not in set(_pairs(words[n])):
                continue   # this word changed since it was listed
            for pair in _pairs(words[n]):
                pairs[pair] -= freqs[n]
            words[n] = merge(words[n], best, new)
            for pair in _pairs(words[n]):
                pairs[pair] += freqs[n]
                where[pair].add(n)
        pairs = +pairs   # drops pairs that no longer occur
    return Tokenizer(merges)
