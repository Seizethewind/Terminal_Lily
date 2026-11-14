# Terminal_Lily

Lily, a terminal AI agent built for Termux. She is made of three layers, each
run by its own sub orchestrator and all coordinated by one main orchestrator:

- **LLM**: talks to your freellmapi router (`auto`, `auto:fast`, `auto:smart`)
- **Tools**: shell, files, web, Termux API, the LilyAi MCP, and your own plugins
- **RAG**: her notes and documents, searched with SQLite

> Status: building in layers. Done: skeleton, config, UI, main orchestrator and
> the LLM layer. Next: Tools, then RAG, then the data layer.

## Quick start (Termux)

```bash
git clone https://github.com/Seizethewind/Terminal_Lily
cd Terminal_Lily
bash scripts/setup_termux.sh   # installs Python deps, creates .env
nano .env                      # set LILY_BASE_URL and LILY_API_KEY
python main.py
```

Commands inside Lily: `/help`, `/clear`, `/profile [auto|fast|smart]`, `/exit`.

## Choosing a model

Lily sends `auto`, `auto:fast` or `auto:smart` to your router (see
`config/models.toml`). Set one by hand with `/profile fast`. While the profile
is `auto`, trigger words in `[rules]` switch a single message to another
profile (for example "code" or "plan" use `smart`, "quick" uses `fast`).

## Rules of this repo

- Every Python file is **120 lines or fewer** and does **one thing**
  (enforced by `tests/test_line_limit.py`).
- Few dependencies, because Termux makes heavy packages painful. Config files
  are TOML so no extra parser is needed.
- Each layer exposes `register(lily)` in its `orchestrator.py`. The main
  orchestrator never reaches into a layer's internals.

## How a message flows

```
you -> ui -> main orchestrator -> agent loop
              |- rag   (fetch relevant notes)
              |- llm   (think; may ask for a tool)
              '- tools (run it; result goes back to the llm)
           -> repeat until the llm gives a final answer
```

## Layout

```
main.py            entry point
config/            settings, models.toml, system_prompt.txt
lily/              orchestrator, agent_loop, router, state, bootstrap
lily/llm/          LLM sub orchestrator, prompt builder, parser, profile picker
lily/llm/providers/  openai_compat.py (standard library only)
lily/ui/           terminal loop, rich renderer, slash commands
lily/utils/        logger, errors, paths
tests/             run: python -m unittest discover -s tests -t .
```

Coming next: `lily/tools/` (+ `plugins/`), `lily/rag/`, `lily/memory/`.

## License

See [LICENSE](LICENSE).
