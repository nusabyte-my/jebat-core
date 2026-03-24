# 🔌 JEBAT IDE Integration Guide

**Connect JEBAT AI to your favorite code editor**

---

## 📋 Table of Contents

1. [Zed Editor](#zed-editor)
2. [VS Code](#vs-code)
3. [Cursor](#cursor)
4. [JetBrains IDEs](#jetbrains-ides)
5. [Neovim](#neovim)
6. [Sublime Text](#sublime-text)
7. [Generic LLM Proxy](#generic-llm-proxy)

---

## 🎯 Quick Start

### **Prerequisites**

1. **JEBAT API Running**
   ```bash
   # Start JEBAT API server
   docker-compose up -d jebat-api
   
   # Or run locally
   python -m uvicorn jebat.services.api.jebat_api:app --reload
   ```

2. **API Endpoint**
   ```
   Base URL: http://localhost:8000/api/v1
   Chat Endpoint: http://localhost:8000/api/v1/chat/completions
   ```

3. **API Key** (Optional for local)
   ```
   For local: jebat-local-key
   For production: Your API key
   ```

---

## 🦓 Zed Editor

### **Method 1: Zed AI Extension**

Zed supports custom AI providers via the `settings.json` file.

#### **Step 1: Open Settings**
```bash
# Open Zed settings
Cmd + , (macOS)
Ctrl + , (Windows/Linux)
```

#### **Step 2: Add JEBAT Provider**

Edit `settings.json`:

```json
{
  "ai": {
    "providers": {
      "jebat": {
        "name": "JEBAT AI",
        "type": "openai-compatible",
        "api_url": "http://localhost:8000/api/v1",
        "api_key": "jebat-local-key",
        "models": {
          "chat": "jebat-pro",
          "completion": "jebat-fast"
        }
      }
    },
    "default_provider": "jebat"
  }
}
```

#### **Step 3: Use JEBAT in Zed**

- **Cmd + K** (macOS) or **Ctrl + K** (Windows/Linux) - Open AI chat
- **Cmd + Shift + A** - Inline edit
- Select "JEBAT AI" from provider dropdown

---

### **Method 2: Zed Custom Extension**

Create a custom Zed extension:

#### **Step 1: Create Extension Folder**
```bash
mkdir -p ~/.config/zed/extensions/jebat-ai
cd ~/.config/zed/extensions/jebat-ai
```

#### **Step 2: Create extension.json**
```json
{
  "name": "jebat-ai",
  "version": "1.0.0",
  "authors": ["Your Name"],
  "description": "JEBAT AI integration for Zed",
  "repository": "https://github.com/yourusername/jebat-zed"
}
```

#### **Step 3: Create src/jebat.rs**
```rust
use zed_extension_api as zed;

struct JebatExtension {
    api_url: String,
    api_key: String,
}

impl JebatExtension {
    fn new() -> Self {
        Self {
            api_url: "http://localhost:8000/api/v1".to_string(),
            api_key: "jebat-local-key".to_string(),
        }
    }
}

impl zed::Extension for JebatExtension {
    fn new() -> Self {
        Self::new()
    }

    fn language_model_completions(
        &mut self,
        prompt: String,
        _context: zed::LanguageModelContext,
    ) -> Result<String, String> {
        // Call JEBAT API
        let response = zed::http::post(
            &format!("{}/chat/completions", self.api_url),
            &[
                ("Authorization", &format!("Bearer {}", self.api_key)),
                ("Content-Type", "application/json"),
            ],
            &serde_json::json!({
                "message": prompt,
                "mode": "deliberate",
                "stream": false
            }).to_string(),
        )?;

        Ok(response)
    }
}

zed::register_extension!(JebatExtension);
```

#### **Step 4: Build & Install**
```bash
# Build extension
zed-extension build

# Install
zed-extension install .
```

---

## 💻 VS Code

### **Method 1: Continue Extension** (Recommended)

Project-start workflow:

- read [VSCODE_JEBAT_HERMES_PROJECT_START.md](/home/humm1ngb1rd/workspace/ai/projects/jebat-core/docs/VSCODE_JEBAT_HERMES_PROJECT_START.md) before starting a new repo
- use `hermes-agent` as the default anchor skill
- capture the repo before implementation begins

[Continue](https://continue.dev) is an open-source AI code assistant that supports custom providers.

#### **Step 1: Install Continue**
1. Open VS Code
2. Go to Extensions (Cmd/Ctrl + Shift + X)
3. Search for "Continue"
4. Install

#### **Step 2: Configure JEBAT**

Open `~/.continue/config.json`:

```json
{
  "models": [
    {
      "title": "JEBAT Pro",
      "provider": "openai-compatible",
      "model": "jebat-pro",
      "apiBase": "http://localhost:8000/api/v1",
      "apiKey": "jebat-local-key"
    },
    {
      "title": "JEBAT Fast",
      "provider": "openai-compatible",
      "model": "jebat-fast",
      "apiBase": "http://localhost:8000/api/v1",
      "apiKey": "jebat-local-key"
    },
    {
      "title": "JEBAT Deep",
      "provider": "openai-compatible",
      "model": "jebat-deep",
      "apiBase": "http://localhost:8000/api/v1",
      "apiKey": "jebat-local-key"
    }
  ],
  "tabAutocompleteModel": {
    "title": "JEBAT Fast",
    "provider": "openai-compatible",
    "model": "jebat-fast",
    "apiBase": "http://localhost:8000/api/v1",
    "apiKey": "jebat-local-key"
  }
}
```

#### **Step 3: Use JEBAT**

- **Cmd/Ctrl + L** - Open chat sidebar
- **Cmd/Ctrl + I** - Inline edit
- **Tab** - Accept autocomplete

---

### **Method 2: CodeGPT Extension**

#### **Step 1: Install CodeGPT**
1. Extensions → Search "CodeGPT"
2. Install

#### **Step 2: Configure Provider**

1. Open CodeGPT settings
2. Click "Add Provider"
3. Select "OpenAI Compatible"
4. Configure:
   ```
   Name: JEBAT AI
   API URL: http://localhost:8000/api/v1/chat/completions
   API Key: jebat-local-key
   Model: jebat-pro
   ```

---

### **Method 3: Custom Extension**

Create your own VS Code extension:

#### **Step 1: Generate Extension**
```bash
npm install -g yo generator-code
yo code
# Choose "New Extension (TypeScript)"
```

#### **Step 2: Add JEBAT Integration**

Edit `src/extension.ts`:

```typescript
import * as vscode from 'vscode';
import axios from 'axios';

export function activate(context: vscode.ExtensionContext) {
    const disposable = vscode.commands.registerCommand(
        'jebat.askAI',
        async () => {
            const editor = vscode.window.activeTextEditor;
            if (!editor) return;

            const selection = editor.document.getText(editor.selection);
            const prompt = await vscode.window.showInputBox({
                prompt: 'Ask JEBAT AI',
                value: selection
            });

            if (!prompt) return;

            vscode.window.withProgress(
                {
                    location: vscode.ProgressLocation.Notification,
                    title: 'JEBAT AI is thinking...',
                    cancellable: false
                },
                async () => {
                    try {
                        const response = await axios.post(
                            'http://localhost:8000/api/v1/chat/completions',
                            {
                                message: prompt,
                                mode: 'deliberate',
                                code: selection
                            },
                            {
                                headers: {
                                    'Authorization': 'Bearer jebat-local-key',
                                    'Content-Type': 'application/json'
                                }
                            }
                        );

                        const result = response.data.response;
                        
                        // Insert result at cursor
                        editor.edit(editBuilder => {
                            editBuilder.replace(editor.selection, result);
                        });

                        vscode.window.showInformationMessage('✅ JEBAT AI completed!');
                    } catch (error) {
                        vscode.window.showErrorMessage('❌ JEBAT AI error: ' + error);
                    }
                }
            );
        }
    );

    context.subscriptions.push(disposable);
}
```

#### **Step 3: Add to package.json**
```json
{
  "contributes": {
    "commands": [
      {
        "command": "jebat.askAI",
        "title": "JEBAT: Ask AI"
      }
    ],
    "keybindings": [
      {
        "command": "jebat.askAI",
        "key": "ctrl+shift+j",
        "mac": "cmd+shift+j",
        "when": "editorTextFocus"
      }
    ]
  }
}
```

#### **Step 4: Run Extension**
```bash
# Install dependencies
npm install

# Run extension (F5)
npm run watch
```

---

## 🎯 Cursor

Cursor natively supports custom OpenAI-compatible endpoints!

### **Step 1: Open Cursor Settings**
```
Cmd/Ctrl + , → AI → Custom Model
```

### **Step 2: Add JEBAT**

```
Model Name: JEBAT Pro
API Endpoint: http://localhost:8000/api/v1/chat/completions
API Key: jebat-local-key
Model ID: jebat-pro
```

### **Step 3: Enable Features**

- ✅ Chat (Cmd/Ctrl + L)
- ✅ Inline Edit (Cmd/Ctrl + K)
- ✅ Tab Autocomplete

---

## 🧠 JetBrains IDEs (IntelliJ, WebStorm, PyCharm)

### **Method 1: CodeGPT Plugin**

#### **Step 1: Install Plugin**
1. Settings → Plugins
2. Search "CodeGPT"
3. Install & Restart

#### **Step 2: Configure**
1. Settings → Tools → CodeGPT
2. Add Provider → OpenAI Compatible
3. Configure:
   ```
   Name: JEBAT
   API URL: http://localhost:8000/api/v1/chat/completions
   API Key: jebat-local-key
   Model: jebat-pro
   ```

---

### **Method 2: Continue Plugin**

#### **Step 1: Install**
1. Plugins → Marketplace
2. Search "Continue"
3. Install

#### **Step 2: Configure**

Edit `~/.continue/config.json`:

```json
{
  "models": [
    {
      "title": "JEBAT Pro",
      "provider": "openai-compatible",
      "apiBase": "http://localhost:8000/api/v1",
      "apiKey": "jebat-local-key",
      "model": "jebat-pro"
    }
  ]
}
```

---

## ⚡ Neovim

### **Using Copilot.vim with JEBAT**

#### **Step 1: Install Dependencies**
```vim
" In your init.vim or init.lua
Plug 'github/copilot.vim'
Plug 'nvim-lua/plenary.nvim'
```

#### **Step 2: Configure**
```lua
-- In init.lua
require('copilot').setup({
  panel = {
    enabled = true,
    auto_refresh = true,
    keymap = {
      jump_next = "<c-j>",
      jump_prev = "<c-k>",
      accept = "<c-y>",
      refresh = "r",
      open = "<M-CR>"
    },
  },
  server = {
    url = "http://localhost:8000/api/v1",
    proxy = nil,
  },
  suggestion = {
    enabled = true,
    auto_trigger = true,
    debounce = 75,
    keymap = {
      accept = "<c-l>",
      accept_word = false,
      accept_line = false,
      next = "<c-j>",
      prev = "<c-k>",
      dismiss = "<c-]>",
    },
  },
})
```

---

### **Using ChatGPT.nvim**

#### **Step 1: Install**
```lua
use {
  "jackMort/ChatGPT.nvim",
  requires = {
    "MunifTanjim/nui.nvim",
    "nvim-lua/plenary.nvim",
    "folke/trouble.nvim",
  },
  config = function()
    require("chatgpt").setup({
      api_url = "http://localhost:8000/api/v1",
      api_key = "jebat-local-key",
      models = {
        "jebat-pro",
        "jebat-fast",
        "jebat-deep"
      },
    })
  end
}
```

#### **Step 2: Use**
```vim
:ChatGPT          " Open chat
:ChatGPTEdit      " Edit selected
:ChatGPTComplete  " Complete code
```

---

## 📝 Sublime Text

### **Using SublimeAI Package**

#### **Step 1: Install Package Control**
```
Cmd/Ctrl + Shift + P → Install Package Control
```

#### **Step 2: Install SublimeAI**
```
Cmd/Ctrl + Shift + P → Package Control: Install Package
Search: SublimeAI
```

#### **Step 3: Configure**

Edit `Packages/User/SublimeAI.sublime-settings`:

```json
{
  "api_url": "http://localhost:8000/api/v1",
  "api_key": "jebat-local-key",
  "model": "jebat-pro",
  "stream": false
}
```

#### **Step 4: Key Bindings**

Edit `Packages/User/Default (OSX).sublime-keymap`:

```json
[
  {
    "keys": ["ctrl+shift+a"],
    "command": "sublime_ai_chat"
  },
  {
    "keys": ["ctrl+shift+e"],
    "command": "sublime_ai_edit"
  }
]
```

---

## 🔧 Generic LLM Proxy Setup

### **Using LiteLLM Proxy**

LiteLLM provides OpenAI-compatible proxy for any LLM.

#### **Step 1: Install LiteLLM**
```bash
pip install litellm[proxy]
```

#### **Step 2: Create config.yaml**
```yaml
model_list:
  - model_name: jebat-pro
    litellm_params:
      model: openai/jebat-pro
      api_base: http://localhost:8000/api/v1
      api_key: jebat-local-key
  
  - model_name: jebat-fast
    litellm_params:
      model: openai/jebat-fast
      api_base: http://localhost:8000/api/v1
      api_key: jebat-local-key

  - model_name: jebat-deep
    litellm_params:
      model: openai/jebat-deep
      api_base: http://localhost:8000/api/v1
      api_key: jebat-local-key
```

#### **Step 3: Run Proxy**
```bash
litellm --config config.yaml
```

#### **Step 4: Connect Any IDE**

Now any IDE that supports OpenAI can use JEBAT:

```
API URL: http://0.0.0.0:4000
API Key: jebat-local-key
Model: jebat-pro
```

---

## 🌐 JEBAT API Server Setup

### **Option 1: Docker (Recommended)**

```bash
# Start API server only
docker-compose up -d jebat-api

# Check status
docker-compose ps jebat-api

# View logs
docker-compose logs -f jebat-api
```

### **Option 2: Local Python**

```bash
# Install dependencies
pip install fastapi uvicorn pydantic

# Start server
python -m uvicorn jebat.services.api.jebat_api:app --reload --host 0.0.0.0 --port 8000
```

### **Option 3: Development Mode**

```bash
# With auto-reload
python -m uvicorn jebat.services.api.jebat_api:app \
  --reload \
  --host 0.0.0.0 \
  --port 8000 \
  --log-level debug
```

---

## 🔐 API Authentication

### **Local Development**
```
API Key: jebat-local-key
(or no key for local-only)
```

### **Production**
```
API Key: Your secure key
Set in .env: API_KEY=your-secure-key-here
```

### **Environment Variables**

Create `.env`:

```bash
# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_KEY=jebat-secure-key-123

# CORS (for web IDEs)
CORS_ORIGINS=http://localhost:3000,http://localhost:5173

# Rate Limiting
RATE_LIMIT_PER_MINUTE=60
```

---

## 📊 Testing Connection

### **Test with cURL**
```bash
curl -X POST http://localhost:8000/api/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer jebat-local-key" \
  -d '{
    "message": "Hello from my IDE!",
    "mode": "fast"
  }'
```

### **Test with Python**
```python
import requests

response = requests.post(
    'http://localhost:8000/api/v1/chat/completions',
    headers={
        'Authorization': 'Bearer jebat-local-key',
        'Content-Type': 'application/json'
    },
    json={
        'message': 'Test from IDE',
        'mode': 'fast'
    }
)

print(response.json())
```

---

## 🐛 Troubleshooting

### **Connection Refused**
```bash
# Check if API is running
curl http://localhost:8000/api/v1/health

# Check port
netstat -ano | findstr :8000

# Restart API
docker-compose restart jebat-api
```

### **Authentication Failed**
```bash
# Verify API key
echo $API_KEY

# Check .env file
cat .env | grep API_KEY
```

### **CORS Errors (Web IDEs)**
```bash
# Add to .env
CORS_ORIGINS=http://your-ide-url.com

# Restart API
docker-compose restart jebat-api
```

---

## 📚 Quick Reference

### **API Endpoints**

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/v1/health` | GET | Health check |
| `/api/v1/chat/completions` | POST | Chat/Completion |
| `/api/v1/code/complete` | POST | Code completion |
| `/api/v1/code/explain` | POST | Explain code |
| `/api/v1/code/debug` | POST | Debug code |

### **Request Format**
```json
{
  "message": "Your prompt",
  "mode": "deliberate",
  "code": "Optional code context",
  "language": "javascript",
  "stream": false
}
```

### **Response Format**
```json
{
  "response": "AI response",
  "confidence": 0.85,
  "thoughts": 12,
  "execution_time": 2.5
}
```

---

## 🎯 Best Practices

### **1. Use Local for Development**
```bash
# Faster, free, private
API_URL=http://localhost:8000
```

### **2. Set Up API Key**
```bash
# Even for local, good practice
API_KEY=jebat-local-key
```

### **3. Enable CORS for Web IDEs**
```bash
CORS_ORIGINS=http://localhost:*,https://your-domain.com
```

### **4. Monitor Usage**
```bash
# Use Analytics dashboard
start jebat/services/webui/analytics.html
```

### **5. Cache Responses**
```json
{
  "cache": true,
  "cache_ttl": 3600
}
```

---

## 🎉 You're Ready!

**JEBAT is now integrated with your IDE!**

Start using AI-powered coding:
- 💬 Chat with AI
- ✏️ Inline edits
- 🤖 Autocomplete
- 🐛 Debug assistance
- 📝 Code explanations

**Happy Coding!** 🚀

---

**JEBAT** - *Because warriors remember everything that matters.* 🗡️
