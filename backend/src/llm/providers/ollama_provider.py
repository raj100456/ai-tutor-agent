"""Ollama provider — local inference via Ollama server."""
from __future__ import annotations

from langchain_core.language_models import BaseChatModel

from .base import AbstractLLMProvider


class OllamaProvider(AbstractLLMProvider):
    def _validate(self) -> None:
        self._require("model")

    def build(self) -> BaseChatModel:
        from langchain_ollama import ChatOllama

        return ChatOllama(
            base_url=self.config.get("base_url", "http://localhost:11434"),
            model=self.config["model"],
            temperature=self.config.get("temperature", 0.7),
            num_predict=self.config.get("max_tokens", 2048),
        )
