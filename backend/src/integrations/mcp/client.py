"""MCP (Model Context Protocol) integration — load any MCP server as LangChain tools."""
from __future__ import annotations

import logging
from typing import Any

from src.integrations.base import BaseIntegration
from src.integrations.registry import IntegrationRegistry

logger = logging.getLogger(__name__)


class MCPIntegration(BaseIntegration):
    """
    Generic MCP server integration.
    Wraps an MCP server process and exposes its tools as LangChain BaseTool objects.

    Config keys (config.yaml → integrations.<name>):
      server_command: list[str]   — command to launch the MCP server
      server_env: dict            — environment variable overrides (with *_env resolution)
      tools: list[str]            — optional whitelist of tool names to expose
    """

    _tools: list[Any] = []

    async def initialize(self) -> None:
        self._require("server_command")
        try:
            from langchain_mcp_adapters.client import MultiServerMCPClient
        except ImportError as exc:
            raise ImportError(
                "langchain-mcp-adapters is required for MCP integrations.\n"
                "Run: uv add langchain-mcp-adapters"
            ) from exc

        command: list[str] = self.config["server_command"]
        server_env: dict[str, str] = self.config.get("server_env", {})
        tool_filter: list[str] = self.config.get("tools", [])

        server_name = self.config.get("description", command[0])

        self._client = MultiServerMCPClient(
            {server_name: {"command": command[0], "args": command[1:], "env": server_env}}
        )
        all_tools = await self._client.get_tools()

        if tool_filter:
            self._tools = [t for t in all_tools if t.name in tool_filter]
        else:
            self._tools = list(all_tools)

        self._mark_ready()
        logger.info(
            "MCP integration ready: %s tools loaded from '%s'",
            len(self._tools),
            server_name,
        )

    async def shutdown(self) -> None:
        if hasattr(self, "_client"):
            await self._client.__aexit__(None, None, None)

    @property
    def tools(self) -> list[Any]:
        """Return LangChain-compatible tools for use in a graph node or agent."""
        return self._tools


# ── Register named MCP integrations ──────────────────────────────────────────
# Each one maps to its own config block in config.yaml → integrations.

@IntegrationRegistry.register("mcp_web_search")
class MCPWebSearchIntegration(MCPIntegration):
    """Brave Search MCP server."""

@IntegrationRegistry.register("mcp_github")
class MCPGitHubIntegration(MCPIntegration):
    """GitHub MCP server."""

@IntegrationRegistry.register("mcp_filesystem")
class MCPFilesystemIntegration(MCPIntegration):
    """Local filesystem MCP server."""
