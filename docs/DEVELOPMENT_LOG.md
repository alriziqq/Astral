# Development Log

> How Astral grew from one Python script into a local-first agent.
> This is kept as a working record — what was added, what was refactored, and what
> was deliberately dropped.

Companion docs: [README](../README.md) · [Model lineup](MODELS.md) ·
[Contributing](../.github/CONTRIBUTING.md) · [License](../LICENSE)

---

## At a glance

| | |
|---|---|
| Project line | Astral 1.x |
| Language | Python 3, Windows-desktop first |
| Model backends | Local (LM Studio), Gemini, Groq, Qwen — switchable at runtime |
| Tools | 6 — applications, filesystem, memory, planner, searxng, shell |
| Tests | 8 pytest modules (safety, tools, UI, context budget) |
| Runtime state | Local JSON under `data/`, never committed |
| License | Source-available, view-only (not open source) |
| Started | 26 July 2026 |

---

## Version history

### 1.0 — Prototype: the harness

The first proof that an LLM could actually *do* something on a machine instead of
just describing it.

* Astral as a single Python script
* Connection to the LM Studio API over HTTP/REST
* Basic validation that the components could talk to each other

Deliberately minimal. No architecture yet — just a loop that worked.

### 1.1 — Modular architecture

* Responsibilities split into separate modules
* `agent.py` — core agent logic
* `llm.py` — model transport
* `Astral.py` — application entry point

Motivation: readability and maintainability. The tool loop became something you
could extend without rewriting the whole file.

### 1.2 — Internet search (SearXNG)

* `searxng_search()` — real-time web results inside the agent loop
* Up to 20 results, with language and time filters
* New module `tools/searxng.py`, HTTP via `requests`
* Returns a list of dicts: `title`, `url`, `content`

SearXNG is self-hosted in a Docker container, so the assistant can search the web
without routing the query through a third-party tracker.

### 1.3 — Refactor & cleanup

* Refactoring for maintainability
* Performance optimisation
* Structural cleanup of the early prototype code

### 1.4 — Filesystem tools

* File and directory operations scoped to the workspace: read, write, list,
  create, delete, move
* Path handling built around explicit allowed roots

This is the point where Astral stopped being "a chatbot with HTTP access" and
started being an agent that can touch a real environment.

### 1.5 — Windows integration & long-term memory

Three new tools, focused on safe and integrated Windows desktop operation:

* **applications** — launch, inspect, and close running processes (by PID or
  executable name)
* **shell command execution** — PowerShell against the workspace directory, with a
  configurable timeout
* **long-term memory** — persistent local memory store so context survives restarts

### 1.6 – 1.8

No entries were recorded for these numbers in the original log.

### 1.9 — Multi-provider model support

The original log entry described a standalone `tools/ai_api.py` with an
`AIAPIClient` class, a `call_ai` command, and a matching test file.

**Re-checked against the source in this repository: that design was not kept.**
Provider support ships today as:

* one OpenAI-compatible transport in `llm.py`, used by every backend — streaming,
  tool calling, usage metadata, and generation timing all live there
* provider settings in `config.py`, all read from environment variables:
  `ASTRAL_LLM_*`, `ASTRAL_GEMINI_*`, `ASTRAL_GROQ_*`, `ASTRAL_QWEN_*`
* live switching from the chat prompt: `/model local | gemini | groq | qwen`
* default backend is the local model served by LM Studio, so Astral still runs with
  no internet connection at all
* API keys default to empty strings and are expected to come from the environment —
  nothing secret is hardcoded

The old note "HTTP/JSON only, no streaming support" is outdated for the same reason.
The current model table lives in [docs/MODELS.md](MODELS.md).

### Later additions (present in the code, not separately logged)

* **Planner and context budget** — `tools/planner.py`, `MAX_CONTEXT_TOKENS`,
  `MAX_HISTORY_MESSAGES`, and an optional compact tool-schema mode
* **Permission gate** — `/permissions on|off`; file writes and shell execution
  require confirmation through the CLI before they run
* **Reasoning controls** — `/thinking`, `/reasoning`, `ASTRAL_REASONING_AUTO`,
  `ASTRAL_SHOW_REASONING`, plus provider-specific budgets (e.g. Groq max tokens)
* **Console UI** — `ui.py` (Rich-based) and `astral.bat`, which starts Docker
  Desktop and the SearXNG container before launching the agent

---

## Decisions that were reversed

| Was | Now | Why |
|---|---|---|
| `tools/ai_api.py` + `call_ai` command | single `llm.py` client, `/model` switch | one transport for every OpenAI-compatible endpoint is less code and fewer bugs |
| MIT license header in README | source-available, view-only `LICENSE` | the project is published as a portfolio piece, not as reusable open source |
| `data/*.json` in the working tree | fully gitignored, auto-created on first run | memory, todos, and calendar are personal state |
| ad-hoc test folders in the repo root | ignored (`.pytest-tmp*/`, caches) | keep the tree reviewable |

---

## Open items

* Complete API documentation for every tool
* Broader pytest coverage, including outside a single machine
* Version numbering — the log jumps 1.5 → 1.9; worth either filling in or
  renumbering before a 2.0

---

## Note on this file

Rebuilt from `development_log.txt` (123 lines, Indonesian, "Versi: 1.5" header with a
later v1.9 section appended). Every claim here was checked against the source in this
repository, and stale entries are marked as such above rather than quietly copied.

Dates are intentionally absent: the original log never recorded them, and inventing a
timeline for a portfolio project would be worse than having none.
