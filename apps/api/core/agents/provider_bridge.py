"""
Cross-Provider LLM Bridge
Enables actual LLM-to-LLM communication across different providers.
Routes messages through provider APIs and converts between formats.
"""

import os
import json
import asyncio
from typing import Optional, Any
from datetime import datetime, timezone
from .llm_protocol import (
    AgentMessage, AgentIdentity, MessageType, Priority,
    MessageTemplates, ProtocolSerializer, ConversationState
)
from .agent_registry import AgentRegistry


class ProviderBridge:
    """
    Manages actual LLM calls across different providers.
    
    Each provider has its own API client, message format, and response handling.
    The bridge normalizes everything into the AgentMessage protocol.
    """
    
    def __init__(self, api_keys: dict = None):
        self.api_keys = api_keys or {
            "openai": os.getenv("OPENAI_API_KEY", ""),
            "anthropic": os.getenv("ANTHROPIC_API_KEY", ""),
            "gemini": os.getenv("GEMINI_API_KEY", ""),
            "zai": os.getenv("ZAI_API_KEY", ""),
        }
        self._session = None  # HTTP client session
    
    async def send_to_agent(self, message: AgentMessage, target_agent: AgentIdentity) -> AgentMessage:
        """
        Send a message to an LLM agent via its provider and return the response.
        """
        if target_agent.provider == "openai":
            return await self._call_openai(message, target_agent)
        elif target_agent.provider == "anthropic":
            return await self._call_anthropic(message, target_agent)
        elif target_agent.provider == "gemini":
            return await self._call_gemini(message, target_agent)
        elif target_agent.provider == "ollama":
            return await self._call_ollama(message, target_agent)
        elif target_agent.provider == "zai":
            return await self._call_zai(message, target_agent)
        else:
            return AgentMessage(
                sender=target_agent,
                recipient=message.sender.agent_id if message.sender else "",
                message_type=MessageType.ERROR,
                subject="Unsupported provider",
                content=f"Provider {target_agent.provider} is not supported.",
                parent_message_id=message.message_id,
                reply_to_message_id=message.message_id,
            )
    
    async def _call_openai(self, message: AgentMessage, agent: AgentIdentity) -> AgentMessage:
        """Call OpenAI API."""
        import httpx
        
        formatted = ProtocolSerializer.to_openai_format(message)
        
        headers = {
            "Authorization": f"Bearer {self.api_keys.get('openai', '')}",
            "Content-Type": "application/json",
        }
        
        payload = {
            "model": agent.model,
            "messages": formatted,
            "max_tokens": min(4096, agent.max_context_tokens // 4),
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=60.0,
            )
            response.raise_for_status()
            data = response.json()
        
        content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
        
        return AgentMessage(
            sender=agent,
            recipient=message.sender.agent_id if message.sender else "",
            message_type=MessageType.RESPONSE,
            subject=f"Response from {agent.agent_name} (OpenAI)",
            content=content,
            parent_message_id=message.message_id,
            reply_to_message_id=message.message_id,
            conversation_id=message.conversation_id,
            requires_response=False,
            structured_data={"provider": "openai", "usage": data.get("usage", {})},
        )
    
    async def _call_anthropic(self, message: AgentMessage, agent: AgentIdentity) -> AgentMessage:
        """Call Anthropic API."""
        import httpx
        
        formatted = ProtocolSerializer.to_anthropic_format(message)
        
        headers = {
            "x-api-key": self.api_keys.get('anthropic', ''),
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
        
        payload = {
            "model": agent.model,
            "max_tokens": min(4096, agent.max_context_tokens // 4),
            "system": formatted.get("system", ""),
            "messages": formatted.get("messages", []),
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers=headers,
                json=payload,
                timeout=60.0,
            )
            response.raise_for_status()
            data = response.json()
        
        content = data.get("content", [{}])[0].get("text", "") if isinstance(data.get("content"), list) else data.get("content", "")
        
        return AgentMessage(
            sender=agent,
            recipient=message.sender.agent_id if message.sender else "",
            message_type=MessageType.RESPONSE,
            subject=f"Response from {agent.agent_name} (Anthropic)",
            content=content,
            parent_message_id=message.message_id,
            reply_to_message_id=message.message_id,
            conversation_id=message.conversation_id,
            requires_response=False,
            structured_data={"provider": "anthropic", "usage": data.get("usage", {})},
        )
    
    async def _call_gemini(self, message: AgentMessage, agent: AgentIdentity) -> AgentMessage:
        """Call Google Gemini API."""
        import httpx
        
        headers = {
            "Content-Type": "application/json",
        }
        
        payload = {
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": message.content}]
                }
            ],
            "systemInstruction": {
                "parts": [{"text": f"You are {agent.agent_name}, a {agent.agent_role} agent running on Gemini ({agent.model})."}]
            },
        }
        
        api_key = self.api_keys.get('gemini', '')
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{agent.model}:generateContent?key={api_key}"
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=payload, timeout=60.0)
            response.raise_for_status()
            data = response.json()
        
        content = ""
        if data.get("candidates"):
            content = data["candidates"][0].get("content", {}).get("parts", [{}])[0].get("text", "")
        
        return AgentMessage(
            sender=agent,
            recipient=message.sender.agent_id if message.sender else "",
            message_type=MessageType.RESPONSE,
            subject=f"Response from {agent.agent_name} (Gemini)",
            content=content,
            parent_message_id=message.message_id,
            reply_to_message_id=message.message_id,
            conversation_id=message.conversation_id,
            requires_response=False,
            structured_data={"provider": "gemini", "usage": data.get("usageMetadata", {})},
        )
    
    async def _call_ollama(self, message: AgentMessage, agent: AgentIdentity) -> AgentMessage:
        """Call local Ollama API."""
        import httpx
        
        ollama_host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
        
        payload = {
            "model": agent.model,
            "messages": ProtocolSerializer.to_openai_format(message),
            "stream": False,
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{ollama_host}/api/chat",
                json=payload,
                timeout=120.0,
            )
            response.raise_for_status()
            data = response.json()
        
        content = data.get("message", {}).get("content", "")
        
        return AgentMessage(
            sender=agent,
            recipient=message.sender.agent_id if message.sender else "",
            message_type=MessageType.RESPONSE,
            subject=f"Response from {agent.agent_name} (Ollama)",
            content=content,
            parent_message_id=message.message_id,
            reply_to_message_id=message.message_id,
            conversation_id=message.conversation_id,
            requires_response=False,
            structured_data={"provider": "ollama", "model": agent.model},
        )
    
    async def _call_zai(self, message: AgentMessage, agent: AgentIdentity) -> AgentMessage:
        """Call ZAI API."""
        import httpx
        
        formatted = ProtocolSerializer.to_openai_format(message)
        
        headers = {
            "Authorization": f"Bearer {self.api_keys.get('zai', '')}",
            "Content-Type": "application/json",
        }
        
        payload = {
            "model": agent.model,
            "messages": formatted,
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.zai.network/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=60.0,
            )
            response.raise_for_status()
            data = response.json()
        
        content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
        
        return AgentMessage(
            sender=agent,
            recipient=message.sender.agent_id if message.sender else "",
            message_type=MessageType.RESPONSE,
            subject=f"Response from {agent.agent_name} (ZAI)",
            content=content,
            parent_message_id=message.message_id,
            reply_to_message_id=message.message_id,
            conversation_id=message.conversation_id,
            requires_response=False,
            structured_data={"provider": "zai", "usage": data.get("usage", {})},
        )


class MultiAgentConversation:
    """
    Manages a conversation between multiple LLM agents across different providers.
    
    Example: OpenAI's Tukang asks Anthropic's Hulubalang to review code,
    then Gemini's Penyemak validates the review.
    """
    
    def __init__(self, bridge: ProviderBridge, registry: AgentRegistry):
        self.bridge = bridge
        self.registry = registry
        self.conversations: dict[str, ConversationState] = {}
    
    async def start_conversation(self, title: str, initiator: AgentIdentity, participants: list[str]) -> ConversationState:
        """Start a new multi-agent conversation."""
        conv_id = f"conv_{len(self.conversations) + 1:04d}"
        state = ConversationState(
            conversation_id=conv_id,
            title=title,
            initiator=initiator.agent_id,
            participants=[initiator.agent_id] + participants,
        )
        self.conversations[conv_id] = state
        return state
    
    async def send_message(self, message: AgentMessage) -> AgentMessage:
        """Send a message and route it to the recipient agent."""
        target = self.registry.get_agent(message.recipient)
        if not target:
            return AgentMessage(
                sender=message.sender,
                recipient="",
                message_type=MessageType.ERROR,
                subject="Agent not found",
                content=f"Agent {message.recipient} is not registered.",
                reply_to_message_id=message.message_id,
                conversation_id=message.conversation_id,
            )
        
        # Update conversation
        if message.conversation_id in self.conversations:
            self.conversations[message.conversation_id].add_message(message)
        
        # Route through provider bridge
        response = await self.bridge.send_to_agent(message, target)
        
        # Record response in conversation
        if message.conversation_id in self.conversations:
            self.conversations[message.conversation_id].add_message(response)
        
        return response
    
    async def run_collaborative_task(self, task: str, agents: list[str], pattern: str = "sequential") -> dict:
        """
        Run a task using multiple agents with a collaboration pattern.
        
        Patterns:
        - sequential: Agent1 → Agent2 → Agent3
        - parallel: All agents work simultaneously
        - consensus: All agents vote, majority wins
        - adversarial: Two agents debate, third decides
        """
        initiator = self.registry.find_best_agent(task)
        if not initiator:
            return {"error": "No agent available to initiate task"}
        
        conv = await self.start_conversation(
            title=f"Collaborative: {task[:50]}",
            initiator=initiator,
            participants=agents,
        )
        
        if pattern == "sequential":
            return await self._sequential_execution(task, conv, agents)
        elif pattern == "parallel":
            return await self._parallel_execution(task, conv, agents)
        elif pattern == "consensus":
            return await self._consensus_execution(task, conv, agents)
        elif pattern == "adversarial":
            return await self._adversarial_execution(task, conv, agents)
        
        return {"error": f"Unknown pattern: {pattern}"}
    
    async def _sequential_execution(self, task: str, conv: ConversationState, agents: list[str]) -> dict:
        """Each agent works in sequence, building on previous results."""
        results = []
        current_context = task
        
        for i, agent_id in enumerate(agents):
            agent = self.registry.get_agent(agent_id)
            if not agent:
                continue
            
            # Update agent status
            self.registry.update_status(agent_id, "busy")
            
            message = AgentMessage(
                sender=agent,
                recipient=agent_id,
                message_type=MessageType.REQUEST,
                subject=f"Sequential task step {i+1}/{len(agents)}",
                content=f"""Step {i+1} of sequential task.

Original task: {task}
Previous context:
{current_context}

Please contribute your expertise and pass the result to the next agent.""",
                conversation_id=conv.conversation_id,
                requires_response=True,
                timeout_seconds=120.0,
            )
            
            response = await self.bridge.send_to_agent(message, agent)
            results.append({
                "agent": agent_id,
                "provider": agent.provider,
                "model": agent.model,
                "response": response.content,
            })
            
            current_context += f"\n\n--- {agent.agent_name} ({agent.provider}/{agent.model}) ---\n{response.content}"
            self.registry.update_status(agent_id, "idle")
        
        conv.status = "completed"
        conv.result = current_context
        
        return {
            "conversation_id": conv.conversation_id,
            "pattern": "sequential",
            "agents_used": len(results),
            "results": results,
            "final_output": current_context,
        }
    
    async def _parallel_execution(self, task: str, conv: ConversationState, agents: list[str]) -> dict:
        """All agents work simultaneously on the same task."""
        async def run_agent(agent_id: str):
            agent = self.registry.get_agent(agent_id)
            if not agent:
                return None
            
            self.registry.update_status(agent_id, "busy")
            message = AgentMessage(
                sender=agent,
                recipient=agent_id,
                message_type=MessageType.REQUEST,
                subject=f"Parallel task",
                content=f"""Parallel task execution.

Task: {task}

Please provide your independent analysis/solution.""",
                conversation_id=conv.conversation_id,
                requires_response=True,
                timeout_seconds=120.0,
            )
            
            response = await self.bridge.send_to_agent(message, agent)
            self.registry.update_status(agent_id, "idle")
            
            return {
                "agent": agent_id,
                "provider": agent.provider,
                "model": agent.model,
                "response": response.content,
            }
        
        # Run all agents in parallel
        tasks = [run_agent(aid) for aid in agents]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        results = [r for r in results if r is not None and not isinstance(r, Exception)]
        
        conv.status = "completed"
        conv.result = f"Parallel results from {len(results)} agents"
        
        return {
            "conversation_id": conv.conversation_id,
            "pattern": "parallel",
            "agents_used": len(results),
            "results": results,
        }
    
    async def _consensus_execution(self, task: str, conv: ConversationState, agents: list[str]) -> dict:
        """All agents vote on a solution, majority wins."""
        # Phase 1: Each agent proposes a solution
        proposals = []
        for agent_id in agents:
            agent = self.registry.get_agent(agent_id)
            if not agent:
                continue
            
            message = AgentMessage(
                sender=agent,
                recipient=agent_id,
                message_type=MessageType.PROPOSAL,
                subject=f"Propose solution for: {task[:50]}",
                content=f"""Please propose your solution to this task:

{task}

Respond with your proposed solution and reasoning.""",
                conversation_id=conv.conversation_id,
                requires_response=True,
                timeout_seconds=120.0,
            )
            
            response = await self.bridge.send_to_agent(message, agent)
            proposals.append({"agent": agent_id, "proposal": response.content})
        
        # Phase 2: Each agent votes on all proposals
        votes = []
        for voter_id in agents:
            voter = self.registry.get_agent(voter_id)
            if not voter:
                continue
            
            proposals_text = "\n\n".join(
                f"--- {p['agent']} ---\n{p['proposal'][:500]}..." for p in proposals
            )
            
            message = AgentMessage(
                sender=voter,
                recipient=voter_id,
                message_type=MessageType.VOTE,
                subject=f"Vote on proposals",
                content=f"""Please vote on the following proposals:

{proposals_text}

Vote AGREE, DISAGREE, or ABSTAIN on each proposal with brief reasoning.""",
                conversation_id=conv.conversation_id,
                requires_response=True,
                timeout_seconds=60.0,
            )
            
            response = await self.bridge.send_to_agent(message, voter)
            votes.append({"voter": voter_id, "vote": response.content})
        
        conv.status = "completed"
        return {
            "conversation_id": conv.conversation_id,
            "pattern": "consensus",
            "proposals": proposals,
            "votes": votes,
            "total_proposals": len(proposals),
            "total_votes": len(votes),
        }
    
    async def _adversarial_execution(self, task: str, conv: ConversationState, agents: list[str]) -> dict:
        """Two agents debate, third agent decides."""
        if len(agents) < 3:
            return {"error": "Adversarial pattern requires at least 3 agents"}
        
        proposer_id, opponent_id, judge_id = agents[0], agents[1], agents[2]
        
        # Round 1: Proposer makes a case
        proposer = self.registry.get_agent(proposer_id)
        opponent = self.registry.get_agent(opponent_id)
        judge = self.registry.get_agent(judge_id)
        
        proposal_msg = AgentMessage(
            sender=proposer,
            recipient=proposer_id,
            message_type=MessageType.PROPOSAL,
            subject=f"Proposal: {task[:50]}",
            content=f"""Present your position on this task:

{task}

Provide your full argument with reasoning.""",
            conversation_id=conv.conversation_id,
            requires_response=True,
            timeout_seconds=120.0,
        )
        
        proposal = await self.bridge.send_to_agent(proposal_msg, proposer)
        
        # Round 2: Opponent counters
        counter_msg = AgentMessage(
            sender=opponent,
            recipient=opponent_id,
            message_type=MessageType.COUNTER_PROPOSAL,
            subject=f"Counter to: {task[:50]}",
            content=f"""Here is the opposing position:

{proposal.content}

Please present your counter-argument.""",
            conversation_id=conv.conversation_id,
            requires_response=True,
            timeout_seconds=120.0,
        )
        
        counter = await self.bridge.send_to_agent(counter_msg, opponent)
        
        # Round 3: Judge decides
        judge_msg = AgentMessage(
            sender=judge,
            recipient=judge_id,
            message_type=MessageType.REQUEST,
            subject=f"Judge decision: {task[:50]}",
            content=f"""You are the judge. Review both arguments and make a decision.

PROPOSAL ({proposer.agent_name} / {proposer.provider}):
{proposal.content}

COUNTER ({opponent.agent_name} / {opponent.provider}):
{counter.content}

Please decide: Which argument is stronger and why? Provide your verdict.""",
            conversation_id=conv.conversation_id,
            requires_response=True,
            timeout_seconds=120.0,
        )
        
        verdict = await self.bridge.send_to_agent(judge_msg, judge)
        
        conv.status = "completed"
        return {
            "conversation_id": conv.conversation_id,
            "pattern": "adversarial",
            "proposer": {"agent": proposer_id, "argument": proposal.content},
            "opponent": {"agent": opponent_id, "counter": counter.content},
            "judge": {"agent": judge_id, "verdict": verdict.content},
        }


# ─── FastAPI Integration ──────────────────────────────────────────────────────

def register_llm_communication_routes(app, bridge: ProviderBridge, registry: AgentRegistry):
    """Register LLM-to-LLM communication endpoints."""
    from fastapi import APIRouter, HTTPException
    from pydantic import BaseModel
    
    router = APIRouter(prefix="/api/v1/llm-communication", tags=["LLM Communication"])
    conversation_manager = MultiAgentConversation(bridge, registry)
    
    class AgentMessageRequest(BaseModel):
        sender_id: str
        recipient_id: str
        message_type: str = "request"
        subject: str = ""
        content: str = ""
        conversation_id: str = ""
        priority: str = "medium"
        timeout_seconds: float = 30.0
    
    class CollaborativeTaskRequest(BaseModel):
        task: str
        agents: list[str]
        pattern: str = "sequential"
    
    @router.post("/send")
    async def send_agent_message(req: AgentMessageRequest):
        """Send a message from one LLM agent to another."""
        sender = registry.get_agent(req.sender_id)
        if not sender:
            raise HTTPException(status_code=404, detail=f"Sender agent {req.sender_id} not found")
        
        message = AgentMessage(
            sender=sender,
            recipient=req.recipient_id,
            message_type=MessageType(req.message_type),
            subject=req.subject,
            content=req.content,
            conversation_id=req.conversation_id,
            priority=Priority(req.priority),
            timeout_seconds=req.timeout_seconds,
        )
        
        response = await conversation_manager.send_message(message)
        return {"response": response.content, "agent": response.sender.agent_name, "provider": response.sender.provider}
    
    @router.post("/collaborate")
    async def run_collaborative_task(req: CollaborativeTaskRequest):
        """Run a collaborative task across multiple LLM agents."""
        result = await conversation_manager.run_collaborative_task(req.task, req.agents, req.pattern)
        return result
    
    @router.get("/agents")
    async def list_agents():
        """List all registered agents."""
        agents = registry.get_all_agents()
        return {"agents": [a.to_dict() for a in agents]}
    
    @router.get("/registry/stats")
    async def registry_stats():
        """Get registry statistics."""
        return registry.get_stats()
    
    @router.get("/conversations/{conv_id}")
    async def get_conversation(conv_id: str):
        """Get conversation state."""
        conv = conversation_manager.conversations.get(conv_id)
        if not conv:
            raise HTTPException(status_code=404, detail="Conversation not found")
        return conv.to_dict()
    
    @router.get("/conversations")
    async def list_conversations():
        """List all conversations."""
        return {
            "conversations": [
                {"id": c.conversation_id, "title": c.title, "status": c.status, "participants": c.participants}
                for c in conversation_manager.conversations.values()
            ]
        }
    
    app.include_router(router)
