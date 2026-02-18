# 🗡️ JEBAT Project Template

**Your own JEBAT-powered AI assistant project**

---

## 🚀 Quick Start

### 1. Copy This Template

```bash
# Copy the template folder
cp -r template my-jebat-project
cd my-jebat-project
```

### 2. Install Dependencies

```bash
# Install JEBAT
pip install jebat-sdk

# Or install from local source
pip install ../../  # If using from Dev folder
```

### 3. Configure

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your settings
notepad .env
```

### 4. Run Your Project

```bash
# Start the assistant
python bot.py

# Or with API
python api_server.py
```

---

## 📁 Project Structure

```
my-jebat-project/
├── bot.py                  # Main chatbot script
├── api_server.py           # REST API server
├── config.py               # Configuration settings
├── .env                    # Environment variables (create from .env.example)
├── .env.example            # Environment template
├── requirements.txt        # Python dependencies
├── README.md               # Your project README
├── plugins/                # Your custom plugins
│   └── .gitkeep
└── data/                   # Your data files
    └── .gitkeep
```

---

## 📝 Files

### bot.py

```python
"""
My JEBAT-Powered AI Assistant

Run: python bot.py
"""

import asyncio
import os
from jebat_sdk import JEBATClient

# Configuration
API_URL = os.getenv("JEBAT_API_URL", "http://localhost:8000")
USER_ID = os.getenv("USER_ID", "default_user")
BOT_NAME = os.getenv("BOT_NAME", "JEBAT Assistant")


async def main():
    """Main chatbot loop"""
    print(f"🗡️  {BOT_NAME}")
    print(f"API: {API_URL}")
    print("Type 'quit' to exit\n")
    
    async with JEBATClient(base_url=API_URL) as client:
        while True:
            # Get user input
            user_input = input("You: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'bye']:
                print(f"{BOT_NAME}: Goodbye! 👋")
                break
            
            if not user_input:
                continue
            
            # Get response from JEBAT
            try:
                response = await client.chat(
                    message=user_input,
                    user_id=USER_ID,
                    mode="deliberate",
                    timeout=30
                )
                
                print(f"{BOT_NAME}: {response.response}")
                print(f"Confidence: {response.confidence:.1%}\n")
                
            except Exception as e:
                print(f"Error: {e}\n")


if __name__ == "__main__":
    asyncio.run(main())
```

---

### api_server.py

```python
"""
Custom JEBAT API Server

Run: python api_server.py
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
import asyncio
from jebat_sdk import JEBATClient

# Configuration
JEBAT_API_URL = "http://localhost:8000"

# FastAPI app
app = FastAPI(
    title="My JEBAT API",
    description="Custom API powered by JEBAT",
    version="1.0.0"
)


# Request/Response models
class ChatRequest(BaseModel):
    message: str
    user_id: Optional[str] = "default"
    mode: Optional[str] = "deliberate"


class ChatResponse(BaseModel):
    response: str
    confidence: float
    thoughts: Optional[int] = None


# API Endpoints
@app.get("/health")
async def health():
    """Health check"""
    return {"status": "healthy"}


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Chat with JEBAT"""
    try:
        async with JEBATClient(base_url=JEBAT_API_URL) as client:
            response = await client.chat(
                message=request.message,
                user_id=request.user_id,
                mode=request.mode
            )
            
            return ChatResponse(
                response=response.response,
                confidence=response.confidence,
                thoughts=response.thoughts
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/memories/{user_id}")
async def get_memories(user_id: str, limit: int = 10):
    """Get user memories"""
    try:
        async with JEBATClient(base_url=JEBAT_API_URL) as client:
            memories = await client.search_memories(query="", user_id=user_id)
            return {"memories": memories[:limit]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Run server
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
```

---

### config.py

```python
"""
Configuration settings for your JEBAT project
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Config:
    """Configuration class"""
    
    # JEBAT API
    JEBAT_API_URL = os.getenv("JEBAT_API_URL", "http://localhost:8000")
    
    # User settings
    DEFAULT_USER_ID = os.getenv("DEFAULT_USER_ID", "default_user")
    BOT_NAME = os.getenv("BOT_NAME", "JEBAT Assistant")
    
    # Chat settings
    DEFAULT_MODE = os.getenv("DEFAULT_MODE", "deliberate")
    DEFAULT_TIMEOUT = int(os.getenv("DEFAULT_TIMEOUT", "30"))
    
    # Memory settings
    ENABLE_MEMORY = os.getenv("ENABLE_MEMORY", "true").lower() == "true"
    MEMORY_LAYER = os.getenv("MEMORY_LAYER", "M1_EPISODIC")
    
    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE = os.getenv("LOG_FILE", "bot.log")


# Global config instance
config = Config()
```

---

### .env.example

```bash
# JEBAT API Configuration
JEBAT_API_URL=http://localhost:8000

# Bot Configuration
DEFAULT_USER_ID=default_user
BOT_NAME=JEBAT Assistant
DEFAULT_MODE=deliberate
DEFAULT_TIMEOUT=30

# Memory Configuration
ENABLE_MEMORY=true
MEMORY_LAYER=M1_EPISODIC

# Logging
LOG_LEVEL=INFO
LOG_FILE=bot.log
```

---

### requirements.txt

```
jebat-sdk>=1.0.0
python-dotenv>=1.0.0
fastapi>=0.109.0
uvicorn>=0.27.0
pydantic>=2.0.0
```

---

### README.md

```markdown
# My JEBAT Project

Your personalized AI assistant powered by JEBAT.

## Features

- 💬 Natural conversation
- 🧠 Memory-enhanced responses
- 🤖 Multi-agent support
- 🔌 Plugin extensibility
- 📊 Analytics tracking

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure

```bash
cp .env.example .env
# Edit .env with your settings
```

### 3. Run

```bash
# Chatbot
python bot.py

# API Server
python api_server.py
```

## Usage

### Chatbot

```bash
python bot.py
```

### API

```bash
python api_server.py

# Then access:
# - API: http://localhost:8001
# - Docs: http://localhost:8001/docs
```

### Custom Plugins

Add your plugins to the `plugins/` folder:

```
plugins/
  my_plugin/
    manifest.json
    plugin.py
```

## Configuration

Edit `.env` file:

- `JEBAT_API_URL` - JEBAT API endpoint
- `BOT_NAME` - Your bot's name
- `DEFAULT_MODE` - Thinking mode (fast, deliberate, deep)
- `ENABLE_MEMORY` - Enable memory features

## Examples

See [QUICKSTART_EXAMPLES.md](../../QUICKSTART_EXAMPLES.md) for more examples.

## License

MIT
```

---

## 🎯 Customization Guide

### Change Bot Personality

Edit `bot.py`:

```python
# Add system prompt
response = await client.chat(
    message=user_input,
    user_id=USER_ID,
    mode="deliberate",
    system_prompt="You are a helpful, friendly assistant."
)
```

### Add Custom Plugins

1. Create plugin folder in `plugins/`
2. Add `manifest.json` and `plugin.py`
3. Load in your code:

```python
from jebat.plugins import PluginManager

manager = PluginManager(plugins_dir="plugins")
await manager.load_plugin("my_plugin")
result = await manager.execute_plugin("my_plugin", data)
```

### Enable Memory

```python
# Store memory
await client.store_memory(
    content="User likes coffee",
    user_id=USER_ID,
    layer="M1_EPISODIC"
)

# Retrieve memories
memories = await client.search_memories(
    query="preferences",
    user_id=USER_ID
)
```

### Track Analytics

```python
from jebat.analytics import AnalyticsEngine

engine = AnalyticsEngine()

# Track usage
await engine.track_event(
    "chat_completion",
    metadata={"duration": 2.5},
    user_id=USER_ID
)
```

---

## 📚 Next Steps

1. **Explore Examples**: See `../../QUICKSTART_EXAMPLES.md`
2. **Read Documentation**: See `../../USAGE_GUIDE.md`
3. **Build Plugins**: Create custom plugins for your use case
4. **Deploy**: Use Docker for production deployment

---

## 🆘 Support

- Documentation: `../../USAGE_GUIDE.md`
- Examples: `../../QUICKSTART_EXAMPLES.md`
- Issues: GitHub Issues
- Discussions: GitHub Discussions

---

**Happy Building!** 🗡️
