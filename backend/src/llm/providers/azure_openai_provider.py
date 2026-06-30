"""Azure OpenAI provider."""
from __future__ import annotations

from langchain_core.language_models import BaseChatModel

from .base import AbstractLLMProvider


class AzureOpenAIProvider(AbstractLLMProvider):
    def _validate(self) -> None:
        self._require("api_key", "endpoint", "deployment")

    def build(self) -> BaseChatModel:
        from langchain_openai import AzureChatOpenAI

        return AzureChatOpenAI(
            api_key=self.config["api_key"],
            azure_endpoint=self.config["endpoint"],
            azure_deployment=self.config["deployment"],
            api_version=self.config.get("api_version", "2024-08-01-preview"),
            temperature=self.config.get("temperature", 0.7),
            max_tokens=self.config.get("max_tokens", 4096),
            streaming=True,
        )
