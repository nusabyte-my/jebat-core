# 🔌 IDE Integration Quick Start

**Connect JEBAT to your IDE in 5 minutes**

---

## 🚀 Universal Setup (Works for All IDEs)

### **Step 1: Start JEBAT API**

```bash
# Navigate to project
cd C:\Users\shaid\Desktop\Dev

# Start API server
docker-compose up -d jebat-api

# Verify running
curl http://localhost:8000/api/v1/health
# Should return: {"status": "healthy"}
```

### **Step 2: Get API Details**

```
Base URL: http://localhost:8000/api/v1
Chat Endpoint: http://localhost:8000/api/v1/chat/completions
API Key: jebat-local-key (or set your own in .env)
```

### **Step 3: Choose Your IDE**

- [Zed](#zed)
- [VS Code](#vs-code)
- [Cursor](#cursor)
- [JetBrains](#jetbrains)
- [Neovim](#neovim)

---

## 🦓 Zed

### **Quick Config**

1. Open settings: **Cmd/Ctrl + ,**
2. Edit `settings.json`:

```json
{
  "ai": {
    "providers": {
      "jebat": {
        "name": "JEBAT AI",
        "type": "openai-compatible",
        "api_url": "http://localhost:8000/api/v1",
        "api_key": "jebat-local-key"
      }
    },
    "default_provider": "jebat"
  }
}
```

3. **Done!** Use **Cmd/Ctrl + K** to chat

**Full Guide**: See `docs/ZED_SETUP.md`

---

## 💻 VS Code

### **Method 1: Continue Extension** (Easiest)

1. **Install Continue**
   - Extensions → Search "Continue" → Install

2. **Configure**
   - Open `~/.continue/config.json`
   - Add:

```json
{
  "models": [
    {
      "title": "JEBAT Pro",
      "provider": "openai-compatible",
      "model": "jebat-pro",
      "apiBase": "http://localhost:8000/api/v1",
      "apiKey": "jebat-local-key"
    }
  ]
}
```

3. **Use It**
   - **Cmd/Ctrl + L** - Chat
   - **Cmd/Ctrl + I** - Inline edit

### **Method 2: CodeGPT**

1. Install "CodeGPT" extension
2. Add provider → OpenAI Compatible
3. Configure:
   ```
   API URL: http://localhost:8000/api/v1/chat/completions
   API Key: jebat-local-key
   ```

**Full Guide**: See `docs/IDE_INTEGRATION_GUIDE.md`

---

## 🎯 Cursor

Cursor has native support!

1. **Settings** → **AI** → **Custom Model**
2. Add:
   ```
   Model Name: JEBAT Pro
   API Endpoint: http://localhost:8000/api/v1/chat/completions
   API Key: jebat-local-key
   Model ID: jebat-pro
   ```
3. **Done!**

---

## 🧠 JetBrains (IntelliJ, WebStorm, PyCharm)

### **Using Continue Plugin**

1. **Install Plugin**
   - Settings → Plugins → Search "Continue" → Install

2. **Configure**
   - Edit `~/.continue/config.json`:

```json
{
  "models": [
    {
      "title": "JEBAT Pro",
      "provider": "openai-compatible",
      "apiBase": "http://localhost:8000/api/v1",
      "apiKey": "jebat-local-key"
    }
  ]
}
```

---

## ⚡ Neovim

### **Using ChatGPT.nvim**

1. **Install** (in init.lua):
```lua
use {
  "jackMort/ChatGPT.nvim",
  config = function()
    require("chatgpt").setup({
      api_url = "http://localhost:8000/api/v1",
      api_key = "jebat-local-key",
    })
  end
}
```

2. **Use**:
```vim
:ChatGPT          " Open chat
:ChatGPTEdit      " Edit selected
```

---

## 🧪 Test Connection

### **Quick Test**

```bash
curl -X POST http://localhost:8000/api/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer jebat-local-key" \
  -d '{"message": "Hello from IDE!"}'
```

### **Expected Response**

```json
{
  "response": "Hello! How can I help you today?",
  "confidence": 0.95,
  "execution_time": 1.2
}
```

---

## 🐛 Troubleshooting

### **"Connection Refused"**

```bash
# Check API is running
docker-compose ps jebat-api

# Restart if needed
docker-compose restart jebat-api
```

### **"Authentication Failed"**

```bash
# Check API key matches
# .env: API_KEY=jebat-local-key
# IDE config: api_key: jebat-local-key
```

### **CORS Errors (Web IDEs)**

Add to `.env`:
```bash
CORS_ORIGINS=http://localhost:*,https://your-ide.com
```

---

## 📊 Quick Reference

### **Keyboard Shortcuts**

| IDE | Chat | Inline Edit |
|-----|------|-------------|
| **Zed** | Cmd/Ctrl + K | Cmd/Ctrl + Shift + A |
| **VS Code** | Cmd/Ctrl + L | Cmd/Ctrl + I |
| **Cursor** | Cmd/Ctrl + L | Cmd/Ctrl + K |
| **JetBrains** | Alt/Option + C | Alt/Option + I |

### **API Endpoints**

| Purpose | Endpoint |
|---------|----------|
| Chat | `/api/v1/chat/completions` |
| Code Complete | `/api/v1/code/complete` |
| Explain | `/api/v1/code/explain` |
| Debug | `/api/v1/code/debug` |

---

## 🎯 Next Steps

1. ✅ **Test connection** - Make sure API responds
2. ✅ **Configure IDE** - Follow steps above
3. ✅ **Try it out** - Ask JEBAT to explain code
4. ✅ **Enable autocomplete** - For faster coding
5. ✅ **Monitor usage** - Check analytics dashboard

---

## 📚 Full Documentation

- **Complete IDE Guide**: `docs/IDE_INTEGRATION_GUIDE.md`
- **Zed Specific**: `docs/ZED_SETUP.md`
- **API Reference**: `http://localhost:8000/api/docs`

---

**You're all set!** 🎉

Start coding with AI assistance in your favorite IDE!

**JEBAT** - *Because warriors remember everything that matters.* 🗡️
