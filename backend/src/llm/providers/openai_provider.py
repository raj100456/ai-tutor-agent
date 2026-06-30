"""OpenAI provider."""
from __future__ import annotations

from langchain_core.language_models import BaseChatModel

from .base import AbstractLLMProvider


class OpenAIProvider(AbstractLLMProvider):
    def _validate(self) -> None:
        self._require("api_key")

    def build(self) -> BaseChatModel:
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(
            api_key=self.config["api_key"],
            model=self.config.get("model", "gpt-4o"),
            temperature=self.config.get("temperature", 0.7),
            max_tokens=self.config.get("max_tokens", 4096),
            streaming=True,
        )
