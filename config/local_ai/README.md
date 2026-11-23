# Local fallback: Lily_Ai 0.1

When the router fails or there is no internet, Lily starts Ollama herself and uses a
model on your phone. **Lily_Ai 0.1** is Google's Gemma 4 (Apache 2.0) run under your own
name. Nothing is added to it except a short plain system prompt you can read in
`config/local_ai/Modelfile`. It runs only on your phone and sends nothing anywhere.

```bash
bash scripts/setup_local_ai.sh              # Gemma 4 E2B, about 4.6 GB download
bash scripts/setup_local_ai.sh gemma4:e4b   # smarter, about 6.6 GB; may be too heavy for 8 GB RAM
```

The script installs `ollama` (`pkg install ollama`) if needed, downloads the model into
`data/models`, and creates the model `lily_ai:0.1`. Test it with `ollama run lily_ai:0.1`.
The name in `config/self.toml` (`[local] model`) must match. Turn the fallback off with
`LILY_LOCAL=false` in `.env`. It is a fallback on this phone, not on the online router.
