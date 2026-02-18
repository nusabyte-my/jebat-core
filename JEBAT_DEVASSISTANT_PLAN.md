# 🗡️ JEBAT DevAssistant - Local Development AI

**Inspired by**: OpenClaw Architecture + Google Stitch MCP + JEBAT Intelligence

**Goal**: Create a local development assistant that works ONLY inside this Dev environment to help you build comprehensive applications.

---

## 🎯 Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│              JEBAT DevAssistant                          │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌──────────────┐         ┌──────────────┐             │
│  │   Gateway    │◄───────►│   Brain      │             │
│  │  (Local FS)  │         │ (JEBAT Core) │             │
│  └──────────────┘         └──────────────┘             │
│         │                       │                       │
│         ▼                       ▼                       │
│  ┌──────────────┐         ┌──────────────┐             │
│  │   Sandbox    │         │   Skills     │             │
│  │  (Dev Env)   │         │ (Dev Tools)  │             │
│  └──────────────┘         └──────────────┘             │
│                                                          │
│  ┌──────────────────────────────────────────────┐      │
│  │        Google Stitch MCP Integration          │      │
│  │     (UI/UX Generation from descriptions)      │      │
│  └──────────────────────────────────────────────┘      │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

---

## 🔧 Components

### 1. Gateway (Local Environment)
**Purpose**: Interface between you and JEBAT

**Channels**:
- ✅ **Terminal CLI** - `jebat <command>`
- ✅ **WebSocket** - Real-time chat at `ws://localhost:8787/ws`
- ✅ **File Watcher** - Monitors Dev folder for changes
- 🔄 **VSCode Extension** - Coming soon

**Implementation**:
```python
# jebat_dev/gateway/local_gateway.py
class LocalGateway:
    - CLI command parser
    - File system watcher
    - WebSocket server
    - Context manager (Dev environment only)
```

### 2. Brain (JEBAT Intelligence)
**Purpose**: Decision making and reasoning

**Components**:
- ✅ **Ultra-Think** - Deep reasoning for complex tasks
- ✅ **Memory System** - Remembers your project context
- ✅ **Decision Engine** - Routes tasks to right skills
- ✅ **Agent Orchestrator** - Manages multiple dev agents

**Implementation**:
```python
# jebat_dev/brain/dev_brain.py
class DevBrain:
    - Ultra-Think integration
    - Project memory (codebase knowledge)
    - Task planning and decomposition
    - Multi-agent coordination
```

### 3. Sandbox (Dev Environment)
**Purpose**: Safe execution of development tasks

**Features**:
- ✅ **Project Isolation** - Only works in `C:\Users\shaid\Desktop\Dev`
- ✅ **File Operations** - Read/write/modify code files
- ✅ **Command Execution** - Run npm, pip, git, etc.
- ✅ **Safety Rules** - No destructive operations without confirmation

**Implementation**:
```python
# jebat_dev/sandbox/dev_sandbox.py
class DevSandbox:
    - Allowed paths: [Dev/, Dev/jebat/, Dev/projects/]
    - Allowed commands: [npm, pip, git, python, node, etc.]
    - Blocked operations: [rm -rf, format, sudo, etc.]
    - Audit logging: All actions logged
```

### 4. Skills (Development Capabilities)
**Purpose**: What JEBAT can do for you

**Core Skills**:

| Skill | Description | Example |
|-------|-------------|---------|
| `code.read` | Read and analyze code files | "Read the chat component" |
| `code.write` | Create/modify code files | "Create a login form" |
| `code.review` | Review code for issues | "Check for bugs in this" |
| `code.generate` | Generate new code | "Generate a REST API" |
| `ui.generate` | Create UI with Stitch MCP | "Make a dashboard UI" |
| `project.scaffold` | Create project structure | "Scaffold a React app" |
| `dependency.manage` | Install/manage packages | "Add React to the project" |
| `git.operations` | Git commands | "Commit my changes" |
| `test.run` | Run tests | "Run the test suite" |
| `debug.analyze` | Analyze errors | "Why is this failing?" |

**Implementation**:
```python
# jebat_dev/skills/
├── code_skills.py      # Code reading/writing
├── ui_skills.py        # UI generation (Stitch MCP)
├── project_skills.py   # Project scaffolding
├── git_skills.py       # Git operations
├── test_skills.py      # Testing
└── debug_skills.py     # Debugging
```

### 5. Google Stitch MCP Integration
**Purpose**: Generate UI/UX from descriptions

**Features**:
- ✅ **Text-to-UI** - Describe UI, get components
- ✅ **Figma Integration** - Import/export designs
- ✅ **Component Generation** - React, Vue, Angular
- ✅ **Style Transfer** - Apply design systems

**Implementation**:
```python
# jebat_dev/integrations/stitch_mcp.py
class StitchMCPClient:
    - Connect to Google Stitch MCP server
    - Send prompts, receive UI designs
    - Export to React/Vue components
    - Apply project styling
```

---

## 🚀 How It Works

### Example Flow: "Create a chat application"

```
1. You type: "jebat create a chat application with React"

2. Gateway receives command
   └─> Parses intent: CREATE_PROJECT
   └─> Extracts params: {type: "chat", framework: "React"}

3. Brain analyzes request (Ultra-Think)
   └─> Decomposes into tasks:
       - Scaffold React project
       - Create chat component
       - Add WebSocket integration
       - Generate UI with Stitch
       - Install dependencies

4. Brain assigns tasks to agents
   └─> Agent 1: Project scaffolding
   └─> Agent 2: Component creation
   └─> Agent 3: UI generation (Stitch MCP)

5. Sandbox executes safely
   └─> Creates files in Dev/projects/chat-app/
   └─> Runs: npx create-react-app
   └─> Installs: socket.io-client
   └─> Generates UI components via Stitch

6. Memory stores context
   └─> Remembers project structure
   └─> Tracks what was created
   └─> Ready for next command: "add user authentication"
```

---

## 📁 Project Structure

```
Dev/
├── jebat_dev/                    # NEW: DevAssistant
│   ├── __init__.py
│   ├── gateway/                  # Input/output
│   │   ├── cli.py               # Command line interface
│   │   ├── websocket.py         # Real-time chat
│   │   └── file_watcher.py      # Monitor changes
│   ├── brain/                   # Intelligence
│   │   ├── dev_brain.py         # Central reasoning
│   │   ├── task_planner.py      # Task decomposition
│   │   └── context_manager.py   # Project context
│   ├── sandbox/                 # Safe execution
│   │   ├── dev_sandbox.py       # Execution environment
│   │   ├── path_validator.py    # Path security
│   │   └── command_runner.py    # Safe command execution
│   ├── skills/                  # Capabilities
│   │   ├── code_skills.py       # Code operations
│   │   ├── ui_skills.py         # UI generation (Stitch)
│   │   ├── project_skills.py    # Scaffolding
│   │   ├── git_skills.py        # Git ops
│   │   └── test_skills.py       # Testing
│   ├── integrations/            # External tools
│   │   ├── stitch_mcp.py        # Google Stitch
│   │   ├── npm.py              # NPM integration
│   │   └── git.py              # Git integration
│   └── config/                  # Configuration
│       ├── dev_config.yaml      # Dev environment config
│       └── safety_rules.yaml    # Safety constraints
│
├── jebat/                        # EXISTING: Core JEBAT
│   ├── core/                     # Memory, Cache, Decision
│   ├── features/                 # Ultra-Loop, Ultra-Think
│   └── services/                 # WebUI, API, MCP
│
└── projects/                     # YOUR PROJECTS
    ├── chat-app/                 # Created by JEBAT
    ├── dashboard/                # Created by JEBAT
    └── ...
```

---

## 🔐 Safety & Security

### Environment Lock
```yaml
# Only allowed to work in these paths
allowed_paths:
  - C:/Users/shaid/Desktop/Dev
  - C:/Users/shaid/Desktop/Dev/jebat
  - C:/Users/shaid/Desktop/Dev/projects
  - C:/Users/shaid/Desktop/Dev/jebat_dev

# Blocked paths (never access)
blocked_paths:
  - C:/Windows
  - C:/Program Files
  - C:/Users/shaid/Documents
  - C:/Users/shaid/Desktop (except Dev/)
```

### Command Safety
```yaml
# Allowed commands
allowed_commands:
  - npm, npx, yarn
  - pip, pip3
  - python, python3
  - node, nodejs
  - git
  - docker
  - curl, wget

# Requires confirmation
confirmation_required:
  - rm, rmdir, del
  - format
  - Any command modifying >10 files

# Blocked commands
blocked_commands:
  - sudo, runas
  - shutdown, reboot
  - Any system-level operations
```

### Audit Logging
```python
# Every action is logged
{
  "timestamp": "2026-02-17T23:30:00",
  "action": "code.write",
  "path": "Dev/projects/chat-app/src/App.js",
  "agent": "CodeAgent-001",
  "status": "success",
  "user_confirmed": false,
}
```

---

## 🎯 Usage Examples

### 1. Create New Project
```bash
# Terminal
jebat create a React dashboard with charts

# JEBAT responds:
🗡️ Creating React dashboard...
  ✓ Scaffolded project: Dev/projects/dashboard/
  ✓ Installed dependencies (react, chart.js, etc.)
  ✓ Generated UI with Stitch MCP
  ✓ Created sample components
  ✓ Initialized git repository

Project ready! Open with: cd projects/dashboard && npm start
```

### 2. Modify Existing Code
```bash
# Terminal
jebat add user authentication to the chat app

# JEBAT:
🗡️ Adding authentication to chat-app...
  ✓ Analyzed existing codebase
  ✓ Added JWT authentication
  ✓ Created login/register components
  ✓ Updated API endpoints
  ✓ Added protected routes

Changes committed to git. View diff with: git diff
```

### 3. Generate UI with Stitch
```bash
# Terminal
jebat ui generate a modern login form with email and social login

# JEBAT + Stitch MCP:
🗡️ Generating UI with Google Stitch...
  ✓ Created LoginForm component
  ✓ Added email validation
  ✓ Integrated Google/Facebook login
  ✓ Applied project theme
  ✓ Generated responsive styles

Files created:
  - src/components/LoginForm.jsx
  - src/styles/LoginForm.css
  - src/hooks/useAuth.js
```

### 4. Debug Issues
```bash
# Terminal
jebat why is the chat not connecting

# JEBAT:
🗡️ Analyzing connection issue...
  ✓ Checked WebSocket configuration
  ✓ Found: Server URL incorrect in config.js
  ✓ Expected: ws://localhost:8787
  ✓ Found: ws://localhost:3000
  
  Fix available. Apply fix? [y/N]
  
  ✓ Applied fix
  ✓ Tested connection: SUCCESS

Issue resolved!
```

---

## 🔧 Configuration

### dev_config.yaml
```yaml
environment:
  root_path: C:/Users/shaid/Desktop/Dev
  workspace: Dev/
  projects_dir: Dev/projects/

brain:
  ultra_think_enabled: true
  default_mode: deliberate
  memory_enabled: true
  max_agents: 5

sandbox:
  strict_mode: true
  require_confirmation:
    - destructive_operations
    - bulk_changes
  auto_confirm:
    - file_read
    - code_analysis

integrations:
  stitch_mcp:
    enabled: true
    server: http://localhost:8080
    default_framework: react
  npm:
    auto_install: true
    save_dev: false
  git:
    auto_commit: false
    commit_template: "JEBAT: {description}"
```

---

## 🚀 Implementation Plan

### Phase 1: Core (Week 1)
- [ ] Create `jebat_dev/` structure
- [ ] Implement LocalGateway (CLI + file watcher)
- [ ] Create DevBrain with Ultra-Think integration
- [ ] Build DevSandbox with safety rules
- [ ] Implement basic Skills (read, write, analyze)

### Phase 2: Stitch MCP (Week 2)
- [ ] Integrate Google Stitch MCP client
- [ ] Create UI generation skills
- [ ] Add component export (React/Vue)
- [ ] Style system integration

### Phase 3: Advanced Skills (Week 3)
- [ ] Project scaffolding
- [ ] Git operations
- [ ] Testing integration
- [ ] Debug analysis

### Phase 4: Polish (Week 4)
- [ ] Memory integration (remembers projects)
- [ ] Multi-agent coordination
- [ ] Audit logging
- [ ] Documentation

---

## 🎯 Success Criteria

- ✅ **Works ONLY in Dev environment** - Locked to `C:\Users\shaid\Desktop\Dev`
- ✅ **Understands development tasks** - Code, UI, projects, debugging
- ✅ **Generates UI with Stitch MCP** - Text-to-UI generation
- ✅ **Safe execution** - Sandbox with strict rules
- ✅ **Remembers context** - Memory of your projects
- ✅ **Multi-agent** - Can parallelize complex tasks
- ✅ **CLI + WebSocket** - Multiple interaction modes

---

## 🗡️ "Your Personal Dev Assistant"

> *"Like Hang Jebat served with loyalty, JEBAT DevAssistant serves your development needs with precision, safety, and intelligence."*

**Status**: Ready to Implement  
**Estimated Time**: 3-4 weeks  
**Priority**: HIGH

---

**Next Action**: Start Phase 1 implementation?
