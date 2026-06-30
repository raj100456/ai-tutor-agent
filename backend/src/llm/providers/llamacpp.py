"""
LlamaCpp provider — local inference via llama-cpp-python.

Installation (macOS / Apple Silicon with Metal GPU):
    CMAKE_ARGS="-DLLAMA_METAL=on" uv add llama-cpp-python

Installation (CUDA):
    CMAKE_ARGS="-DLLAMA_CUDA=on" uv add llama-cpp-python

CPU only:
    uv add llama-cpp-python

Download a model (example):
    mkdir -p backend/models
    curl -L -o backend/models/llama-3.2-3b-instruct.Q4_K_M.gguf \\
        https://huggingface.co/bartowski/Meta-Llama-3.2-3B-Instruct-GGUF/resolve/main/Meta-Llama-3.2-3B-Instruct-Q4_K_M.gguf
"""
from __future__ import annotations

from typing import Any

from langchain_core.language_models import BaseChatModel

from .base import AbstractLLMProvider


class LlamaCppProvider(AbstractLLMProvider):
    """Local LLM via llama-cpp-python (GGUF models)."""

    def _validate(self) -> None:
        self._require("model_path")

    def build(self) -> BaseChatModel:
        try:
            from langchain_community.chat_models import ChatLlamaCpp
        except ImportError as exc:
            raise ImportError(
                "langchain-community is required for LlamaCpp.\n"
                "Run: uv add langchain-community llama-cpp-python"
            ) from exc

        return ChatLlamaCpp(
            model_path=self.config["model_path"],
            n_ctx=self.config.get("n_ctx", 4096),
            n_gpu_layers=self.config.get("n_gpu_layers", -1),
            n_batch=self.config.get("n_batch", 512),
            temperature=self.config.get("temperature", 0.7),
            max_tokens=self.config.get("max_tokens", 2048),
            verbose=self.config.get("verbose", False),
            chat_format=self.config.get("chat_format", "llama-3"),
            streaming=True,
        )
