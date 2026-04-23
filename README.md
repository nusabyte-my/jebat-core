# 🗡️ JEBATCore — AI Agent Operating System

**Because warriors remember everything that matters.**

[![Version](https://img.shields.io/badge/version-0.1.0-blue.svg)](https://github.com/nusabyte-my/jebat-core)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Node](https://img.shields.io/badge/node-%3E%3D18-green.svg)](https://nodejs.org)
[![Python](https://img.shields.io/badge/python-3.12+-blue.svg)](https://python.org)

---

JEBATCore is an **AI agent operating system** that installs context, rules, design systems, and skills into your IDE and project — plus provides a local MCP server for structured asset delivery. It works with any LLM provider (Claude, GPT, Gemini, Ollama) and is optimized for token efficiency on both input and output.

---

## 🚀 Quick Start

### Install via CLI

```bash
# Install with defaults (auto-detects IDEs)
npx jebatcore install --yes

# Interactive wizard
npx jebatcore install

# Dry run to preview changes
npx jebatcore install --dry-run --yes
```

### What Gets Installed

| Target | What |
|--------|------|
| **IDE context files** | System prompts, rules, and agent configs for VS Code, Cursor, Zed, JetBrains, Neovim, and more |
| **Project context** | `.cursorrules`, `CLAUDE.md`, `AGENTS.md` — AI agents read these automatically |
| **MCP server** | Local Model Context Protocol server with tools for serving JEBAT assets |
| **Skills** | 23+ specialized skills (dev, security, design, marketing, strategy) |
| **Design systems** | Vercel, Cursor, Supabase — drop into any project for AI-consistent UI |

---

## 📦 Ecosystem

### Token Optimization

| Layer | What | Savings |
|-------|------|---------|
| **Input compression** | Context shrinking, prompt optimization | 25-50% |
| **Output fluff stripping** | Removes greetings, filler, sycophancy | 30-60% |
| **MCP caching** | Response caching for repeated calls | Variable |
| **Budget management** | Per-operation token limits with tracking | Controlled |

```bash
npx jebatcore token-analyze --file AGENTS.md --model claude
npx jebatcore token-compress --file context.txt --level aggressive --target-tokens 3000
npx jebatcore output-fluff --file llm-response.txt
npx jebatcore token-budget --budget implementation
```

### Design Systems

Three production-ready systems from [awesome-design-md](https://github.com/VoltAgent/awesome-design-md):

| System | Style | Key Traits |
|--------|-------|------------|
| **Vercel** (Geist) | Minimalist developer infra | Shadow-as-border, Geist font, white canvas |
| **Cursor** | Warm craft minimalism | Cream `#f2f1ed`, jjannon serif, oklab borders |
| **Supabase** | Dark-mode-native | `#171717` void, emerald green, Circular font |

```bash
npx jebatcore design-system --list
npx jebatcore design-system --name vercel
```

### Icon Catalog

100+ tech logos from [developer-icons](https://github.com/xandemon/developer-icons) for UI/UX enhancement:

```bash
npx jebatcore icon-search --query react
npx jebatcore icon-search --list-all
```

### Skill Manager

Anthropic-compatible [SKILL.md](https://agentskills.io) format with SHA-256 integrity:

```bash
npx jebatcore skill-list                # List all 23 skills
npx jebatcore skill --skill panglima    # View full skill content
npx jebatcore skill-search --query react
npx jebatcore skill-create --skill my-api --description "REST API patterns"
npx jebatcore skill-verify              # Integrity check
```

**23 Skills across 12 categories:**

| Category | Skills |
|----------|--------|
| jebat-native | panglima, memory-core, hermes-agent |
| development | fullstack, web-developer, app-development |
| orchestration | agent-dispatch |
| security | security-pentest |
| database | database |
| automation | automation |
| design | ui-ux |
| growth | marketing, seo |
| strategy | brand-strategy, product-strategy |
| commercial | proposal-writing, sales-enablement |
| content | content-creation, copywriting |
| quality | qa-validation |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────┐
│                    JEBATCore                         │
├─────────────────────────────────────────────────────┤
│                                                      │
│  ┌──────────────┐    ┌──────────────┐               │
│  │  CLI Engine  │    │  MCP Server  │               │
│  │  (Node.js)   │    │  (stdio)     │               │
│  └──────┬───────┘    └──────┬───────┘               │
│         │                   │                        │
│  ┌──────┴───────────────────┴───────┐               │
│  │         Core Libraries            │               │
│  ├───────────────────────────────────┤               │
│  │  • install.js   (file deploy)     │               │
│  │  • detect.js    (IDE scanning)    │               │
│  │  • cli.js       (arg routing)      │               │
│  │  • mcp-server.js  (asset server)   │               │
│  │  • token-utils.js  (counting)      │               │
│  │  • context-compression.js          │               │
│  │  • skill-manager.js  (lifecycle)   │               │
│  └───────────────────────────────────┘               │
│                     │                                │
│  ┌──────────────────┴──────────────────┐            │
│  │         Assets & Config             │            │
│  ├─────────────────────────────────────┤            │
│  │  • vault/ (playbooks, templates)     │            │
│  │  • skills/ (23 SKILL.md files)       │            │
│  │  • adapters/ (IDE-specific configs)  │            │
│  │  • docs/ (token optimization guide)  │            │
│  └─────────────────────────────────────┘            │
│                                                      │
└─────────────────────────────────────────────────────┘
```

---

## 📋 CLI Commands

### Core

| Command | Description |
|---------|-------------|
| `jebatcore install` | Install context files and MCP setup |
| `jebatcore detect` | Scan for installed IDEs |
| `jebatcore prompt` | Print universal system prompt |
| `jebatcore doctor` | Diagnose workspace setup |

### Token Optimization

| Command | Description |
|---------|-------------|
| `token-analyze` | Count tokens for any text/file |
| `token-compress` | Compress context with configurable levels |
| `token-compress-prompt` | Optimize system prompts |
| `token-budget` | View per-operation token budgets |
| `output-fluff` | Analyze and strip LLM output filler |

### Design & Icons

| Command | Description |
|---------|-------------|
| `design-system --list` | List available design systems |
| `design-system --name <system>` | View full design spec |
| `icon-search --query <term>` | Search tech logos |
| `icon-search --list-all` | Full icon catalog |

### Skills

| Command | Description |
|---------|-------------|
| `skill-list` | List all installed skills |
| `skill --skill <name>` | View skill content + integrity |
| `skill-search --query <term>` | Search skills by tag |
| `skill-create --skill <name>` | Author new skill |
| `skill-install --source <path>` | Install from path |
| `skill-remove --skill <name>` | Remove skill |
| `skill-verify` | SHA-256 integrity check |

---

## 🔧 Supported IDEs

| IDE | Extension | MCP | Both |
|-----|-----------|-----|------|
| VS Code | ✅ | ✅ | ✅ |
| Cursor | ✅ | ✅ | ✅ |
| Windsurf | ✅ | ✅ | ✅ |
| Zed | ✅ | ✅ | ✅ |
| VSCodium | ✅ | ✅ | ✅ |
| JetBrains | ✅ | — | ✅ |
| Neovim | ✅ | — | ✅ |
| Sublime Text | ✅ | — | ✅ |
| Trae | ✅ | — | ✅ |
| Antigravity | ✅ | — | ✅ |

---

## 📁 Project Structure

```
jebat-core/
├── bin/                    # CLI entry point
├── lib/                    # Core libraries
│   ├── cli.js              # CLI router
│   ├── install.js          # File deployment
│   ├── detect.js           # IDE detection
│   ├── mcp-server.js       # MCP stdio server
│   ├── token-utils.js      # Token counting & budgets
│   ├── context-compression.js  # Input-side compression
│   ├── skill-manager.js    # Skill lifecycle
│   └── token-config.json   # Token defaults
├── adapters/               # IDE-specific configs
│   ├── profiles/           # Specialized agent profiles
│   ├── cursor/             # .cursorrules
│   ├── vscode/             # copilot-instructions.md
│   ├── zed/                # system-prompt.md
│   └── generic/            # JEBAT.md (universal)
├── skills/                 # 23 Anthropic-compatible skills
│   ├── _core/              # Shared CODEX_CORE.md
│   ├── panglima/           # Orchestration
│   ├── fullstack/          # Development
│   └── ...
├── vault/                  # Playbooks, templates, checklists
│   ├── design-systems/     # Vercel, Cursor, Supabase
│   ├── references/         # Icon catalog
│   ├── playbooks/          # Workflow guides
│   ├── templates/          # Brief templates
│   └── checklists/         # Verification checklists
└── docs/
    └── TOKEN-OPTIMIZATION.md  # Complete guide
```

---

## 🤝 Contributing

```bash
# Clone
git clone https://github.com/nusabyte-my/jebat-core.git
cd jebat-core

# Test CLI
node bin/jebatcore.js help

# Dry run install
npm run cli:dry-run

# Validate structure
powershell -NoProfile -ExecutionPolicy Bypass -File .\validate-workspace.ps1
```

---

## 📄 License

**MIT License** — see [LICENSE](LICENSE) for details.

---

## 🙏 Credits

- **Hang Jebat** — Legendary Malay warrior who inspired the name
- [awesome-design-md](https://github.com/VoltAgent/awesome-design-md) — Design system collection
- [developer-icons](https://github.com/xandemon/developer-icons) — Tech logo icon set
- [Agent Skills](https://agentskills.io) — SKILL.md standard (Anthropic)
- [skilld](https://github.com/harlan-zw/skilld) — NPM skill packaging inspiration

---

**🗡️ JEBATCore** — *Because warriors remember everything that matters.*

Made by [NusaByte](https://github.com/nusabyte-my).
