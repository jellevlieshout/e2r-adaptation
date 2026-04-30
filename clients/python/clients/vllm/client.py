import base64
import os
from typing import Optional

from langchain_openai import ChatOpenAI


class VLLMClient:
    """
    Client for an OpenAI-compatible vLLM endpoint behind ngrok HTTP basic auth.

    Used for the RQ1 open-weights baseline running on the UPM A100 cluster.
    See scripts/UPM_VLLM_README.md for how the endpoint is provisioned and why
    the URL rotates on every pod restart.

    Configured from env:
        VLLM_BASE_URL    full URL ending in `/v1`, e.g.
                         "https://kristin-caissoned-nonfervently.ngrok-free.dev/v1"
        VLLM_BASIC_AUTH  either pre-computed `Basic <base64(user:pass)>`,
                         or raw `user:pass` (this client will base64-encode it).
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        basic_auth: Optional[str] = None,
    ):
        self.base_url = base_url or os.environ.get("VLLM_BASE_URL", "")
        raw_auth = basic_auth if basic_auth is not None else os.environ.get("VLLM_BASIC_AUTH", "")
        self.auth_header = self._normalize_auth(raw_auth)

    @staticmethod
    def _normalize_auth(value: str) -> str:
        if not value:
            return ""
        if value.lower().startswith("basic "):
            return value
        if ":" in value:
            encoded = base64.b64encode(value.encode("utf-8")).decode("ascii")
            return f"Basic {encoded}"
        # Already base64-encoded user:pass without the "Basic " prefix.
        return f"Basic {value}"

    def get_chat_model(self, model_name: str, temperature: float = 0.0, max_tokens: int = 2000) -> ChatOpenAI:
        if not self.base_url:
            raise RuntimeError(
                "VLLM_BASE_URL is not set — cannot construct vLLM chat model. "
                "Set it to the rotating ngrok URL printed by upm_vllm_startup.sh."
            )

        kwargs = {
            "model": model_name,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "base_url": self.base_url,
            # vLLM ignores api_key but langchain-openai requires a non-empty value.
            "api_key": "vllm",
        }
        if self.auth_header:
            kwargs["default_headers"] = {"Authorization": self.auth_header}

        return ChatOpenAI(**kwargs)
