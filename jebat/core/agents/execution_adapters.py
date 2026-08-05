"""
Bounded read-only execution adapters for JEBAT swarm agents.

These adapters intentionally avoid destructive actions. They only inspect the
workspace and return structured evidence that agents can use for judgment.
"""

from __future__ import annotations

import asyncio
import os
import re
from pathlib import Path
from typing import Any, Dict, Iterable, List


class BoundedExecutionAdapters:
    """Role-aware read-only adapters for repo inspection."""

    def __init__(self, repo_root: str | Path | None = None):
        self.repo_root = Path(repo_root or Path(__file__).resolve().parents[3]).resolve()

    async def run(self, role: str, task, agent_info: Dict[str, Any]) -> Dict[str, Any]:
        """Dispatch to a role adapter."""
        normalized_role = role or "general"
        params = getattr(task, "parameters", {}) or {}
        scope = params.get("agent_scope", {}) if isinstance(params, dict) else {}
        seed_text = " ".join(
            part for part in [str(getattr(task, "description", "")), str(scope.get("focus", ""))] if part
        )
        task_terms = self._extract_terms(seed_text)

        dispatch = {
            "development": self._development_adapter,
            "frontend": self._frontend_adapter,
            "database": self._database_adapter,
            "operations": self._operations_adapter,
            "security": self._security_adapter,
            "review": self._review_adapter,
            "application": self._application_adapter,
            "orchestration": self._orchestration_adapter,
            "research": self._research_adapter,
            "design": self._design_adapter,
            "strategy": self._strategy_adapter,
            "reconnaissance": self._reconnaissance_adapter,
            "defense": self._defense_adapter,
            "stability": self._stability_adapter,
            "intelligence": self._intelligence_adapter,
        }

        adapter = dispatch.get(normalized_role, self._generic_adapter)
        return await adapter(task_terms, task, agent_info)

    async def _generic_adapter(self, terms: List[str], task, agent_info: Dict[str, Any]) -> Dict[str, Any]:
        files = await self._find_files(terms[:2], limit=5)
        return {
            "adapter": "generic",
            "actions_executed": ["find candidate files"],
            "findings": files,
        }

    async def _development_adapter(self, terms: List[str], task, agent_info: Dict[str, Any]) -> Dict[str, Any]:
        files = await self._find_files(terms[:3], limit=6)
        tests = await self._find_files(["test", *terms[:2]], limit=4)
        return {
            "adapter": "development",
            "actions_executed": ["locate implementation files", "locate related tests"],
            "findings": files,
            "tests": tests,
        }

    async def _frontend_adapter(self, terms: List[str], task, agent_info: Dict[str, Any]) -> Dict[str, Any]:
        files = await self._find_globbed_files(
            ["*.tsx", "*.ts", "*.jsx", "*.js", "*.html", "*.svelte", "*.css"],
            terms[:3],
            limit=8,
        )
        return {
            "adapter": "frontend",
            "actions_executed": ["scan frontend surfaces"],
            "findings": files,
        }

    async def _database_adapter(self, terms: List[str], task, agent_info: Dict[str, Any]) -> Dict[str, Any]:
        files = await self._find_globbed_files(["*.sql", "*migration*.py"], terms[:3], limit=8)
        schema_hits = await self._rg_search(["CREATE TABLE", "ALTER TABLE", *terms[:2]], subpath="database", limit=8)
        return {
            "adapter": "database",
            "actions_executed": ["scan schema and migration files", "scan SQL statements"],
            "findings": files,
            "schema_hits": schema_hits,
        }

    async def _operations_adapter(self, terms: List[str], task, agent_info: Dict[str, Any]) -> Dict[str, Any]:
        infra_files = await self._find_globbed_files(
            [
                "Dockerfile",
                "docker-compose*.yml",
                "docker-compose*.yaml",
                "*.service",
                "*.conf",
                "*.toml",
                "*.yml",
                "*.yaml",
            ],
            terms[:2],
            limit=10,
        )
        workflow_hits = await self._find_files(["workflow", "deploy", *terms[:2]], limit=6)
        return {
            "adapter": "operations",
            "actions_executed": ["scan deployment and workflow files"],
            "findings": infra_files,
            "workflow_hits": workflow_hits,
        }

    async def _security_adapter(self, terms: List[str], task, agent_info: Dict[str, Any]) -> Dict[str, Any]:
        pattern_hits = await self._rg_search(
            [
                "password",
                "secret",
                "token",
                "shell=True",
                "subprocess",
                "eval(",
                "exec(",
                *terms[:2],
            ],
            limit=10,
        )
        return {
            "adapter": "security",
            "actions_executed": ["scan for risky patterns"],
            "findings": pattern_hits,
        }

    async def _review_adapter(self, terms: List[str], task, agent_info: Dict[str, Any]) -> Dict[str, Any]:
        tests = await self._find_files(["test", *terms[:2]], limit=8)
        docs = await self._find_globbed_files(["*.md"], terms[:2], limit=6)
        return {
            "adapter": "review",
            "actions_executed": ["scan test coverage", "scan nearby docs"],
            "tests": tests,
            "docs": docs,
        }

    async def _application_adapter(self, terms: List[str], task, agent_info: Dict[str, Any]) -> Dict[str, Any]:
        files = await self._find_files(terms[:3], limit=10)
        categorized = self._categorize_paths([item["path"] for item in files])
        return {
            "adapter": "application",
            "actions_executed": ["scan cross-layer files"],
            "findings": files,
            "layers": categorized,
        }

    async def _orchestration_adapter(self, terms: List[str], task, agent_info: Dict[str, Any]) -> Dict[str, Any]:
        files = await self._find_files(["orchestrator", "workflow", *terms[:2]], limit=8)
        return {
            "adapter": "orchestration",
            "actions_executed": ["scan orchestration and workflow surfaces"],
            "findings": files,
        }

    async def _research_adapter(self, terms: List[str], task, agent_info: Dict[str, Any]) -> Dict[str, Any]:
        docs = await self._find_globbed_files(["*.md"], terms[:3], limit=8)
        return {
            "adapter": "research",
            "actions_executed": ["scan repo documentation"],
            "findings": docs,
        }

    async def _design_adapter(self, terms: List[str], task, agent_info: Dict[str, Any]) -> Dict[str, Any]:
        design_hits = await self._find_files(["DESIGN", "ui", "ux", *terms[:2]], limit=8)
        return {
            "adapter": "design",
            "actions_executed": ["scan design-related files"],
            "findings": design_hits,
        }

    async def _strategy_adapter(self, terms: List[str], task, agent_info: Dict[str, Any]) -> Dict[str, Any]:
        findings = await self._find_files(["ROADMAP", "ARCHITECTURE", "plan", *terms[:2]], limit=8)
        return {
            "adapter": "strategy",
            "actions_executed": ["scan roadmap and architecture surfaces"],
            "findings": findings,
        }

    async def _reconnaissance_adapter(self, terms: List[str], task, agent_info: Dict[str, Any]) -> Dict[str, Any]:
        findings = await self._rg_search(["TODO", "FIXME", "search", "investigate", *terms[:2]], limit=10)
        return {
            "adapter": "reconnaissance",
            "actions_executed": ["scan for discovery signals and unresolved work"],
            "findings": findings,
        }

    async def _defense_adapter(self, terms: List[str], task, agent_info: Dict[str, Any]) -> Dict[str, Any]:
        findings = await self._rg_search(
            ["password", "secret", "token", "requirepass", "secure", "harden", *terms[:2]],
            limit=10,
        )
        return {
            "adapter": "defense",
            "actions_executed": ["scan defensive and hardening signals"],
            "findings": findings,
        }

    async def _stability_adapter(self, terms: List[str], task, agent_info: Dict[str, Any]) -> Dict[str, Any]:
        tests = await self._find_files(["test", "verify", "checklist", *terms[:2]], limit=8)
        return {
            "adapter": "stability",
            "actions_executed": ["scan validation and reliability surfaces"],
            "findings": tests,
        }

    async def _intelligence_adapter(self, terms: List[str], task, agent_info: Dict[str, Any]) -> Dict[str, Any]:
        findings = await self._find_files(["agent", "router", "skill", "intent", *terms[:2]], limit=10)
        return {
            "adapter": "intelligence",
            "actions_executed": ["scan routing, skill, and agent context surfaces"],
            "findings": findings,
        }

    async def _find_files(self, terms: Iterable[str], limit: int = 8) -> List[Dict[str, Any]]:
        """Find files whose names or paths match any of the terms."""
        process = await asyncio.create_subprocess_exec(
            "rg",
            "--files",
            str(self.repo_root),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, _stderr = await process.communicate()
        if process.returncode != 0:
            return []

        paths = stdout.decode("utf-8", errors="replace").splitlines()
        matches: List[Dict[str, Any]] = []
        lowered_terms = [term.lower() for term in terms if term]

        for path in paths:
            relative = os.path.relpath(path, self.repo_root)
            haystack = relative.lower()
            if lowered_terms and not any(term in haystack for term in lowered_terms):
                continue
            matches.append({"path": relative})
            if len(matches) >= limit:
                break
        return matches

    async def _find_globbed_files(
        self,
        globs: Iterable[str],
        terms: Iterable[str],
        limit: int = 8,
    ) -> List[Dict[str, Any]]:
        """Find files by glob and optional term filtering."""
        lowered_terms = [term.lower() for term in terms if term]
        matches: List[Dict[str, Any]] = []

        for pattern in globs:
            for path in self.repo_root.rglob(pattern):
                if not path.is_file():
                    continue
                relative = os.path.relpath(path, self.repo_root)
                haystack = relative.lower()
                if lowered_terms and not any(term in haystack for term in lowered_terms):
                    continue
                matches.append({"path": relative})
                if len(matches) >= limit:
                    return matches
        return matches

    async def _rg_search(
        self,
        terms: Iterable[str],
        *,
        subpath: str | None = None,
        limit: int = 8,
    ) -> List[Dict[str, Any]]:
        """Run fixed-string ripgrep searches and collect bounded hits."""
        search_root = self.repo_root / subpath if subpath else self.repo_root
        results: List[Dict[str, Any]] = []
        seen = set()

        for term in terms:
            normalized = str(term).strip()
            if not normalized:
                continue
            process = await asyncio.create_subprocess_exec(
                "rg",
                "-n",
                "-i",
                "-F",
                "--max-count",
                "3",
                normalized,
                str(search_root),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, _stderr = await process.communicate()
            if process.returncode not in (0, 1):
                continue

            for line in stdout.decode("utf-8", errors="replace").splitlines():
                parts = line.split(":", 3)
                if len(parts) < 4:
                    continue
                path, line_no, _column, snippet = parts
                relative = os.path.relpath(path, self.repo_root)
                key = (relative, line_no)
                if key in seen:
                    continue
                results.append(
                    {
                        "term": normalized,
                        "path": relative,
                        "line": int(line_no),
                        "snippet": snippet.strip(),
                    }
                )
                seen.add(key)
                if len(results) >= limit:
                    return results
        return results

    def _extract_terms(self, text: str) -> List[str]:
        """Extract a few useful search terms from the task text."""
        terms = []
        for token in re.findall(r"[A-Za-z0-9_.:-]{3,}", text):
            lowered = token.lower()
            if lowered in {"with", "from", "that", "this", "should", "would", "could"}:
                continue
            if lowered not in terms:
                terms.append(lowered)
            if len(terms) >= 6:
                break
        return terms

    def _categorize_paths(self, paths: Iterable[str]) -> Dict[str, int]:
        """Count rough layer distribution from path strings."""
        counters = {"database": 0, "api": 0, "web": 0, "docs": 0, "other": 0}
        for path in paths:
            lowered = path.lower()
            if "database" in lowered or lowered.endswith(".sql"):
                counters["database"] += 1
            elif "/services/api/" in lowered or "/api/" in lowered:
                counters["api"] += 1
            elif "/webui/" in lowered or "/web/" in lowered or lowered.endswith((".tsx", ".jsx", ".html", ".css")):
                counters["web"] += 1
            elif lowered.endswith(".md"):
                counters["docs"] += 1
            else:
                counters["other"] += 1
        return counters
