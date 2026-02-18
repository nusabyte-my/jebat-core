# 🚀 Enhanced JEBAT - Quick Start Guide

**Get up and running with JEBAT Enhanced in under 10 minutes!**

---

## 📋 What You'll Get

JEBAT Enhanced includes everything you need for a powerful, intelligent AI assistant:

✅ **MCP Protocol Server** - Work with any AI client  
✅ **WebSocket Gateway** - Real-time communication  
✅ **Decision Engine** - Intelligent routing and reasoning  
✅ **Smart Caching** - Lightning-fast performance  
✅ **Error Recovery** - Automatic failure handling  
✅ **Memory System** - Eternal memory for every conversation  
✅ **Specialized Agents** - Optimized for different tasks  

---

## 🎯 Prerequisites

### System Requirements
- **OS**: Windows, macOS, or Linux
- **Python**: 3.11 or higher
- **RAM**: 4GB minimum, 8GB recommended
- **Disk**: 10GB free space
- **Network**: Internet connection (for AI models)

### Software Dependencies
- Docker (optional, for containerized deployment)
- Git (for cloning the repository)

---

## 📦 Installation

### Option 1: Quick Install (Recommended)

```bash
# Clone the repository
git clone https://github.com/yourusername/jebat.git
cd jebat

# Run the automated setup
python setup_enhanced.py --setup-deps --create-dirs --init
```

This command:
- ✅ Installs all Python dependencies
- ✅ Creates necessary directory structure
- ✅ Initializes the system with default configuration

### Option 2: Manual Install

```bash
# Step 1: Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Step 2: Install dependencies
pip install fastapi uvicorn websockets aiohttp asyncpg redis python-multipart pydantic structlog python-dotenv httpx langchain langgraph openai anthropic

# Step 3: Create directories
mkdir -p config logs data cache backups workspace temp

# Step 4: Initialize system
python -m jebat.setup_enhanced --init
```

---

## ⚡ Quick Start

### 1. Start the System

```bash
# Start all enhanced services
python setup_enhanced.py --start
```

You'll see:
```
🚀 Initializing Enhanced JEBAT System...
✓ Error Recovery System initialized
✓ Cache Manager initialized
✓ Memory Manager initialized
✓ Agent Orchestrator initialized
✓ Decision Engine initialized
✓ MCP Protocol Server initialized with integrations
✅ Enhanced JEBAT System fully initialized and ready

🎯 Starting Enhanced JEBAT System...
✓ MCP Protocol Server started
✓ WebSocket Gateway started
✅ Enhanced JEBAT System started successfully

📊 System Health: healthy
🌐 WebSocket Gateway: ws://0.0.0.0:18789
🔌 MCP Server: 0.0.0.0:18790

🎯 System is running. Press Ctrl+C to shutdown...
```

### 2. Check System Status

```bash
# Check if everything is running
python setup_enhanced.py --status
```

You'll see a detailed status dashboard:
```
============================================================
🗡️ JEBAT Enhanced System Status
============================================================
Status:           HEALTHY
Uptime:           42.3s
Total Requests:   0
Success Rate:     0.00%
Active Sessions:  0

Components:
  ✅ mcp_server: HEALTHY
  ✅ decision_engine: HEALTHY
  ✅ cache_manager: HEALTHY
  ✅ error_recovery: HEALTHY
  ✅ memory_manager: HEALTHY
  ✅ agent_orchestrator: HEALTHY

Metrics:
  Cache Hit Rate:  0.00%
  Decisions Made:  0
  Success Rate:    0.00%
============================================================
```

---

## 💬 Basic Usage

### Option 1: WebSocket Client (JavaScript)

```javascript
// Connect to JEBAT WebSocket Gateway
const ws = new WebSocket('ws://localhost:18789');

// Authenticate
ws.send(JSON.stringify({
  type: 'auth',
  payload: {
    token: 'your-auth-token',
    user_id: 'user-123'
  }
}));

// Send a message
ws.send(JSON.stringify({
  type: 'message',
  payload: {
    content: 'Hello JEBAT! What can you do?'
  }
}));

// Listen for responses
ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  console.log('Response:', message.payload);
};
```

### Option 2: Python Client

```python
import asyncio
import websockets
import json

async def chat_with_jebat():
    uri = "ws://localhost:18789"
    
    async with websockets.connect(uri) as websocket:
        # Authenticate
        auth_message = {
            "type": "auth",
            "payload": {
                "token": "your-auth-token",
                "user_id": "user-123"
            }
        }
        await websocket.send(json.dumps(auth_message))
        
        # Send message
        chat_message = {
            "type": "message",
            "payload": {
                "content": "Hello JEBAT! Analyze this data for me."
            }
        }
        await websocket.send(json.dumps(chat_message))
        
        # Receive response
        response = await websocket.recv()
        print(f"JEBAT: {json.loads(response)['payload']['content']}")

asyncio.run(chat_with_jebat())
```

### Option 3: MCP Protocol Client

```python
import asyncio
from jebat.mcp.client import MCPClient

async def use_mcp_client():
    # Connect to MCP server
    client = MCPClient(host="localhost", port=18790)
    await client.connect()
    
    # List available tools
    tools = await client.list_tools()
    print(f"Available tools: {[tool['name'] for tool in tools]}")
    
    # Call a tool
    result = await client.call_tool(
        tool_name="memory_search",
        parameters={
            "query": "previous conversations about AI",
            "limit": 5
        }
    )
    print(f"Result: {result}")
    
    # Disconnect
    await client.disconnect()

asyncio.run(use_mcp_client())
```

---

## 🧠 Memory System Usage

### Store a Memory

```python
from jebat.integration.enhanced_system import EnhancedJEBATSystem

# Initialize system
system = EnhancedJEBATSystem(config={})
await system.initialize()

# Store a memory
await system.memory_manager.store(
    content="The user prefers Python over JavaScript for data analysis",
    tags=["preference", "programming"],
    heat_score=0.8  # High importance
)
```

### Retrieve Memories

```python
# Search memories
memories = await system.memory_manager.search_memories(
    query="user programming preferences",
    limit=10
)

for memory in memories:
    print(f"Memory: {memory['content']}")
    print(f"Tags: {memory['tags']}")
    print(f"Score: {memory['score']}")
```

---

## 🤖 Using Specialized Agents

### Automatically Selected by Decision Engine

```python
# The decision engine automatically selects the best agent
context = RequestContext(
    request_id="req-123",
    user_id="user-456",
    session_id="session-789",
    request_type="message",
    input_data={
        "request": "Analyze market trends for AI in healthcare",
        "type": "analysis"
    }
)

# Process - decision engine selects analyst agent automatically
result = await system.process_request(context)

print(f"Selected Agent: {result.decisions['agent'].selected_option}")
print(f"Response: {result.data}")
```

### Explicit Agent Selection

```python
from jebat.specialized_agents.templates import (
    create_researcher,
    create_analyst,
    create_executor
)

# Create specialized agents
researcher = create_researcher(
    decision_engine=system.decision_engine,
    cache_client=system.cache_manager,
    memory_system=system.memory_manager
)

analyst = create_analyst(
    decision_engine=system.decision_engine,
    cache_client=system.cache_manager,
    memory_system=system.memory_manager
)

# Execute task with specific agent
from jebat.specialized_agents.templates import Task, AgentCapability

task = Task(
    description="Analyze sales data from Q1 2024",
    parameters={"data": sales_data},
    required_capabilities=[
        AgentCapability.DATA_ANALYSIS,
        AgentCapability.TREND_ANALYSIS
    ]
)

result = await analyst.process_task(task)
print(f"Analysis Result: {result.result}")
```

---

## ⚙️ Configuration

### Basic Configuration

Edit `config_enhanced.yaml`:

```yaml
system:
  name: "JEBAT Enhanced"
  environment: "development"
  log_level: "INFO"

mcp_server:
  enabled: true
  port: 18790

websocket_gateway:
  enabled: true
  port: 18789

decision_engine:
  enabled: true
  cache_ttl: 3600  # 1 hour
  learning_enabled: true

cache:
  enabled: true
  memory_hot_size: 100  # MB
  memory_hot_entries: 1000

memory:
  enabled: true
  layers:
    m0_ttl: 30  # seconds
    m1_ttl: 86400  # 24 hours
    m2_ttl: 2592000  # 30 days
```

### Environment Variables

Create a `.env` file:

```bash
# Database
DATABASE_URL=postgresql://jebat:password@localhost:5432/jebat
REDIS_URL=redis://localhost:6379

# Authentication
AUTH_SECRET_KEY=your-secret-key-here
MCP_SECRET_KEY=your-mcp-secret-key

# AI Models
OPENAI_API_KEY=your-openai-api-key
ANTHROPIC_API_KEY=your-anthropic-api-key

# Channels (optional)
TELEGRAM_BOT_TOKEN=your-telegram-token
DISCORD_BOT_TOKEN=your-discord-token
```

---

## 🎛️ Common Commands

### System Management

```bash
# Initialize system
python setup_enhanced.py --init

# Start all services
python setup_enhanced.py --start

# Stop all services
python setup_enhanced.py --stop

# Check status
python setup_enhanced.py --status

# Full deployment
python setup_enhanced.py --deploy
```

### Development

```bash
# Run tests
pytest tests/

# Run specific test
pytest tests/test_decision_engine.py

# Run with coverage
pytest --cov=jebat tests/

# Start in debug mode
python -m jebat.main --debug
```

### Database

```bash
# Run migrations
alembic upgrade head

# Create new migration
alembic revision --autogenerate -m "description"

# Rollback migration
alembic downgrade -1
```

---

## 🔍 Monitoring & Debugging

### View Logs

```bash
# View all logs
tail -f logs/jebat.log

# View error logs only
grep ERROR logs/jebat.log

# View logs for specific component
grep "Decision Engine" logs/jebat.log
```

### Access Metrics

```bash
# Prometheus metrics endpoint
curl http://localhost:9090/metrics

# Health check
curl http://localhost:18789/health

# Detailed health check
curl http://localhost:18789/health/detailed
```

### Performance Analysis

```python
# Get cache statistics
cache_stats = await system.cache_manager.get_all_stats()
print(f"Cache Hit Rate: {cache_stats['memory_cache']['performance']['hit_rate']:.2%}")

# Get decision engine statistics
decision_stats = system.decision_engine.get_stats()
print(f"Total Decisions: {decision_stats['total_decisions']}")
print(f"Success Rate: {decision_stats['success_rate']:.2%}")

# Get error recovery statistics
error_stats = system.error_recovery.get_error_statistics()
print(f"Total Errors: {error_stats['total_errors']}")
print(f"DLQ Size: {error_stats['dlq_size']}")
```

---

## 🐛 Troubleshooting

### Common Issues

#### 1. Port Already in Use

**Error**: `Address already in use`

**Solution**:
```bash
# Find process using the port
lsof -i :18789  # On Windows: netstat -ano | findstr :18789

# Kill the process
kill -9 <PID>  # On Windows: taskkill /PID <PID> /F

# Or change port in config_enhanced.yaml
```

#### 2. Database Connection Failed

**Error**: `Connection refused` or `Authentication failed`

**Solution**:
```bash
# Check if PostgreSQL is running
sudo systemctl status postgresql  # On Linux
brew services list  # On macOS

# Verify connection string in .env
echo $DATABASE_URL

# Test connection
psql $DATABASE_URL
```

#### 3. Out of Memory

**Error**: `MemoryError` or system slowdown

**Solution**:
```yaml
# Reduce cache sizes in config_enhanced.yaml
cache:
  memory_hot_size: 50  # Was 100
  memory_hot_entries: 500  # Was 1000
```

#### 4. High CPU Usage

**Error**: System becomes unresponsive

**Solution**:
```python
# Reduce worker count
system.config['system']['max_workers'] = 2  # Was 4

# Enable more aggressive caching
cache_config['behavior']['cache_warming_enabled'] = True
```

---

## 📚 Next Steps

### Learn More

- **[Full Documentation](./JEBAT.md)** - Complete system documentation
- **[API Reference](./API.md)** - Detailed API documentation
- **[Architecture Guide](./ARCHITECTURE.md)** - System architecture
- **[Implementation Plan](./IMPLEMENTATION_PLAN_ENHANCED.md)** - Development roadmap

### Explore Features

- **[Memory System](./MEMORY.md)** - Eternal memory capabilities
- **[Decision Engine](./DECISION_ENGINE.md)** - Intelligent routing
- **[Specialized Agents](./AGENTS.md)** - Agent templates
- **[MCP Protocol](./MCP.md)** - Client integration

### Get Help

- **[GitHub Issues](https://github.com/yourusername/jebat/issues)** - Bug reports
- **[Discord Community](https://discord.gg/jebat)** - Community support
- **[Documentation](https://docs.jebat.online)** - Online docs
- **[Email Support](mailto:support@jebat.online)** - Direct support

---

## 🎯 Quick Examples

### Example 1: Personal Assistant

```python
import asyncio
from jebat.integration.enhanced_system import create_enhanced_system
from jebat.integration.enhanced_system import RequestContext

async def personal_assistant():
    # Initialize system
    system = await create_enhanced_system({})
    
    # Process user request
    context = RequestContext(
        request_id="req-001",
        user_id="user-123",
        session_id="session-456",
        request_type="message",
        input_data={
            "request": "Remind me to call John at 3 PM tomorrow"
        }
    )
    
    result = await system.process_request(context)
    print(f"Response: {result.data}")
    
    # Shutdown
    await system.shutdown()

asyncio.run(personal_assistant())
```

### Example 2: Research Assistant

```python
from jebat.specialized_agents.templates import create_researcher

async def research_assistant():
    researcher = create_researcher()
    
    task = Task(
        description="Research the latest developments in AI for healthcare",
        parameters={
            "depth": "comprehensive",
            "sources": ["academic", "industry_reports"]
        }
    )
    
    result = await researcher.process_task(task)
    print(f"Research Summary: {result.result['synthesis']}")
    print(f"Sources: {result.result['sources']}")
    
    await researcher.shutdown()

asyncio.run(research_assistant())
```

### Example 3: Data Analyst

```python
from jebat.specialized_agents.templates import create_analyst

async def data_analyst():
    analyst = create_analyst()
    
    task = Task(
        description="Analyze Q1 2024 sales data",
        parameters={
            "data": sales_data,
            "analysis_type": "trend_analysis"
        }
    )
    
    result = await analyst.process_task(task)
    print(f"Key Insights: {result.result['insights']}")
    print(f"Confidence: {result.result['confidence']}")
    
    await analyst.shutdown()

asyncio.run(data_analyst())
```

---

## 🎉 You're Ready!

Congratulations! You now have JEBAT Enhanced up and running. Here's what you can do:

✅ **Connect via WebSocket** - Build real-time applications  
✅ **Use MCP Protocol** - Integrate with any AI client  
✅ **Store Memories** - Never forget important information  
✅ **Use Specialized Agents** - Get optimized task execution  
✅ **Monitor Performance** - Track system health and metrics  

**Need help?** Check the documentation or join our community!

---

**Happy coding with JEBAT Enhanced!** 🚀

---

*For more information, visit [docs.jebat.online](https://docs.jebat.online)*