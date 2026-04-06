# 🗡️ JEBAT Tok Guru

**"Tok Guru" = Respected Master/Teacher (Malay)**

Universal Skill Catalog for JEBAT Platform

864+ AI-powered skills for development, security, data, business, and more.

---

## 📋 Table of Contents

- [Quick Start](#quick-start)
- [Installation](#installation)
- [Skill Catalog](#skill-catalog)
- [IDE Integration](#ide-integration)
- [Bundles](#bundles)
- [Workflows](#workflows)
- [Creating Skills](#creating-skills)

---

## 🚀 Quick Start

```bash
# Install all skills
npx jebat-tokguru

# Or clone manually
git clone https://github.com/nusabyte-my/jebat-tokguru.git ~/.jebat/skills
```

---

## 📦 Installation

### Option 1: NPX (Recommended)

```bash
# Universal installation (default: ~/.jebat/skills)
npx jebat-tokguru

# IDE-specific installation
npx jebat-tokguru --vscode
npx jebat-tokguru --zed
npx jebat-tokguru --cursor
npx jebat-tokguru --claude
npx jebat-tokguru --gemini
npx jebat-tokguru --path ./my-skills
```

### Option 2: Git Clone

```bash
# Universal
git clone https://github.com/nusabyte-my/jebat-tokguru.git ~/.jebat/skills

# IDE-specific
git clone https://github.com/nusabyte-my/jebat-tokguru.git ~/.vscode/jebat-tokguru
git clone https://github.com/nusabyte-my/jebat-tokguru.git ~/.config/zed/jebat-tokguru
```

### Option 3: JEBAT CLI

```bash
# Using JEBAT CLI
jebat skills install
jebat skills install --category development
jebat skills install typescript-expert
```

---

## 📚 Skill Catalog

### 🏗️ Architecture (45 skills)

| Skill | Description | IDE Support |
|-------|-------------|-------------|
| `architecture` | System design and architecture patterns | All |
| `c4-context` | C4 model context diagrams | All |
| `senior-architect` | Senior architect review | All |
| `microservices-design` | Microservices architecture | All |
| `event-driven-design` | Event-driven architecture | All |
| `api-design` | RESTful API design patterns | All |
| `domain-driven-design` | DDD patterns and practices | All |

### 💼 Business (78 skills)

| Skill | Description | IDE Support |
|-------|-------------|-------------|
| `brainstorming` | Creative brainstorming assistant | All |
| `copywriting` | Marketing copy and content | All |
| `pricing-strategy` | Pricing model analysis | All |
| `seo-audit` | SEO optimization audit | All |
| `gtm-strategy` | Go-to-market strategy | All |
| `cro-optimization` | Conversion rate optimization | All |

### 🤖 Data & AI (156 skills)

| Skill | Description | IDE Support |
|-------|-------------|-------------|
| `rag-engineer` | RAG pipeline development | All |
| `prompt-engineer` | Prompt optimization | All |
| `langgraph` | LangGraph agent workflows | All |
| `llm-app-architect` | LLM application architecture | All |
| `ml-ops` | MLOps and deployment | All |
| `data-pipeline` | Data pipeline design | All |
| `embedding-expert` | Vector embeddings specialist | All |

### 💻 Development (312 skills)

| Skill | Description | IDE Support |
|-------|-------------|-------------|
| `typescript-expert` | TypeScript best practices | All |
| `python-patterns` | Python design patterns | All |
| `react-patterns` | React best practices | All |
| `nodejs-expert` | Node.js architecture | All |
| `rust-expert` | Rust systems programming | All |
| `go-expert` | Go concurrency patterns | All |
| `frontend-master` | Frontend architecture | All |
| `backend-architect` | Backend system design | All |
| `fullstack-lead` | Full-stack development | All |
| `mobile-expert` | React Native/Flutter | All |
| `database-designer` | Database schema design | All |
| `graphql-expert` | GraphQL schema design | All |

### 🔒 Security (89 skills)

| Skill | Description | IDE Support |
|-------|-------------|-------------|
| `api-security-best-practices` | API security checklist | All |
| `sql-injection-testing` | SQL injection testing | All |
| `pentest-web` | Web application pentesting | All |
| `security-audit` | Security code review | All |
| `owasp-top-10` | OWASP Top 10 mitigation | All |
| `auth-expert` | Authentication/authorization | All |
| `crypto-expert` | Cryptography best practices | All |

### 🧪 Testing (67 skills)

| Skill | Description | IDE Support |
|-------|-------------|-------------|
| `test-driven-development` | TDD methodology | All |
| `testing-patterns` | Testing best practices | All |
| `test-fixing` | Fix failing tests | All |
| `unit-test-generator` | Generate unit tests | All |
| `e2e-testing` | End-to-end testing | All |
| `performance-testing` | Performance test design | All |

### ⚙️ Infrastructure (98 skills)

| Skill | Description | IDE Support |
|-------|-------------|-------------|
| `docker-expert` | Docker containerization | All |
| `aws-serverless` | AWS serverless architecture | All |
| `kubernetes-expert` | Kubernetes orchestration | All |
| `ci-cd-pipelines` | CI/CD pipeline design | All |
| `terraform-expert` | Infrastructure as code | All |
| `devops-engineer` | DevOps practices | All |
| `cloud-architect` | Cloud architecture | All |

### 🔄 Workflow (52 skills)

| Skill | Description | IDE Support |
|-------|-------------|-------------|
| `workflow-automation` | Workflow automation | All |
| `project-planning` | Project planning assistant | All |
| `code-review-workflow` | Code review process | All |
| `deployment-workflow` | Deployment automation | All |

### 🗡️ JEBAT Native (67 skills)

| Skill | Description | IDE Support |
|-------|-------------|-------------|
| `cortex-reasoning` | Deep reasoning with JEBAT Cortex | All |
| `continuum-loop` | Continuous processing with Continuum | All |
| `memory-query` | Query JEBAT eternal memory | All |
| `agent-orchestrate` | Multi-agent coordination | All |
| `ml-train` | ML model training | All |
| `db-connect` | Database connectivity | All |

---

## 💻 IDE Integration

### VSCode

```bash
# Install skills for VSCode
npx jebat-tokguru --vscode

# Or manually
git clone https://github.com/nusabyte-my/jebat-tokguru.git ~/.vscode/jebat-tokguru
```

**Configuration** (`.vscode/mcp.json`):
```json
{
  "mcp": {
    "servers": {
      "jebat": {
        "command": "python",
        "args": ["-m", "jebat.mcp.server"],
        "skills_path": "~/.vscode/jebat-tokguru"
      }
    }
  }
}
```

**Usage**: `@skill-name` in chat

---

### Zed

```bash
# Install skills for Zed
npx jebat-tokguru --zed

# Or manually
git clone https://github.com/nusabyte-my/jebat-tokguru.git ~/.config/zed/jebat-tokguru
```

**Configuration** (`~/.config/zed/settings.json`):
```json
{
  "jebat": {
    "skills_path": "~/.config/zed/jebat-tokguru",
    "auto_load": true,
    "enabled_skills": ["all"]
  }
}
```

**Usage**: `@skill-name` in AI panel

---

### Cursor

```bash
# Install skills for Cursor
npx jebat-tokguru --cursor

# Or manually
git clone https://github.com/nusabyte-my/jebat-tokguru.git ~/.cursor/jebat-tokguru
```

**Configuration** (`.cursor/mcp.json`):
```json
{
  "jebat": {
    "skills_path": "~/.cursor/jebat-tokguru",
    "enabled": true
  }
}
```

**Usage**: `@skill-name` in chat

---

### Claude Code CLI

```bash
# Install skills for Claude
npx jebat-tokguru --claude

# Or manually
git clone https://github.com/nusabyte-my/jebat-tokguru.git ~/.claude/skills
```

**Usage**: `/skill-name` or `@skill-name`

---

### Gemini CLI

```bash
# Install skills for Gemini
npx jebat-tokguru --gemini

# Or manually
git clone https://github.com/nusabyte-my/jebat-tokguru.git ~/.gemini/skills
```

**Usage**: Reference in prompts

---

## 📦 Bundles

Curated skill collections by role:

### Web Wizard Bundle
```bash
jebat skills install-bundle web-wizard
```
Includes: `typescript-expert`, `react-patterns`, `nodejs-expert`, `frontend-master`, `graphql-expert`

### Security Engineer Bundle
```bash
jebat skills install-bundle security-engineer
```
Includes: `api-security-best-practices`, `pentest-web`, `security-audit`, `owasp-top-10`, `auth-expert`

### Data Scientist Bundle
```bash
jebat skills install-bundle data-scientist
```
Includes: `rag-engineer`, `ml-ops`, `data-pipeline`, `embedding-expert`, `prompt-engineer`

### DevOps Engineer Bundle
```bash
jebat skills install-bundle devops-engineer
```
Includes: `docker-expert`, `kubernetes-expert`, `ci-cd-pipelines`, `terraform-expert`, `aws-serverless`

### Full-Stack Developer Bundle
```bash
jebat skills install-bundle fullstack-developer
```
Includes: `typescript-expert`, `react-patterns`, `nodejs-expert`, `database-designer`, `fullstack-lead`

---

## 🔄 Workflows

Step-by-step playbooks:

### Ship a SaaS MVP
```bash
jebat workflow run saas-mvp
```

**Steps:**
1. `brainstorming` - Idea validation
2. `architecture` - System design
3. `database-designer` - Schema design
4. `typescript-expert` - Setup TypeScript
5. `react-patterns` - Frontend setup
6. `nodejs-expert` - Backend API
7. `docker-expert` - Containerization
8. `aws-serverless` - Deployment
9. `security-audit` - Security review
10. `seo-audit` - SEO optimization

### Security Audit Workflow
```bash
jebat workflow run security-audit
```

**Steps:**
1. `owasp-top-10` - OWASP checklist
2. `api-security-best-practices` - API review
3. `sql-injection-testing` - SQL injection tests
4. `pentest-web` - Penetration testing
5. `security-audit` - Final audit report

---

## 📝 Creating Skills

### Skill Template (SKILL.md format)

```markdown
---
name: skill-name
description: What the skill does
category: development
tags:
  - tag1
  - tag2
ide_support:
  - vscode
  - zed
  - cursor
author: Your Name
version: 1.0.0
---

# Skill Name

## Description
Detailed description of what this skill does.

## When to Use
- Use case 1
- Use case 2

## How to Invoke
- VSCode: `@skill-name`
- Zed: `@skill-name`
- Cursor: `@skill-name`
- Claude: `/skill-name`

## Example Usage
```
@skill-name Please help me with [task]
```

## Related Skills
- `related-skill-1`
- `related-skill-2`
```

### Submit a Skill

```bash
# Create skill file
mkdir -p skills/category
cp skills/_template.md skills/category/your-skill.md

# Validate
python scripts/validate_skills.py

# Submit PR
git add skills/category/your-skill.md
git commit -m "Add your-skill"
git push
```

---

## 🛠️ CLI Commands

```bash
# Install all skills
jebat skills install

# Install specific skill
jebat skills install python-expert

# Install by category
jebat skills install --category development

# List available skills
jebat skills list

# Search skills
jebat skills search keyword

# Update skills
jebat skills update

# Validate skills
jebat skills validate
```

---

## 📊 Statistics

- **Total Skills**: 864+
- **Categories**: 9
- **IDE Integrations**: 7
- **Bundles**: 15
- **Workflows**: 25
- **Contributors**: 100+

---

## 🔗 Links

- **GitHub**: https://github.com/nusabyte-my/jebat-tokguru
- **Documentation**: https://jebat.online/docs/tokguru
- **Skill Index**: https://jebat.online/skills-index.json
- **Catalog**: https://jebat.online/CATALOG.md

---

## 📄 License

MIT License - See LICENSE file

---

**🗡️ "Belajar dari Tok Guru, menjadi master." (Learn from the Master, become a master.)**
