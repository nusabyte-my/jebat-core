# 🗡️ JEBAT - Complete Usage Guide

**Version**: 1.0.0  
**Last Updated**: 2026-02-18  
**Status**: Production Ready

---

## 📋 Table of Contents

1. [Quick Start](#quick-start)
2. [Installation](#installation)
3. [Configuration](#configuration)
4. [Core Features](#core-features)
5. [API Reference](#api-reference)
6. [SDK Usage](#sdk-usage)
7. [Plugin Development](#plugin-development)
8. [Multi-Tenancy](#multi-tenancy)
9. [Analytics](#analytics)
10. [Advanced ML](#advanced-ml)
11. [Deployment](#deployment)
12. [Troubleshooting](#troubleshooting)

---

## 🚀 Quick Start

### 5-Minute Setup

```bash
# 1. Navigate to project
cd C:\Users\shaid\Desktop\Dev

# 2. Run quick setup
py setup.py --quick

# 3. Start all services
docker-compose up -d

# 4. Check status
py -m jebat.cli.launch status

# 5. Open dashboard
start jebat\services\webui\dashboard.html
```

### Verify Installation

```bash
# Test core systems
py -c "from jebat import UltraLoop, UltraThink; print('✅ JEBAT Ready!')"

# Test API (when running)
curl http://localhost:8000/api/v1/health
```

---

## 📦 Installation

### Prerequisites

- Python 3.11+
- Docker & Docker Compose
- PostgreSQL 16+ (with TimescaleDB)
- Redis 7+

### Option 1: Docker (Recommended)

```bash
# Start complete stack
docker-compose up -d

# Services available:
# - API: http://localhost:8000
# - Dashboard: jebat/services/webui/dashboard.html
# - Grafana: http://localhost:3000
# - PostgreSQL: localhost:5432
# - Redis: localhost:6379
```

### Option 2: Local Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Initialize database
py -m jebat.database.setup --init

# Start API server
py -m uvicorn jebat.services.api.jebat_api:app --reload

# Start Ultra-Loop
py -m jebat.ultra_process_runner --loop
```

### Option 3: Development Setup

```bash
# Install with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/

# Run linters
black jebat/
flake8 jebat/
mypy jebat/
```

---

## ⚙️ Configuration

### Environment Variables

Create a `.env` file in the project root:

```bash
# Database
DATABASE_URL=postgresql+asyncpg://jebat:password@localhost:5432/jebat
REDIS_URL=redis://localhost:6379/0

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=false

# LLM Configuration (optional)
OPENAI_API_KEY=sk-your-key-here
ANTHROPIC_API_KEY=sk-ant-key-here

# Channel Configuration
TELEGRAM_BOT_TOKEN=your-telegram-token
WHATSAPP_PHONE_ID=your-phone-id
WHATSAPP_ACCESS_TOKEN=your-access-token
DISCORD_BOT_TOKEN=your-discord-token

# Analytics
ANALYTICS_ENABLED=true
ANALYTICS_RETENTION_DAYS=30
```

### YAML Configuration

Create `config/jebat.yaml`:

```yaml
app:
  name: JEBAT
  version: 1.0.0
  environment: development
  debug: true

database:
  url: ${DATABASE_URL}
  pool_size: 10
  echo: false

redis:
  url: ${REDIS_URL}
  max_connections: 20

memory:
  layers:
    M0_TTL: "30s"
    M1_TTL: "24h"
    M2_TTL: "7d"
    M3_TTL: "permanent"
  heat_thresholds:
    high: 0.8
    low: 0.4

ultra_loop:
  cycle_interval: 1.0
  max_cycles: null
  db_persistence: true

ultra_think:
  max_thoughts: 20
  default_mode: deliberate
  db_persistence: true

logging:
  level: INFO
  format: json
```

---

## 🎯 Core Features

### 1. Ultra-Loop (Continuous Processing)

The 5-phase continuous processing cycle:

```python
import asyncio
from jebat.ultra_loop import create_ultra_loop

async def main():
    # Create Ultra-Loop
    loop = await create_ultra_loop(
        config={
            "cycle_interval": 1.0,  # seconds
            "max_cycles": 100,
        }
    )
    
    # Start continuous processing
    await loop.start()
    
    # Let it run
    await asyncio.sleep(60)
    
    # Stop
    await loop.stop()

asyncio.run(main())
```

**5 Phases**:
1. **Perception** - Gather inputs from channels
2. **Cognition** - Process and reason
3. **Memory** - Store experiences
4. **Action** - Execute via agents
5. **Learning** - Update models

### 2. Ultra-Think (Deep Reasoning)

6 thinking modes for different tasks:

```python
import asyncio
from jebat.ultra_think import create_ultra_think, ThinkingMode

async def main():
    think = await create_ultra_think()
    
    # FAST mode - Quick responses
    result = await think.think(
        "What is 2 + 2?",
        mode=ThinkingMode.FAST,
        timeout=5
    )
    print(f"Answer: {result.conclusion}")
    
    # DELIBERATE mode - Balanced reasoning
    result = await think.think(
        "Should we use PostgreSQL or MongoDB?",
        mode=ThinkingMode.DELIBERATE,
        timeout=30
    )
    print(f"Analysis: {result.conclusion}")
    print(f"Confidence: {result.confidence:.1%}")
    
    # DEEP mode - Complex analysis
    result = await think.think(
        "What is the meaning of consciousness?",
        mode=ThinkingMode.DEEP,
        timeout=60
    )
    print(f"Deep thoughts: {result.conclusion}")

asyncio.run(main())
```

**Thinking Modes**:
- `FAST` - Quick, intuitive responses
- `DELIBERATE` - Balanced, logical reasoning
- `DEEP` - Complex, multi-layered analysis
- `STRATEGIC` - Long-term planning
- `CREATIVE` - Innovative, lateral thinking
- `CRITICAL` - Analytical, evaluative thinking

### 3. Memory System (5 Layers)

Eternal memory architecture:

```python
import asyncio
from jebat.memory_system import MemoryManager, MemoryLayer

async def main():
    manager = MemoryManager()
    
    # Store in different layers
    await manager.store(
        "User prefers dark mode",
        layer=MemoryLayer.M1_EPISODIC,
        user_id="user123"
    )
    
    await manager.store(
        "Python is a programming language",
        layer=MemoryLayer.M2_SEMANTIC,
        user_id="user123"
    )
    
    # Retrieve memories
    memories = await manager.retrieve(
        query="user preferences",
        user_id="user123",
        layer=MemoryLayer.M1_EPISODIC
    )
    
    for memory in memories:
        print(f"Memory: {memory.content}")
        print(f"Confidence: {memory.confidence:.1%}")

asyncio.run(main())
```

**Memory Layers**:
- `M0_TTL` - Temporary (30 seconds)
- `M1_EPISODIC` - Short-term experiences (24 hours)
- `M2_SEMANTIC` - Facts and knowledge (7 days)
- `M3_PROCEDURAL` - Skills and procedures (permanent)
- `M4_PERMANENT` - Core identity (permanent)

### 4. Agent System (Multi-Agent)

Coordinate multiple specialized agents:

```python
import asyncio
from jebat.orchestration import AgentOrchestrator

async def main():
    orchestrator = AgentOrchestrator()
    
    # Execute task with specific agent
    result = await orchestrator.execute_task(
        agent_type="research",
        task="Find latest AI developments",
        user_id="user123"
    )
    
    print(f"Result: {result.output}")
    print(f"Duration: {result.duration:.2f}s")
    
    # Execute with multiple agents
    results = await orchestrator.execute_multi_agent(
        tasks=[
            {"agent_type": "research", "task": "Research topic"},
            {"agent_type": "analysis", "task": "Analyze findings"},
            {"agent_type": "writing", "task": "Write report"},
        ]
    )
    
    for r in results:
        print(f"{r.agent_type}: {r.output}")

asyncio.run(main())
```

**Agent Types**:
- `general` - General purpose assistant
- `research` - Information gathering
- `analysis` - Data analysis
- `writing` - Content creation
- `coding` - Code generation
- `review` - Quality assurance

---

## 🌐 API Reference

### REST API Endpoints

Base URL: `http://localhost:8000/api/v1`

#### Health Check

```bash
GET /health

# Response
{
  "status": "healthy",
  "timestamp": "2026-02-18T10:30:00Z",
  "version": "1.0.0"
}
```

#### System Status

```bash
GET /status

# Response
{
  "ultra_loop": {"status": "running", "cycles": 1234},
  "ultra_think": {"status": "idle", "sessions": 56},
  "memory": {"status": "healthy", "count": 10000},
  "agents": {"active": 5, "total_tasks": 500}
}
```

#### Chat Completion

```bash
POST /chat/completions
Content-Type: application/json

{
  "message": "What is artificial intelligence?",
  "mode": "deliberate",
  "user_id": "user123",
  "timeout": 30
}

# Response
{
  "response": "Artificial intelligence is...",
  "confidence": 0.85,
  "thoughts": 15,
  "duration": 2.5
}
```

#### Memory Operations

```bash
# Store memory
POST /memories
Content-Type: application/json

{
  "content": "User likes Python",
  "user_id": "user123",
  "layer": "M1_EPISODIC"
}

# List memories
GET /memories?user_id=user123&limit=10

# Search memories
GET /memories/search?query=python&user_id=user123
```

### OpenAPI Documentation

When API is running, access interactive docs:
- **Swagger UI**: http://localhost:8000/api/docs
- **ReDoc**: http://localhost:8000/api/redoc

---

## 💻 SDK Usage

### Python SDK

```python
from jebat_sdk import JEBATClient
import asyncio

async def main():
    # Initialize client
    async with JEBATClient(base_url="http://localhost:8000") as client:
        
        # Chat
        response = await client.chat(
            "What is machine learning?",
            mode="deliberate"
        )
        print(f"Response: {response.response}")
        print(f"Confidence: {response.confidence:.1%}")
        
        # Store memory
        memory = await client.store_memory(
            content="I prefer Python over JavaScript",
            user_id="user123",
            layer="M1_EPISODIC"
        )
        print(f"Stored: {memory.id}")
        
        # Search memories
        memories = await client.search_memories(
            query="programming languages",
            user_id="user123"
        )
        for m in memories:
            print(f"- {m.content}")
        
        # Get metrics
        metrics = await client.metrics()
        print(f"System uptime: {metrics.system.uptime}s")
        
        # List agents
        agents = await client.agents()
        for agent in agents:
            print(f"- {agent.name}: {agent.status}")

asyncio.run(main())
```

### JavaScript/TypeScript SDK

```typescript
import { JEBATClient } from '@jebat/sdk';

async function main() {
  const client = new JEBATClient({
    baseURL: 'http://localhost:8000'
  });

  // Chat
  const response = await client.chat('What is AI?', {
    mode: 'deliberate'
  });
  console.log(response.response);

  // Store memory
  const memory = await client.storeMemory({
    content: 'TypeScript is typed JavaScript',
    userId: 'user123'
  });

  // Search
  const memories = await client.searchMemories('TypeScript', {
    userId: 'user123'
  });

  // Get metrics
  const metrics = await client.metrics();
  console.log(metrics.system.uptime);
}

main();
```

---

## 🔌 Plugin Development

### Plugin Structure

```
plugins/
  my_plugin/
    manifest.json
    plugin.py
    requirements.txt
    README.md
```

### manifest.json

```json
{
  "name": "my_plugin",
  "version": "1.0.0",
  "description": "My custom JEBAT plugin",
  "author": "Your Name",
  "type": "tool",
  "entry_point": "plugin.py",
  "dependencies": ["requests"],
  "permissions": ["network", "storage"],
  "config_schema": {
    "api_key": {
      "type": "string",
      "required": true
    }
  }
}
```

### plugin.py

```python
"""My Custom Plugin"""

from typing import Any, Dict

async def init(config: Dict[str, Any]):
    """Initialize plugin"""
    print(f"Plugin initialized with config: {config}")

async def execute(data: Any, **kwargs) -> Any:
    """Execute plugin logic"""
    # Your plugin logic here
    result = {
        "success": True,
        "data": f"Processed: {data}"
    }
    return result

async def cleanup():
    """Cleanup resources"""
    print("Plugin cleanup complete")
```

### Loading and Using Plugins

```python
from jebat.plugins import PluginManager

async def main():
    manager = PluginManager(plugins_dir="plugins")
    
    # Discover plugins
    plugins = manager.discover_plugins()
    print(f"Found: {plugins}")
    
    # Load plugin
    plugin = await manager.load_plugin(
        "my_plugin",
        config={"api_key": "secret"}
    )
    
    # Execute plugin
    result = await manager.execute_plugin(
        "my_plugin",
        data="Hello World"
    )
    print(f"Result: {result}")
    
    # List all plugins
    for p in manager.list_plugins():
        print(f"- {p['name']} v{p['version']} ({p['status']})")

# asyncio.run(main())
```

---

## 🏢 Multi-Tenancy

### Tenant Management

```python
from jebat.multitenancy import TenantManager, PlanType

async def main():
    manager = TenantManager()
    
    # Create tenant
    tenant = await manager.create_tenant(
        name="acme-corp",
        display_name="Acme Corporation",
        plan=PlanType.PRO,
        admin_email="admin@acme.com"
    )
    print(f"Created tenant: {tenant.id}")
    
    # Set quotas
    await manager.set_quota(
        tenant.id,
        "api_calls_per_day",
        100000
    )
    
    await manager.set_quota(
        tenant.id,
        "storage_gb",
        50
    )
    
    # Check quota
    available = await manager.check_quota(
        tenant.id,
        "api_calls_per_day"
    )
    print(f"API calls remaining: {available}")
    
    # Consume quota
    await manager.consume_quota(
        tenant.id,
        "api_calls_per_day",
        1
    )
    
    # Get usage
    usage = await manager.get_usage_summary(
        tenant.id,
        period="day"
    )
    print(f"Today's usage: {usage}")

# asyncio.run(main())
```

### Plan Types

- `FREE` - Basic features, limited usage
- `PRO` - Full features, moderate limits
- `ENTERPRISE` - Unlimited, priority support
- `CUSTOM` - Custom configuration

---

## 📊 Analytics

### Event Tracking

```python
from jebat.analytics import AnalyticsEngine

async def main():
    engine = AnalyticsEngine()
    
    # Track events
    await engine.track_event(
        "chat_completion",
        metadata={
            "duration": 2.5,
            "model": "gpt-4",
            "tokens": 150
        },
        user_id="user123"
    )
    
    await engine.track_event(
        "memory_stored",
        metadata={
            "layer": "M1_EPISODIC",
            "size_bytes": 256
        },
        user_id="user123"
    )
    
    # Get insights
    insights = await engine.get_insights(period="day")
    for insight in insights:
        print(f"{insight.metric}: {insight.value} ({insight.change:+.1f}%)")
    
    # Get usage report
    report = await engine.get_usage_report(period="week")
    print(f"Total events: {report['total_events']}")
    print(f"Unique users: {report['unique_users']}")
    
    # Get user analytics
    user_analytics = await engine.get_user_analytics("user123")
    print(f"Retention score: {user_analytics['retention_score']:.1%}")

# asyncio.run(main())
```

### Analytics Dashboard

```bash
# Install Streamlit
pip install streamlit pandas

# Run dashboard
streamlit run jebat/analytics/dashboard.py

# Access at http://localhost:8501
```

---

## 🤖 Advanced ML

### Model Fine-Tuning

```python
from jebat.ml import AdvancedMLEngine

async def main():
    engine = AdvancedMLEngine()
    
    # Prepare training data
    training_data = [
        {"input": "What is AI?", "output": "Artificial Intelligence..."},
        {"input": "Explain ML", "output": "Machine Learning..."},
        # More examples...
    ]
    
    # Start fine-tuning
    job_id = await engine.fine_tune_model(
        base_model="gpt-3.5-turbo",
        training_data=training_data,
        hyperparameters={
            "epochs": 3,
            "batch_size": 16,
            "learning_rate": 0.001
        }
    )
    
    # Monitor progress
    job = await engine.get_training_job_status(job_id)
    print(f"Status: {job.status}")
    print(f"Progress: {job.progress:.1f}%")
    
    # Wait for completion
    while job.status == "running":
        await asyncio.sleep(5)
        job = await engine.get_training_job_status(job_id)
        print(f"Progress: {job.progress:.1f}%")
    
    if job.status == "completed":
        print(f"Training complete! Metrics: {job.metrics}")

# asyncio.run(main())
```

### Knowledge Graph

```python
from jebat.ml import AdvancedMLEngine

async def main():
    engine = AdvancedMLEngine()
    
    # Add nodes
    python_id = await engine.add_knowledge_node(
        label="Python",
        node_type="programming_language",
        properties={"paradigm": "multi-paradigm", "year": 1991}
    )
    
    ai_id = await engine.add_knowledge_node(
        label="Artificial Intelligence",
        node_type="field",
        properties={}
    )
    
    # Add edge
    await engine.add_knowledge_edge(
        source_id=python_id,
        target_id=ai_id,
        relation="used_in"
    )
    
    # Query graph
    result = await engine.query_knowledge_graph(
        node_type="programming_language"
    )
    print(f"Found {result['total_nodes']} nodes")
    
    # Get related nodes
    related = await engine.get_related_nodes(python_id)
    for node in related:
        print(f"- {node.label} ({node.node_type})")
    
    # Export graph
    json_export = await engine.export_knowledge_graph()
    print(json_export)

# asyncio.run(main())
```

---

## 🚀 Deployment

### Docker Deployment

```bash
# Development
docker-compose up -d

# Production
docker-compose -f docker-compose.prod.yml up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f jebat

# Restart service
docker-compose restart jebat
```

### Production Checklist

- [ ] Set `DEBUG=false`
- [ ] Configure SSL/TLS
- [ ] Set strong database passwords
- [ ] Configure backup strategy
- [ ] Set up monitoring alerts
- [ ] Configure log aggregation
- [ ] Test disaster recovery
- [ ] Document runbooks

### Environment Variables (Production)

```bash
# Security
SECRET_KEY=your-secret-key-here
DEBUG=false
ALLOWED_HOSTS=your-domain.com

# Database
DATABASE_URL=postgresql+asyncpg://user:pass@db-host:5432/jebat

# Redis
REDIS_URL=redis://redis-host:6379/0

# SSL
SSL_CERT_FILE=/etc/ssl/certs/jebat.crt
SSL_KEY_FILE=/etc/ssl/private/jebat.key
```

---

## 🐛 Troubleshooting

### Common Issues

#### 1. Database Connection Failed

```bash
# Check PostgreSQL is running
docker-compose ps postgres

# Check connection string
echo $DATABASE_URL

# Test connection
psql $DATABASE_URL -c "SELECT 1"
```

#### 2. Redis Connection Failed

```bash
# Check Redis is running
docker-compose ps redis

# Test connection
redis-cli ping
```

#### 3. API Not Starting

```bash
# Check logs
docker-compose logs jebat-api

# Check port is free
netstat -ano | findstr :8000

# Restart service
docker-compose restart jebat-api
```

#### 4. Import Errors

```bash
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall

# Check Python version
python --version  # Should be 3.11+
```

#### 5. Memory Issues

```bash
# Clear old memories
from jebat.database import clear_old_memories
await clear_old_memories(days=30)

# Check database size
# In PostgreSQL:
SELECT pg_size_pretty(pg_database_size('jebat'));
```

### Getting Help

- **Documentation**: `docs/` folder
- **Issues**: GitHub Issues
- **Discussions**: GitHub Discussions
- **Logs**: `logs/jebat.log`

---

## 📚 Additional Resources

### Documentation Files

- `ARCHITECTURE.md` - System architecture
- `ROADMAP.md` - Product roadmap
- `DEPLOYMENT_GUIDE.md` - Deployment guide
- `API_REFERENCE.md` - Full API docs
- `CHANGELOG.md` - Version history

### Example Projects

- `examples/` - Code examples
- `tests/` - Test cases
- `plugins/` - Plugin examples

### Community

- GitHub: [Your Repo]
- Discord: [Your Server]
- Twitter: [@YourHandle]

---

**JEBAT** - *Because warriors remember everything that matters.* 🗡️
