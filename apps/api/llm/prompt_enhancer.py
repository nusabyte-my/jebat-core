"""
Prompt Enhancer Engine
Transforms raw prompts into optimized LLM instructions through multi-stage enhancement.

Stages:
1. Context Injection — Add memory, workspace, agent context
2. Role Assignment — Assign appropriate agent role and personality
3. Constraint Addition — Add safety, format, scope constraints
4. Example Injection — Add few-shot examples if available
5. Structure Optimization — Format for optimal LLM comprehension
6. Token Budget Management — Ensure prompt fits within context window
"""

import os
import json
from typing import Optional
from datetime import datetime, timezone
from dataclasses import dataclass, field


@dataclass
class PromptContext:
    """Context information for prompt enhancement."""
    agent_name: str = "JEBAT"
    agent_role: str = "operator"
    agent_capabilities: list[str] = field(default_factory=list)
    user_name: str = "emmet"
    workspace_path: str = ""
    memory_context: str = ""
    conversation_history: list[dict] = field(default_factory=list)
    available_tools: list[str] = field(default_factory=list)
    current_task: str = ""
    provider: str = "ollama"
    model: str = ""
    thinking_mode: str = "deliberate"


@dataclass
class EnhancedPrompt:
    """Result of prompt enhancement."""
    original: str
    enhanced: str
    stages_applied: list[str]
    estimated_tokens: int
    compression_ratio: float = 1.0
    metadata: dict = field(default_factory=dict)


class PromptEnhancer:
    """
    Multi-stage prompt enhancement engine.
    
    Each stage transforms the prompt to improve LLM comprehension,
    accuracy, and relevance.
    """
    
    def __init__(self, max_context_tokens: int = 128000):
        self.max_context_tokens = max_context_tokens
        self._few_shot_examples: dict[str, list[dict]] = {}
        self._load_examples()
    
    def _load_examples(self):
        """Load few-shot examples for common tasks."""
        self._few_shot_examples = {
            "code_review": [
                {
                    "user": "Review this Python function:\n```python\ndef get_user(id):\n    return db.query(f\"SELECT * FROM users WHERE id={id}\")\n```",
                    "assistant": """🔴 **CRITICAL — SQL Injection Vulnerability**

**File:** `get_user()`
**Issue:** User input directly interpolated into SQL query
**Severity:** CRITICAL
**Line:** 2

**Current code:**
```python
return db.query(f"SELECT * FROM users WHERE id={id}")
```

**Fixed code:**
```python
return db.query("SELECT * FROM users WHERE id=?", (id,))
```

**Why:** The f-string allows arbitrary SQL injection. Parameterized queries prevent this.

**Additional concerns:**
- Missing error handling for non-existent users
- No input validation (id should be int > 0)
- Consider adding caching for frequent lookups""",
                }
            ],
            "security_audit": [
                {
                    "user": "Audit this nginx config:\n```\nserver { listen 80; location / { proxy_pass http://localhost:8000; } }\n```",
                    "assistant": """🟡 **Security Audit — nginx Configuration**

| Issue | Severity | Description |
|-------|----------|-------------|
| No HTTPS redirect | HIGH | Port 80 without SSL/redirect |
| Missing security headers | MEDIUM | No HSTS, X-Frame-Options, CSP |
| Server tokens exposed | LOW | Default nginx version disclosure |

**Recommended config:**
```nginx
server {
    listen 80;
    server_name jebat.online;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl;
    server_name jebat.online;
    
    ssl_certificate /etc/letsencrypt/live/jebat.online/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/jebat.online/privkey.pem;
    
    add_header X-Frame-Options DENY always;
    add_header X-Content-Type-Options nosniff always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    
    server_tokens off;
    
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}```""",
                }
            ],
        }
    
    def enhance(self, raw_prompt: str, context: PromptContext = None) -> EnhancedPrompt:
        """
        Run full enhancement pipeline on a raw prompt.
        
        Returns EnhancedPrompt with all stages applied.
        """
        context = context or PromptContext()
        enhanced = raw_prompt
        stages_applied = []
        
        # Stage 1: Context Injection
        enhanced, applied = self._inject_context(enhanced, context)
        if applied:
            stages_applied.append("context_injection")
        
        # Stage 2: Role Assignment
        enhanced, applied = self._assign_role(enhanced, context)
        if applied:
            stages_applied.append("role_assignment")
        
        # Stage 3: Constraint Addition
        enhanced, applied = self._add_constraints(enhanced, context)
        if applied:
            stages_applied.append("constraint_addition")
        
        # Stage 4: Example Injection
        enhanced, applied = self._inject_examples(enhanced, context)
        if applied:
            stages_applied.append("example_injection")
        
        # Stage 5: Structure Optimization
        enhanced, applied = self._optimize_structure(enhanced, context)
        if applied:
            stages_applied.append("structure_optimization")
        
        # Stage 6: Token Budget
        estimated_tokens = self._estimate_tokens(enhanced)
        if estimated_tokens > self.max_context_tokens * 0.8:
            enhanced = self._compress_prompt(enhanced, context)
            stages_applied.append("token_compression")
        
        return EnhancedPrompt(
            original=raw_prompt,
            enhanced=enhanced,
            stages_applied=stages_applied,
            estimated_tokens=self._estimate_tokens(enhanced),
            compression_ratio=len(enhanced) / max(len(raw_prompt), 1),
            metadata={
                "agent": context.agent_name,
                "provider": context.provider,
                "model": context.model,
                "thinking_mode": context.thinking_mode,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )
    
    def _inject_context(self, prompt: str, context: PromptContext) -> tuple[str, bool]:
        """Stage 1: Inject relevant context into the prompt."""
        context_parts = []
        
        # Agent context
        context_parts.append(f"""[Agent Context]
Name: {context.agent_name}
Role: {context.agent_role}
Capabilities: {', '.join(context.agent_capabilities)}
Provider: {context.provider} ({context.model})""")
        
        # User context
        context_parts.append(f"""[User Context]
Name: {context.user_name}
Workspace: {context.workspace_path}""")
        
        # Memory context
        if context.memory_context:
            context_parts.append(f"""[Relevant Memory]
{context.memory_context[:2000]}""")  # Limit memory context
        
        # Available tools
        if context.available_tools:
            context_parts.append(f"""[Available Tools]
{', '.join(context.available_tools)}""")
        
        if context_parts:
            prompt = "\n\n".join(context_parts) + f"""

[User Request]
{prompt}"""
            return prompt, True
        
        return prompt, False
    
    def _assign_role(self, prompt: str, context: PromptContext) -> tuple[str, bool]:
        """Stage 2: Assign appropriate role and personality."""
        role_prefixes = {
            "development": "You are an expert software developer. Write clean, tested, production-ready code. Follow best practices and explain your reasoning.",
            "security": "You are a cybersecurity expert. Identify vulnerabilities, provide fixes, and assess risk levels. Be thorough and precise.",
            "research": "You are a research analyst. Gather, synthesize, and present information clearly. Cite sources and highlight uncertainties.",
            "orchestration": "You are a senior project coordinator. Break down complex tasks, delegate appropriately, and track progress. Be decisive.",
            "operations": "You are a senior DevOps engineer. Automate everything, monitor proactively, and plan for failure. Be practical.",
            "database": "You are a senior database engineer. Design efficient schemas, optimize queries, and plan for scale. Be precise.",
            "analytics": "You are a senior data analyst. Find patterns, validate assumptions, and present actionable insights. Be data-driven.",
            "qa": "You are a senior QA engineer. Find edge cases, write thorough tests, and validate requirements. Be meticulous.",
            "memory": "You are a memory management specialist. Organize, consolidate, and retrieve information efficiently. Be thorough.",
            "cybersec": "You are a cybersecurity operator. Scan, analyze, remediate, and report. Be systematic.",
        }
        
        role_prefix = role_prefixes.get(context.agent_role, f"You are {context.agent_name}, a {context.agent_role} specialist.")
        
        # Check if role is already mentioned in prompt
        if context.agent_role.lower() not in prompt.lower() and context.agent_name.lower() not in prompt.lower():
            prompt = f"{role_prefix}\n\n{prompt}"
            return prompt, True
        
        return prompt, False
    
    def _add_constraints(self, prompt: str, context: PromptContext) -> tuple[str, bool]:
        """Stage 3: Add safety, format, and scope constraints."""
        constraints = []
        
        # Thinking mode constraints
        if context.thinking_mode == "fast":
            constraints.append("Respond concisely. Maximum 3 paragraphs. No unnecessary details.")
        elif context.thinking_mode == "deep":
            constraints.append("Think deeply. Show your reasoning step by step. Consider edge cases and alternatives.")
        elif context.thinking_mode == "strategic":
            constraints.append("Think strategically. Consider short, medium, and long-term implications. Recommend the option that optimizes across all timeframes.")
        elif context.thinking_mode == "creative":
            constraints.append("Think creatively. Propose unconventional approaches. Challenge assumptions. Consider lateral solutions.")
        elif context.thinking_mode == "critical":
            constraints.append("Think critically. Identify weaknesses, failure modes, and risks. Challenge every assumption. Provide failure analysis.")
        
        # Output format
        constraints.append("Format your response clearly with headers, code blocks, and lists where appropriate.")
        
        # Safety
        constraints.append("If the request involves security risks, destructive actions, or unauthorized access, refuse and explain why.")
        
        prompt += f"""

[Constraints]
""" + "\n".join(f"- {c}" for c in constraints)
        
        return prompt, True
    
    def _inject_examples(self, prompt: str, context: PromptContext) -> tuple[str, bool]:
        """Stage 4: Add few-shot examples if relevant."""
        # Detect task type
        prompt_lower = prompt.lower()
        task_type = None
        
        if any(kw in prompt_lower for kw in ["review", "audit code", "check code"]):
            task_type = "code_review"
        elif any(kw in prompt_lower for kw in ["security", "vulnerability", "audit", "scan"]):
            task_type = "security_audit"
        
        if task_type and task_type in self._few_shot_examples:
            examples = self._few_shot_examples[task_type]
            example_text = "\n\n".join(
                f"""Example {i+1}:
User: {ex['user']}

Response: {ex['assistant']}"""
                for i, ex in enumerate(examples)
            )
            
            prompt += f"""

[Examples — Follow this format and depth]
{example_text}"""
            return prompt, True
        
        return prompt, False
    
    def _optimize_structure(self, prompt: str, context: PromptContext) -> tuple[str, bool]:
        """Stage 5: Optimize prompt structure for LLM comprehension."""
        # Check if prompt already has structure
        has_sections = any(marker in prompt for marker in ["[", "##", "###", "Task:", "Request:"])
        
        if not has_sections:
            # Add clear section markers
            if "[User Request]" not in prompt:
                prompt = f"[Request]\n{prompt}"
            
            # Add response template
            prompt += """

[Response Template]
1. **Summary:** One-line answer
2. **Analysis:** Detailed reasoning
3. **Action:** Concrete steps
4. **Confidence:** High/Medium/Low with reasoning"""
            return prompt, True
        
        return prompt, False
    
    def _estimate_tokens(self, text: str) -> int:
        """Rough token estimation (4 chars ≈ 1 token for English)."""
        return max(1, len(text) // 4)
    
    def _compress_prompt(self, prompt: str, context: PromptContext) -> str:
        """Compress prompt to fit within token budget."""
        max_chars = self.max_context_tokens * 4 * 0.8  # 80% of budget
        
        if len(prompt) <= max_chars:
            return prompt
        
        # Priority: keep [Constraints] and [User Request], compress [Memory] and [Examples]
        sections = prompt.split("\n\n")
        compressed = []
        current_length = 0
        
        for section in sections:
            section_length = len(section)
            if current_length + section_length <= max_chars:
                compressed.append(section)
                current_length += section_length
            else:
                # Truncate this section
                remaining = max_chars - current_length
                if remaining > 100:
                    compressed.append(section[:remaining] + "... [truncated for token budget]")
                break
        
        return "\n\n".join(compressed)
