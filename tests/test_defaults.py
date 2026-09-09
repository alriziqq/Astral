from agent import Agent
from config import GROQ_MAX_TOKENS, MAX_CONTEXT_TURNS, get_llm_config


def test_reasoning_is_visible_by_default():
    assert Agent().reasoning_enabled is True


def test_context_and_groq_defaults_leave_provider_headroom():
    assert MAX_CONTEXT_TURNS == 3
    assert GROQ_MAX_TOKENS == 1200


def test_qwen_provider_defaults_to_qwen38_flash():
    settings = get_llm_config("qwen")
    assert settings["model"] == "qwen3.8-flash"
    assert settings["base_url"] == "https://dashscope-intl.aliyuncs.com/compatible-mode/v1"
