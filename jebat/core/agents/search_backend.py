"""
Canonical search backend for JEBAT swarm agents.

This backend prefers deterministic local-repo search and then extends to
remote search providers when runtime configuration allows it.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import re
from pathlib import Path
from typing import Any, Dict, Iterable, List
from urllib.parse import urlencode
from urllib.request import Request, urlopen

logger = logging.getLogger(__name__)


class SwarmSearchBackend:
    """Hybrid search backend for swarm agents."""

    def __init__(
        self,
        repo_root: str | Path | None = None,
        max_local_results: int = 8,
        max_remote_results: int = 5,
        remote_enabled: bool | None = None,
    ):
        self.repo_root = Path(repo_root or Path(__file__).resolve().parents[3]).resolve()
        self.max_local_results = max_local_results
        self.max_remote_results = max_remote_results
        self.searxng_base_url = os.getenv("SEARXNG_BASE_URL", "").rstrip("/")
        self.searxng_api_key = os.getenv("SEARXNG_API_KEY", "")
        self.remote_enabled = (
            remote_enabled
            if remote_enabled is not None
            else os.getenv("JEBAT_ENABLE_REMOTE_SEARCH", "1") not in {"0", "false", "False"}
        )

    async def search(self, task, agent_info: Dict[str, Any], queries: Iterable[str]) -> Dict[str, Any]:
        """Search local repo context and optional remote sources."""
        query_list = [query.strip() for query in queries if query and query.strip()]
        local_results = await self._search_local(query_list)
        remote_results = await self._search_remote(query_list)

        return {
            "backend": self._backend_label(remote_results),
            "repo_root": str(self.repo_root),
            "queries": query_list,
            "local_results": local_results,
            "remote_results": remote_results,
            "results": local_results + remote_results,
            "agent_role": agent_info.get("role", "general"),
            "task_description": getattr(task, "description", ""),
        }

    def _backend_label(self, remote_results: List[Dict[str, Any]]) -> str:
        """Summarize which backends produced results."""
        if remote_results:
            providers = sorted({result.get("source", "remote") for result in remote_results})
            return f"local+{'+'.join(providers)}"
        return "local"

    async def _search_local(self, queries: List[str]) -> List[Dict[str, Any]]:
        """Search within the local repo using ripgrep."""
        results: List[Dict[str, Any]] = []
        seen = set()

        for query in queries:
            for term in self._query_terms(query):
                matches = await self._rg_search(term)
                for match in matches:
                    key = (match["path"], match["line"])
                    if key in seen:
                        continue
                    results.append(
                        {
                            "source": "local",
                            "query": query,
                            **match,
                        }
                    )
                    seen.add(key)
                    if len(results) >= self.max_local_results:
                        return results
        return results

    async def _rg_search(self, term: str) -> List[Dict[str, Any]]:
        """Run ripgrep for a single fixed-string term."""
        process = await asyncio.create_subprocess_exec(
            "rg",
            "-n",
            "-i",
            "-F",
            "--max-count",
            "3",
            term,
            str(self.repo_root),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, _stderr = await process.communicate()
        if process.returncode not in (0, 1):
            return []

        matches: List[Dict[str, Any]] = []
        for line in stdout.decode("utf-8", errors="replace").splitlines():
            parts = line.split(":", 3)
            if len(parts) < 4:
                continue
            path, line_no, _column, snippet = parts
            matches.append(
                {
                    "path": os.path.relpath(path, self.repo_root),
                    "line": int(line_no),
                    "snippet": snippet.strip(),
                }
            )
        return matches

    async def _search_remote(self, queries: List[str]) -> List[Dict[str, Any]]:
        """Search remote sources if enabled."""
        if not self.remote_enabled or not queries:
            return []

        for provider in (self._search_searxng, self._search_ddgs, self._search_duckduckgo_instant):
            try:
                results = await provider(queries)
                if results:
                    return results[: self.max_remote_results]
            except Exception as exc:
                logger.debug("Remote search provider %s failed: %s", provider.__name__, exc)

        return []

    async def _search_searxng(self, queries: List[str]) -> List[Dict[str, Any]]:
        """Search via SearXNG when configured."""
        if not self.searxng_base_url:
            return []

        results: List[Dict[str, Any]] = []
        for query in queries[:2]:
            params = urlencode({"q": query, "format": "json"})
            url = f"{self.searxng_base_url}/search?{params}"
            headers = {"User-Agent": "JEBAT/1.0"}
            if self.searxng_api_key:
                headers["Authorization"] = f"Bearer {self.searxng_api_key}"

            payload = await asyncio.to_thread(self._http_get_json, url, headers)
            for item in payload.get("results", [])[: self.max_remote_results]:
                results.append(
                    {
                        "source": "searxng",
                        "query": query,
                        "title": item.get("title", ""),
                        "url": item.get("url", ""),
                        "snippet": item.get("content", "")[:500],
                    }
                )
        return results

    async def _search_ddgs(self, queries: List[str]) -> List[Dict[str, Any]]:
        """Search via duckduckgo-search if the optional dependency is installed."""
        try:
            from ddgs import DDGS
        except Exception:
            return []

        def run_query(query: str) -> List[Dict[str, Any]]:
            with DDGS() as ddgs:
                raw = list(ddgs.text(query, max_results=self.max_remote_results))
            return [
                {
                    "source": "ddgs",
                    "query": query,
                    "title": item.get("title", ""),
                    "url": item.get("href", ""),
                    "snippet": item.get("body", ""),
                }
                for item in raw
            ]

        results: List[Dict[str, Any]] = []
        for query in queries[:2]:
            results.extend(await asyncio.to_thread(run_query, query))
        return results

    async def _search_duckduckgo_instant(self, queries: List[str]) -> List[Dict[str, Any]]:
        """Search via DuckDuckGo Instant Answer API as a zero-dependency fallback."""
        results: List[Dict[str, Any]] = []
        for query in queries[:2]:
            params = urlencode(
                {
                    "q": query,
                    "format": "json",
                    "no_redirect": "1",
                    "no_html": "1",
                    "skip_disambig": "1",
                }
            )
            payload = await asyncio.to_thread(
                self._http_get_json,
                f"https://api.duckduckgo.com/?{params}",
                {"User-Agent": "JEBAT/1.0"},
            )
            results.extend(self._extract_duckduckgo_results(query, payload))
        return results[: self.max_remote_results]

    def _extract_duckduckgo_results(self, query: str, payload: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Normalize DuckDuckGo instant answer payload."""
        results: List[Dict[str, Any]] = []

        if payload.get("AbstractText"):
            results.append(
                {
                    "source": "duckduckgo",
                    "query": query,
                    "title": payload.get("Heading", query),
                    "url": payload.get("AbstractURL", ""),
                    "snippet": payload.get("AbstractText", ""),
                }
            )

        for topic in payload.get("RelatedTopics", []):
            if isinstance(topic, dict) and topic.get("Text"):
                results.append(
                    {
                        "source": "duckduckgo",
                        "query": query,
                        "title": topic.get("Text", "")[:80],
                        "url": topic.get("FirstURL", ""),
                        "snippet": topic.get("Text", ""),
                    }
                )
            if len(results) >= self.max_remote_results:
                break

        return results

    def _http_get_json(self, url: str, headers: Dict[str, str]) -> Dict[str, Any]:
        """HTTP JSON helper executed in a worker thread."""
        request = Request(url, headers=headers)
        with urlopen(request, timeout=10) as response:
            payload = response.read().decode("utf-8", errors="replace")
        return json.loads(payload)

    def _query_terms(self, query: str) -> List[str]:
        """Reduce a natural-language query to a few useful repo-search terms."""
        tokens = [
            token
            for token in re.findall(r"[A-Za-z0-9_.:-]{3,}", query)
            if token.lower()
            not in {
                "that",
                "this",
                "with",
                "from",
                "into",
                "about",
                "what",
                "when",
                "where",
                "which",
                "should",
                "would",
                "could",
            }
        ]

        ordered: List[str] = []
        for token in [query.strip(), *tokens]:
            normalized = token.strip()
            if not normalized or normalized in ordered:
                continue
            ordered.append(normalized)
            if len(ordered) >= 4:
                break

        return ordered
