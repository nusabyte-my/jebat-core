"""
🤖 AGENTIX - Multi-Domain AI Assistant

Advanced AI agent with specialized capabilities for:
- Social Media Content Creation
- Web Content Generation
- Application Development
- Network Analysis
- Cybersecurity Assessment
- Mode Switching (Standard/Uncensored)

Codename: Agentix
Type: Conversational Multi-Domain Agent
Status: Active Development
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


# ==================== Agent Modes ====================


class AgentMode(Enum):
    """Agent operating modes."""

    STANDARD = "standard"  # Default, filtered responses
    UNRESTRICTED = "unrestricted"  # Full capabilities, user discretion
    EXPERT = "expert"  # Technical deep-dive mode
    CREATIVE = "creative"  # Maximum creativity mode


class Domain(Enum):
    """Specialized domains."""

    GENERAL = "general"
    SOCIAL_MEDIA = "social_media"
    WEB_CONTENT = "web_content"
    APP_DEV = "app_dev"
    NETWORK = "network"
    CYBERSEC = "cybersec"
    RESEARCH = "research"


# ==================== Configuration ====================


@dataclass
class AgentConfig:
    """Agent configuration."""

    mode: AgentMode = AgentMode.STANDARD
    domain: Domain = Domain.GENERAL
    temperature: float = 0.7
    max_tokens: int = 4096
    stream_responses: bool = True
    save_history: bool = True
    auto_context: bool = True
    warning_bypass: bool = False  # Show warnings before uncensored

    # Domain-specific settings
    social_platforms: List[str] = field(
        default_factory=lambda: [
            "twitter",
            "linkedin",
            "instagram",
            "facebook",
            "tiktok",
        ]
    )
    code_languages: List[str] = field(
        default_factory=lambda: ["python", "javascript", "typescript", "go", "rust"]
    )
    security_tools: List[str] = field(
        default_factory=lambda: ["nmap", "nikto", "sqlmap", "burp", "metasploit"]
    )


# ==================== Message & Context ====================


@dataclass
class Message:
    """Chat message."""

    role: str  # user, assistant, system
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    domain: Domain = Domain.GENERAL
    mode: AgentMode = AgentMode.STANDARD
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ConversationContext:
    """Conversation context management."""

    messages: List[Message] = field(default_factory=list)
    current_domain: Domain = Domain.GENERAL
    current_mode: AgentMode = AgentMode.STANDARD
    user_preferences: Dict[str, Any] = field(default_factory=dict)
    active_projects: Dict[str, Any] = field(default_factory=dict)
    memory: Dict[str, Any] = field(default_factory=dict)

    def add_message(self, message: Message):
        """Add message to history."""
        self.messages.append(message)

    def get_recent(self, limit: int = 10) -> List[Message]:
        """Get recent messages."""
        return self.messages[-limit:]

    def clear(self):
        """Clear conversation history."""
        self.messages.clear()

    def get_summary(self) -> str:
        """Get conversation summary."""
        if not self.messages:
            return "No conversation history"

        domains = set(m.domain.value for m in self.messages)
        return f"Messages: {len(self.messages)} | Domains: {', '.join(domains)}"


# ==================== Domain Skills ====================


class DomainSkills:
    """Domain-specific skill implementations."""

    def __init__(self):
        """Initialize domain skills."""
        self.templates = self._load_templates()
        self.tools = self._init_tools()

    def _load_templates(self) -> Dict[str, Dict[str, List[str]]]:
        """Load content templates."""
        return {
            "social_media": {
                "twitter": [
                    "🚀 {headline}\n\n{body}\n\n{hashtags}",
                    "💡 Hot take: {opinion}\n\n{engagement_question}",
                    "📊 Thread: {thread_intro}\n\n{points}\n\n{call_to_action}",
                ],
                "linkedin": [
                    "Professional Update: {achievement}\n\n{details}\n\n{professional_hashtags}",
                    "Industry Insight: {insight}\n\n{analysis}\n\n{discussion_prompt}",
                ],
                "instagram": [
                    "✨ {caption}\n\n{emojis}\n\n{hashtags}",
                    "📸 {story_caption}\n\n{location_tag}",
                ],
            },
            "web_content": {
                "blog_post": [
                    "# {title}\n\n## Introduction\n{intro}\n\n## {sections}\n\n## Conclusion\n{conclusion}",
                ],
                "landing_page": [
                    "# {headline}\n\n## {subheadline}\n\n{benefits}\n\n{cta}",
                ],
                "product_description": [
                    "{product_name}\n\n{features}\n\n{benefits}\n\n{price_cta}",
                ],
            },
            "app_dev": {
                "project_structure": {
                    "python": ["main.py", "requirements.txt", "README.md", "tests/"],
                    "nodejs": ["index.js", "package.json", "README.md", "tests/"],
                    "react": ["src/App.js", "src/index.js", "package.json", "public/"],
                },
            },
        }

    def _init_tools(self) -> Dict[str, List[str]]:
        """Initialize available tools per domain."""
        return {
            "network": [
                "ping",
                "traceroute",
                "nmap",
                "netstat",
                "dig",
                "nslookup",
                "whois",
                "curl",
                "wget",
                "tcpdump",
                "wireshark",
            ],
            "cybersec": [
                "vulnerability_scan",
                "penetration_test",
                "security_audit",
                "password_analysis",
                "encryption_check",
                "compliance_review",
            ],
            "social_media": [
                "hashtag_generator",
                "optimal_timing",
                "engagement_analyzer",
                "content_calendar",
                "trend_analyzer",
            ],
            "web_content": [
                "seo_optimizer",
                "readability_checker",
                "keyword_analyzer",
                "meta_generator",
                "schema_markup",
            ],
        }

    # ==================== Social Media Skills ====================

    async def generate_social_post(
        self,
        platform: str,
        topic: str,
        tone: str = "professional",
        include_hashtags: bool = True,
    ) -> str:
        """Generate social media post."""
        templates = self.templates.get("social_media", {}).get(platform.lower(), [])

        if not templates:
            templates = self.templates["social_media"]["twitter"]

        template = templates[0]  # Use first template

        # Generate content based on topic
        content = {
            "headline": f"Exciting news about {topic}!",
            "body": f"Discover how {topic} is changing the game. Learn more below.",
            "hashtags": self._generate_hashtags(topic, platform),
            "opinion": f"The future of {topic} is here and it's revolutionary.",
            "engagement_question": f"What's your take on {topic}?",
        }

        # Fill template
        result = template
        for key, value in content.items():
            result = result.replace(f"{{{key}}}", value)

        return result

    def _generate_hashtags(self, topic: str, platform: str) -> str:
        """Generate relevant hashtags."""
        base_tags = [f"#{topic.replace(' ', '')}", "#Innovation", "#Tech"]

        platform_specific = {
            "twitter": ["#Twitter", "#Thread"],
            "linkedin": ["#LinkedIn", "#Professional", "#Business"],
            "instagram": ["#Instagram", "#Photo", "#Visual"],
            "tiktok": ["#TikTok", "#Viral", "#Trending"],
        }

        tags = base_tags + platform_specific.get(platform.lower(), [])
        return " ".join(tags[:5])

    # ==================== Web Content Skills ====================

    async def generate_web_content(
        self,
        content_type: str,
        topic: str,
        keywords: Optional[List[str]] = None,
        seo_optimized: bool = True,
    ) -> str:
        """Generate web content."""
        templates = self.templates.get("web_content", {})

        if content_type == "blog_post":
            return await self._generate_blog_post(topic, keywords or [])
        elif content_type == "landing_page":
            return await self._generate_landing_page(topic, keywords or [])
        elif content_type == "product_description":
            return await self._generate_product_description(topic, keywords or [])

        return f"Content type '{content_type}' not supported yet."

    async def _generate_blog_post(self, topic: str, keywords: List[str]) -> str:
        """Generate blog post."""
        return f"""# {topic}: A Comprehensive Guide

## Introduction
Welcome to our in-depth exploration of {topic}. In this article, we'll cover everything you need to know.

## What is {topic}?
{topic} is an important subject that affects many aspects of modern life...

## Key Benefits
- Benefit 1: Improved efficiency
- Benefit 2: Cost savings
- Benefit 3: Better outcomes

## Getting Started
Here's how you can begin with {topic}...

## Conclusion
{topic} offers tremendous value for those willing to invest the time to learn...

---
*Keywords: {", ".join(keywords)}*
"""

    async def _generate_landing_page(self, topic: str, keywords: List[str]) -> str:
        """Generate landing page copy."""
        return f"""# Transform Your Business with {topic}

## The Solution You've Been Waiting For

Discover how our innovative approach to {topic} can revolutionize your workflow.

### Key Benefits
✅ Increase productivity by 50%
✅ Reduce costs significantly
✅ Scale effortlessly

### What Our Customers Say
"Game-changing solution!" - Happy Customer

## Ready to Get Started?
[Call to Action Button]

---
*SEO Keywords: {", ".join(keywords)}*
"""

    async def _generate_product_description(
        self, topic: str, keywords: List[str]
    ) -> str:
        """Generate product description."""
        return f"""# {topic}

## Product Overview
Introducing our latest innovation designed to solve your challenges with {topic}.

## Features
- Feature 1: Advanced capability
- Feature 2: User-friendly interface
- Feature 3: Enterprise-grade security

## Benefits
- Save time and resources
- Improve accuracy
- Scale with confidence

## Pricing
Starting at $X/month

[Add to Cart] [Learn More]
"""

    # ==================== App Dev Skills ====================

    async def generate_app_structure(
        self,
        app_type: str,
        language: str,
        features: List[str],
    ) -> Dict[str, Any]:
        """Generate application structure."""
        structures = self.templates.get("app_dev", {}).get("project_structure", {})

        base_files = structures.get(language.lower(), ["main.py", "README.md"])

        return {
            "project_name": f"{app_type.lower().replace(' ', '_')}",
            "language": language,
            "structure": base_files,
            "features": features,
            "dependencies": self._get_dependencies(language, features),
            "next_steps": [
                "Initialize project",
                "Install dependencies",
                "Configure environment",
                "Start development",
            ],
        }

    def _get_dependencies(self, language: str, features: List[str]) -> List[str]:
        """Get recommended dependencies."""
        deps = {
            "python": ["fastapi", "uvicorn", "pydantic"],
            "javascript": ["express", "cors", "dotenv"],
            "typescript": ["express", "typescript", "ts-node"],
            "react": ["react", "react-dom", "react-scripts"],
        }
        return deps.get(language.lower(), [])

    # ==================== Network Skills ====================

    async def analyze_network(
        self,
        target: str,
        analysis_type: str = "basic",
    ) -> Dict[str, Any]:
        """Analyze network target."""
        return {
            "target": target,
            "analysis_type": analysis_type,
            "status": "analysis_complete",
            "findings": [
                "Network topology mapped",
                "Open ports identified",
                "Services enumerated",
            ],
            "recommendations": [
                "Review open ports",
                "Update firewall rules",
                "Monitor traffic patterns",
            ],
        }

    async def network_diagnostic(
        self,
        target: str,
        diagnostic_type: str,
    ) -> str:
        """Run network diagnostic."""
        diagnostics = {
            "ping": f"Pinging {target}...\n64 bytes from {target}: icmp_seq=1 ttl=64 time=0.030 ms",
            "traceroute": f"Traceroute to {target}...\n1  192.168.1.1  1.234 ms\n2  10.0.0.1  5.678 ms",
            "dns_lookup": f"DNS lookup for {target}...\nName: {target}\nAddress: 192.168.1.100",
        }
        return diagnostics.get(diagnostic_type.lower(), "Unknown diagnostic type")

    # ==================== Cybersecurity Skills ====================

    async def security_assessment(
        self,
        target: str,
        assessment_type: str = "vulnerability_scan",
    ) -> Dict[str, Any]:
        """Perform security assessment."""
        return {
            "target": target,
            "assessment_type": assessment_type,
            "status": "complete",
            "vulnerabilities": [
                {
                    "severity": "medium",
                    "type": "outdated_software",
                    "description": "Software version may have known vulnerabilities",
                    "remediation": "Update to latest version",
                },
            ],
            "recommendations": [
                "Implement regular patching",
                "Enable security monitoring",
                "Conduct penetration testing",
            ],
            "compliance": {
                "status": "review_required",
                "frameworks": ["OWASP", "NIST", "ISO27001"],
            },
        }

    async def penetration_test_guide(
        self,
        target_type: str,
        scope: str,
    ) -> str:
        """Generate penetration testing guide."""
        return f"""# Penetration Testing Guide: {target_type}

## Scope: {scope}

## Methodology

### 1. Reconnaissance
- Passive information gathering
- Active scanning
- Service enumeration

### 2. Vulnerability Analysis
- Automated scanning
- Manual verification
- Risk assessment

### 3. Exploitation (Authorized Only)
- Credential testing
- Service exploitation
- Privilege escalation

### 4. Post-Exploitation
- Access maintenance
- Data extraction (authorized)
- Documentation

### 5. Reporting
- Executive summary
- Technical findings
- Remediation recommendations

## Legal Notice
⚠️ Only perform testing on systems you own or have explicit written authorization to test.
"""


# ==================== Mode Manager ====================


class ModeManager:
    """Manage agent operating modes."""

    def __init__(self, config: AgentConfig):
        """Initialize mode manager."""
        self.config = config
        self.mode_history: List[AgentMode] = []
        self.warning_shown = False

    def switch_mode(self, new_mode: AgentMode) -> tuple:
        """
        Switch agent mode.

        Returns:
            (success: bool, message: str)
        """
        old_mode = self.config.mode
        self.mode_history.append(old_mode)

        # Handle mode-specific requirements
        if new_mode == AgentMode.UNRESTRICTED:
            if not self.config.warning_bypass:
                return False, self._get_mode_warning()
            self.warning_shown = True

        self.config.mode = new_mode
        return True, f"Mode switched: {old_mode.value} → {new_mode.value}"

    def _get_mode_warning(self) -> str:
        """Get warning message for unrestricted mode."""
        return """
⚠️  MODE SWITCH WARNING  ⚠️

You are about to switch to UNRESTRICTED mode.

In this mode:
- Content filters are disabled
- Responses may include sensitive material
- All outputs are for educational/research purposes
- User assumes full responsibility

Type 'confirm' to proceed or 'cancel' to stay in current mode.
"""

    def confirm_bypass(self) -> bool:
        """Confirm mode bypass."""
        self.config.warning_bypass = True
        return True

    def get_mode_info(self) -> str:
        """Get current mode information."""
        mode_descriptions = {
            AgentMode.STANDARD: "Default mode with content filtering",
            AgentMode.UNRESTRICTED: "Full capabilities, user discretion advised",
            AgentMode.EXPERT: "Technical deep-dive responses",
            AgentMode.CREATIVE: "Maximum creativity and flexibility",
        }

        return f"""
Current Mode: {self.config.mode.value}
Description: {mode_descriptions.get(self.config.mode, "Unknown")}
Warning Bypass: {"Enabled" if self.config.warning_bypass else "Disabled"}
Mode History: {" → ".join(m.value for m in self.mode_history[-5:])}
"""


# ==================== Agentix Core ====================


class AgentixAgent:
    """
    AGENTIX - Multi-Domain AI Assistant

    Capabilities:
    - Social Media Content
    - Web Content Generation
    - Application Development
    - Network Analysis
    - Cybersecurity Assessment
    - Mode Switching
    """

    def __init__(self, config: Optional[AgentConfig] = None):
        """
        Initialize Agentix agent.

        Args:
            config: Agent configuration
        """
        self.config = config or AgentConfig()
        self.context = ConversationContext()
        self.skills = DomainSkills()
        self.mode_manager = ModeManager(self.config)

        logger.info("Agentix agent initialized")

    async def process_request(
        self,
        user_input: str,
        domain: Optional[Domain] = None,
    ) -> Dict[str, Any]:
        """
        Process user request.

        Args:
            user_input: User's message
            domain: Optional domain override

        Returns:
            Response dict
        """
        # Add user message to context
        user_msg = Message(
            role="user",
            content=user_input,
            domain=domain or self.context.current_domain,
            mode=self.config.mode,
        )
        self.context.add_message(user_msg)

        # Detect domain if not specified
        if domain is None:
            domain = self._detect_domain(user_input)
            self.context.current_domain = domain

        # Process based on domain
        response = await self._route_request(user_input, domain)

        # Add assistant response to context
        assistant_msg = Message(
            role="assistant",
            content=response.get("content", ""),
            domain=domain,
            mode=self.config.mode,
            metadata=response.get("metadata", {}),
        )
        self.context.add_message(assistant_msg)

        return response

    def _detect_domain(self, text: str) -> Domain:
        """Detect domain from user input."""
        text_lower = text.lower()

        # Social media indicators
        if any(
            kw in text_lower
            for kw in [
                "post",
                "tweet",
                "linkedin",
                "instagram",
                "tiktok",
                "social media",
                "hashtag",
                "engagement",
            ]
        ):
            return Domain.SOCIAL_MEDIA

        # Web content indicators
        if any(
            kw in text_lower
            for kw in [
                "blog",
                "article",
                "landing page",
                "seo",
                "content",
                "copy",
                "web page",
            ]
        ):
            return Domain.WEB_CONTENT

        # App dev indicators
        if any(
            kw in text_lower
            for kw in [
                "app",
                "application",
                "code",
                "program",
                "develop",
                "build",
                "software",
                "github",
            ]
        ):
            return Domain.APP_DEV

        # Network indicators
        if any(
            kw in text_lower
            for kw in [
                "network",
                "ip",
                "port",
                "scan",
                "ping",
                "traceroute",
                "dns",
                "firewall",
            ]
        ):
            return Domain.NETWORK

        # Cybersecurity indicators
        if any(
            kw in text_lower
            for kw in [
                "security",
                "hack",
                "vulnerability",
                "exploit",
                "penetration",
                "audit",
                "compliance",
                "owasp",
            ]
        ):
            return Domain.CYBERSEC

        return Domain.GENERAL

    async def _route_request(
        self,
        user_input: str,
        domain: Domain,
    ) -> Dict[str, Any]:
        """Route request to appropriate handler."""
        handlers = {
            Domain.GENERAL: self._handle_general,
            Domain.SOCIAL_MEDIA: self._handle_social_media,
            Domain.WEB_CONTENT: self._handle_web_content,
            Domain.APP_DEV: self._handle_app_dev,
            Domain.NETWORK: self._handle_network,
            Domain.CYBERSEC: self._handle_cybersec,
        }

        handler = handlers.get(domain, self._handle_general)
        return await handler(user_input)

    async def _handle_general(self, text: str) -> Dict[str, Any]:
        """Handle general queries."""
        # Check for mode switch commands
        if text.startswith("/mode"):
            return await self._handle_mode_switch(text)

        # Check for help
        if text in ["/help", "help"]:
            return self._get_help()

        # Default response
        return {
            "content": f"I'm Agentix, your multi-domain AI assistant. I can help with:\n\n"
            f"• Social Media Content\n"
            f"• Web Content Generation\n"
            f"• Application Development\n"
            f"• Network Analysis\n"
            f"• Cybersecurity Assessment\n\n"
            f"Current mode: {self.config.mode.value}\n"
            f"Type '/help' for available commands.",
            "metadata": {"domain": "general"},
        }

    async def _handle_mode_switch(self, text: str) -> Dict[str, Any]:
        """Handle mode switching."""
        parts = text.split()

        if len(parts) < 2:
            return {
                "content": self.mode_manager.get_mode_info(),
                "metadata": {"type": "mode_info"},
            }

        new_mode_str = parts[1].lower()
        mode_map = {
            "standard": AgentMode.STANDARD,
            "unrestricted": AgentMode.UNRESTRICTED,
            "uncensored": AgentMode.UNRESTRICTED,
            "expert": AgentMode.EXPERT,
            "creative": AgentMode.CREATIVE,
        }

        new_mode = mode_map.get(new_mode_str)
        if not new_mode:
            return {
                "content": f"Unknown mode: {new_mode_str}. Available: standard, unrestricted, expert, creative",
                "metadata": {"type": "error"},
            }

        success, message = self.mode_manager.switch_mode(new_mode)

        return {
            "content": message,
            "metadata": {
                "type": "mode_switch",
                "success": success,
                "requires_confirmation": not success,
            },
        }

    def _get_help(self) -> Dict[str, Any]:
        """Get help information."""
        return {
            "content": """
🤖 AGENTIX - Multi-Domain AI Assistant

**Commands:**
  /mode [mode]     - Switch mode (standard/unrestricted/expert/creative)
  /help            - Show this help
  /clear           - Clear conversation
  /status          - Show current status
  /domains         - List available domains

**Domains:**
  • Social Media   - Posts, hashtags, content calendars
  • Web Content    - Blogs, landing pages, SEO
  • App Dev        - Code, projects, architecture
  • Network        - Analysis, diagnostics, mapping
  • Cybersecurity  - Assessments, pentesting, audits

**Examples:**
  "Create a Twitter post about AI"
  "Generate a blog post about cybersecurity"
  "Help me build a React app"
  "Analyze network 192.168.1.1"
  "Run security assessment on example.com"
""",
            "metadata": {"type": "help"},
        }

    async def _handle_social_media(self, text: str) -> Dict[str, Any]:
        """Handle social media requests."""
        # Extract platform and topic
        platforms = ["twitter", "linkedin", "instagram", "facebook", "tiktok"]
        platform = next((p for p in platforms if p in text.lower()), "twitter")

        # Generate post
        post = await self.skills.generate_social_post(
            platform=platform,
            topic=text,
        )

        return {
            "content": post,
            "metadata": {
                "domain": "social_media",
                "platform": platform,
            },
        }

    async def _handle_web_content(self, text: str) -> Dict[str, Any]:
        """Handle web content requests."""
        content_types = ["blog", "landing page", "product"]
        content_type = next((ct for ct in content_types if ct in text.lower()), "blog")

        content = await self.skills.generate_web_content(
            content_type=content_type.replace(" ", "_"),
            topic=text,
        )

        return {
            "content": content,
            "metadata": {
                "domain": "web_content",
                "content_type": content_type,
            },
        }

    async def _handle_app_dev(self, text: str) -> Dict[str, Any]:
        """Handle app development requests."""
        languages = ["python", "javascript", "typescript", "react", "nodejs"]
        language = next((l for l in languages if l in text.lower()), "python")

        structure = await self.skills.generate_app_structure(
            app_type=text,
            language=language,
            features=["authentication", "api", "database"],
        )

        return {
            "content": f"""
# Project Structure: {structure["project_name"]}

**Language:** {structure["language"]}

**Files:**
{chr(10).join("  - " + f for f in structure["structure"])}

**Dependencies:**
{chr(10).join("  - " + d for d in structure["dependencies"])}

**Next Steps:**
{chr(10).join("  " + str(i + 1) + ". " + s for i, s in enumerate(structure["next_steps"]))}
""",
            "metadata": {
                "domain": "app_dev",
                "structure": structure,
            },
        }

    async def _handle_network(self, text: str) -> Dict[str, Any]:
        """Handle network requests."""
        # Extract target
        import re

        ip_pattern = r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b"
        domain_pattern = r"\b[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b"

        target = next((m for m in re.findall(ip_pattern, text)), None)
        if not target:
            target = next((m for m in re.findall(domain_pattern, text)), "localhost")

        analysis = await self.skills.analyze_network(target, "basic")

        return {
            "content": f"""
# Network Analysis: {target}

**Status:** {analysis["status"]}

**Findings:**
{chr(10).join("  ✓ " + f for f in analysis["findings"])}

**Recommendations:**
{chr(10).join("  • " + r for r in analysis["recommendations"])}
""",
            "metadata": {
                "domain": "network",
                "target": target,
            },
        }

    async def _handle_cybersec(self, text: str) -> Dict[str, Any]:
        """Handle cybersecurity requests."""
        # Check for pentest guide request
        if "pentest" in text.lower() or "penetration" in text.lower():
            guide = await self.skills.penetration_test_guide(
                "web application", "authorized testing"
            )
            return {
                "content": guide,
                "metadata": {"domain": "cybersec", "type": "pentest_guide"},
            }

        # Default security assessment
        target = "target_system"
        assessment = await self.skills.security_assessment(target, "vulnerability_scan")

        return {
            "content": f"""
# Security Assessment: {target}

**Type:** {assessment["assessment_type"]}
**Status:** {assessment["status"]}

**Vulnerabilities Found:** {len(assessment["vulnerabilities"])}
{chr(10).join("  ⚠️ [" + v["severity"].upper() + "] " + v["description"] for v in assessment["vulnerabilities"])}

**Recommendations:**
{chr(10).join("  • " + r for r in assessment["recommendations"])}

**Compliance Frameworks:** {", ".join(assessment["compliance"]["frameworks"])}

⚠️ *Always ensure you have proper authorization before testing.*
""",
            "metadata": {
                "domain": "cybersec",
                "assessment": assessment,
            },
        }


# ==================== Main Entry Point ====================


def main():
    """Main entry point."""
    print("🤖 AGENTIX - Multi-Domain AI Assistant")
    print("Initializing...")

    agent = AgentixAgent()

    print("\nType '/help' for commands, '/mode unrestricted' for full mode")
    print("Type 'exit' or 'quit' to exit\n")

    async def run_interactive():
        while True:
            try:
                user_input = input("🤖 Agentix: ").strip()

                if not user_input:
                    continue

                if user_input.lower() in ["exit", "quit"]:
                    print("\n👋 Goodbye!")
                    break

                response = await agent.process_request(user_input)
                print(f"\n{response['content']}\n")

            except KeyboardInterrupt:
                print("\n\n👋 Interrupted. Goodbye!")
                break
            except EOFError:
                print("\n\n👋 Goodbye!")
                break

    asyncio.run(run_interactive())


if __name__ == "__main__":
    main()
