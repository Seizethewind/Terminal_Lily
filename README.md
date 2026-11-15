# Terminal_Lily

Lily, a terminal AI agent built for Termux. She is made of three layers, each
run by its own sub orchestrator and all coordinated by one main orchestrator:

- **LLM**: talks to your freellmapi router (`auto`, `auto:fast`, `auto:smart`)
- **Tools**: shell, files, web, Termux API, the LilyAi MCP, and your own plugins
- **RAG**: her notes and documents, searched with SQLite
- **Data layer**: run log, your feedback, lessons, history and a dataset export

> Status: building in layers. Done: skeleton, config, UI, main orchestrator,
> the LLM layer, the Tools layer, RAG and the data layer.

## Quick start (Termux)

```bash
git clone https://github.com/Seizethewind/Terminal_Lily
cd Terminal_Lily
bash scripts/setup_termux.sh   # installs Python deps, creates .env
nano .env                      # set LILY_BASE_URL and LILY_API_KEY
python main.py
```

Commands inside Lily: `/help`, `/clear`, `/profile [auto|fast|smart]`, `/tools`,
`/reload`, `/ingest <path>`, `/notes`, `/forget <source>`, `/good`, `/bad`,
`/lesson <text>`, `/lessons`, `/unlearn <n>`, `/history [n]`, `/summarize`,
`/export [all]`, `/stats`, `/code`, `/entity`, `/exit`.

## Choosing a model

Lily sends `auto`, `auto:fast` or `auto:smart` to your router (see
`config/models.toml`). Set one by hand with `/profile fast`. While the profile
is `auto`, trigger words in `[rules]` switch a single message to another
profile (for example "code" or "plan" use `smart`, "quick" uses `fast`).

## Tools

Lily asks you before **every** tool runs (answer `y` to allow). Built in:
`shell`, `read_file`, `write_file`, `web_search` (DuckDuckGo's HTML page; it is
unofficial and may break), `termux_api` (battery, clipboard, notifications;
needs `pkg install termux-api` and the Termux:API app) and `rag_search` (works
once the RAG layer exists). `/tools` lists what is loaded and what failed.

**Your own tools:** copy `plugins/example_plugin.py`, change it, then type
`/reload`. One file = one tool: a class named `Tool` that extends `BaseTool`.
Files starting with `_` are ignored. A broken plugin is reported by `/tools`
and never stops Lily.

**LilyAi MCP:** edit `config/mcp_servers.toml` (fill in the url, set
`enabled = true`), put the token in `.env` as `LILYAI_MCP_TOKEN`, then
`/reload`. Its tools appear as `lilyai__<tool>`. Only the Streamable HTTP
transport is supported.

## Updating (Termux)

```bash
bash ~/Terminal_Lily/scripts/update.sh
```

It pulls the latest version from GitHub, lists what changed, and reinstalls
Python packages only if `requirements.txt` changed. It never overwrites your
own edits: if you changed a tracked file it stops and tells you. Your `.env`
and `data/` are never touched. Restart Lily afterwards.

For a short command, run this once and reopen Termux, then type `lily-update`:

```bash
echo "alias lily-update='bash ~/Terminal_Lily/scripts/update.sh'" >> ~/.bashrc
```

## Notes (RAG)

`/ingest ~/notes` indexes a file or folder (text, markdown, code, json, csv and
similar; hidden folders and files over 1 MB are skipped; at most 500 files per
run). Before each answer Lily searches the notes for your message and gives the
3 best passages to the model. Searching is SQLite full-text search (FTS5) with
word stemming, so there is no embedding model and nothing extra to install.
`/notes` lists what is indexed, `/forget <source>` removes one source, and
indexing the same file again replaces its old passages. The database is
`data/rag.db` (gitignored).

## Learning from results (data layer)

Everything Lily does becomes data in `data/lily.db` (gitignored, local only):
every message with the profile asked for, the model that really answered
(from the router's `X-Routed-Via` header), the tools used, steps, time and any
error. Tool outputs and file contents are **not** stored, only tool names.

- `/good` and `/bad` rate Lily's last answer (add a note if you like).
- **Profile learning:** while the profile is `auto` and no `[rules]` word
  matches, Lily looks at past answers to similar questions that you rated. Two
  or more agreeing verdicts (good on `smart`, or bad on `fast`/`auto`) make her
  ask the router for `auto:smart` or `auto:fast` instead. A profile you set by
  hand always wins.
- `/lesson <text>` teaches her something. Lessons are indexed as notes, so they
  come back when relevant. `/lessons` lists them, `/unlearn <n>` removes one.
- `/summarize` asks the model to condense recent chats into a note she keeps.
- `/history [n]` shows recent exchanges. `/stats` shows runs and verdicts per
  profile.
- `/export` writes chats you rated `/good` to `data/dataset.jsonl` (chat
  messages format, one chat per line) for later fine-tuning; `/export all`
  writes every finished chat.

## Coding taxonomy

Every code block in a chat (yours or Lily's) is filed by language, as
`group > family > language`, for example `programming > systems > rust`. It
happens automatically after each answer, costs no API calls (it reads the
``` fence tag, or guesses an untagged block from its content), and the code
is stored in `data/lily.db`.

**Any language is stored.** The list in `config/languages.toml` (about 50
languages, with aliases such as `py`, `c++`, `rs`) only decides the tree. A
language that is not on the list is kept under `unknown` and flagged, so
nothing is lost. Add it to the file and run `/code scan` to file it properly.

- `/code` shows languages with block and chat counts.
- `/code show <language> [n]` lists the latest blocks (aliases work).
- `/code scan` re-files every stored chat (after editing the list, or to
  fill in chats from before this feature).
- `/code export <language>` writes the chats containing that language to
  `data/code_<language>.jsonl`.

## Entity taxonomy (entity, location, object)

Everything else Lily hears about is sorted into three classes, each with basic
subclasses:

| Class | Subclasses |
|---|---|
| **entity** (living things, groups of people) | person, animal, plant, organization |
| **location** | country, city, region, water, landform, place |
| **object** | device, vehicle, tool, food, clothing |

After each answer Lily scans your message and her answer for the words listed in
`config/entities.toml` and files each one as `class > subclass` (it also finds
plurals, and ignores code). No API calls. It is a **word list**, so it cannot
tell meanings apart ("mouse" is always a device) and it only knows the words
you give it.

- `/entity` shows the tree with counts, `/entity classes` lists the subclasses.
- `/entity show <class[/sub]>` lists the words filed there, for example
  `/entity show object/device`.
- `/entity find <word>` shows the latest chats that mention a word.
- `/entity add <word> <class/sub>` teaches her a word, for example
  `/entity add seize entity/person` or `/entity add cebu pines location/place`.
  Subclasses are free: a new name makes a new subclass. `/entity remove <word>`
  removes one you added.
- `/entity scan` re-files all stored chats after you add words or edit the file.

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
config/            settings, models.toml, mcp_servers.toml, languages.toml, entities.toml, system_prompt.txt
plugins/           your own tools (one file = one tool)
scripts/           setup_termux.sh (first install), update.sh (update from GitHub)
lily/              orchestrator, agent_loop, router, state, bootstrap
lily/llm/          LLM sub orchestrator, prompt builder, parser, profile picker
lily/llm/providers/  openai_compat.py (standard library only)
lily/tools/        Tools sub orchestrator, registry, loader, permissions
lily/tools/builtin/  shell, read_file, write_file, web_search, termux_api, rag_search
lily/tools/mcp/    MCP client, adapter and config
lily/rag/          RAG sub orchestrator, SQLite store, chunker, loader, retriever, ingest
lily/memory/       data layer: run log, feedback, lessons, history, summarizer, profile hints, export, coding and entity taxonomies
lily/ui/           terminal loop, rich renderer, slash commands
lily/utils/        logger, errors, paths
tests/             run: python -m unittest discover -s tests -t .
```

All planned layers are in. Next steps are up to you.

## License

See [LICENSE](LICENSE).
