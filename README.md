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

### LilyAi MCP

Only the Streamable HTTP transport is supported. Two places hold the setup:

- `config/mcp_servers.toml` holds the server **url** and the **name of the
  variable** that has the key. Never put the key itself in this file.
- `.env` holds the key itself, in `MCP_API_KEYS`.

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

Then type `/reload` and `/tools`. Its tools appear as `lilyai__<tool>`.

- `MCP_API_KEYS` must hold **one** key. Lily sends it as `Bearer <value>`, so a
  comma-separated list will be rejected.
- The url is used exactly as written. Leave out `/mcp` and you will likely get
  `HTTP 404`. A wrong or missing key gives `HTTP 401`. "Cannot reach the MCP
  server" means a wrong host or no network.
- Old setups used `LILYAI_MCP_TOKEN`. Rename it to `MCP_API_KEYS` in `.env`, or
  keep your own name and set `auth_env` to it.

## Updating (Termux)

Update your local Lily to the latest version on GitHub. Only changes that are
**merged into `main`** are pulled, so merge any pull request first.

### The short way

```bash
bash ~/Terminal_Lily/scripts/update.sh
```

For a short command, run this once and reopen Termux, then type `lily-update`:

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

Your `.env`, `data/` (`lily.db`, `rag.db`) and `plugins/` files you added are
never touched, because git ignores them or does not track them.

**Restart Lily afterwards** (`/exit`, then `python main.py`). `/reload` only
re-reads plugins and `config/mcp_servers.toml`. It does not reload Lily's own
Python code.

### The same thing by hand (git pull)

```bash
cd ~/Terminal_Lily
git branch --show-current     # should say: main
git status                    # should say: nothing to commit (untracked files are fine)
git pull --ff-only            # fetch and fast-forward to the latest main
git log --oneline -5          # see what you now have
pip install -r requirements.txt   # only needed if requirements.txt changed
python -m unittest discover -s tests -t .   # optional: run the tests
```

Check what changed before you pull, if you like:

```bash
git fetch
git log --oneline HEAD..origin/main    # commits you do not have yet
git diff --stat HEAD origin/main       # files they touch
```

Check which version you run: `git log -1 --oneline` and `git status -sb`.

### Update after you edited a tracked file

A common case is a local url in `config/mcp_servers.toml`. The update stops
with "You have local changes". Park your edits, update, then put them back:

```bash
cd ~/Terminal_Lily
git stash                     # sets your edits aside
bash scripts/update.sh        # or: git pull --ff-only
git stash pop                 # brings your edits back
```

If `git stash pop` reports a conflict, the upstream file changed in the same
place you edited. Open the file, keep the lines you want and delete the
`<<<<<<<`, `=======` and `>>>>>>>` markers, then run `git add <file>` and
`git stash drop`.

If you want to throw your edits away and use the file from GitHub:
`git checkout -- <file>`.

### Troubleshooting

| What you see | What it means and what to do |
|---|---|
| `not a git clone` | The folder was copied, not cloned. Clone again (see Quick start) and copy your `.env` and `data/` across. |
| `You have local changes` | You edited a tracked file. Use the stash steps above. |
| `Not possible to fast-forward` | Your local `main` has commits GitHub does not, or the two histories split. Look with `git log --oneline origin/main..HEAD`. Keep your work with `git switch -c my-work` first, then continue below. |
| `untracked working tree files would be overwritten` | A new file from GitHub has the same name as a file you made. Rename yours (`mv file file.bak`), then pull again. |
| `You are not on main` | `git switch main`, then update. |
| `pip install` fails | Run `pkg update && pkg upgrade`, then `pip install -r requirements.txt` again. |
| Lily acts like the old version | You did not restart. `/exit`, then `python main.py`. |
| New setting missing in `.env` | `.env` is never overwritten. Compare with `.env.example` and copy the new lines: `diff .env .env.example`. |

### Make your local Lily match GitHub exactly

Use this only when you want to **discard local edits and commits** to tracked
files. Your `.env` and `data/` are ignored by git and survive it.

```bash
cd ~/Terminal_Lily
git fetch origin
git switch main
git reset --hard origin/main      # throws away local changes to tracked files
pip install -r requirements.txt
```

Then restart Lily, and set your url in `config/mcp_servers.toml` again.

### After every update

1. Restart Lily (`/exit`, `python main.py`).
2. Run `/tools` and check that built-ins, plugins and `lilyai__` tools loaded.
3. If a new setting appeared, add it to your `.env` (see `.env.example`).
4. If you added words to `config/languages.toml` or `config/entities.toml`, run
   `/code scan` and `/entity scan` to re-file stored chats.

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
language tag on the code fence, or guesses an untagged block from its
content), and the code is stored in `data/lily.db`.

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

## Taxonomy of things, subjects and computing (9 classes)

Everything else Lily hears about is sorted into nine classes, each with basic
subclasses:

| Class | Subclasses |
|---|---|
| **entity** (living things, groups of people) | person, animal, plant, organization |
| **location** | country, city, region, water, landform, place |
| **object** | device, vehicle, tool, food, clothing |
| **literature** | genre, form, device, author |
| **science** | physics, chemistry, biology, astronomy, earth |
| **math** | arithmetic, algebra, geometry, trigonometry, calculus, statistics, linear algebra |
| **history** | era, event, civilization, institution |
| **computing** (computer science) | algorithm, data structure, os, network, database, ai, security, hardware, theory |
| **programming** | concept, paradigm, practice, tool, web, language |

**Code vs. words about code.** The coding taxonomy above files the code blocks
themselves, by language (`/code`). The `computing` and `programming` classes
file the words you write in sentences, such as "recursion", "linked list" or
"python". Code blocks are ignored here, so the two never double count.

After each answer Lily scans your message and her answer for the words listed in
`config/entities.toml` and files each one as `class > subclass` (it also finds
plurals and phrases like "black hole", and ignores code). No API calls. It is a
**word list**, so it cannot tell meanings apart ("mouse" is always a device) and
it only knows the words you give it. The subject classes leave out everyday
words such as "force", "cell", "function" or "limit" on purpose, so they are
not filed by accident.

- `/entity` shows the tree with counts, `/entity classes` lists the subclasses.
- `/entity show <class[/sub]>` lists the words filed there, for example
  `/entity show science/biology` or `/entity show computing/data structure`.
- `/entity find <word>` shows the latest chats that mention a word.
- `/entity add <word> <class/sub>` teaches her a word, for example
  `/entity add seize entity/person` or `/entity add force science/physics`.
  Subclasses are free (spaces are fine): a new name makes a new subclass.
  `/entity remove <word>` removes one you added.
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
