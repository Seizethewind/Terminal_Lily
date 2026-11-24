"""Step 3: python -m lily_ai.generate --size test --prompt "Hello"  (the trained model continues the text)."""
import argparse
from pathlib import Path

import torch

from lily_ai import checkpoint
from lily_ai.config import SIZES
from lily_ai.model import GPT
from lily_ai.tokenizer import END, Tokenizer


def main(argv=None):
    ask = argparse.ArgumentParser(description=__doc__)
    ask.add_argument("--size", choices=SIZES, default="test")
    ask.add_argument("--data", default="lily_ai_data")
    ask.add_argument("--prompt", default="")
    ask.add_argument("--tokens", type=int, default=100)
    ask.add_argument("--temperature", type=float, default=0.8, help="lower is safer, higher is wilder")
    ask.add_argument("--top-k", type=int, default=40)
    args = ask.parse_args(argv)
    folder = Path(args.data)
    state = checkpoint.load(folder / f"{args.size}.pt")
    model = GPT(state["config"])
    model.load_state_dict(state["model"])
    model.eval()
    tokenizer = Tokenizer.load(folder / "tokenizer.json")
    ids = torch.tensor([tokenizer.encode(args.prompt) or [END]])
    print(tokenizer.decode(model.generate(ids, args.tokens, args.temperature, args.top_k)[0].tolist()))


if __name__ == "__main__":
    main()
