import os
from typing import Optional

from langchain_openai import ChatOpenAI


class OpenRouterClient:
    """
    Client for interacting with OpenRouter API.
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("OPENROUTER_API_KEY")
        if not self.api_key:
            # Fallback to OPENAI_API_KEY if OPENROUTER_API_KEY is not set, 
            # though this class is specifically named OpenRouterClient.
            # However, the node logic seemed to treat them somewhat interchangeably 
            # or at least prioritizes OpenRouter but falls back to standard OpenAI if not present.
            # But strictly speaking, if we want an OpenRouter client, we expect OpenRouter key.
            # If the user wants to use standard OpenAI, they might use a different client or 
            # we can make this client smart enough to handle both.
            # The original code:
            # openrouter_api_key = os.environ.get("OPENROUTER_API_KEY")
            # if openrouter_api_key: ... use base_url ... else: ... use standard ...
            pass

    def get_chat_model(self, model_name: str, temperature: float = 0.0) -> ChatOpenAI:
        """
        Returns a configured ChatOpenAI instance for OpenRouter.
        If OPENROUTER_API_KEY is properly set, it configures the base_url.
        If not, it defaults to standard OpenAI behavior (which relies on OPENAI_API_KEY).
        """
        if self.api_key:
            return ChatOpenAI(
                model=model_name,
                temperature=temperature,
                api_key=self.api_key,
                base_url="https://openrouter.ai/api/v1",
            )
        
        # Fallback to standard OpenAI if no OpenRouter key is found
        # This preserves the original logic flow where if OpenRouter key wasn't present,
        # it just returned ChatOpenAI(model=...)
        return ChatOpenAI(model=model_name, temperature=temperature)
