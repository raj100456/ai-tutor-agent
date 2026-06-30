"""Google Gemini provider."""
from __future__ import annotations

from langchain_core.language_models import BaseChatModel

from .base import AbstractLLMProvider


class GoogleProvider(AbstractLLMProvider):
    def _validate(self) -> None:
        self._require("api_key")

    def build(self) -> BaseChatModel:
        from langchain_google_genai import ChatGoogleGenerativeAI

        return ChatGoogleGenerativeAI(
            google_api_key=self.config["api_key"],
            model=self.config.get("model", "gemini-2.0-flash"),
            temperature=self.config.get("temperature", 0.7),
            max_output_tokens=self.config.get("max_tokens", 4096),
            streaming=True,
        )
