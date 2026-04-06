# 🗡️ JEBAT Interactive CLI Guide

**Modern, interactive command-line interface** inspired by Claude Code, Mistral Vibe, and Kilocode.

---

## 🚀 Quick Start

### Start Interactive Mode

```bash
# Using module
python -m jebat_dev.gateway

# Using launch script
python -m jebat_dev.launch

# Or with command
jebat
```

### Single Command Mode

```bash
# Execute single command
python -m jebat_dev.gateway "create a React app"

# Force interactive mode
python -m jebat_dev.gateway -i
```

---

## ✨ Features

### 1. REPL-Style Interaction

```
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║   🗡️  JEBAT DevAssistant  v1.0.0                         ║
║                                                           ║
║   Your Personal Development AI Assistant                  ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝

📚 Commands: [...]
🔧 Slash Commands: /help /clear /history /config /status ...
💡 Tips: Use Tab for auto-completion, ↑/↓ for history

🗡️  create a React chat application
⏳ Thinking...
╭─────────────────────────────────────────────╮
│ ✅ Success                                  │
│ Created: projects/chat                      │
╰─────────────────────────────────────────────╯
```

### 2. Rich UI Components

- **Colored Panels** - Success/failure with borders
- **Tables** - Formatted command output
- **Spinners** - Real-time processing indicators
- **Syntax Highlighting** - Code snippets
- **Progress Bars** - Long-running tasks

### 3. Auto-Completion (Tab)

Press `Tab` for context-aware completions:

```
🗡️  scr[Tab]          → src/
🗡️  gi[Tab]           → git
🗡️  scaffold --type [Tab]  → python_package, react_app, nodejs_app
🗡️  ui --framework [Tab]   → react, vue, angular
🗡️  test --framework [Tab] → pytest, jest, unittest
```

### 4. Command History

- **↑/↓ arrows** - Navigate history
- **`/history`** - View command history
- **Persistent** - Saved to `~/.jebat_history`

### 5. Slash Commands

| Command | Description |
|---------|-------------|
| `/help` | Show detailed help |
| `/clear` | Clear screen |
| `/history` | Show command history |
| `/config` | Show configuration |
| `/status` | Show system status |
| `/models` | Show available AI models |
| `/files` | Show recent files |
| `/undo` | Undo last action |
| `/settings` | Open settings |
| `/exit` | Exit JEBAT |

---

## 📚 Commands

### Create & Scaffold

```bash
# Create from description
🗡️  create a React chat application with WebSocket

# Scaffold project
🗡️  scaffold myapp --type python_package
🗡️  scaffold dashboard --type react_app
🗡️  scaffold api --type nodejs_app
```

### Code Operations

```bash
# Review code
🗡️  review src/main.py
🗡️  review components/Login.tsx

# Generate code
🗡️  generate a Flask REST API with JWT authentication
🗡️  generate a Python utility to parse CSV files
```

### UI Generation

```bash
# Generate UI with Stitch MCP
🗡️  ui modern login form with email and social login
🗡️  ui analytics dashboard with charts --framework react
🗡️  ui e-commerce product card --framework vue
```

### Debug

```bash
# Debug error
🗡️  debug "ModuleNotFoundError: No module named 'flask'"

# Debug with file context
🗡️  debug "TypeError: NoneType has no attribute 'split'" --file src/parser.py
```

### Git Operations

```bash
# Initialize repo
🗡️  git init --path projects/myapp

# Stage and commit
🗡️  git add --path projects/myapp --files src/
🗡️  git commit --path projects/myapp -m "feat: add user authentication"

# Check status
🗡️  git status --path projects/myapp

# View log
🗡️  git log --path projects/myapp
```

### Tests

```bash
# Auto-detect framework
🗡️  test --path tests/

# Specify framework
🗡️  test --framework pytest --path tests/
🗡️  test --framework jest --path src/__tests__/
```

---

## 🎨 Interactive Mode Features

### Real-Time Status

```bash
🗡️  /status

╭─────────────────────────────────────────────╮
│ 📊 System Status                            │
├─────────────────────────────────────────────┤
│ Commands Executed: 15                       │
│ Successful: 12                              │
│ Failed: 3                                   │
│ Uptime: 0:23:45                             │
│ Rich UI: Enabled                            │
│ Prompt Toolkit: Enabled                     │
╰─────────────────────────────────────────────╯
```

### Command History

```bash
🗡️  /history

╭──────────────────────────────────────────────────────────────╮
│ 📜 Command History (last 20)                                 │
├────┬────────────────────────────┬────────┬──────────────────┤
│ #  │ Command                    │ Result │ Time             │
├────┼────────────────────────────┼────────┼──────────────────┤
│ 1  │ create a React chat app    │ ✓      │ 2026-02-18 10:30 │
│ 2  │ review src/main.py         │ ✓      │ 2026-02-18 10:32 │
│ 3  │ debug "ModuleNotFound..."  │ ✓      │ 2026-02-18 10:35 │
│ 4  │ git commit -m "fix: bug"   │ ✗      │ 2026-02-18 10:37 │
╰────┴────────────────────────────┴────────┴──────────────────╯
```

### Configuration View

```bash
🗡️  /config

╭─────────────────────────────────────────────╮
│ ⚙️  Configuration                           │
├─────────────────────────────────────────────┤
│ Sandbox Strict Mode: True                   │
│ Allowed Paths: 4                            │
│ Allowed Commands: 15                        │
│ Current Project: myapp                      │
╰─────────────────────────────────────────────╯
```

### Available Models

```bash
🗡️  /models

╭──────────────────────────────────────────────────────────────╮
│ 🤖 Available AI Models                                       │
├──────────────┬─────────────┬─────────────────┬──────────────┤
│ Model        │ Type        │ Status          │ Description  │
├──────────────┼─────────────┼─────────────────┼──────────────┤
│ Ultra-Think  │ Reasoning   │ ✓ Active        │ Deep reason  │
│ Ultra-Loop   │ Processing  │ ✓ Active        │ Continuous   │
│ Stitch MCP   │ UI Gen      │ ⏳ Simulated    │ Text-to-UI   │
╰──────────────┴─────────────┴─────────────────┴──────────────╯
```

---

## ⌨️ Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `Tab` | Auto-completion |
| `↑` / `↓` | History navigation |
| `Ctrl+D` | Exit |
| `Ctrl+C` | Cancel current input |
| `Ctrl+L` | Clear screen (in some terminals) |

---

## 🔧 Configuration

### Disable Features

```bash
# Disable Rich UI (plain text output)
python -m jebat_dev.gateway --no-rich

# Disable prompt-toolkit (no auto-completion)
python -m jebat_dev.gateway --no-prompt-toolkit

# Disable both
python -m jebat_dev.gateway --no-rich --no-prompt-toolkit
```

### Environment Variables

```bash
# Set in .env or environment
JEBAT_RICH_ENABLED=true
JEBAT_PROMPT_TOOLKIT_ENABLED=true
JEBAT_HISTORY_FILE=~/.jebat_history
```

---

## 📊 Output Examples

### Success Output

```
🗡️  scaffold myapp --type python_package
⏳ Thinking...
╭─────────────────────────────────────────────╮
│ ✅ Success                                  │
│ Scaffolded python_package project: myapp    │
╰─────────────────────────────────────────────╯

📁 Files:
  ✓ projects/myapp
  ✓ projects/myapp/setup.py
  ✓ projects/myapp/README.md
  ✓ projects/myapp/myapp/__init__.py
```

### Error Output

```
🗡️  debug "ModuleNotFoundError: No module named 'flask'"
⏳ Thinking...
╭─────────────────────────────────────────────╮
│ ✅ Success                                  │
│ Debug analysis complete                     │
╰─────────────────────────────────────────────╯

⚠️  Issues:
  • Import Error

🔍 Cause: Module 'flask' is not installed or not found
🔧 Fix: Install the module: pip install flask
```

### Test Results

```
🗡️  test --framework pytest
⏳ Thinking...
╭─────────────────────────────────────────────╮
│ ✅ Success                                  │
│ Tests: 10 passed, 2 failed                  │
╰─────────────────────────────────────────────╯

📊 Test Results:
  Total: 12 | Passed: 10 | Failed: 2

  Failures:
    - test_login_failed: AssertionError: Expected 200, got 401...
    - test_user_creation: ValueError: Invalid email format...
```

---

## 🎯 Best Practices

### 1. Use Descriptive Commands

```bash
# ❌ Too vague
🗡️  create app

# ✅ Specific and clear
🗡️  create a React dashboard with real-time charts and user authentication
```

### 2. Leverage Auto-Completion

```bash
# Start typing and press Tab
🗡️  scaf[Tab] → scaffold
🗡️  scaffold --type [Tab] → python_package, react_app, nodejs_app
```

### 3. Review Before Committing

```bash
# Check git status first
🗡️  git status --path projects/myapp

# Then commit
🗡️  git commit --path projects/myapp -m "feat: add authentication"
```

### 4. Use History for Repetition

```bash
# Press ↑ to recall last command
# Edit and re-execute
```

### 5. Check Status Regularly

```bash
🗡️  /status
🗡️  /history
```

---

## 🐛 Troubleshooting

### Issue: Auto-completion not working

```bash
# Ensure prompt-toolkit is installed
pip install prompt-toolkit

# Or disable and use basic mode
python -m jebat_dev.gateway --no-prompt-toolkit
```

### Issue: Rich UI not displaying correctly

```bash
# Check terminal supports colors
# Or disable Rich
python -m jebat_dev.gateway --no-rich
```

### Issue: History not persisting

```bash
# Check ~/.jebat_history exists
# Ensure write permissions
```

---

## 🆚 Comparison with Other Tools

| Feature | JEBAT | Claude Code | Mistral Vibe | Kilocode |
|---------|-------|-------------|--------------|----------|
| REPL Interface | ✅ | ✅ | ✅ | ✅ |
| Auto-Completion | ✅ | ✅ | ✅ | ✅ |
| Rich UI | ✅ | ✅ | ⚠️ | ✅ |
| Slash Commands | ✅ | ✅ | ✅ | ✅ |
| Git Integration | ✅ | ✅ | ⚠️ | ✅ |
| Test Running | ✅ | ⚠️ | ❌ | ✅ |
| UI Generation | ✅ | ❌ | ❌ | ❌ |
| Local-Only | ✅ | ❌ | ❌ | ✅ |

---

## 🗡️ "Code with Precision"

> *"Like Hang Jebat, code with precision, speed, and intelligence."*

---

**Next**: Try it now with `python -m jebat_dev.gateway`
