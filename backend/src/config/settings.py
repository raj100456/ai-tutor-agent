"""
Settings — Single source of truth for all configuration.

Load order (highest priority first):
  1. Environment variables
  2. .env file
  3. config.yaml

config.yaml conventions:
  • Plain values are used as-is.
  • Keys ending in ``_env`` are resolved to the named environment variable:
      api_key_env: "OPENAI_API_KEY"  →  os.environ["OPENAI_API_KEY"]

Usage:
    from src.config.settings import get_settings
    settings = get_settings()
    cfg = settings.get_provider_config("openai")
"""
from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml
from pydantic_settings import BaseSettings, SettingsConfigDict

_CONFIG_PATH = Path(__file__).parent.parent.parent / "config.yaml"


# ── YAML helpers ────────────────────────────────────────────────────────────


def _load_yaml(path: Path = _CONFIG_PATH) -> dict[str, Any]:
    """Load config.yaml; raises a descriptive error if the file is missing."""
    if not path.exists():
        raise FileNotFoundError(
            f"\n\nConfig file not found: {path}\n"
            "Run:  cp backend/config.yaml.example backend/config.yaml\n"
            "Then customise it for your environment.\n"
        )
    with path.open(encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


def _resolve_env_refs(obj: Any) -> Any:
    """
    Recursively replace ``*_env`` keys with their environment variable values.

    Example input:
        {"api_key_env": "OPENAI_API_KEY", "model": "gpt-4o"}
    Output:
        {"api_key": "<$OPENAI_API_KEY value>", "model": "gpt-4o"}

    If the referenced environment variable is not set, the value is ``""``.
    """
    if isinstance(obj, dict):
        resolved: dict[str, Any] = {}
        for k, v in obj.items():
            if isinstance(k, str) and k.endswith("_env"):
                real_key = k[:-4]  # strip "_env" suffix
                resolved[real_key] = os.environ.get(str(v), "")
            else:
                resolved[k] = _resolve_env_refs(v)
        return resolved
    if isinstance(obj, list):
        return [_resolve_env_refs(item) for item in obj]
    return obj


# ── Settings ────────────────────────────────────────────────────────────────


class Settings(BaseSettings):
    """
    Merges config.yaml + .env + environment variables into a single object.
    All nested config is accessible via typed properties.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_nested_delimiter="__",
        extra="ignore",
    )

    _raw: dict[str, Any] = {}

    def model_post_init(self, __context: Any) -> None:  # noqa: ANN401
        object.__setattr__(self, "_raw", _load_yaml())

    # ── Top-level section accessors ──────────────────────────────────────────

    @property
    def app(self) -> dict[str, Any]:
        return self._raw.get("app", {})

    @property
    def llm(self) -> dict[str, Any]:
        return self._raw.get("llm", {})

    @property
    def graph(self) -> dict[str, Any]:
        return self._raw.get("graph", {})

    @property
    def tutor(self) -> dict[str, Any]:
        return self._raw.get("tutor", {})

    @property
    def decorators_cfg(self) -> dict[str, Any]:
        return self._raw.get("decorators", {})

    @property
    def integrations(self) -> dict[str, Any]:
        return self._raw.get("integrations", {})

    @property
    def knowledge_feed(self) -> dict[str, Any]:
        return self._raw.get("knowledge_feed", {})

    @property
    def notifier(self) -> dict[str, Any]:
        return self._raw.get("notifier", {})

    @property
    def data(self) -> dict[str, Any]:
        """Data section with env refs resolved."""
        return _resolve_env_refs(self._raw.get("data", {}))

    @property
    def security(self) -> dict[str, Any]:
        """Security section with env refs resolved."""
        return _resolve_env_refs(self._raw.get("security", {}))

    # ── LLM helpers ──────────────────────────────────────────────────────────

    def get_task_provider(self, task: str) -> str:
        """Return the configured provider name for a given task type."""
        return self.llm.get("task_providers", {}).get(task, "llamacpp")

    def get_provider_config(self, provider_name: str) -> dict[str, Any]:
        """
        Return provider config with all ``*_env`` keys resolved.
        Raises KeyError if the provider is not defined in config.yaml.
        """
        raw = self.llm.get("providers", {}).get(provider_name)
        if raw is None:
            available = list(self.llm.get("providers", {}).keys())
            raise KeyError(
                f"LLM provider '{provider_name}' not found in config.yaml → llm.providers.\n"
                f"Available providers: {available}"
            )
        return _resolve_env_refs(raw)

    def get_fallback_chain(self) -> list[str]:
        """Return the ordered list of fallback providers."""
        return self.llm.get("fallback_chain", [])

    def get_circuit_breaker_cfg(self) -> dict[str, Any]:
        return self.llm.get("circuit_breaker", {})

    # ── Integration helpers ───────────────────────────────────────────────────

    def get_enabled_integrations(self) -> list[str]:
        return self.integrations.get("enabled", [])

    def get_integration_config(self, name: str) -> dict[str, Any]:
        """
        Return integration config with env refs resolved.
        Raises KeyError if not defined.
        """
        raw = self.integrations.get(name)
        if raw is None:
            raise KeyError(
                f"Integration '{name}' not defined in config.yaml → integrations.\n"
                f"Add its config block before enabling it."
            )
        return _resolve_env_refs(raw)

    # ── Decorator helpers ─────────────────────────────────────────────────────

    def get_active_decorators(self) -> list[str]:
        return self.tutor.get("active_decorators", [])

    def get_decorator_config(self, name: str) -> dict[str, Any]:
        return self.decorators_cfg.get("available", {}).get(name, {})

    # ── Convenience properties ────────────────────────────────────────────────

    @property
    def auth_mode(self) -> str:
        return self.security.get("auth_mode", "none")

    @property
    def cors_origins(self) -> list[str]:
        return self.app.get("cors_origins", ["*"])

    @property
    def log_level(self) -> str:
        return self.app.get("log_level", "INFO")

    @property
    def environment(self) -> str:
        return os.environ.get("ENVIRONMENT", self.app.get("environment", "development"))

    @property
    def is_production(self) -> bool:
        return self.environment == "production"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached singleton Settings instance."""
    return Settings()
