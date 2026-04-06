# 💬 JEBAT Chatbot Examples

**Working chatbot implementations you can use right now**

---

## 🚀 Quick Start

### Option 1: Standalone Chatbot (Recommended)

Works WITHOUT API server - uses JEBAT components directly:

```bash
# Navigate to examples
cd C:\Users\shaid\Desktop\Dev

# Run standalone chatbot
py examples\chat\standalone_chatbot.py
```

**Features**:
- ✅ No API server needed
- ✅ Uses Ultra-Think directly
- ✅ Multiple thinking modes
- ✅ Conversation history
- ✅ Memory support (when available)

---

### Option 2: Simple Chatbot (With API)

Requires JEBAT API server running:

```bash
# 1. Start API server
docker-compose up -d

# 2. Run simple chatbot
py examples\chat\simple_chatbot.py
```

**Features**:
- ✅ Simple and lightweight
- ✅ Shows confidence scores
- ✅ Easy to customize

---

### Option 3: Interactive Chatbot (With API + Rich UI)

Requires API server and rich package:

```bash
# 1. Install rich (optional, for better UI)
pip install rich

# 2. Start API server
docker-compose up -d

# 3. Run interactive chatbot
py examples\chat\interactive_chatbot.py
```

**Features**:
- ✅ Beautiful colored output
- ✅ Conversation history viewer
- ✅ Mode selection menu
- ✅ Status display

---

## 📋 Chatbot Comparison

| Feature | Standalone | Simple | Interactive |
|---------|-----------|--------|-------------|
| API Server Needed | ❌ No | ✅ Yes | ✅ Yes |
| Rich UI | ✅ Yes | ❌ No | ✅ Yes |
| Thinking Modes | ✅ Yes | ❌ No | ✅ Yes |
| Conversation History | ✅ Yes | ❌ No | ✅ Yes |
| Memory Support | ✅ Yes | ✅ Yes | ✅ Yes |
| File Size | ~200 lines | ~80 lines | ~180 lines |
| Best For | Offline use | Simple testing | Best experience |

---

## 🎯 Usage Examples

### Standalone Chatbot

```
============================================================
🗡️  JEBAT Standalone Chatbot
============================================================
Commands: quit, mode, history, memory

🗡️  JEBAT - Initializing components...
  ✓ Ultra-Think initialized
  ✓ Memory Manager initialized

✅ JEBAT Ready!

You: Hello
⏳ Thinking...

🗡️ JEBAT: Hello! I'm JEBAT, your AI assistant. How can I help you today?
💭 Thoughts: 5 | Confidence: 85% | Duration: 2.34s

You: What is artificial intelligence?
⏳ Thinking...

🗡️ JEBAT: Artificial intelligence is the simulation of human intelligence...
💭 Thoughts: 12 | Confidence: 92% | Duration: 5.67s

You: mode
🎯 Select Thinking Mode:
  1. fast - ⚡ Quick responses
  2. deliberate - 🤔 Balanced reasoning
  3. deep - 🧠 Deep analysis
  ...

You: quit
🗡️  Goodbye! Have a great day! 👋
```

---

## 🔧 Customization

### Change Default Settings

Edit the chatbot file:

```python
# Change user ID
self.user_id = "my_custom_user"

# Change default thinking mode
self.thinking_mode = "deep"  # or fast, deliberate, strategic, creative, critical

# Change max thoughts
config={"max_thoughts": 20}
```

### Add Custom Responses

Edit the `_generate_simple_response` method:

```python
def _generate_simple_response(self, message: str) -> str:
    message_lower = message.lower()
    
    # Add your custom responses
    if 'what is jebat' in message_lower:
        return "JEBAT is an advanced AI assistant with eternal memory!"
    
    if 'tell me a joke' in message_lower:
        return "Why did the AI go to therapy? Because it had deep learning issues!"
    
    # ... existing code ...
```

### Add Memory Support

In `standalone_chatbot.py`:

```python
async def get_response(self, message: str) -> dict:
    # Retrieve relevant memories
    if self.memory_manager:
        memories = await self.memory_manager.retrieve(
            query=message,
            user_id=self.user_id
        )
        
        # Use memories to enhance response
        if memories:
            context = "\n".join([m.content for m in memories[:3]])
            message = f"Context from memory: {context}\n\nQuestion: {message}"
    
    # ... rest of the method ...
```

---

## 🐛 Troubleshooting

### "Module not found" Error

```bash
# Make sure you're in the project root
cd C:\Users\shaid\Desktop\Dev

# Run from there
py examples\chat\standalone_chatbot.py
```

### "Ultra-Think not available" Warning

This is normal if dependencies are missing. The chatbot will run in basic mode.

To enable full features:

```bash
# Install all dependencies
pip install -r requirements.txt
```

### API Connection Error (Simple/Interactive Chatbots)

```bash
# Check if API is running
docker-compose ps

# Start API if not running
docker-compose up -d

# Check API logs
docker-compose logs jebat-api
```

### Rich Not Installed (Interactive Chatbot)

```bash
# Install rich for better UI
pip install rich

# Or run without it (will still work)
py examples\chat\interactive_chatbot.py
```

---

## 📦 Requirements

### Standalone Chatbot

```txt
# Required
python 3.11+

# Optional (for better UI)
rich>=13.0.0
```

### Simple/Interactive Chatbots

```txt
# Required
python 3.11+
aiohttp>=3.9.0

# Optional (for better UI)
rich>=13.0.0

# API Server (Docker)
docker-compose
```

---

## 🎓 Next Steps

1. **Try the standalone chatbot** - No setup needed
2. **Customize responses** - Add your own logic
3. **Add memory support** - Enable persistent conversations
4. **Deploy** - Use Docker for production

---

## 📚 Related Documentation

- **Full Usage Guide**: `USAGE_GUIDE.md`
- **More Examples**: `QUICKSTART_EXAMPLES.md`
- **Project Template**: `PROJECT_TEMPLATE/`
- **API Reference**: `API_REFERENCE.md`

---

**Happy Chatting!** 💬🗡️
