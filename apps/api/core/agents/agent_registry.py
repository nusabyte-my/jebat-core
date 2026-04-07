"""
Agent Registry — Cross-Provider Agent Discovery
Maintains a registry of all available agents across all LLM providers.
Supports discovery by capability, role, provider, and availability.
"""

import os
import json
import asyncio
from typing import Optional
from datetime import datetime, timezone
from .llm_protocol import AgentIdentity, AgentStatus, AgentMessage, MessageType


class AgentRegistry:
    """
    Central registry for all LLM agents in the JEBAT ecosystem.
    
    Agents register with their provider, model, capabilities, and status.
    Other agents can discover and communicate with registered agents.
    """
    
    def __init__(self, data_dir: str = None):
        self.data_dir = data_dir or os.path.join(os.getcwd(), "security", "agent-registry")
        os.makedirs(self.data_dir, exist_ok=True)
        
        self._agents: dict[str, AgentIdentity] = {}
        self._capabilities_index: dict[str, list[str]] = {}  # capability -> agent_ids
        self._provider_index: dict[str, list[str]] = {}      # provider -> agent_ids
        self._role_index: dict[str, list[str]] = {}          # role -> agent_ids
        
        self._load_from_disk()
    
    def register(self, agent: AgentIdentity) -> bool:
        """Register an agent with the registry."""
        self._agents[agent.agent_id] = agent
        
        # Update indexes
        for cap in agent.capabilities:
            if cap not in self._capabilities_index:
                self._capabilities_index[cap] = []
            if agent.agent_id not in self._capabilities_index[cap]:
                self._capabilities_index[cap].append(agent.agent_id)
        
        if agent.provider not in self._provider_index:
            self._provider_index[agent.provider] = []
        if agent.agent_id not in self._provider_index[agent.provider]:
            self._provider_index[agent.provider].append(agent.agent_id)
        
        if agent.agent_role not in self._role_index:
            self._role_index[agent.agent_role] = []
        if agent.agent_id not in self._role_index[agent.agent_role]:
            self._role_index[agent.agent_role].append(agent.agent_id)
        
        self._save_to_disk()
        return True
    
    def deregister(self, agent_id: str) -> bool:
        """Remove an agent from the registry."""
        if agent_id not in self._agents:
            return False
        
        agent = self._agents.pop(agent_id)
        
        # Remove from indexes
        for cap in agent.capabilities:
            if cap in self._capabilities_index:
                self._capabilities_index[cap] = [a for a in self._capabilities_index[cap] if a != agent_id]
                if not self._capabilities_index[cap]:
                    del self._capabilities_index[cap]
        
        for index in [self._provider_index, self._role_index]:
            key = agent.provider if index == self._provider_index else agent.agent_role
            if key in index:
                index[key] = [a for a in index[key] if a != agent_id]
                if not index[key]:
                    del index[key]
        
        self._save_to_disk()
        return True
    
    def get_agent(self, agent_id: str) -> Optional[AgentIdentity]:
        """Get agent by ID."""
        return self._agents.get(agent_id)
    
    def find_by_capability(self, capability: str) -> list[AgentIdentity]:
        """Find agents that have a specific capability."""
        agent_ids = self._capabilities_index.get(capability, [])
        return [self._agents[a] for a in agent_ids if a in self._agents]
    
    def find_by_provider(self, provider: str) -> list[AgentIdentity]:
        """Find all agents from a specific provider."""
        agent_ids = self._provider_index.get(provider, [])
        return [self._agents[a] for a in agent_ids if a in self._agents]
    
    def find_by_role(self, role: str) -> list[AgentIdentity]:
        """Find all agents with a specific role."""
        agent_ids = self._role_index.get(role, [])
        return [self._agents[a] for a in agent_ids if a in self._agents]
    
    def find_available(self, capability: str = None, provider: str = None) -> list[AgentIdentity]:
        """Find available (idle/thinking) agents, optionally filtered."""
        agents = []
        if capability:
            agents = self.find_by_capability(capability)
        elif provider:
            agents = self.find_by_provider(provider)
        else:
            agents = list(self._agents.values())
        
        return [a for a in agents if a.status in (AgentStatus.IDLE, AgentStatus.THINKING)]
    
    def find_best_agent(self, task_description: str) -> Optional[AgentIdentity]:
        """Find the best agent for a task using keyword matching on capabilities."""
        task_lower = task_description.lower()
        
        # Score each agent
        scores = {}
        for agent_id, agent in self._agents.items():
            if agent.status == AgentStatus.OFFLINE:
                continue
            
            score = 0
            for cap in agent.capabilities:
                if cap.lower() in task_lower:
                    score += 2  # Direct capability match
                elif any(word in cap.lower() for word in task_lower.split()):
                    score += 1  # Partial match
            
            # Prefer idle agents
            if agent.status == AgentStatus.IDLE:
                score += 1
            
            scores[agent_id] = score
        
        if not scores:
            return None
        
        best_id = max(scores, key=scores.get)
        return self._agents[best_id] if scores[best_id] > 0 else None
    
    def get_all_agents(self) -> list[AgentIdentity]:
        """Get all registered agents."""
        return list(self._agents.values())
    
    def get_stats(self) -> dict:
        """Get registry statistics."""
        provider_counts = {p: len(ids) for p, ids in self._provider_index.items()}
        role_counts = {r: len(ids) for r, ids in self._role_index.items()}
        status_counts = {}
        for agent in self._agents.values():
            status_counts[agent.status.value] = status_counts.get(agent.status.value, 0) + 1
        
        return {
            "total_agents": len(self._agents),
            "providers": provider_counts,
            "roles": role_counts,
            "status": status_counts,
            "capabilities": {cap: len(ids) for cap, ids in self._capabilities_index.items()},
        }
    
    def update_status(self, agent_id: str, status: AgentStatus):
        """Update an agent's status."""
        if agent_id in self._agents:
            self._agents[agent_id].status = status
            self._save_to_disk()
    
    def _save_to_disk(self):
        """Save registry to disk."""
        registry_file = os.path.join(self.data_dir, "registry.json")
        data = {
            "agents": {aid: a.to_dict() for aid, a in self._agents.items()},
            "capabilities_index": self._capabilities_index,
            "provider_index": self._provider_index,
            "role_index": self._role_index,
            "last_updated": datetime.now(timezone.utc).isoformat(),
        }
        with open(registry_file, "w") as f:
            json.dump(data, f, indent=2)
    
    def _load_from_disk(self):
        """Load registry from disk."""
        registry_file = os.path.join(self.data_dir, "registry.json")
        if not os.path.exists(registry_file):
            return
        
        with open(registry_file) as f:
            data = json.load(f)
        
        for aid, agent_data in data.get("agents", {}).items():
            self._agents[aid] = AgentIdentity(**agent_data)
        
        self._capabilities_index = data.get("capabilities_index", {})
        self._provider_index = data.get("provider_index", {})
        self._role_index = data.get("role_index", {})


# ─── Built-in Agent Registration ──────────────────────────────────────────────

def register_builtin_agents(registry: AgentRegistry, providers: dict = None):
    """Register JEBAT's built-in agents with the registry."""
    providers = providers or {
        "default": {"provider": "ollama", "model": "qwen2.5-coder:7b"},
        "security": {"provider": "ollama", "model": "hermes-sec-v2"},
        "reasoning": {"provider": "anthropic", "model": "claude-sonnet-4-20250514"},
        "creative": {"provider": "openai", "model": "gpt-4o"},
        "fast": {"provider": "zai", "model": "glm-5"},
    }
    
    builtin_agents = [
        AgentIdentity(
            agent_id="panglima-001",
            agent_name="Panglima",
            agent_role="orchestration",
            provider=providers["reasoning"]["provider"],
            model=providers["reasoning"]["model"],
            capabilities=["orchestration", "routing", "delegation", "consensus", "planning"],
            languages=["en", "ms"],
        ),
        AgentIdentity(
            agent_id="tukang-001",
            agent_name="Tukang",
            agent_role="development",
            provider=providers["default"]["provider"],
            model=providers["default"]["model"],
            capabilities=["coding", "debugging", "testing", "deployment", "refactoring"],
            languages=["en"],
        ),
        AgentIdentity(
            agent_id="hulubalang-001",
            agent_name="Hulubalang",
            agent_role="security",
            provider=providers["security"]["provider"],
            model=providers["security"]["model"],
            capabilities=["pentesting", "vulnerability_scanning", "hardening", "audit", "threat_modeling"],
            languages=["en"],
        ),
        AgentIdentity(
            agent_id="pengawal-001",
            agent_name="Pengawal",
            agent_role="cybersec",
            provider=providers["security"]["provider"],
            model=providers["security"]["model"],
            capabilities=["defensive_security", "monitoring", "incident_response", "compliance", "offensive_security"],
            languages=["en"],
        ),
        AgentIdentity(
            agent_id="pawang-001",
            agent_name="Pawang",
            agent_role="research",
            provider=providers["reasoning"]["provider"],
            model=providers["reasoning"]["model"],
            capabilities=["research", "analysis", "documentation", "investigation", "synthesis"],
            languages=["en", "ms"],
        ),
        AgentIdentity(
            agent_id="syahbandar-001",
            agent_name="Syahbandar",
            agent_role="operations",
            provider=providers["default"]["provider"],
            model=providers["default"]["model"],
            capabilities=["deployment", "ci_cd", "docker", "monitoring", "automation"],
            languages=["en"],
        ),
        AgentIdentity(
            agent_id="bendahara-001",
            agent_name="Bendahara",
            agent_role="database",
            provider=providers["default"]["provider"],
            model=providers["default"]["model"],
            capabilities=["sql", "schema_design", "migrations", "optimization", "backup"],
            languages=["en"],
        ),
        AgentIdentity(
            agent_id="hikmat-001",
            agent_name="Hikmat",
            agent_role="memory",
            provider=providers["reasoning"]["provider"],
            model=providers["reasoning"]["model"],
            capabilities=["memory_management", "search", "consolidation", "recall", "vector_search"],
            languages=["en", "ms"],
        ),
        AgentIdentity(
            agent_id="penganalisis-001",
            agent_name="Penganalisis",
            agent_role="analytics",
            provider=providers["reasoning"]["provider"],
            model=providers["reasoning"]["model"],
            capabilities=["data_analysis", "kpi_review", "funnel_analysis", "reporting", "experiments"],
            languages=["en"],
        ),
        AgentIdentity(
            agent_id="penyemak-001",
            agent_name="Penyemak",
            agent_role="qa",
            provider=providers["reasoning"]["provider"],
            model=providers["reasoning"]["model"],
            capabilities=["testing", "code_review", "validation", "regression", "acceptance"],
            languages=["en"],
        ),
    ]
    
    for agent in builtin_agents:
        registry.register(agent)
    
    return builtin_agents
