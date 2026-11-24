# Lily_Ai: a language model built from scratch

A small GPT-style model whose every part is in this folder: the tokenizer, the data
pipeline, the network, the training loop and the text generator. Nothing is downloaded
except PyTorch (needed only for training and running; Kaggle and Colab already have it).
No pretrained weights are used, so the finished model is entirely yours.

## What each file does

| File | Job |
|---|---|
| `config.py` | the model sizes (`test`, `small`, `medium`) and their exact parameter counts |
| `tokenizer.py`, `bpe_train.py` | your own tokenizer, learned from your text (byte-level BPE) |
| `data.py`, `prepare.py` | text files -> token ids on disk, training batches |
| `attention.py`, `model.py` | the network |
| `schedule.py`, `checkpoint.py`, `train.py` | the learning rate, saving and resuming, the training loop |
| `generate.py` | writes text with the trained model |

## Sizes

| Name | Parameters | Use |
|---|---|---|
| `test` | 0.9M | checks that the code works. It will write nonsense, on purpose |
| `small` | 12.3M | Lily_Ai 0.1, the first real model (needs much more text and a GPU) |
| `medium` | 27.4M | later |

## Try it on Kaggle (the 1M test)

Kaggle setup: new notebook, Accelerator = GPU, Internet = on (needs a verified phone number).

```python
!git clone https://github.com/Seizethewind/Terminal_Lily
%cd Terminal_Lily
!python -m lily_ai.prepare README.md --vocab 1024     # any .txt or .md files or folders work
!python -m lily_ai.train --size test --every 50
!python -m lily_ai.generate --size test --prompt "Lily" --tokens 60
```

Expect the check loss to fall during training and the text to be gibberish: the repo's
README is far too little text for any model, so this only proves the pipeline works.
The finished files are in `lily_ai_data/`. Keep them: copy the folder to `/kaggle/working`
before the session ends.

Training saves a checkpoint every `--every` steps. If a session is cut off, run the same
`train` command again and it carries on from the last save.

## The same on your phone's CPU

If PyTorch is installed (it is heavy on Termux, so this is optional), the same three
commands work; use `--size test`. A GPU is only needed for `small`.

## What comes next (not done yet)

1. Pick public simple-text training data and check its licence.
2. Train `small` (about 12M) on a GPU with 100 to 200 million words.
3. Add your own question-and-answer text so it starts to behave like Lily.
4. Export it so Lily on your phone can use it as the local fallback.

## Honest limits

This is a learning project. A 12M model writes short, simple text. It does not answer
questions, follow instructions or write code until it is taught with a lot more data.
There is no dropout, no mixed-in instructions and no safety tuning.
