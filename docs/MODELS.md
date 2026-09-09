# Model Lineup & Provider Switching

> Astral is **model-agnostic**. The agent loop, the tool registry, and the safety
> layer never change — only the brain behind them does.

Astral can talk to several backends at once and switch between them without
rewriting a single line of agent logic. Every backend is reached through the
same OpenAI-compatible chat interface, so a prompt stays a prompt no matter which
model is active.
---

## The Lineup

| # | Provider | Model | Where it runs | Best for |
|---|----------|-------|---------------|----------|
| 1 | **Groq** | `gpt-oss-120b` | Cloud | Very fast reasoning, long tool chains, snappy replies |
| 2 | **Qwen** | `Qwen 3.8 Flash` | Cloud | Balanced quality / speed / cost for everyday assistance |
| 3 | **Gemini** | `Gemini 3.6 Flash` | Cloud | Long-context drafting and summarising |
| 4 | **Local (LM Studio)** | `Qwen 3.5 4B` | Your machine | Fully offline & private work — nothing leaves the PC |

**Default:** the local `Qwen 3.5 4B` served by LM Studio through an
OpenAI-compatible endpoint (`http://localhost:1234/v1`), so Astral works even
with no internet connection.

---

## What Goes In, What Comes Out

Astral sends text to every backend. A single message can carry:

* **Prompts** - what you type into the chat loop
* **File contents** - whatever a filesystem tool just read
* **Command output** - captured stdout and stderr from `run_shell_command`
* **Search snippets** - the results SearXNG hands back

That is the whole contract today.
`llm.py` builds plain string `content` fields: it never constructs `image_url` parts, and
there is no PDF or audio pipeline anywhere in the repo. Image and document input are a
roadmap item (`v1.7` in the README), not a feature.

> So: point Astral at a screenshot and it will say it cannot see it, instead of
> pretending otherwise.

---

## Why Multiple Models?

Each backend is a different trade-off, and Astral lets you choose per task:

* **Latency** — Groq's `gpt-oss-120b` for instant answers and long tool chains.
* **Quality** — Gemini / Qwen Flash when the task needs deeper reasoning.
* **Privacy** — the local Qwen model for anything touching personal files.
* **Cost** — free-tier cloud quota for research, local inference for everything else.
* **Resilience** — if one endpoint is down or rate-limited, Astral keeps going
  with another provider instead of dead-ending the session.

---

## Switching Providers

Provider selection lives in one place: `config.py`, which reads the active
backend and its credentials from environment variables so nothing is hardcoded
in the source.

| Variable prefix | Controls |
|-----------------|----------|
| `ASTRAL_LLM_*` | Active provider, base URL, API key, model, timeout |
| `ASTRAL_GEMINI_*` | Gemini endpoint, key, model |
| `ASTRAL_GROQ_*` | Groq endpoint, key, model |
| `ASTRAL_QWEN_*` | Qwen endpoint, key, model |
| `ASTRAL_WORKSPACE` | Root folder Astral is allowed to operate in |

Set the provider, start LM Studio for the local model, and relaunch Astral —
the agent, its tools, and its confirmation rules stay exactly the same.

> Run `python -c "import config; print(config.LLM_PROVIDER)"` from the project
> root to see which backend is currently active.

---

## Live Telemetry

Every turn reports what actually happened, so switching models is measurable
rather than a guess:

```
   1,204 in  •  318 out  •  1,618 total  •  96 reasoning
    42.7 tok/s  •  7.44s  •  visible 318
```

Tokens per second, elapsed time, reasoning-token accounting, visible content
versus tool payload — all printed per response.

---

## Related

* [README](../README.md) — architecture, tools, quick start
* [Contributing Guide](../.github/CONTRIBUTING.md)
* [License](../LICENSE) — source-available, view-only
