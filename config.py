"""Konfigurasi runtime Astral.

Semua nilai dapat diganti melalui environment variable agar kredensial dan
konfigurasi mesin tidak perlu di-hardcode di source code.
"""

import os
from pathlib import Path


def _positive_float(name: str, default: float) -> float:
    try:
        value = float(os.getenv(name, str(default)))
    except ValueError:
        return default
    return value if value > 0 else default


def _positive_int(name: str, default: int) -> int:
    try:
        value = int(os.getenv(name, str(default)))
    except ValueError:
        return default
    return value if value > 0 else default


PROJECT_ROOT = Path(__file__).resolve().parent
WORKSPACE_ROOT = Path(
    os.getenv("ASTRAL_WORKSPACE", str(PROJECT_ROOT))
).expanduser().resolve()

# Additional filesystem root; defaults to the current Windows user's profile.
ASTRAL_USER_ROOT = Path(
    os.getenv("ASTRAL_USER_ROOT", str(Path.home()))
).expanduser().resolve()

ASTRAL_D_ROOT = Path(
    os.getenv("ASTRAL_D_ROOT", "D:\\")
).expanduser().resolve()

LLM_BASE_URL = os.getenv("ASTRAL_LLM_BASE_URL", "http://localhost:1234/v1")
LLM_API_KEY = os.getenv("ASTRAL_LLM_API_KEY", "lm-studio")
LLM_MODEL = os.getenv(
    "ASTRAL_LLM_MODEL", "qwen3.5-4b-uncensored-hauhaucs-aggressive"
)

# Optional hosted Gemini provider. The Gemini API exposes an OpenAI-compatible
# endpoint, so Astral can reuse the same client and tool-calling pipeline.
GEMINI_BASE_URL = os.getenv(
    "ASTRAL_GEMINI_BASE_URL",
    "https://generativelanguage.googleapis.com/v1beta/openai/",
)
GEMINI_API_KEY = os.getenv("ASTRAL_GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("ASTRAL_GEMINI_MODEL", "gemini-3.6-flash")

# Groq provides an OpenAI-compatible endpoint with fast hosted inference.
GROQ_BASE_URL = os.getenv("ASTRAL_GROQ_BASE_URL", "https://api.groq.com/openai/v1")
GROQ_API_KEY = os.getenv("ASTRAL_GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("ASTRAL_GROQ_MODEL", "openai/gpt-oss-120b")

# QwenCloud exposes an OpenAI-compatible endpoint for Qwen3.8-Flash.
QWEN_BASE_URL = os.getenv(
    "ASTRAL_QWEN_BASE_URL",
    "https://dashscope-intl.aliyuncs.com/compatible-mode/v1",
)
QWEN_API_KEY = os.getenv("ASTRAL_QWEN_API_KEY", "")
QWEN_MODEL = os.getenv("ASTRAL_QWEN_MODEL", "qwen3.8-flash")

LLM_PROVIDER = os.getenv("ASTRAL_LLM_PROVIDER", "local").strip().lower()


def get_llm_config(provider: str | None = None) -> dict[str, str]:
    """Return the configured connection settings for a supported provider."""
    selected = (provider or LLM_PROVIDER).strip().lower()
    configs = {
        "local": {
            "base_url": LLM_BASE_URL,
            "api_key": LLM_API_KEY,
            "model": LLM_MODEL,
        },
        "gemini": {
            "base_url": GEMINI_BASE_URL,
            "api_key": GEMINI_API_KEY,
            "model": GEMINI_MODEL,
        },
        "groq": {
            "base_url": GROQ_BASE_URL,
            "api_key": GROQ_API_KEY,
            "model": GROQ_MODEL,
        },
        "qwen": {
            "base_url": QWEN_BASE_URL,
            "api_key": QWEN_API_KEY,
            "model": QWEN_MODEL,
        },
    }
    if selected not in configs:
        raise ValueError(
            f"Provider tidak dikenal: {selected}. Pilih 'local', 'gemini', 'groq', atau 'qwen'."
        )
    return {"provider": selected, **configs[selected]}


# Local models can take minutes before emitting their first token.  A finite,
# configurable timeout prevents an indefinitely frozen CLI while avoiding the
# frequent ReadTimeout caused by the old short/default client timeout.
# Long-form generation can spend several minutes before finishing. Keep a
# generous default while allowing deployments to override it per environment.
LLM_TIMEOUT_SECONDS = _positive_float("ASTRAL_LLM_TIMEOUT_SECONDS", 1800.0)
LLM_MAX_TOKENS = _positive_int("ASTRAL_LLM_MAX_TOKENS", 4096)
# Hosted providers commonly enforce a tight tokens-per-minute budget. Three
# turns is enough continuity for the CLI while preventing unbounded growth.
MAX_CONTEXT_TURNS = _positive_int("ASTRAL_MAX_CONTEXT_TURNS", 3)
# Leave headroom under Groq's default 8k TPM tier when the prompt is already
# large. Override this when the account/model has a higher limit.
GROQ_MAX_TOKENS = _positive_int("ASTRAL_GROQ_MAX_TOKENS", 1200)
MAX_MEMORY_RESULTS = _positive_int("ASTRAL_MAX_MEMORY_RESULTS", 3)
MAX_MEMORY_CONTEXT_CHARS = _positive_int(
    "ASTRAL_MAX_MEMORY_CONTEXT_CHARS", 2400
)

SEARXNG_URL = os.getenv("ASTRAL_SEARXNG_URL", "http://localhost:8080/search")
SEARXNG_TIMEOUT_SECONDS = _positive_float(
    "ASTRAL_SEARXNG_TIMEOUT_SECONDS", 30.0
)

# Tool output is model context, not a terminal transcript. Keep the default
# deliberately small; callers can still opt into a larger value per machine.
MAX_TOOL_RESULT_CHARS = _positive_int("ASTRAL_MAX_TOOL_RESULT_CHARS", 3500)
MAX_HISTORY_TOOL_RESULT_CHARS = _positive_int(
    "ASTRAL_MAX_HISTORY_TOOL_RESULT_CHARS", 1400
)
COMPACT_TOOL_SCHEMAS = os.getenv("ASTRAL_COMPACT_TOOL_SCHEMAS", "1").lower() not in {
    "0", "false", "no", "off"
}
MEMORY_FILE = Path(os.getenv("ASTRAL_MEMORY_FILE", str(WORKSPACE_ROOT / "data" / "memory.json"))).expanduser().resolve()
MAX_MEMORY_ENTRIES = _positive_int("ASTRAL_MAX_MEMORY_ENTRIES", 1000)
SHELL_COMMAND_TIMEOUT_SECONDS = _positive_float(
    "ASTRAL_SHELL_COMMAND_TIMEOUT_SECONDS", 60.0
)
