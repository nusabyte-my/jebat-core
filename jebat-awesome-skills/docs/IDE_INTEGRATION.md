# 🗡️ JEBAT Skills - IDE Integration Guide

**Install and use 864+ AI skills in your favorite IDE**

---

## 🚀 Quick Start

### One-Line Install

```bash
# Auto-detect IDE and install
npx jebat-skills
```

### Manual Install

```bash
# For specific IDE
npx jebat-skills --vscode
npx jebat-skills --zed
npx jebat-skills --cursor

# Custom path
npx jebat-skills --path ./my-skills
```

---

## 📦 Installation Methods

### Method 1: NPX (Recommended)

```bash
# Universal installation
npx jebat-skills

# This will:
# 1. Detect your IDE
# 2. Clone skills to correct location
# 3. Configure MCP settings
```

### Method 2: Git Clone

```bash
# VSCode
git clone https://github.com/nusabyte-my/jebat-awesome-skills.git ~/.vscode/jebat-skills

# Zed
git clone https://github.com/nusabyte-my/jebat-awesome-skills.git ~/.config/zed/jebat-skills

# Cursor
git clone https://github.com/nusabyte-my/jebat-awesome-skills.git ~/.cursor/jebat-skills

# Universal
git clone https://github.com/nusabyte-my/jebat-awesome-skills.git ~/.jebat/skills
```

### Method 3: JEBAT CLI

```bash
# Install via JEBAT
jebat skills install

# Install specific skill
jebat skills install typescript-expert

# Install by category
jebat skills install --category development
```

---

## 💻 IDE-Specific Setup

### VSCode

#### Step 1: Install Skills

```bash
npx jebat-skills --vscode
```

#### Step 2: Configure MCP

Create `.vscode/mcp.json`:

```json
{
  "mcp": {
    "servers": {
      "jebat": {
        "command": "python",
        "args": ["-m", "jebat.mcp.server"],
        "skills_path": "~/.vscode/jebat-skills"
      }
    }
  }
}
```

#### Step 3: Use Skills

In chat panel:
```
@typescript-expert Help me fix these types
@react-patterns Review this component
@docker-expert Create a Dockerfile
```

---

### Zed

#### Step 1: Install Skills

```bash
npx jebat-skills --zed
```

#### Step 2: Configure Settings

Edit `~/.config/zed/settings.json`:

```json
{
  "jebat": {
    "skills_path": "~/.config/zed/jebat-skills",
    "auto_load": true,
    "enabled_skills": ["all"]
  },
  
  "ai": {
    "default_provider": "jebat",
    "inline_suggestions": true
  }
}
```

#### Step 3: Use Skills

In AI panel:
```
@python-patterns Optimize this code
@api-security-best-practices Review for vulnerabilities
```

---

### Cursor

#### Step 1: Install Skills

```bash
npx jebat-skills --cursor
```

#### Step 2: Configure

Create `.cursor/mcp.json`:

```json
{
  "jebat": {
    "skills_path": "~/.cursor/jebat-skills",
    "enabled": true
  }
}
```

#### Step 3: Use Skills

In chat:
```
@rag-engineer Build a RAG pipeline
@cortex-reasoning Analyze this architecture
```

---

### Claude Code CLI

#### Step 1: Install Skills

```bash
npx jebat-skills --claude
```

#### Step 2: Use Skills

```bash
# In Claude CLI
/typescript-expert
@python-patterns
```

---

### Gemini CLI

#### Step 1: Install Skills

```bash
npx jebat-skills --gemini
```

#### Step 2: Use Skills

Reference in prompts:
```
Using the python-patterns skill, review this code...
```

---

## 📚 Available Skills

### Development (312 skills)

```bash
# Install all development skills
jebat skills install --category development

# Individual skills
@typescript-expert
@python-patterns
@react-patterns
@nodejs-expert
@rust-expert
@go-expert
```

### Security (89 skills)

```bash
# Install all security skills
jebat skills install --category security

# Individual skills
@api-security-best-practices
@owasp-top-10
@pentest-web
@security-audit
```

### Data & AI (156 skills)

```bash
# Install all data & AI skills
jebat skills install --category data-ai

# Individual skills
@rag-engineer
@llm-app-architect
@prompt-engineer
@ml-ops
```

### Infrastructure (98 skills)

```bash
# Install all infrastructure skills
jebat skills install --category infrastructure

# Individual skills
@docker-expert
@kubernetes-expert
@terraform-expert
@aws-serverless
```

### JEBAT Native (67 skills)

```bash
# Install all JEBAT native skills
jebat skills install --category jebat-native

# Individual skills
@cortex-reasoning
@continuum-loop
@memory-query
@agent-orchestrate
```

---

## 📦 Skill Bundles

Pre-curated skill collections:

### Web Wizard Bundle

```bash
jebat skills install-bundle web-wizard
```

Includes:
- `typescript-expert`
- `react-patterns`
- `nodejs-expert`
- `frontend-master`
- `graphql-expert`

### Security Engineer Bundle

```bash
jebat skills install-bundle security-engineer
```

Includes:
- `api-security-best-practices`
- `pentest-web`
- `security-audit`
- `owasp-top-10`
- `auth-expert`

### Data Scientist Bundle

```bash
jebat skills install-bundle data-scientist
```

Includes:
- `rag-engineer`
- `ml-ops`
- `data-pipeline`
- `embedding-expert`
- `prompt-engineer`

### DevOps Engineer Bundle

```bash
jebat skills install-bundle devops-engineer
```

Includes:
- `docker-expert`
- `kubernetes-expert`
- `ci-cd-pipelines`
- `terraform-expert`
- `aws-serverless`

---

## 🔄 Updating Skills

```bash
# Update all skills
npx jebat-skills update

# Or manually
cd ~/.jebat/skills && git pull

# Update specific skill
jebat skills update typescript-expert
```

---

## 🛠️ Creating Custom Skills

### Skill Template

Create `skills/category/my-skill/SKILL.md`:

```markdown
---
name: my-skill
description: What my skill does
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

# My Skill

## Description
Detailed description...

## When to Use
- Use case 1
- Use case 2

## How to Invoke
- VSCode: `@my-skill`
- Zed: `@my-skill`
- Cursor: `@my-skill`

## Example
```
@my-skill Please help me with [task]
```
```

### Validate Skill

```bash
# Validate your skill
python scripts/validate_skills.py skills/category/my-skill/SKILL.md

# Submit to repository
git add skills/category/my-skill/SKILL.md
git commit -m "Add my-skill"
git push
```

---

## 🐛 Troubleshooting

### Skills Not Loading

```bash
# Check installation
ls ~/.jebat/skills

# Verify MCP config
cat ~/.vscode/mcp.json

# Restart IDE
```

### Skill Not Found

```bash
# List available skills
jebat skills list

# Search for skill
jebat skills search keyword

# Reinstall skills
npx jebat-skills
```

### MCP Connection Issues

```bash
# Test MCP server
python -m jebat.mcp.server --help

# Check logs
tail -f ~/.jebat/mcp.log
```

---

## 📊 Statistics

- **Total Skills**: 864+
- **Categories**: 9
- **IDE Support**: 7
- **Bundles**: 15
- **Workflows**: 25

---

## 🔗 Resources

- **Repository**: https://github.com/nusabyte-my/jebat-awesome-skills
- **Skill Index**: https://github.com/nusabyte-my/jebat-awesome-skills/blob/main/skills_index.json
- **Full Catalog**: https://github.com/nusabyte-my/jebat-awesome-skills/blob/main/CATALOG.md
- **Documentation**: https://jebat.online/docs/skills

---

**🗡️ "Equip yourself with the best skills."**
