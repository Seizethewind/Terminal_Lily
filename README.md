<div align="center">

# Terminal_Lily

**A terminal AI agent for Termux, with tools, notes and a memory that learns from your feedback.**

![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)
![Platform: Termux](https://img.shields.io/badge/platform-Termux-black.svg)
![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-3776AB.svg)

</div>

---

## Contents

- [Overview](#overview)
- [Quick start](#quick-start)
- [Configuration](#configuration)
- [Using Lily](#using-lily)
- [Tools and plugins](#tools-and-plugins)
- [LilyAi MCP](#lilyai-mcp)
- [Notes (RAG)](#notes-rag)
- [Learning from results](#learning-from-results)
- [Taxonomies](#taxonomies)
- [Updating](#updating)
- [Architecture](#architecture)
- [Development](#development)
- [License](#license)

---

## Overview

Lily runs in your terminal and talks to your own `freellmapi` router. Four
layers, each run by its own sub-orchestrator and coordinated by one main
orchestrator, do the work:

| Layer | What it does |
|---|---|
| **LLM** | Talks to your router using the `auto`, `auto:fast` and `auto:smart` profiles. |
| **Tools** | Shell, files, web search, Termux API, the LilyAi MCP and your own plugins. |
| **RAG** | Searches her notes and your documents with SQLite full-text search. |
| **Data** | Keeps a run log, your feedback, lessons and history, and can export a dataset. |

> **Status:** all planned layers are complete: skeleton, config, UI, main
> orchestrator, LLM, Tools, RAG and the data layer.

**Design principles**

- **You stay in control.** Lily asks before every tool runs.
- **Local first.** Everything she learns stays on your device.
- **Light on dependencies.** Termux makes heavy packages painful, so the
  project avoids them and uses TOML for configuration.

## Quick start

**Requirements:** Termux, Python 3.11 or newer (configuration is read with the
standard `tomllib`), `git`, and a running `freellmapi` router.

```bash
git clone https://github.com/Seizethewind/Terminal_Lily
cd Terminal_Lily
bash scripts/setup_termux.sh   # installs Python dependencies and creates .env
nano .env                      # set LILY_BASE_URL and LILY_API_KEY
python main.py
```

## Configuration

### Environment variables (`.env`)

`scripts/setup_termux.sh` creates `.env` from `.env.example`. The file is
never committed and never overwritten by an update.

| Variable | Purpose | Example |
|---|---|---|
| `LILY_BASE_URL` | Your router's OpenAI-compatible `/v1` endpoint. | `http://127.0.0.1:3001/v1` |
| `LILY_API_KEY` | Your router's unified key. | `freellmapi-...` |
| `LILY_MAX_STEPS` | Maximum think/act steps per message. | `8` |
| `LILY_TIMEOUT` | Seconds to wait for the router before giving up. | `60` |
| `MCP_API_KEYS` | Bearer key for the LilyAi MCP. One key only. | `your-real-key` |
| `LILY_SEARCH_URL` | Optional. A page that mimics DuckDuckGo's HTML search. | |

### Config files (`config/`)

| File | Controls |
|---|---|
| `models.toml` | Model profiles and the `[rules]` trigger words. |
| `mcp_servers.toml` | MCP servers: url and the name of the key variable. |
| `languages.toml` | The coding taxonomy (about 50 languages and aliases). |
| `entities.toml` | The word list for the subject taxonomy. |
| `system_prompt.txt` | Lily's system prompt. |

## Using Lily

### Choosing a model

Lily sends `auto`, `auto:fast` or `auto:smart` to your router. Set one by hand
with `/profile fast`. While the profile is `auto`, trigger words in `[rules]`
switch a single message to another profile: for example, "code" or "plan" use
`smart`, and "quick" uses `fast`.

### Commands

| Group | Commands |
|---|---|
| Session | `/help`, `/clear`, `/exit` |
| Model | `/profile [auto\|fast\|smart]` |
| Tools | `/tools`, `/reload` |
| Notes | `/ingest <path>`, `/notes`, `/forget <source>` |
| Feedback | `/good`, `/bad`, `/lesson <text>`, `/lessons`, `/unlearn <n>` |
| History | `/history [n]`, `/summarize`, `/stats`, `/export [all]` |
| Taxonomies | `/code`, `/entity` |

## Tools and plugins

Lily asks permission before **every** tool runs. Answer `y` to allow it.
`/tools` lists what is loaded and what failed.

| Tool | Notes |
|---|---|
| `shell` | Runs a command. |
| `read_file`, `write_file` | Read and write files. |
| `web_search` | Uses DuckDuckGo's HTML page. It is unofficial and may break. |
| `termux_api` | Battery, clipboard, notifications. Needs `pkg install termux-api` and the Termux:API app. |
| `rag_search` | Searches your indexed notes. |

**Writing your own tool.** Copy `plugins/example_plugin.py`, change it, then
type `/reload`. One file is one tool: a class named `Tool` that extends
`BaseTool`. Files starting with `_` are ignored. A broken plugin is reported
by `/tools` and never stops Lily.

## LilyAi MCP

Lily supports MCP servers over the **Streamable HTTP** transport only. The
setup is split in two so that no secret ever lands in a tracked file:

- `config/mcp_servers.toml` holds the server **url** and the **name of the
  variable** that contains the key.
- `.env` holds the key itself.

```toml
# config/mcp_servers.toml
[[servers]]
name = "lilyai"
url = "https://your-real-host/mcp"   # the full endpoint, usually ending in /mcp
auth_env = "MCP_API_KEYS"
enabled = true
```

```bash
# .env
MCP_API_KEYS=your-real-key
```

Run `/reload`, then `/tools`. The server's tools appear as `lilyai__<tool>`.

**Good to know**

- `MCP_API_KEYS` holds **one** key. Lily sends it as `Bearer <value>`, so a
  comma-separated list is rejected.
- The url is used exactly as written. A missing `/mcp` usually gives
  `HTTP 404`, a wrong or missing key gives `HTTP 401`, and "cannot reach the
  MCP server" means a wrong host or no network.
- Older setups used `LILYAI_MCP_TOKEN`. Rename it to `MCP_API_KEYS` in
  `.env`, or keep your own name and set `auth_env` to match.

## Notes (RAG)

`/ingest ~/notes` indexes a file or folder: text, markdown, code, JSON, CSV
and similar. Hidden folders and files over 1 MB are skipped, with at most 500
files per run. Before each answer, Lily searches the notes for your message
and hands the 3 best passages to the model.

Search is SQLite full-text search (FTS5) with word stemming, so there is no
embedding model and nothing extra to install. Indexing the same file again
replaces its old passages. The database is `data/rag.db` (gitignored).

| Command | Effect |
|---|---|
| `/ingest <path>` | Index a file or folder. |
| `/notes` | List what is indexed. |
| `/forget <source>` | Remove one source. |

## Learning from results

Everything Lily does is logged to `data/lily.db` (gitignored, local only):
the message, the profile requested, the model that actually answered (from the
router's `X-Routed-Via` header), the tools used, steps, time and any error.
Tool outputs and file contents are **not** stored, only tool names.

| Command | Effect |
|---|---|
| `/good`, `/bad` | Rate Lily's last answer, with an optional note. |
| `/lesson <text>` | Teach her something. Lessons are indexed as notes and come back when relevant. |
| `/lessons`, `/unlearn <n>` | List lessons, or remove one. |
| `/summarize` | Condense recent chats into a note she keeps. |
| `/history [n]` | Show recent exchanges. |
| `/stats` | Show runs and verdicts per profile. |
| `/export` | Write chats you rated `/good` to `data/dataset.jsonl` for later fine-tuning. |
| `/export all` | Write every finished chat. |

**Profile learning.** While the profile is `auto` and no `[rules]` word
matches, Lily looks at past answers to similar questions that you rated. Two
or more agreeing verdicts (good on `smart`, or bad on `fast` or `auto`) make
her ask the router for `auto:smart` or `auto:fast` instead. A profile you set
by hand always wins.

## Taxonomies

Both taxonomies run automatically after each answer, make no API calls, and
store their results in `data/lily.db`.

### Coding taxonomy

Every code block in a chat, yours or Lily's, is filed as
`group > family > language`, for example `programming > systems > rust`. The
language comes from the tag on the code fence, or is guessed from the content
of an untagged block.

Any language is stored. `config/languages.toml` only decides the tree. A
language that is not listed is kept under `unknown` and flagged, so nothing is
lost. Add it to the file and run `/code scan` to file it properly.

| Command | Effect |
|---|---|
| `/code` | Languages with block and chat counts. |
| `/code show <language> [n]` | Latest blocks (aliases work). |
| `/code scan` | Re-file every stored chat. |
| `/code export <language>` | Write matching chats to `data/code_<language>.jsonl`. |

### Subject taxonomy (7 classes)

Lily scans your message and her answer for the words in
`config/entities.toml` and files each as `class > subclass`. It also finds
plurals and phrases such as "black hole", and ignores code.

| Class | Subclasses |
|---|---|
| **entity** (living things, groups of people) | person, animal, plant, organization |
| **location** | country, city, region, water, landform, place |
| **object** | device, vehicle, tool, food, clothing |
| **literature** | genre, form, device, author |
| **science** | physics, chemistry, biology, astronomy, earth |
| **math** | arithmetic, algebra, geometry, trigonometry, calculus, statistics, linear algebra |
| **history** | era, event, civilization, institution |

This is a **word list**, so it cannot tell meanings apart ("mouse" is always a
device) and only knows the words you give it. Everyday words such as "force",
"cell" or "limit" are left out on purpose so they are not filed by accident.

| Command | Effect |
|---|---|
| `/entity` | The tree with counts. |
| `/entity classes` | List the subclasses. |
| `/entity show <class[/sub]>` | Words filed there, e.g. `/entity show science/biology`. |
| `/entity find <word>` | Latest chats that mention a word. |
| `/entity add <word> <class/sub>` | Teach a word, e.g. `/entity add force science/physics`. A new subclass name creates a new subclass. |
| `/entity remove <word>` | Remove a word you added. |
| `/entity scan` | Re-file all stored chats after changing words. |

## Updating

Only changes **merged into `main`** are pulled, so merge any open pull
request first.

### Quick update

```bash
bash ~/Terminal_Lily/scripts/update.sh
```

For a shorter command, run this once, reopen Termux, then type `lily-update`:

```bash
echo "alias lily-update='bash ~/Terminal_Lily/scripts/update.sh'" >> ~/.bashrc
```

The script:

1. stops if the folder is not a git clone or git is missing (`pkg install git`);
2. stops if you edited a tracked file, and lists the files;
3. runs `git pull --ff-only`, so it never merges or overwrites your edits;
4. prints what changed (up to 15 commits);
5. runs `pip install -r requirements.txt` only if that file changed;
6. creates `.env` from `.env.example` if you have none.

Your `.env` and `data/` are never touched, and neither are plugins you added.

**Restart Lily afterwards** (`/exit`, then `python main.py`). `/reload` only
re-reads plugins and `config/mcp_servers.toml`, not Lily's own Python code.

### Manual update with git

```bash
cd ~/Terminal_Lily
git branch --show-current                   # should say: main
git status                                  # should be clean (untracked files are fine)
git pull --ff-only                          # fast-forward to the latest main
git log --oneline -5                        # see what you now have
pip install -r requirements.txt             # only if requirements.txt changed
python -m unittest discover -s tests -t .   # optional: run the tests
```

To preview before you pull:

```bash
git fetch
git log --oneline HEAD..origin/main    # commits you do not have yet
git diff --stat HEAD origin/main       # files they touch
```

To see which version you run: `git log -1 --oneline` and `git status -sb`.

### If you edited a tracked file

A common case is a local url in `config/mcp_servers.toml`. The update stops
with "You have local changes". Set your edits aside, update, then restore them:

```bash
cd ~/Terminal_Lily
git stash                 # sets your edits aside
bash scripts/update.sh    # or: git pull --ff-only
git stash pop             # brings your edits back
```

If `git stash pop` reports a conflict, the upstream file changed where you
edited. Open the file, keep the lines you want, delete the `<<<<<<<`,
`=======` and `>>>>>>>` markers, then run `git add <file>` and
`git stash drop`. To discard your edits instead and take the GitHub version,
run `git checkout -- <file>`.

### Match GitHub exactly

Use this only when you want to **discard local edits and commits** to tracked
files. Your `.env` and `data/` are ignored by git and survive it.

```bash
cd ~/Terminal_Lily
git fetch origin
git switch main
git reset --hard origin/main      # discards local changes to tracked files
pip install -r requirements.txt
```

Then restart Lily and set your url in `config/mcp_servers.toml` again.

### After every update

1. Restart Lily.
2. Run `/tools` and check that built-ins, plugins and `lilyai__` tools loaded.
3. Check `diff .env .env.example` for new settings to add to your `.env`.
4. If you changed `config/languages.toml` or `config/entities.toml`, run
   `/code scan` and `/entity scan`.

### Troubleshooting

| What you see | Cause and fix |
|---|---|
| `not a git clone` | The folder was copied, not cloned. Clone again (see [Quick start](#quick-start)) and copy your `.env` and `data/` across. |
| `You have local changes` | You edited a tracked file. Use the stash steps above. |
| `Not possible to fast-forward` | Your local `main` has commits GitHub lacks, or the histories split. Inspect with `git log --oneline origin/main..HEAD`, save your work with `git switch -c my-work`, then use [Match GitHub exactly](#match-github-exactly). |
| `untracked working tree files would be overwritten` | A new file from GitHub has the same name as one you made. Rename yours (`mv file file.bak`) and pull again. |
| Not on `main` | `git switch main`, then update. |
| `pip install` fails | Run `pkg update && pkg upgrade`, then retry `pip install -r requirements.txt`. |
| Lily behaves like the old version | You did not restart. `/exit`, then `python main.py`. |

## Architecture

### How a message flows

```
you -> ui -> main orchestrator -> agent loop
              |- rag   (fetch relevant notes)
              |- llm   (think; may ask for a tool)
              '- tools (run it; result goes back to the llm)
           -> repeat until the llm gives a final answer
```

### Project layout

```
main.py                 entry point
config/                 settings, models, MCP servers, languages, entities, system prompt
plugins/                your own tools (one file = one tool)
scripts/                setup_termux.sh (first install), update.sh (update from GitHub)
tests/                  run: python -m unittest discover -s tests -t .
lily/                   orchestrator, agent_loop, router, state, bootstrap
lily/llm/               LLM sub-orchestrator, prompt builder, parser, profile picker
lily/llm/providers/     openai_compat.py (standard library only)
lily/tools/             Tools sub-orchestrator, registry, loader, permissions
lily/tools/builtin/     shell, read_file, write_file, web_search, termux_api, rag_search
lily/tools/mcp/         MCP client, adapter and config
lily/rag/               RAG sub-orchestrator, SQLite store, chunker, loader, retriever, ingest
lily/memory/            data layer: run log, feedback, lessons, history, summarizer,
                        profile hints, export, coding and subject taxonomies
lily/ui/                terminal loop, rich renderer, slash commands
lily/utils/             logger, errors, paths
```

## Development

- Every Python file is **120 lines or fewer** and does **one thing**. This is
  enforced by `tests/test_line_limit.py`.
- Dependencies stay few, and configuration stays in TOML so no extra parser
  is needed.
- Each layer exposes `register(lily)` in its `orchestrator.py`. The main
  orchestrator never reaches into a layer's internals.

Run the tests with:

```bash
python -m unittest discover -s tests -t .
```

## License

Released under the MIT License. See [LICENSE](LICENSE).
