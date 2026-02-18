# 🗡️ JEBAT - Quick Reference Card

**Your go-to guide for common JEBAT tasks**

---

## 🚀 Quick Commands

### Start JEBAT

```bash
# Start all services (Docker)
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Run Examples

```bash
# Basic chatbot
py examples/chatbot/basic_bot.py

# Memory assistant
py examples/memory/memory_assistant.py

# Research team
py examples/agents/research_team.py

# Deep thinking
py examples/thinking/deep_analysis.py
```

### Analytics Dashboard

```bash
# Install dependencies
pip install streamlit pandas

# Run dashboard
streamlit run jebat/analytics/dashboard.py

# Access at http://localhost:8501
```

---

## 📡 API Endpoints

Base URL: `http://localhost:8000/api/v1`

```bash
# Health check
GET /health

# System status
GET /status

# Chat
POST /chat/completions
{"message": "Hello!", "mode": "deliberate"}

# Store memory
POST /memories
{"content": "Test", "user_id": "user1"}

# Search memories
GET /memories/search?query=test&user_id=user1

# Get metrics
GET /metrics
```

---

## 💻 Python SDK

```python
from jebat_sdk import JEBATClient

async with JEBATClient() as client:
    # Chat
    response = await client.chat("Hello!", mode="deliberate")
    
    # Store memory
    await client.store_memory("I like Python", user_id="user1")
    
    # Search memories
    memories = await client.search_memories("Python", user_id="user1")
    
    # Get metrics
    metrics = await client.metrics()
```

---

## 🧠 Thinking Modes

| Mode | Use Case | Speed |
|------|----------|-------|
| `FAST` | Quick answers | Instant |
| `DELIBERATE` | Balanced reasoning | Fast |
| `DEEP` | Complex analysis | Medium |
| `STRATEGIC` | Long-term planning | Slow |
| `CREATIVE` | Innovation | Medium |
| `CRITICAL` | Evaluation | Slow |

---

## 🧠 Memory Layers

| Layer | Duration | Use Case |
|-------|----------|----------|
| `M0_TTL` | 30s | Temporary data |
| `M1_EPISODIC` | 24h | Recent conversations |
| `M2_SEMANTIC` | 7d | Facts and knowledge |
| `M3_PROCEDURAL` | Permanent | Skills |
| `M4_PERMANENT` | Permanent | Core identity |

---

## 🔌 Plugin Development

```bash
# Plugin structure
plugins/
  my_plugin/
    manifest.json
    plugin.py
    requirements.txt
```

```json
// manifest.json
{
  "name": "my_plugin",
  "version": "1.0.0",
  "type": "tool",
  "entry_point": "plugin.py"
}
```

```python
# plugin.py
async def init(config): ...
async def execute(data, **kwargs): ...
async def cleanup(): ...
```

---

## 🏢 Multi-Tenancy

```python
from jebat.multitenancy import TenantManager, PlanType

manager = TenantManager()

# Create tenant
tenant = await manager.create_tenant(
    name="company",
    plan=PlanType.PRO
)

# Set quota
await manager.set_quota(tenant.id, "api_calls_per_day", 10000)

# Check quota
remaining = await manager.check_quota(tenant.id, "api_calls_per_day")
```

---

## 📊 Analytics

```python
from jebat.analytics import AnalyticsEngine

engine = AnalyticsEngine()

# Track event
await engine.track_event(
    "chat_completion",
    metadata={"duration": 2.5},
    user_id="user1"
)

# Get insights
insights = await engine.get_insights(period="day")

# Get usage report
report = await engine.get_usage_report(period="week")
```

---

## 🤖 Advanced ML

```python
from jebat.ml import AdvancedMLEngine

engine = AdvancedMLEngine()

# Fine-tune model
job_id = await engine.fine_tune_model(
    base_model="gpt-3.5-turbo",
    training_data=data
)

# Add knowledge graph node
node_id = await engine.add_knowledge_node(
    label="Python",
    node_type="programming_language"
)

# Query graph
result = await engine.query_knowledge_graph()
```

---

## 🐛 Troubleshooting

### Database Connection Failed

```bash
# Check PostgreSQL
docker-compose ps postgres

# Test connection
psql $DATABASE_URL -c "SELECT 1"
```

### Redis Connection Failed

```bash
# Check Redis
docker-compose ps redis

# Test connection
redis-cli ping
```

### API Not Starting

```bash
# Check logs
docker-compose logs jebat-api

# Check port
netstat -ano | findstr :8000

# Restart
docker-compose restart jebat-api
```

---

## 📚 Documentation

| Document | Purpose |
|----------|---------|
| `USAGE_GUIDE.md` | Complete usage guide |
| `QUICKSTART_EXAMPLES.md` | 8 working examples |
| `PROJECT_TEMPLATE/` | Starter project |
| `ARCHITECTURE.md` | System design |
| `DEPLOYMENT_GUIDE.md` | Deployment |

---

## 🎯 Project Template

```bash
# Copy template
cp -r PROJECT_TEMPLATE my-project
cd my-project

# Install
pip install -r requirements.txt

# Configure
cp .env.example .env

# Run
python bot.py
```

---

## ⚡ Environment Variables

```bash
# Essential
DATABASE_URL=postgresql+asyncpg://...
REDIS_URL=redis://...
JEBAT_API_URL=http://localhost:8000

# Optional
DEBUG=false
LOG_LEVEL=INFO
ENABLE_MEMORY=true
```

---

## 🎓 Learning Path

**Day 1**: Run basic chatbot example  
**Day 2**: Read USAGE_GUIDE.md sections 1-4  
**Day 3**: Use project template  
**Day 4**: Add memory features  
**Day 5**: Create custom plugin  
**Day 6-10**: Advanced features  

---

**JEBAT** - *Because warriors remember everything that matters.* 🗡️

**Quick Links**:
- Examples: `QUICKSTART_EXAMPLES.md`
- Full Guide: `USAGE_GUIDE.md`
- Template: `PROJECT_TEMPLATE/`
- Summary: `Q4_COMPLETION_SUMMARY.md`
