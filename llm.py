import time

from openai import OpenAI

from config import GROQ_MAX_TOKENS, LLM_MAX_TOKENS


class LLMClient:
    """
    Wrapper untuk koneksi ke backend model OpenAI-compatible.

    Menangani:
    - streaming response
    - tool calling
    - usage metadata
    - generation timing
    """

    def __init__(
        self,
        base_url="http://localhost:1234/v1",
        api_key=None,
        model="qwen3.5-4b-uncensored-hauhaucs-aggressive",
        timeout=600.0
    ):
        self.base_url = base_url
        self.api_key = api_key or "lm-studio"
        self.model = model
        self.timeout = timeout
        self.is_gemini = "generativelanguage.googleapis.com" in self.base_url

        self.client = OpenAI(
            base_url=self.base_url,
            api_key=self.api_key,
            timeout=self.timeout,
            max_retries=0
        )

    def chat_stream(
        self,
        messages,
        temperature=0.4,
        tools=None
    ):
        """
        Streaming response dari backend model.

        Exception sengaja diteruskan ke Agent.
        Agent yang menangani retry dan recovery.
        """

        request_args = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            # A fixed 4096 completion budget can push Groq over its TPM limit
            # even when the generated answer would be short. Keep a smaller
            # provider-specific ceiling by default; it is configurable.
            "max_tokens": GROQ_MAX_TOKENS if "api.groq.com" in self.base_url else LLM_MAX_TOKENS,
            "stream": True,
            "stream_options": {
                "include_usage": True
            }
        }

        if tools:
            request_args["tools"] = tools

        generation_start = None

        response = self.client.chat.completions.create(
            **request_args
        )

        for chunk in response:

            if chunk.choices:
                delta = chunk.choices[0].delta

                has_generation_data = any([
                    bool(
                        getattr(
                            delta,
                            "content",
                            None
                        )
                    ),
                    bool(
                        getattr(
                            delta,
                            "reasoning_content",
                            None
                        )
                    ),
                    bool(
                        getattr(
                            delta,
                            "tool_calls",
                            None
                        )
                    )
                ])

                if (
                    has_generation_data
                    and generation_start is None
                ):
                    generation_start = time.perf_counter()

                yield {
                    "type": "delta",
                    "data": delta
                }

            if chunk.usage:

                elapsed = (
                    time.perf_counter() - generation_start
                    if generation_start is not None
                    else 0.0
                )

                yield {
                    "type": "usage",
                    "data": chunk.usage,
                    "elapsed": elapsed
                }


__all__ = ["LLMClient"]
