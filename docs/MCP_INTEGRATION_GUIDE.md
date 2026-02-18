# 🗡️ JEBAT MCP Integration Guide

**Model Context Protocol (MCP) Integration for Major IDEs**

Connect JEBAT to your favorite IDE for AI-powered development assistance.

---

## 📋 Table of Contents

1. [What is MCP?](#what-is-mcp)
2. [JEBAT MCP Server](#jebat-mcp-server)
3. [IDE Integration Guides](#ide-integration-guides)
   - [VSCode](#vscode)
   - [Zed](#zed)
   - [Cursor](#cursor)
   - [Windsurf](#windsurf)
   - [Trae](#trae)
   - [Antigravity](#antigravity)
4. [Configuration Reference](#configuration-reference)
5. [Troubleshooting](#troubleshooting)

---

## 🔌 What is MCP?

**Model Context Protocol (MCP)** is an open protocol that enables AI assistants to integrate with external tools and data sources.

### Benefits
- 🔄 **Universal Integration** - Works across multiple IDEs
- 🔐 **Secure** - Sandboxed execution with explicit permissions
- 🧩 **Extensible** - Easy to add new capabilities
- ⚡ **Real-time** - Low-latency communication

### JEBAT MCP Capabilities

| Capability | Description |
|------------|-------------|
| `code.read` | Read and analyze code files |
| `code.write` | Create/modify code files |
| `code.review` | Review code for issues |
| `code.generate` | Generate new code |
| `project.scaffold` | Create project structure |
| `git.operations` | Git commands |
| `test.run` | Run tests |
| `debug.analyze` | Analyze errors |
| `db.connect` | Database operations |
| `ml.train` | ML model training |

---

## 🖥️ JEBAT MCP Server

### Installation

```bash
# Install JEBAT with MCP support
pip install jebat[mcp]

# Or from source
cd jebat-core
pip install -e .
```

### Start MCP Server

```bash
# Start MCP server
python -m jebat.mcp.server

# Or with specific port
python -m jebat.mcp.server --port 8787
```

### Server Configuration

```yaml
# jebat_mcp_config.yaml
server:
  host: localhost
  port: 8787
  protocol: stdio  # or http

capabilities:
  code:
    read: true
    write: true
    review: true
    generate: true
  
  project:
    scaffold: true
    git: true
    test: true
  
  database:
    enabled: true
    supported:
      - postgresql
      - mysql
      - mongodb
  
  ml:
    enabled: true
    frameworks:
      - sklearn
      - pytorch
      - tensorflow

security:
  allowed_paths:
    - ~/projects
    - ~/dev
  blocked_commands:
    - rm -rf
    - sudo
  require_confirmation:
    - file.write
    - git.push
```

---

## 💻 IDE Integration Guides

### VSCode

#### Step 1: Install MCP Extension

1. Open VSCode
2. Go to Extensions (`Ctrl+Shift+X`)
3. Search for **"MCP"** or **"Model Context Protocol"**
4. Install the extension

**Recommended Extensions:**
- [MCP Client](https://marketplace.visualstudio.com/items?itemName=mcp.client)
- [AI Assistant MCP](https://marketplace.visualstudio.com/items?itemName=ai-assistant.mcp)

#### Step 2: Configure MCP

Create `.vscode/mcp.json`:

```json
{
  "mcp": {
    "servers": {
      "jebat": {
        "command": "python",
        "args": ["-m", "jebat.mcp.server"],
        "cwd": "${workspaceFolder}",
        "env": {
          "JEBAT_API_KEY": "${env:JEBAT_API_KEY}",
          "JEBAT_CONFIG": "${workspaceFolder}/jebat_config.yaml"
        },
        "capabilities": [
          "code.read",
          "code.write",
          "code.review",
          "code.generate",
          "project.scaffold",
          "git.operations",
          "test.run"
        ]
      }
    }
  }
}
```

#### Step 3: Create JEBAT Config

Create `jebat_config.yaml` in your workspace:

```yaml
# JEBAT Configuration for VSCode
ide: vscode
project_root: ${workspaceFolder}

features:
  autocomplete: true
  inline_suggestions: true
  chat_panel: true
  code_review: true

context:
  include_files:
    - "**/*.py"
    - "**/*.js"
    - "**/*.ts"
    - "**/*.jsx"
    - "**/*.tsx"
  exclude_files:
    - "node_modules/**"
    - ".git/**"
    - "**/__pycache__/**"
    - "**/*.min.js"
```

#### Step 4: Test Connection

Open Command Palette (`Ctrl+Shift+P`):
```
MCP: Check Server Status
MCP: List Available Tools
```

#### Step 5: Usage Examples

**Chat Panel:**
```
@jebat Create a Flask API with JWT authentication
@jebat Review this code for security issues
@jebat Generate unit tests for this function
```

**Inline Commands:**
- `Ctrl+Space` - Trigger AI suggestions
- `Ctrl+I` - Inline edit
- `Ctrl+Shift+I` - Generate code

---

### Zed

#### Step 1: Install MCP Extension

Zed has built-in MCP support. Configure in settings:

1. Open Zed
2. Go to Settings (`Ctrl+,`)
3. Navigate to **Extensions** → **MCP**

#### Step 2: Configure MCP

Edit `~/.config/zed/settings.json`:

```json
{
  "mcp": {
    "enabled": true,
    "servers": {
      "jebat": {
        "type": "stdio",
        "command": "python",
        "arguments": ["-m", "jebat.mcp.server"],
        "env": {
          "JEBAT_MODE": "assistant",
          "JEBAT_PROJECT": "${ZED_WORKSPACE}"
        }
      }
    },
    "tools": {
      "jebat": {
        "enabled": [
          "code.read",
          "code.write",
          "code.generate",
          "code.review"
        ]
      }
    }
  },
  
  "ai": {
    "default_provider": "jebat",
    "inline_suggestions": true,
    "chat_enabled": true
  }
}
```

#### Step 3: Workspace Configuration

Create `.zed/settings.json` in your project:

```json
{
  "jebat": {
    "enabled": true,
    "context_aware": true,
    "auto_review": true,
    "suggestions": {
      "inline": true,
      "popup": true
    }
  }
}
```

#### Step 4: Keyboard Shortcuts

Add to `~/.config/zed/keymap.json`:

```json
[
  {
    "context": "Editor",
    "bindings": {
      "ctrl-shift-j": "mcp:jebat:generate",
      "ctrl-shift-r": "mcp:jebat:review",
      "ctrl-shift-t": "mcp:jebat:test"
    }
  }
]
```

---

### Cursor

#### Step 1: Install MCP

Cursor has native MCP support (v0.40+).

1. Open Cursor
2. Go to Settings (`Ctrl+,`)
3. Navigate to **AI** → **MCP Servers**

#### Step 2: Add JEBAT Server

Click **"Add Server"**:

```
Name: JEBAT
Type: stdio
Command: python -m jebat.mcp.server
Working Directory: ${workspaceFolder}
Environment:
  JEBAT_API_KEY: your_api_key
  JEBAT_MODE: assistant
```

#### Step 3: Configure

Create `.cursor/mcp.json`:

```json
{
  "servers": {
    "jebat": {
      "enabled": true,
      "priority": 1,
      "capabilities": {
        "code_generation": true,
        "code_review": true,
        "refactoring": true,
        "debugging": true,
        "testing": true
      },
      "settings": {
        "temperature": 0.7,
        "max_tokens": 4096,
        "context_window": 8192
      }
    }
  }
}
```

#### Step 4: Usage

**Chat:**
```
@jebat Explain this code
@jebat Refactor this function
@jebat Add error handling
```

**Inline Edit:**
- Select code → `Ctrl+K` → Type instruction

**Tab Autocomplete:**
- JEBAT provides intelligent completions

---

### Windsurf

#### Step 1: Install MCP Extension

Windsurf (by Codeium) supports MCP:

1. Open Windsurf
2. Go to Extensions
3. Install **MCP Integration**

#### Step 2: Configure

Edit `~/.windsurf/config.json`:

```json
{
  "mcp": {
    "jebat": {
      "enabled": true,
      "endpoint": "stdio",
      "command": ["python", "-m", "jebat.mcp.server"],
      "features": {
        "cascade": true,
        "flow": true,
        "autocomplete": true
      }
    }
  }
}
```

#### Step 3: Cascade Integration

Enable JEBAT in Cascade (Windsurf's AI chat):

```
Settings → AI → Cascade → Add Provider → JEBAT
```

#### Step 4: Flow Mode

Configure Flow for automatic suggestions:

```json
{
  "flow": {
    "jebat": {
      "auto_suggest": true,
      "suggestion_delay": 500,
      "max_suggestions": 3
    }
  }
}
```

---

### Trae

#### Step 1: Install MCP

Trae has built-in MCP support:

1. Open Trae
2. Settings → **AI Assistants**
3. Click **"Add MCP Server"**

#### Step 2: Configure Server

```yaml
# trae_mcp_config.yaml
name: JEBAT
type: stdio
executable: python
args:
  - -m
  - jebat.mcp.server
working_dir: ${project_root}
env:
  JEBAT_MODE: trae_integration
  JEBAT_CONTEXT: full
```

#### Step 3: Enable Features

In Trae Settings:

```
✓ Code Generation
✓ Code Review
✓ Auto-complete
✓ Chat Assistant
✓ Test Generation
```

#### Step 4: Keyboard Shortcuts

Configure in Trae keybindings:

```json
{
  "key": "ctrl+shift+j",
  "command": "jebat.generate",
  "when": "editorFocus"
}
```

---

### Antigravity

#### Step 1: Install MCP Plugin

Antigravity (Python IDE) MCP plugin:

```bash
# Install antigravity-mcp plugin
pip install antigravity-mcp jebat-mcp

# Or via Antigravity package manager
antigravity install mcp jebat
```

#### Step 2: Configure

Create `~/.antigravity/mcp.json`:

```json
{
  "mcp_servers": {
    "jebat": {
      "enabled": true,
      "module": "jebat.mcp.server",
      "config": {
        "python_version": "3.11",
        "virtualenv": "${VIRTUAL_ENV}",
        "features": {
          "intellisense": true,
          "refactoring": true,
          "debugging": true,
          "profiling": true
        }
      }
    }
  }
}
```

#### Step 3: Python-Specific Features

Enable JEBAT for Python development:

```yaml
# jebat_python.yaml
python:
  type_hints: true
  docstrings: true
  testing:
    framework: pytest
    auto_generate: true
  linting:
    enabled: true
    tools:
      - flake8
      - pylint
      - black
  debugging:
    breakpoints: true
    watch_variables: true
```

---

## 📖 Configuration Reference

### Full MCP Configuration

```yaml
# jebat_mcp_full.yaml
mcp:
  version: "1.0"
  
  server:
    type: stdio  # or http, websocket
    host: localhost
    port: 8787
    timeout: 30
  
  authentication:
    type: api_key
    key_env: JEBAT_API_KEY
  
  capabilities:
    code:
      read:
        enabled: true
        max_file_size: 1MB
      write:
        enabled: true
        require_confirmation: true
      review:
        enabled: true
        auto_review_on_save: false
      generate:
        enabled: true
        max_tokens: 4096
    
    project:
      scaffold:
        enabled: true
        templates:
          - python_package
          - react_app
          - nodejs_app
      git:
        enabled: true
        auto_commit: false
    
    testing:
      run:
        enabled: true
        frameworks:
          - pytest
          - jest
          - unittest
      generate:
        enabled: true
    
    database:
      enabled: true
      connections:
        postgresql:
          enabled: true
        mysql:
          enabled: true
        mongodb:
          enabled: true
    
    ml:
      enabled: true
      frameworks:
        - sklearn
        - pytorch
        - tensorflow
  
  security:
    allowed_paths:
      - ~/projects
      - ~/dev
      - ${WORKSPACE}
    
    blocked_commands:
      - rm -rf
      - sudo
      - format
    
    require_confirmation:
      - file.write
      - file.delete
      - git.push
      - db.write
  
  logging:
    level: info
    file: ~/.jebat/mcp.log
    max_size: 10MB
    backup_count: 5
  
  performance:
    cache_enabled: true
    cache_ttl: 3600
    max_concurrent_requests: 5
```

### Environment Variables

```bash
# Required
export JEBAT_API_KEY="your_api_key"

# Optional
export JEBAT_MODE="assistant"  # assistant, expert, creative
export JEBAT_CONFIG="/path/to/config.yaml"
export JEBAT_LOG_LEVEL="info"  # debug, info, warning, error
export JEBAT_CONTEXT_WINDOW="8192"
export JEBAT_MAX_TOKENS="4096"
export JEBAT_TEMPERATURE="0.7"
```

---

## 🔧 Troubleshooting

### Common Issues

#### 1. MCP Server Not Starting

```bash
# Check if Python can import jebat
python -c "from jebat.mcp import server; print('OK')"

# Check port availability
netstat -an | grep 8787

# Run in debug mode
python -m jebat.mcp.server --debug
```

#### 2. IDE Not Connecting

**Check:**
- MCP server is running
- Port is not blocked by firewall
- Configuration file syntax is correct
- Environment variables are set

**VSCode Specific:**
```
1. Open Output panel (Ctrl+Shift+U)
2. Select "MCP" from dropdown
3. Check for errors
```

#### 3. Tools Not Available

```json
// Verify capabilities in config
{
  "mcp": {
    "servers": {
      "jebat": {
        "capabilities": ["code.read", "code.write"]
      }
    }
  }
}
```

#### 4. Slow Responses

**Solutions:**
- Reduce context window size
- Enable caching
- Check network latency
- Increase timeout

```yaml
performance:
  cache_enabled: true
  cache_ttl: 3600
  timeout: 60
```

### Debug Commands

```bash
# Test MCP connection
jebat-mcp ping

# List available tools
jebat-mcp tools list

# Test specific tool
jebat-mcp tools test code.read --path test.py

# View logs
tail -f ~/.jebat/mcp.log
```

---

## 📚 Additional Resources

- [JEBAT Documentation](https://github.com/nusabyte-my/jebat-core/wiki)
- [MCP Specification](https://modelcontextprotocol.io/)
- [VSCode MCP Extension](https://marketplace.visualstudio.com/items?itemName=mcp.client)
- [Zed Documentation](https://zed.dev/docs)
- [Cursor Documentation](https://docs.cursor.com/)

---

## 🗡️ Quick Start Summary

```bash
# 1. Install JEBAT
pip install jebat[mcp]

# 2. Configure
echo "JEBAT_API_KEY=your_key" >> ~/.env

# 3. Start server
python -m jebat.mcp.server

# 4. Configure your IDE
# See IDE-specific sections above

# 5. Test
# Open IDE chat and type: @jebat hello
```

---

**🗡️ "Code with JEBAT at your side."**

For support: [GitHub Issues](https://github.com/nusabyte-my/jebat-core/issues)
