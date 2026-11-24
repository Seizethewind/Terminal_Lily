"""Step 1: python -m lily_ai.prepare <text files or folders> --vocab 1024  (builds the tokenizer and the data)."""
import argparse
from pathlib import Path

from lily_ai import bpe_train, data

SUFFIXES = {".txt", ".md"}
OUT = "lily_ai_data"


def find_files(args):
    found = []
    for arg in args:
        path = Path(arg)
        found += sorted(p for p in path.rglob("*") if p.suffix in SUFFIXES) if path.is_dir() else [path]
    return found


def sample_text(files, megabytes):
    """The first part of the text, enough to learn the tokenizer from."""
    left, parts = int(megabytes * 1_000_000), []
    for path in files:
        text = path.read_text(encoding="utf-8", errors="replace")[:left]
        parts.append(text)
        left -= len(text)
        if left <= 0:
            break
    return "\n".join(parts)


def main(argv=None):
    ask = argparse.ArgumentParser(description=__doc__)
    ask.add_argument("text", nargs="+", help="text files or folders (.txt and .md)")
    ask.add_argument("--vocab", type=int, default=1024, help="tokens to learn (must match the model size)")
    ask.add_argument("--out", default=OUT)
    ask.add_argument("--sample-mb", type=float, default=20, help="how much text to learn the tokenizer from")
    args = ask.parse_args(argv)
    files = find_files(args.text)
    if not files:
        raise SystemExit("no .txt or .md files found")
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    tokenizer = bpe_train.train(sample_text(files, args.sample_mb), args.vocab)
    tokenizer.save(out / "tokenizer.json")
    training, checking = data.split(data.encode_files(files, tokenizer))
    data.save(training, out / "train.bin")
    data.save(checking, out / "val.bin")
    print(f"tokenizer: {tokenizer.size} tokens. training text: {len(training):,} tokens, checking: {len(checking):,}")


if __name__ == "__main__":
    main()
