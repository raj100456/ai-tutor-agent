"""
Knowledge feed node — fetches and surfaces relevant technical content.

Sources configured in config.yaml → knowledge_feed.sources:
  • Hacker News top stories (filtered by keywords)
  • GitHub Trending (by language)
  • RSS feeds (optional)

If MCP web-search is enabled in integrations, it is also used.
Populates state['knowledge_items'].
"""
from __future__ import annotations

import logging
from typing import Any

import httpx
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig

from src.config.settings import get_settings
from src.graph.state import TutorState
from src.llm.factory import get_llm

logger = logging.getLogger(__name__)

_FEED_SYSTEM = """You are a technical content curator for a senior software engineer.
Summarise the following raw feed items into concise, actionable insights.
Focus on relevance to system design, algorithms, and engineering best practices.
Format as a brief numbered list — 3-5 items max, each 1-2 sentences."""


async def knowledge_feed_node(state: TutorState, config: RunnableConfig) -> dict[str, Any]:
    """Fetch latest technical content relevant to the user's topics."""
    settings = get_settings()
    sources = settings.knowledge_feed.get("sources", [])

    raw_items: list[str] = []

    for source in sources:
        if not source.get("enabled", False):
            continue
        try:
            items = await _fetch_source(source)
            raw_items.extend(items)
        except Exception as exc:
            logger.warning("Feed source '%s' failed: %s", source.get("type"), exc)

    if not raw_items:
        return {"knowledge_items": []}

    # Summarise with LLM
    llm = get_llm("knowledge_feed")
    summary = ""
    try:
        joined = "\n".join(f"- {item}" for item in raw_items[:20])
        response = await llm.ainvoke(
            [
                SystemMessage(content=_FEED_SYSTEM),
                HumanMessage(content=joined),
            ],
            config=config,
        )
        summary = str(response.content).strip()
    except Exception as exc:
        logger.error("Feed summarisation failed: %s", exc)
        summary = "\n".join(raw_items[:5])

    return {
        "knowledge_items": [{"summary": summary, "raw": raw_items[:10]}]
    }


async def _fetch_source(source: dict[str, Any]) -> list[str]:
    source_type = source.get("type")

    if source_type == "hackernews":
        return await _fetch_hackernews(
            keywords=source.get("keywords", []),
            max_items=source.get("max_items", 10),
        )
    if source_type == "github_trending":
        return await _fetch_github_trending(
            language=source.get("language", "python"),
            since=source.get("since", "daily"),
        )
    return []


async def _fetch_hackernews(keywords: list[str], max_items: int) -> list[str]:
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(
            "https://hacker-news.firebaseio.com/v0/topstories.json"
        )
        resp.raise_for_status()
        story_ids = resp.json()[:50]

        results: list[str] = []
        for sid in story_ids:
            if len(results) >= max_items:
                break
            try:
                item_resp = await client.get(
                    f"https://hacker-news.firebaseio.com/v0/item/{sid}.json"
                )
                item = item_resp.json()
                title = item.get("title", "")
                url = item.get("url", "")
                if keywords and not any(kw.lower() in title.lower() for kw in keywords):
                    continue
                results.append(f"{title} — {url}" if url else title)
            except Exception:
                continue

        return results


async def _fetch_github_trending(language: str, since: str) -> list[str]:
    # GitHub doesn't have an official trending API; use the web page via scraping
    # or a third-party service. Here we use a public GitHub trending mirror.
    url = f"https://github.com/trending/{language}?since={since}"
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(url, headers={"User-Agent": "PersonalAITutor/1.0"})
        resp.raise_for_status()
        # Very basic extraction — returns up to 5 repo names from the HTML
        lines = [
            line.strip()
            for line in resp.text.split("\n")
            if 'h2 class="h3 lh-condensed"' in line or ("/" in line and "class" not in line)
        ]
        return [ln.strip() for ln in lines if ln.strip()][:5]
