# 🗡️ JEBAT DevAssistant

**Your Personal Development AI Assistant**

Inspired by OpenClaw Architecture + Google Stitch MCP + JEBAT Intelligence.

Works **ONLY** inside this Dev environment to help you build applications.

---

## 🚀 Quick Start

### CLI Usage

```bash
# Run via module
python -m jebat_dev.gateway.cli <command> [options]

# Or use the jebat command (after adding to PATH)
jebat <command> [options]
```

### Available Commands

| Command | Description | Example |
|---------|-------------|---------|
| `create` | Create new projects/components | `jebat create a React chat app` |
| `modify` | Modify existing code | `jebat modify add logging` |
| `review` | Review code for issues | `jebat review src/app.py` |
| `generate` | Generate code | `jebat generate a REST API` |
| `ui` | Generate UI with Stitch MCP | `jebat ui modern login form` |
| `debug` | Debug issues | `jebat debug "ModuleNotFoundError"` |
| `scaffold` | Scaffold a new project | `jebat scaffold myapp --type react_app` |
| `git` | Git operations | `jebat git commit -m "fix: bug"` |
| `test` | Run tests | `jebat test --framework pytest` |

---

## 📁 Project Structure

```
jebat_dev/
├── __init__.py              # Package init
├── brain/
│   └── dev_brain.py         # Central intelligence with Ultra-Think
├── gateway/
│   ├── cli.py               # Command-line interface
│   └── websocket.py         # WebSocket server (coming soon)
├── sandbox/
│   └── dev_sandbox.py       # Safe execution environment
├── skills/
│   ├── __init__.py
│   ├── code_skills.py       # Code read/write/review/generate
│   ├── project_skills.py    # Project scaffolding
│   ├── git_skills.py        # Git operations
│   ├── test_skills.py       # Test running
│   └── debug_skills.py      # Error analysis
├── integrations/
│   └── stitch_mcp.py        # Google Stitch MCP integration
└── config/
    └── dev_config.yaml      # Configuration
```

---

## 🔧 Skills System

### Code Skills
- **code.read**: Read and analyze code files
- **code.write**: Create/modify code files
- **code.review**: Review code for issues and best practices
- **code.generate**: Generate new code using Ultra-Think

### Project Skills
- **project.scaffold**: Create project structure from templates
- Supports: Python packages, React apps, Node.js apps

### Git Skills
- **git.init**: Initialize repository
- **git.add**: Stage files
- **git.commit**: Commit changes
- **git.status**: Show status
- **git.push/pull**: Remote operations

### Test Skills
- **test.run**: Run tests with auto-detection
- Supports: pytest, Jest, unittest

### Debug Skills
- **debug.analyze**: Analyze error messages
- **debug.stack_trace**: Parse stack traces
- Pattern matching for common errors

---

## 🔐 Safety & Security

### Environment Lock
Only works in allowed paths:
- `C:/Users/shaid/Desktop/Dev`
- `C:/Users/shaid/Desktop/Dev/jebat`
- `C:/Users/shaid/Desktop/Dev/jebat_dev`
- `C:/Users/shaid/Desktop/Dev/projects`

### Command Safety
```yaml
# Allowed commands
allowed:
  - npm, npx, yarn
  - pip, pip3
  - python, python3
  - node
  - git
  - mkdir, copy, del

# Blocked commands
blocked:
  - sudo, runas
  - shutdown, reboot
  - format
  - System-level operations
```

### Audit Logging
Every action is logged with:
- Timestamp
- Action type
- Path/file affected
- Success/failure status

---

## 🎯 Usage Examples

### 1. Create a New Project

```bash
# Scaffold a Python package
jebat scaffold my_package --type python_package

# Scaffold a React app
jebat scaffold my_dashboard --type react_app

# Scaffold a Node.js app
jebat scaffold my_api --type nodejs_app
```

### 2. Generate Code

```bash
# Generate a REST API
jebat generate a Flask REST API with user authentication

# Generate a utility function
jebat generate a Python function to validate email addresses
```

### 3. Review Code

```bash
# Review a Python file
jebat review src/main.py

# Review a JavaScript file
jebat review components/Login.js
```

### 4. Debug Issues

```bash
# Debug an error
jebat debug "ModuleNotFoundError: No module named 'flask'"

# Debug with file context
jebat debug "TypeError: NoneType has no attribute 'split'" --file src/parser.py
```

### 5. Git Operations

```bash
# Initialize a repo
jebat git init --path projects/myapp

# Stage and commit
jebat git add --path projects/myapp --files src/
jebat git commit --path projects/myapp -m "feat: add user authentication"

# Check status
jebat git status --path projects/myapp
```

### 6. Run Tests

```bash
# Auto-detect framework
jebat test --path tests/

# Specify framework
jebat test --framework pytest --path tests/
jebat test --framework jest --path src/__tests__/
```

### 7. Generate UI with Stitch MCP

```bash
# Generate a login form
jebat ui modern login form with email and social login

# Generate a dashboard
jebat ui analytics dashboard with charts --framework react
```

---

## ⚙️ Configuration

### dev_config.yaml

```yaml
environment:
  root_path: C:/Users/shaid/Desktop/Dev
  workspace: Dev/
  projects_dir: Dev/projects/

brain:
  ultra_think_enabled: true
  default_mode: deliberate
  max_thoughts: 20

sandbox:
  strict_mode: true
  require_confirmation:
    - destructive_operations
    - bulk_changes

integrations:
  stitch_mcp:
    enabled: true
    server: http://localhost:8080
    default_framework: react
```

---

## 🧪 Testing

```bash
# Run DevAssistant tests
python -m pytest jebat_dev/tests/

# Test specific skill
python -m pytest jebat_dev/tests/test_code_skills.py
```

---

## 📝 Implementation Status

| Component | Status | Notes |
|-----------|--------|-------|
| DevBrain | ✅ Complete | Ultra-Think integration |
| DevSandbox | ✅ Complete | Safety rules implemented |
| CLI Gateway | ✅ Complete | All commands working |
| Code Skills | ✅ Complete | Read, write, review, generate |
| Project Skills | ✅ Complete | Templates for 3 project types |
| Git Skills | ✅ Complete | All common operations |
| Test Skills | ✅ Complete | pytest, Jest, unittest |
| Debug Skills | ✅ Complete | Error pattern matching |
| Stitch MCP | ⚠️ Partial | Simulated (server not running) |
| WebSocket | 🔄 Pending | Coming soon |

---

## 🗡️ "Your Personal Dev Assistant"

> *"Like Hang Jebat served with loyalty, JEBAT DevAssistant serves your development needs with precision, safety, and intelligence."*

---

## 📄 License

MIT License - See LICENSE file for details
