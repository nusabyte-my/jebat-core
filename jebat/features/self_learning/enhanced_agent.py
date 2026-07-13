"""
JEBAT Coding Agent — Enhanced with Branch Agents, Multi-Orchestration, Loop Optimizations.

New Features:
- Branch-to-Agent: Spawn agents on git branches for parallel work
- Multi-Orchestration: Parallel agent swarms with consensus/voting
- Loop Optimizations: Smart iteration limits, early exit, cost tracking
- Agent Branching: Fork agents with inherited context
- Spec-Driven Development: /spec command for design→code workflow
- Cost Tracking: Token/cost budgets with alerts
- Skill Marketplace: Dynamic skill loading
- Agent Memory: Cross-session learning
"""

from __future__ import annotations

import asyncio
import json
import os
import shutil
import subprocess
import sys
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

# Rich formatting
try:
    from rich.console import Console
    from rich.live import Live
    from rich.markdown import Markdown
    from rich.panel import Panel
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from rich.spinner import Spinner
    from rich.syntax import Syntax
    from rich.table import Table
    from rich.text import Text

    RICH_AVAILABLE = True
    console = Console()
except ImportError:
    RICH_AVAILABLE = False
    console = None

# Prompt toolkit for interactive input
try:
    from prompt_toolkit import PromptSession
    from prompt_toolkit.history import FileHistory

    PROMPT_TOOLKIT_AVAILABLE = True
except ImportError:
    PROMPT_TOOLKIT_AVAILABLE = False


# ── Enhanced Enums & Types ───────────────────────────────────────────────


class OrchestrationMode(str, Enum):
    SEQUENTIAL = "sequential"      # Agents run one after another
    PARALLEL = "parallel"          # All agents run simultaneously
    CONSENSUS = "consensus"        # Run multiple, vote on best result
    PIPELINE = "pipeline"          # Chain agents (output of A → input of B)
    COMPETITIVE = "competitive"    # Run multiple, pick best by evaluation


class AgentBranchStrategy(str, Enum):
    NEW_BRANCH = "new_branch"           # Create new git branch for agent work
    WORKTREE = "worktree"               # Use git worktree for isolation
    STASH = "stash"                     # Stash current, apply agent changes
    INLINE = "inline"                   # Work directly on current branch


class LoopExitCondition(str, Enum):
    MAX_ITERATIONS = "max_iterations"
    TOKEN_BUDGET = "token_budget"
    COST_BUDGET = "cost_budget"
    TIME_BUDGET = "time_budget"
    CONVERGENCE = "convergence"         # Output stops changing significantly
    GOAL_ACHIEVED = "goal_achieved"     # Explicit goal completion signal
    ERROR_THRESHOLD = "error_threshold" # Too many errors


@dataclass
class AgentSpec:
    """Specification for an agent branch/task."""
    name: str
    role: str
    task: str
    branch_strategy: AgentBranchStrategy = AgentBranchStrategy.NEW_BRANCH
    base_branch: str = "main"
    inherit_context: bool = True
    allowed_tools: list[str] = field(default_factory=list)
    max_iterations: int = 10
    token_budget: int = 50000
    cost_budget_usd: float = 1.0


@dataclass
class OrchestrationPlan:
    """Plan for multi-agent orchestration."""
    mode: OrchestrationMode = OrchestrationMode.PARALLEL
    agents: list[AgentSpec] = field(default_factory=list)
    consensus_threshold: float = 0.6  # For consensus mode
    pipeline_order: list[str] = field(default_factory=list)  # For pipeline mode
    evaluator_agent: str | None = None  # For competitive mode
    max_parallel: int = 3
    timeout_seconds: int = 300


@dataclass
class LoopConfig:
    """Enhanced loop configuration with multiple exit conditions."""
    max_iterations: int = 25
    exit_conditions: list[LoopExitCondition] = field(default_factory=lambda: [
        LoopExitCondition.MAX_ITERATIONS,
        LoopExitCondition.TOKEN_BUDGET,
        LoopExitCondition.COST_BUDGET,
    ])
    token_budget: int = 100000
    cost_budget_usd: float = 5.0
    time_budget_seconds: int = 600
    convergence_threshold: float = 0.95  # Similarity for convergence detection
    convergence_window: int = 3  # Last N iterations to compare
    error_threshold: int = 5
    early_exit_on_goal: bool = True


@dataclass
class CostTracker:
    """Track token usage and costs across agents."""
    total_tokens: int = 0
    total_cost_usd: float = 0.0
    by_agent: dict[str, dict[str, float]] = field(default_factory=dict)
    by_provider: dict[str, dict[str, float]] = field(default_factory=dict)

    def add_usage(self, agent: str, provider: str, tokens: int, cost: float) -> None:
        self.total_tokens += tokens
        self.total_cost_usd += cost
        self.by_agent.setdefault(agent, {"tokens": 0, "cost": 0.0})
        self.by_agent[agent]["tokens"] += tokens
        self.by_agent[agent]["cost"] += cost
        self.by_provider.setdefault(provider, {"tokens": 0, "cost": 0.0})
        self.by_provider[provider]["tokens"] += tokens
        self.by_provider[provider]["cost"] += cost

    def check_budget(self, token_budget: int, cost_budget: float) -> tuple[bool, str]:
        """Return (within_budget, warning_message)."""
        warnings = []
        if self.total_tokens >= token_budget * 0.9:
            warnings.append(f"Token budget at {self.total_tokens}/{token_budget}")
        if self.total_cost_usd >= cost_budget * 0.9:
            warnings.append(f"Cost budget at ${self.total_cost_usd:.2f}/${cost_budget:.2f}")
        within = self.total_tokens < token_budget and self.total_cost_usd < cost_budget
        return within, "; ".join(warnings) if warnings else ""


# ── Spec-Driven Development ─────────────────────────────────────────────


@dataclass
class SpecDocument:
    """A specification document for spec-driven development."""
    id: str
    title: str
    description: str
    requirements: list[str] = field(default_factory=list)
    acceptance_criteria: list[str] = field(default_factory=list)
    technical_design: str = ""
    test_plan: str = ""
    status: str = "draft"  # draft, reviewed, approved, implemented
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


class SpecManager:
    """Manage specification documents for spec-driven development."""

    def __init__(self, project_path: Path):
        self.project_path = project_path
        self.specs_dir = project_path / ".jebat" / "specs"
        self.specs_dir.mkdir(parents=True, exist_ok=True)
        self.index_file = self.specs_dir / "index.json"
        self._load_index()

    def _load_index(self) -> None:
        if self.index_file.exists():
            with open(self.index_file) as f:
                self.index = json.load(f)
        else:
            self.index = {"specs": {}}

    def _save_index(self) -> None:
        with open(self.index_file, "w") as f:
            json.dump(self.index, f, indent=2, default=str)

    def create_spec(
        self,
        title: str,
        description: str,
        requirements: list[str] | None = None,
        acceptance_criteria: list[str] | None = None,
    ) -> SpecDocument:
        spec = SpecDocument(
            id=f"spec_{uuid.uuid4().hex[:8]}",
            title=title,
            description=description,
            requirements=requirements or [],
            acceptance_criteria=acceptance_criteria or [],
        )
        self.index["specs"][spec.id] = {
            "id": spec.id,
            "title": spec.title,
            "status": spec.status,
            "created_at": spec.created_at.isoformat(),
            "updated_at": spec.updated_at.isoformat(),
        }
        self._save_index()
        self._save_spec(spec)
        return spec

    def _save_spec(self, spec: SpecDocument) -> None:
        spec_file = self.specs_dir / f"{spec.id}.md"
        content = f"""# {spec.title}

**ID:** {spec.id}
**Status:** {spec.status}
**Created:** {spec.created_at}
**Updated:** {spec.updated_at}

## Description
{spec.description}

## Requirements
{chr(10).join(f"- {r}" for r in spec.requirements) or "*None*"}

## Acceptance Criteria
{chr(10).join(f"- {c}" for c in spec.acceptance_criteria) or "*None*"}

## Technical Design
{spec.technical_design or "*Not yet designed*"}

## Test Plan
{spec.test_plan or "*Not yet planned*"}
"""
        spec_file.write_text(content, encoding="utf-8")

    def get_spec(self, spec_id: str) -> SpecDocument | None:
        if spec_id not in self.index["specs"]:
            return None
        spec_file = self.specs_dir / f"{spec_id}.md"
        if not spec_file.exists():
            return None
        # Parse markdown back to SpecDocument (simplified)
        return SpecDocument(id=spec_id, title="", description="")

    def list_specs(self) -> list[dict]:
        return list(self.index["specs"].values())

    def update_spec(self, spec_id: str, **kwargs) -> SpecDocument | None:
        spec = self.get_spec(spec_id)
        if not spec:
            return None
        for key, value in kwargs.items():
            if hasattr(spec, key):
                setattr(spec, key, value)
        spec.updated_at = datetime.now()
        self._save_spec(spec)
        return spec


# ── Skill Marketplace ───────────────────────────────────────────────────


@dataclass
class Skill:
    """A reusable skill/prompt template."""
    id: str
    name: str
    description: str
    category: str
    prompt_template: str
    parameters: dict[str, Any] = field(default_factory=dict)
    tags: list[str] = field(default_factory=list)
    version: str = "1.0.0"
    author: str = "community"


class SkillMarketplace:
    """Dynamic skill loading from local and remote sources."""

    def __init__(self, project_path: Path):
        self.project_path = project_path
        self.local_skills_dir = project_path / ".jebat" / "skills"
        self.local_skills_dir.mkdir(parents=True, exist_ok=True)
        self._skills: dict[str, Skill] = {}
        self._load_local_skills()

    def _load_local_skills(self) -> None:
        for skill_file in self.local_skills_dir.glob("*.json"):
            try:
                with open(skill_file) as f:
                    data = json.load(f)
                    skill = Skill(**data)
                    self._skills[skill.id] = skill
            except Exception:
                pass

    def install_skill(self, skill: Skill) -> None:
        skill_file = self.local_skills_dir / f"{skill.id}.json"
        with open(skill_file, "w") as f:
            json.dump(skill.__dict__, f, indent=2, default=str)
        self._skills[skill.id] = skill

    def get_skill(self, skill_id: str) -> Skill | None:
        return self._skills.get(skill_id)

    def list_skills(self, category: str | None = None) -> list[Skill]:
        skills = list(self._skills.values())
        if category:
            skills = [s for s in skills if s.category == category]
        return skills

    def render_skill(self, skill_id: str, **params) -> str | None:
        skill = self.get_skill(skill_id)
        if not skill:
            return None
        try:
            return skill.prompt_template.format(**params)
        except KeyError as e:
            raise ValueError(f"Missing parameter for skill {skill.name}: {e}")


# ── Agent Memory (Cross-Session Learning) ───────────────────────────────


@dataclass
class MemoryEntry:
    """A learned pattern from agent interactions."""
    id: str
    pattern_type: str  # "success", "failure", "preference", "pattern"
    context: str
    action: str
    outcome: str
    confidence: float = 0.5
    usage_count: int = 0
    created_at: datetime = field(default_factory=datetime.now)
    last_used: datetime | None = None
    tags: list[str] = field(default_factory=list)


class AgentMemory:
    """Persistent memory for agent learning across sessions."""

    def __init__(self, project_path: Path):
        self.project_path = project_path
        self.memory_dir = project_path / ".jebat" / "memory"
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        self.memory_file = self.memory_dir / "memory.json"
        self.entries: dict[str, MemoryEntry] = {}
        self._load()

    def _load(self) -> None:
        if self.memory_file.exists():
            try:
                with open(self.memory_file) as f:
                    data = json.load(f)
                    self.entries = {
                        k: MemoryEntry(**v) for k, v in data.items()
                    }
            except Exception:
                pass

    def _save(self) -> None:
        with open(self.memory_file, "w") as f:
            json.dump(
                {k: v.__dict__ for k, v in self.entries.items()},
                f, indent=2, default=str
            )

    def remember(
        self,
        pattern_type: str,
        context: str,
        action: str,
        outcome: str,
        confidence: float = 0.5,
        tags: list[str] | None = None,
    ) -> MemoryEntry:
        entry = MemoryEntry(
            id=f"mem_{uuid.uuid4().hex[:8]}",
            pattern_type=pattern_type,
            context=context,
            action=action,
            outcome=outcome,
            confidence=confidence,
            tags=tags or [],
        )
        self.entries[entry.id] = entry
        self._save()
        return entry

    def recall(self, context: str, pattern_type: str | None = None, limit: int = 5) -> list[MemoryEntry]:
        """Find relevant memories for a context."""
        results = []
        context_lower = context.lower()
        for entry in self.entries.values():
            if pattern_type and entry.pattern_type != pattern_type:
                continue
            # Simple relevance: context overlap + confidence
            relevance = 0
            if context_lower in entry.context.lower():
                relevance += 2
            if any(tag.lower() in context_lower for tag in entry.tags):
                relevance += 1
            relevance += entry.confidence
            if relevance > 0:
                results.append((relevance, entry))
        results.sort(key=lambda x: x[0], reverse=True)
        return [e for _, e in results[:limit]]

    def reinforce(self, entry_id: str, success: bool) -> None:
        """Update confidence based on outcome."""
        if entry_id in self.entries:
            entry = self.entries[entry_id]
            if success:
                entry.confidence = min(1.0, entry.confidence + 0.1)
            else:
                entry.confidence = max(0.1, entry.confidence - 0.1)
            entry.usage_count += 1
            entry.last_used = datetime.now()
            self._save()


# ── Branch Agent Manager ────────────────────────────────────────────────


class BranchAgentManager:
    """Manage agent execution on git branches/worktrees."""

    def __init__(self, project_path: Path):
        self.project_path = project_path

    def _run_git(self, args: list[str]) -> subprocess.CompletedProcess:
        return subprocess.run(
            ["git", "-C", str(self.project_path)] + args,
            capture_output=True, text=True
        )

    def get_current_branch(self) -> str:
        result = self._run_git(["branch", "--show-current"])
        return result.stdout.strip() or "main"

    def list_branches(self) -> list[str]:
        result = self._run_git(["branch", "--format=%(refname:short)"])
        return [b.strip() for b in result.stdout.splitlines() if b.strip()]

    def create_branch(self, branch_name: str, base: str = "main") -> bool:
        result = self._run_git(["checkout", "-b", branch_name, base])
        return result.returncode == 0

    def create_worktree(self, path: Path, branch: str, base: str = "main") -> bool:
        result = self._run_git(["worktree", "add", "-b", branch, str(path), base])
        return result.returncode == 0

    def remove_worktree(self, path: Path) -> bool:
        result = self._run_git(["worktree", "remove", "--force", str(path)])
        return result.returncode == 0

    def stash_changes(self) -> bool:
        result = self._run_git(["stash", "push", "-m", "jebat-agent-stash"])
        return result.returncode == 0

    def pop_stash(self) -> bool:
        result = self._run_git(["stash", "pop"])
        return result.returncode == 0

    def apply_agent_changes(
        self,
        agent_branch: str,
        target_branch: str = "main",
        strategy: str = "merge",
    ) -> subprocess.CompletedProcess:
        """Apply agent's changes from their branch to target."""
        self._run_git(["checkout", target_branch])
        if strategy == "rebase":
            return self._run_git(["rebase", agent_branch])
        else:
            return self._run_git(["merge", "--no-ff", agent_branch])

    def get_diff(self, branch1: str, branch2: str = "main") -> str:
        result = self._run_git(["diff", branch2, branch1])
        return result.stdout

    async def run_agent_on_branch(
        self,
        spec: AgentSpec,
        prompt: str,
        agent_runner: callable,
    ) -> tuple[str, str]:
        """Run an agent on an isolated branch/worktree."""
        branch_name = f"jebat/{spec.name}/{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        if spec.branch_strategy == AgentBranchStrategy.WORKTREE:
            worktree_path = self.project_path.parent / f"{self.project_path.name}-{spec.name}"
            if self.create_worktree(worktree_path, branch_name, spec.base_branch):
                try:
                    result = await agent_runner(prompt, cwd=worktree_path)
                    return branch_name, result
                finally:
                    self.remove_worktree(worktree_path)
        else:
            # Use stash or new branch
            current = self.get_current_branch()
            if spec.branch_strategy == AgentBranchStrategy.STASH:
                self.stash_changes()
            self.create_branch(branch_name, spec.base_branch)

            try:
                result = await agent_runner(prompt)
                return branch_name, result
            finally:
                if spec.branch_strategy == AgentBranchStrategy.STASH:
                    self._run_git(["checkout", current])
                    self.pop_stash()

        return "", ""


# ── Enhanced CodeAgent with New Features ────────────────────────────────


class EnhancedCodeAgent:
    """Enhanced CodeAgent with branch agents, multi-orchestration, loop optimizations."""

    def __init__(
        self,
        project_path: str | None = None,
        provider_override: str | None = None,
        model_override: str | None = None,
        preset: str | None = None,
        safety_mode: str = "auto",
        yolo: bool = False,
        stream: bool = True,
        auto_commit: bool = False,
        # New params
        loop_config: LoopConfig | None = None,
        cost_tracker: CostTracker | None = None,
        memory: AgentMemory | None = None,
        spec_manager: SpecManager | None = None,
        skill_marketplace: SkillMarketplace | None = None,
    ):
        self.project_path = Path(project_path or os.getcwd())
        self.provider_override = provider_override
        self.model_override = model_override
        self.preset = preset
        self.safety_mode = "confirm" if yolo else safety_mode
        self.yolo = yolo
        self.stream = stream
        self.auto_commit = auto_commit
        self.running = True

        # Enhanced components
        self.loop_config = loop_config or LoopConfig()
        self.cost_tracker = cost_tracker or CostTracker()
        self.memory = memory or AgentMemory(self.project_path)
        self.spec_manager = spec_manager or SpecManager(self.project_path)
        self.skill_marketplace = skill_marketplace or SkillMarketplace(self.project_path)
        self.branch_manager = BranchAgentManager(self.project_path)

        # Project detection
        self.project_info = _detect_project(self.project_path)
        self.project_context = _build_context_section(self.project_info)
        self._capture_results = self._run_workspace_capture()

        # Orchestrator
        self._orchestrator = None

    def _run_workspace_capture(self) -> dict[str, list[str]]:
        try:
            from jebat_project.workspace_capture import WorkspaceCapture
            cap = WorkspaceCapture(self.project_path)
            result = cap.write_vscode_capture(overwrite=False, include_copilot=True)
            return {
                "written": [str(p) for p in result.written],
                "skipped": [str(p) for p in result.skipped],
            }
        except Exception as e:
            return {"written": [], "skipped": [], "error": str(e)}

    async def _init_orchestrator(self) -> Any:
        if self._orchestrator is None:
            from jebat.core.agents.orchestrator import AgentOrchestrator
            self._orchestrator = AgentOrchestrator(config={
                "auto_swarm": True,
                "full_orchestration": True,
                "force_swarm_for_all_tasks": True,
                "full_orchestration_execution_mode": "consensus",
                "full_orchestration_max_agents": 5,
                "default_swarm_size": 3,
            })
            self._orchestrator.register_builtin_agents()
            await self._orchestrator.start()
            _print("  agents ready", "dim")
        return self._orchestrator

    # ── Spec-Driven Commands ──────────────────────────────────────────

    async def _handle_spec_command(self, args: str) -> None:
        """Handle /spec command for spec-driven development."""
        parts = args.split(maxsplit=1)
        subcmd = parts[0].lower() if parts else "list"
        subargs = parts[1] if len(parts) > 1 else ""

        if subcmd in ("create", "new"):
            await self._spec_create(subargs)
        elif subcmd in ("list", "ls"):
            self._spec_list()
        elif subcmd in ("show", "view"):
            self._spec_show(subargs)
        elif subcmd in ("edit", "update"):
            await self._spec_edit(subargs)
        elif subcmd in ("implement", "impl"):
            await self._spec_implement(subargs)
        elif subcmd in ("approve",):
            self._spec_approve(subargs)
        else:
            _print("  Usage: /spec <create|list|show|edit|implement|approve> [args]", "yellow")

    async def _spec_create(self, args: str) -> None:
        """Create a new spec interactively."""
        title = subargs.strip() if subargs else ""
        if not title:
            title = await _input_line("  Spec title: ")
        if not title:
            _print("  Title required", "red")
            return

        description = await _input_line("  Description: ")
        requirements = []
        _print("  Requirements (empty line to finish):", "dim")
        while True:
            req = await _input_line("    - ")
            if not req:
                break
            requirements.append(req)

        acceptance = []
        _print("  Acceptance criteria (empty line to finish):", "dim")
        while True:
            ac = await _input_line("    - ")
            if not ac:
                break
            acceptance.append(ac)

        spec = self.spec_manager.create_spec(title, description, requirements, acceptance)
        _print(f"  Created spec: {spec.id} — {spec.title}", "green")

    def _spec_list(self) -> None:
        specs = self.spec_manager.list_specs()
        if not specs:
            _print("  No specs found. Create one with /spec create", "dim")
            return
        _print("  Specs:", "bold")
        for s in specs:
            status_color = {"draft": "yellow", "reviewed": "cyan", "approved": "green", "implemented": "green"}.get(s["status"], "white")
            _print(f"  {s['id']:15s} {s['title']:30s} [{s['status']}]", status_color)

    def _spec_show(self, spec_id: str) -> None:
        spec = self.spec_manager.get_spec(spec_id.strip())
        if not spec:
            _print(f"  Spec not found: {spec_id}", "red")
            return
        # Display full spec (would read from markdown file)
        _print(f"  {spec.title} ({spec.id})", "bold")
        _print(f"  Status: {spec.status}")
        _print(f"  {spec.description}")

    async def _spec_edit(self, spec_id: str) -> None:
        spec_id = spec_id.strip()
        if not spec_id:
            _print("  Spec ID required", "red")
            return
        spec = self.spec_manager.get_spec(spec_id)
        if not spec:
            _print(f"  Spec not found: {spec_id}", "red")
            return
        # Interactive editing
        _print(f"  Editing {spec.title} (leave empty to keep current)", "dim")
        new_title = await _input_line(f"  Title [{spec.title}]: ")
        if new_title:
            spec.title = new_title
        new_desc = await _input_line(f"  Description [{spec.description[:50]}...]: ")
        if new_desc:
            spec.description = new_desc
        self.spec_manager.update_spec(spec.id, title=spec.title, description=spec.description)
        _print("  Spec updated", "green")

    async def _spec_implement(self, spec_id: str) -> None:
        """Implement a spec using branch agent."""
        spec_id = spec_id.strip()
        if not spec_id:
            _print("  Spec ID required", "red")
            return
        spec = self.spec_manager.get_spec(spec_id)
        if not spec:
            _print(f"  Spec not found: {spec_id}", "red")
            return

        if spec.status not in ("approved", "reviewed"):
            _print(f"  Spec must be approved first (current: {spec.status})", "yellow")
            return

        # Create implementation prompt
        prompt = f"""Implement the following specification:

**Spec:** {spec.title} ({spec.id})
**Description:** {spec.description}

**Requirements:**
{chr(10).join(f"- {r}" for r in spec.requirements)}

**Acceptance Criteria:**
{chr(10).join(f"- {c}" for c in spec.acceptance_criteria)}

**Technical Design:**
{spec.technical_design or "Design as needed"}

**Test Plan:**
{spec.test_plan or "Create appropriate tests"}

Follow the project conventions and ensure all acceptance criteria are met.
"""

        # Create branch agent spec
        agent_spec = AgentSpec(
            name=f"impl-{spec.id}",
            role="implementer",
            task=prompt,
            branch_strategy=AgentBranchStrategy.NEW_BRANCH,
            base_branch=self.branch_manager.get_current_branch(),
            max_iterations=15,
        )

        _print(f"  Starting implementation on branch: impl-{spec.id}", "green")
        branch_name = f"impl/{spec.id}/{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # Create branch
        self.branch_manager.create_branch(branch_name)

        # Run implementation
        result = await self._run_branch_agent(agent_spec, prompt)

        # Update spec status
        self.spec_manager.update_spec(spec_id, status="implemented")
        _print(f"  Implementation complete on branch: {branch_name}", "green")

    def _spec_approve(self, spec_id: str) -> None:
        spec_id = spec_id.strip()
        if not spec_id:
            _print("  Spec ID required", "red")
            return
        self.spec_manager.update_spec(spec_id, status="approved")
        _print(f"  Spec {spec_id} approved", "green")

    # ── Skill Commands ────────────────────────────────────────────────

    async def _handle_skill_command(self, args: str) -> None:
        """Handle /skill command for skill marketplace."""
        parts = args.split(maxsplit=1)
        subcmd = parts[0].lower() if parts else "list"
        subargs = parts[1] if len(parts) > 1 else ""

        if subcmd in ("list", "ls"):
            self._skill_list()
        elif subcmd in ("install", "add"):
            await self._skill_install(subargs)
        elif subcmd in ("use", "run"):
            await self._skill_use(subargs)
        elif subcmd in ("create", "new"):
            await self._skill_create(subargs)
        elif subcmd in ("remove", "rm"):
            self._skill_remove(subargs)
        else:
            _print("  Usage: /skill <list|install|use|create|remove> [args]", "yellow")

    def _skill_list(self) -> None:
        skills = self.skill_marketplace.list_skills()
        if not skills:
            _print("  No skills installed. Install from marketplace or create with /skill create", "dim")
            return
        _print("  Installed Skills:", "bold")
        for s in skills:
            _print(f"  {s.name:20s} ({s.category:15s}) v{s.version} - {s.description[:50]}", "white")

    async def _skill_install(self, args: str) -> None:
        # Would fetch from remote registry
        _print("  Skill registry not yet configured. Create local skills with /skill create", "yellow")

    async def _skill_use(self, args: str) -> None:
        parts = args.split(maxsplit=1)
        skill_id = parts[0] if parts else ""
        params_str = parts[1] if len(parts) > 1 else ""
        if not skill_id:
            _print("  Skill ID required", "red")
            return
        skill = self.skill_marketplace.get_skill(skill_id)
        if not skill:
            _print(f"  Skill not found: {skill_id}", "red")
            return
        # Parse params (simple key=value)
        params = {}
        for pair in params_str.split():
            if "=" in pair:
                k, v = pair.split("=", 1)
                params[k] = v
        try:
            rendered = self.skill_marketplace.render_skill(skill_id, **params)
            _print(f"  Skill rendered (use in prompt):", "green")
            _print(rendered[:500], "dim")
        except ValueError as e:
            _print(f"  {e}", "red")

    async def _skill_create(self, args: str) -> None:
        name = await _input_line("  Skill name: ")
        if not name:
            return
        desc = await _input_line("  Description: ")
        category = await _input_line("  Category (code/review/test/docs/devops): ")
        template = await _input_line("  Prompt template (use {param} for variables): ")
        skill = Skill(
            id=f"skill_{uuid.uuid4().hex[:8]}",
            name=name,
            description=desc,
            category=category,
            prompt_template=template,
        )
        self.skill_marketplace.install_skill(skill)
        _print(f"  Skill created: {skill.id}", "green")

    def _skill_remove(self, skill_id: str) -> None:
        skill_id = skill_id.strip()
        if skill_id in self.skill_marketplace._skills:
            del self.skill_marketplace._skills[skill_id]
            skill_file = self.skill_marketplace.local_skills_dir / f"{skill_id}.json"
            if skill_file.exists():
                skill_file.unlink()
            _print(f"  Skill removed: {skill_id}", "green")
        else:
            _print(f"  Skill not found: {skill_id}", "red")

    # ── Branch Agent Commands ────────────────────────────────────────

    async def _handle_branch_command(self, args: str) -> None:
        """Handle /branch command for branch agent management."""
        parts = args.split(maxsplit=1)
        subcmd = parts[0].lower() if parts else "list"
        subargs = parts[1] if len(parts) > 1 else ""

        if subcmd in ("list", "ls"):
            self._branch_list()
        elif subcmd in ("create", "new"):
            await self._branch_create(subargs)
        elif subcmd in ("apply", "merge"):
            await self._branch_apply(subargs)
        elif subcmd in ("diff",):
            self._branch_diff(subargs)
        elif subcmd in ("remove", "rm", "delete"):
            self._branch_remove(subargs)
        else:
            _print("  Usage: /branch <list|create|apply|diff|remove> [args]", "yellow")

    def _branch_list(self) -> None:
        branches = self.branch_manager.list_branches()
        jebat_branches = [b for b in branches if b.startswith("jebat/") or b.startswith("impl/")]
        if not jebat_branches:
            _print("  No agent branches", "dim")
            return
        _print("  Agent Branches:", "bold")
        for b in jebat_branches:
            current = self.branch_manager.get_current_branch()
            marker = " *" if b == current else ""
            _print(f"  {b}{marker}", "white")

    async def _branch_create(self, args: str) -> None:
        name = args.strip() if args else await _input_line("  Branch name: ")
        if not name:
            _print("  Branch name required", "red")
            return
        base = await _input_line(f"  Base branch [{self.branch_manager.get_current_branch()}]: ")
        base = base.strip() or self.branch_manager.get_current_branch()
        if self.branch_manager.create_branch(name, base):
            _print(f"  Created branch: {name}", "green")
        else:
            _print("  Failed to create branch", "red")

    async def _branch_apply(self, args: str) -> None:
        branch = args.strip() if args else await _input_line("  Branch to apply: ")
        if not branch:
            _print("  Branch name required", "red")
            return
        target = await _input_line(f"  Target branch [main]: ")
        target = target.strip() or "main"
        strategy = await _input_line("  Strategy (merge/rebase) [merge]: ")
        strategy = strategy.strip() or "merge"

        _print(f"  Applying {branch} → {target} ({strategy})...", "yellow")
        result = self.branch_manager.apply_agent_changes(branch, target, strategy)
        if result.returncode == 0:
            _print("  Applied successfully", "green")
        else:
            _print(f"  Failed: {result.stderr}", "red")

    def _branch_diff(self, args: str) -> None:
        branch = args.strip() if args else self.branch_manager.get_current_branch()
        base = "main"
        diff = self.branch_manager.get_diff(branch, base)
        if diff:
            _print(diff[:3000], "white")
            if len(diff) > 3000:
                _print(f"... ({len(diff)} chars total)", "dim")
        else:
            _print("  No differences", "dim")

    def _branch_remove(self, args: str) -> None:
        branch = args.strip()
        if not branch:
            _print("  Branch name required", "red")
            return
        current = self.branch_manager.get_current_branch()
        if branch == current:
            _print("  Cannot delete current branch", "red")
            return
        self.branch_manager._run_git(["branch", "-D", branch])
        _print(f"  Deleted branch: {branch}", "green")

    # ── Memory Commands ──────────────────────────────────────────────

    async def _handle_memory_command(self, args: str) -> None:
        parts = args.split(maxsplit=1)
        subcmd = parts[0].lower() if parts else "list"
        subargs = parts[1] if len(parts) > 1 else ""

        if subcmd in ("list", "ls"):
            self._memory_list()
        elif subcmd in ("recall", "search"):
            self._memory_recall(subargs)
        elif subcmd in ("forget", "remove"):
            self._memory_forget(subargs)
        else:
            _print("  Usage: /memory <list|recall|forget> [args]", "yellow")

    def _memory_list(self) -> None:
        entries = list(self.memory.entries.values())
        if not entries:
            _print("  No memories stored", "dim")
            return
        _print(f"  Memories ({len(entries)}):", "bold")
        for e in sorted(entries, key=lambda x: x.created_at, reverse=True)[:20]:
            _print(f"  [{e.pattern_type}] {e.context[:50]}... → {e.outcome[:50]}...", "white")
            _print(f"    confidence: {e.confidence:.1f}, used: {e.usage_count}x", "dim")

    def _memory_recall(self, query: str) -> None:
        if not query:
            _print("  Query required", "red")
            return
        results = self.memory.recall(query, limit=5)
        if not results:
            _print("  No relevant memories", "dim")
            return
        _print(f"  Relevant memories for: {query}", "bold")
        for e in results:
            _print(f"  [{e.pattern_type}] {e.action} → {e.outcome} (conf: {e.confidence:.1f})", "white")

    def _memory_forget(self, entry_id: str) -> None:
        if entry_id in self.memory.entries:
            del self.memory.entries[entry_id]
            self.memory._save()
            _print(f"  Forgotten: {entry_id}", "green")
        else:
            _print(f"  Not found: {entry_id}", "red")

    # ── Cost & Stats ─────────────────────────────────────────────────

    def _show_cost_report(self) -> None:
        _print("  Cost Report:", "bold")
        _print(f"  Total tokens: {self.cost_tracker.total_tokens:,}", "white")
        _print(f"  Total cost:   ${self.cost_tracker.total_cost_usd:.4f}", "white")
        if self.cost_tracker.by_agent:
            _print("  By agent:", "dim")
            for agent, data in self.cost_tracker.by_agent.items():
                _print(f"  {agent:20s} {data['tokens']:>10,} tokens  ${data['cost']:.4f}", "white")
        within, warning = self.cost_tracker.check_budget(
            self.loop_config.token_budget,
            self.loop_config.cost_budget_usd
        )
        if warning:
            _print(f"  ⚠ {warning}", "yellow" if within else "red")

    # ── Multi-Orchestration ──────────────────────────────────────────

    async def run_orchestration(self, plan: OrchestrationPlan) -> dict[str, Any]:
        """Run a multi-agent orchestration plan."""
        _print(f"  Starting {plan.mode.value} orchestration with {len(plan.agents)} agents", "green")

        if plan.mode == OrchestrationMode.SEQUENTIAL:
            return await self._run_sequential(plan)
        elif plan.mode == OrchestrationMode.PARALLEL:
            return await self._run_parallel(plan)
        elif plan.mode == OrchestrationMode.CONSENSUS:
            return await self._run_consensus(plan)
        elif plan.mode == OrchestrationMode.PIPELINE:
            return await self._run_pipeline(plan)
        elif plan.mode == OrchestrationMode.COMPETITIVE:
            return await self._run_competitive(plan)
        else:
            raise ValueError(f"Unknown orchestration mode: {plan.mode}")

    async def _run_sequential(self, plan: OrchestrationPlan) -> dict[str, Any]:
        results = {}
        for agent_spec in plan.agents:
            _print(f"  ▸ Running {agent_spec.name}...", "dim")
            result = await self._run_branch_agent(agent_spec, agent_spec.task)
            results[agent_spec.name] = result
            # Pass output to next agent as context
        return {"mode": "sequential", "results": results}

    async def _run_parallel(self, plan: OrchestrationPlan) -> dict[str, Any]:
        semaphore = asyncio.Semaphore(plan.max_parallel)

        async def run_one(spec: AgentSpec) -> tuple[str, Any]:
            async with semaphore:
                _print(f"  ▸ {spec.name} started", "dim")
                result = await self._run_branch_agent(spec, spec.task)
                return spec.name, result

        tasks = [run_one(spec) for spec in plan.agents]
        results = dict(await asyncio.gather(*tasks))
        return {"mode": "parallel", "results": results}

    async def _run_consensus(self, plan: OrchestrationPlan) -> dict[str, Any]:
        """Run all agents in parallel, then use evaluator to pick best."""
        results = await self._run_parallel(plan)
        agent_results = results["results"]

        if plan.evaluator_agent:
            # Use evaluator agent to pick best
            eval_prompt = f"""Evaluate these {len(agent_results)} solutions and pick the best:

{chr(10).join(f"--- {name} ---\n{result}" for name, result in agent_results.items())}

Pick the best based on: correctness, completeness, code quality, and adherence to requirements.
Output only the name of the best solution."""
            eval_result = await self._run_branch_agent(
                AgentSpec(name="evaluator", role="evaluator", task=eval_prompt),
                eval_prompt
            )
            best = eval_result.strip()
            if best in agent_results:
                return {"mode": "consensus", "best": best, "all_results": agent_results}
        # Fallback: return all with scores
        return {"mode": "consensus", "results": agent_results}

    async def _run_pipeline(self, plan: OrchestrationPlan) -> dict[str, Any]:
        """Chain agents: output of A becomes input to B."""
        results = {}
        context = ""
        for name in plan.pipeline_order:
            spec = next((s for s in plan.agents if s.name == name), None)
            if not spec:
                continue
            task = f"{spec.task}\n\nPrevious context:\n{context}" if context else spec.task
            result = await self._run_branch_agent(spec, task)
            results[name] = result
            context = result  # Pass to next
        return {"mode": "pipeline", "results": results}

    async def _run_competitive(self, plan: OrchestrationPlan) -> dict[str, Any]:
        """Run multiple agents on same task, pick best via evaluator."""
        if not plan.evaluator_agent:
            _print("  Evaluator agent required for competitive mode", "red")
            return {"mode": "competitive", "error": "No evaluator"}

        # Run all agents with same task
        tasks = [
            self._run_branch_agent(spec, spec.task)
            for spec in plan.agents
        ]
        raw_results = await asyncio.gather(*tasks)

        # Evaluate
        eval_prompt = f"""Evaluate these {len(plan.agents)} solutions to the same task:

Task: {plan.agents[0].task}

Solutions:
{chr(10).join(f"--- Agent {i+1} ---\n{r}" for i, r in enumerate(raw_results))}

Pick the best and explain why. Output: BEST_AGENT=<index>"""
        
        eval_spec = AgentSpec(name="evaluator", role="evaluator", task=eval_prompt)
        eval_result = await self._run_branch_agent(eval_spec, eval_prompt)

        # Parse best agent index
        import re
        match = re.search(r"BEST_AGENT=(\d+)", eval_result)
        if match:
            best_idx = int(match.group(1)) - 1
            if 0 <= best_idx < len(raw_results):
                return {"mode": "competitive", "best": raw_results[best_idx], "all": raw_results}
        return {"mode": "competitive", "all": raw_results, "evaluation": eval_result}

    # ── Branch Agent Runner ──────────────────────────────────────────

    async def _run_branch_agent(self, spec: AgentSpec, prompt: str) -> str:
        """Run an agent on an isolated branch."""
        branch_name = f"jebat/{spec.name}/{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        if spec.branch_strategy == AgentBranchStrategy.WORKTREE:
            worktree_path = self.project_path.parent / f"{self.project_path.name}-{spec.name}"
            if self.branch_manager.create_worktree(worktree_path, branch_name, spec.base_branch):
                try:
                    from jebat.core.agent_loop import AgentLoop, SafetyMode
                    loop = AgentLoop(
                        provider_override=self.provider_override,
                        model_override=self.model_override,
                        preset=self.preset,
                        safety_mode=SafetyMode.AUTO,
                        max_iterations=spec.max_iterations,
                        system_prompt=get_agent_prompt(self.project_context),
                    )
                    result = await loop.run(
                        user_message=prompt,
                        conversation_history=[],
                        mode=None,
                    )
                    return result.final_response
                finally:
                    self.branch_manager.remove_worktree(worktree_path)
        else:
            current = self.branch_manager.get_current_branch()
            if spec.branch_strategy == AgentBranchStrategy.STASH:
                self.branch_manager.stash_changes()
            self.branch_manager.create_branch(branch_name, spec.base_branch)

            try:
                from jebat.core.agent_loop import AgentLoop, SafetyMode
                loop = AgentLoop(
                    provider_override=self.provider_override,
                    model_override=self.model_override,
                    preset=self.preset,
                    safety_mode=SafetyMode.AUTO,
                    max_iterations=spec.max_iterations,
                    system_prompt=get_agent_prompt(self.project_context),
                )
                result = await loop.run(
                    user_message=prompt,
                    conversation_history=[],
                    mode=None,
                )
                return result.final_response
            finally:
                if spec.branch_strategy == AgentBranchStrategy.STASH:
                    self.branch_manager._run_git(["checkout", current])
                    self.branch_manager.pop_stash()

        return ""

    # ── Enhanced Loop with Optimizations ─────────────────────────────

    async def run_optimized_loop(
        self,
        prompt: str,
        config: LoopConfig | None = None,
    ) -> str:
        """Run agent loop with enhanced exit conditions and cost tracking."""
        config = config or self.loop_config
        from jebat.core.agent_loop import AgentLoop, SafetyMode

        safety_map = {
            "auto": SafetyMode.AUTO,
            "confirm": SafetyMode.CONFIRM,
            "dangerous": SafetyMode.DANGEROUS,
        }
        safety = safety_map.get(self.safety_mode, SafetyMode.AUTO)

        system_prompt = get_agent_prompt(self.project_context, auto_commit=self.auto_commit)

        loop = AgentLoop(
            provider_override=self.provider_override,
            model_override=self.model_override,
            preset=self.preset,
            safety_mode=safety,
            max_iterations=config.max_iterations,
            system_prompt=system_prompt,
        )

        start_time = time.time()
        iteration = 0
        last_responses: list[str] = []
        total_tokens = 0
        total_cost = 0.0
        error_count = 0

        while iteration < config.max_iterations:
            iteration += 1

            # Check exit conditions
            if LoopExitCondition.TIME_BUDGET in config.exit_conditions:
                if time.time() - start_time > config.time_budget_seconds:
                    _print(f"  Time budget exceeded ({config.time_budget_seconds}s)", "yellow")
                    break

            if LoopExitCondition.TOKEN_BUDGET in config.exit_conditions:
                if total_tokens >= config.token_budget:
                    _print(f"  Token budget exceeded ({total_tokens}/{config.token_budget})", "yellow")
                    break

            if LoopExitCondition.COST_BUDGET in config.exit_conditions:
                if total_cost >= config.cost_budget_usd:
                    _print(f"  Cost budget exceeded (${total_cost:.2f}/${config.cost_budget_usd})", "yellow")
                    break

            if LoopExitCondition.ERROR_THRESHOLD in config.exit_conditions:
                if error_count >= config.error_threshold:
                    _print(f"  Error threshold exceeded ({error_count})", "red")
                    break

            # Run one iteration
            try:
                result = await loop.run(
                    user_message=prompt if iteration == 1 else "Continue",
                    conversation_history=[],
                    mode=None,
                )

                if result.tokens_used:
                    total_tokens += result.tokens_used.get("total_tokens", 0)
                    # Estimate cost (rough)
                    total_cost += total_tokens * 0.00001  # Rough estimate

                final_text = result.final_response

                # Check convergence
                if LoopExitCondition.CONVERGENCE in config.exit_conditions and len(last_responses) >= config.convergence_window:
                    # Simple similarity check
                    recent = last_responses[-config.convergence_window:]
                    similarity = self._compute_similarity(recent)
                    if similarity > config.convergence_threshold:
                        _print(f"  Convergence detected (similarity: {similarity:.2f})", "green")
                        break

                last_responses.append(final_text)
                if len(last_responses) > config.convergence_window:
                    last_responses.pop(0)

                # Check goal achievement
                if config.early_exit_on_goal and self._check_goal_achieved(final_text, prompt):
                    _print("  Goal achieved", "green")
                    break

                prompt = "Continue"  # Continue prompt for next iteration

            except Exception as e:
                error_count += 1
                _print(f"  Iteration {iteration} error: {e}", "red")
                if error_count >= config.error_threshold:
                    break

        elapsed = time.time() - start_time
        _print(f"  Completed in {elapsed:.1f}s, {iteration} iterations, {total_tokens:,} tokens", "dim")
        return final_text if 'final_text' in locals() else ""

    def _compute_similarity(self, responses: list[str]) -> float:
        """Simple similarity metric for convergence detection."""
        if len(responses) < 2:
            return 0.0
        # Simple word overlap similarity
        words_list = [set(r.lower().split()) for r in responses]
        intersections = sum(len(a & b) for a, b in zip(words_list, words_list[1:]))
        unions = sum(len(a | b) for a, b in zip(words_list, words_list[1:]))
        return intersections / unions if unions > 0 else 0.0

    def _check_goal_achieved(self, response: str, original_prompt: str) -> bool:
        """Simple heuristic to detect goal completion."""
        goal_indicators = [
            "complete", "finished", "done", "implemented", "deployed",
            "all tests pass", "build successful", "ready for review",
        ]
        response_lower = response.lower()
        return any(indicator in response_lower for indicator in goal_indicators)

    # ── Command Handling ────────────────────────────────────────────

    async def _handle_command(self, cmd_raw: str) -> None:
        parts = cmd_raw.strip().split(maxsplit=1)
        cmd = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ""

        if cmd in ("/quit", "/exit", "/q"):
            self.running = False

        elif cmd == "/spec":
            await self._handle_spec_command(args)

        elif cmd == "/skill":
            await self._handle_skill_command(args)

        elif cmd == "/branch":
            await self._handle_branch_command(args)

        elif cmd == "/memory":
            await self._handle_memory_command(args)

        elif cmd == "/cost":
            self._show_cost_report()

        elif cmd == "/orchestrate":
            await self._handle_orchestrate(args)

        elif cmd == "/optimize":
            await self._handle_optimize(args)

        else:
            # Fall back to original command handling
            await self._handle_original_command(cmd_raw)

    async def _handle_orchestrate(self, args: str) -> None:
        """Handle /orchestrate command for multi-agent orchestration."""
        parts = args.split()
        if not parts:
            _print("  Usage: /orchestrate <mode> [agents...]", "yellow")
            _print("  Modes: sequential, parallel, consensus, pipeline, competitive", "dim")
            return

        mode = OrchestrationMode(parts[0].lower()) if parts[0].lower() in [m.value for m in OrchestrationMode] else OrchestrationMode.PARALLEL
        agent_names = parts[1:] if len(parts) > 1 else []

        # Quick orchestration with defaults
        if not agent_names:
            # Default agent team
            agents = [
                AgentSpec(name="architect", role="architect", task="Design solution"),
                AgentSpec(name="implementer", role="implementer", task="Write code"),
                AgentSpec(name="reviewer", role="reviewer", task="Review code"),
            ]
        else:
            agents = [
                AgentSpec(name=n, role="generalist", task="Assist with task")
                for n in agent_names
            ]

        plan = OrchestrationPlan(
            mode=mode,
            agents=agents,
            evaluator_agent="evaluator" if mode == OrchestrationMode.COMPETITIVE else None,
        )

        _print(f"  Running {mode.value} orchestration...", "green")
        result = await self.run_orchestration(plan)

        if "best" in result:
            _print(f"  Best: {result['best']}", "green")
        else:
            _print("  Completed", "green")

    async def _handle_optimize(self, args: str) -> None:
        """Handle /optimize command for loop optimization."""
        parts = args.split()
        subcmd = parts[0].lower() if parts else "config"
        subargs = parts[1] if len(parts) > 1 else ""

        if subcmd in ("config", "show"):
            self._show_loop_config()
        elif subcmd in ("set",):
            self._set_loop_config(subargs)
        elif subcmd in ("budget",):
            self._set_budget(subargs)
        else:
            _print("  Usage: /optimize <config|set|budget> [args]", "yellow")

    def _show_loop_config(self) -> None:
        c = self.loop_config
        _print("  Loop Configuration:", "bold")
        _print(f"  max_iterations:     {c.max_iterations}", "white")
        _print(f"  exit_conditions:    {[e.value for e in c.exit_conditions]}", "white")
        _print(f"  token_budget:       {c.token_budget:,}", "white")
        _print(f"  cost_budget_usd:    ${c.cost_budget_usd:.2f}", "white")
        _print(f"  time_budget_seconds: {c.time_budget_seconds}s", "white")
        _print(f"  convergence_thresh: {c.convergence_threshold:.0%}", "white")
        _print(f"  early_exit_on_goal: {c.early_exit_on_goal}", "white")

    def _set_loop_config(self, args: str) -> None:
        parts = args.split()
        if len(parts) < 2:
            _print("  Usage: /optimize set <key> <value>", "yellow")
            return
        key, value = parts[0], parts[1]
        if key == "max_iterations":
            self.loop_config.max_iterations = int(value)
        elif key == "token_budget":
            self.loop_config.token_budget = int(value)
        elif key == "cost_budget":
            self.loop_config.cost_budget_usd = float(value)
        elif key == "time_budget":
            self.loop_config.time_budget_seconds = int(value)
        elif key == "convergence":
            self.loop_config.convergence_threshold = float(value)
        else:
            _print(f"  Unknown key: {key}", "red")
            return
        _print(f"  Set {key} = {value}", "green")

    def _set_budget(self, args: str) -> None:
        parts = args.split()
        if len(parts) < 2:
            _print("  Usage: /optimize budget <tokens> <usd>", "yellow")
            return
        self.loop_config.token_budget = int(parts[0])
        self.loop_config.cost_budget_usd = float(parts[1])
        _print(f"  Budget set: {parts[0]} tokens, ${parts[1]}", "green")


# ── Factory Functions ──────────────────────────────────────────────────


def create_enhanced_agent(
    project_path: str | None = None,
    **kwargs
) -> EnhancedCodeAgent:
    """Factory to create an EnhancedCodeAgent with all features enabled."""
    return EnhancedCodeAgent(project_path=project_path, **kwargs)


def create_orchestration_plan(
    mode: str,
    tasks: list[dict[str, str]],
    **kwargs
) -> OrchestrationPlan:
    """Create an orchestration plan from simple task definitions."""
    agents = [
        AgentSpec(
            name=t.get("name", f"agent_{i}"),
            role=t.get("role", "generalist"),
            task=t.get("task", ""),
            max_iterations=t.get("max_iterations", 10),
            branch_strategy=AgentBranchStrategy(t.get("branch", "new_branch")),
        )
        for i, t in enumerate(tasks)
    ]
    return OrchestrationPlan(
        mode=OrchestrationMode(mode),
        agents=agents,
        **kwargs
    )


# ── Register New Commands in Original CodeAgent ──────────────────────

# These would be added to the original CodeAgent's _handle_command method:
# - /spec
# - /skill
# - /branch
# - /memory
# - /cost
# - /orchestrate
# - /optimize