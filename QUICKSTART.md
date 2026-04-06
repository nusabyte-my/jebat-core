# JEBAT - Quick Start Guide 🚀

Get up and running with JEBAT memory system in under 10 minutes!

## 📋 Prerequisites

- **Python 3.10+**
- **Docker** (recommended) or PostgreSQL 15+
- **OpenAI API Key** (for embeddings)
- **Git** (to clone the repository)

---

## 🎯 Step 1: Clone and Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/jebat.git
cd jebat

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

---

## 🐳 Step 2: Setup Database

### Option A: Docker (Easiest)

```bash
# Pull and run TimescaleDB with pgvector support
docker run -d \
  --name jebat-db \
  -p 5432:5432 \
  -e POSTGRES_USER=jebat \
  -e POSTGRES_PASSWORD=jebat_secure_pass \
  -e POSTGRES_DB=jebat_memory \
  -v jebat_data:/var/lib/postgresql/data \
  timescale/timescaledb-ha:pg16

# Wait a few seconds for database to start
sleep 5

# Verify it's running
docker ps | grep jebat-db
```

### Option B: Docker Compose

```bash
# Use the provided docker-compose file
docker-compose up -d

# Check status
docker-compose ps
```

### Option C: Manual PostgreSQL

See [DATABASE_SETUP.md](memory_system/DATABASE_SETUP.md) for detailed manual installation instructions.

---

## 🔑 Step 3: Configure Environment

Create a `.env` file in the project root:

```bash
# Database Configuration
DATABASE_HOST=localhost
DATABASE_PORT=5432
DATABASE_NAME=jebat_memory
DATABASE_USER=jebat
DATABASE_PASSWORD=jebat_secure_pass

# OpenAI Configuration (required for embeddings)
OPENAI_API_KEY=sk-your-key-here

# Optional: Model Configuration
OPENAI_MODEL=gpt-4
EMBEDDING_MODEL=text-embedding-3-small

# Optional: Server Configuration
JEBAT_HOST=0.0.0.0
JEBAT_PORT=8000
JEBAT_ENV=development
```

Or set environment variables directly:

```bash
# Windows PowerShell
$env:OPENAI_API_KEY="sk-your-key-here"
$env:DATABASE_URL="postgresql://jebat:jebat_secure_pass@localhost:5432/jebat_memory"

# macOS/Linux
export OPENAI_API_KEY="sk-your-key-here"
export DATABASE_URL="postgresql://jebat:jebat_secure_pass@localhost:5432/jebat_memory"
```

---

## ✅ Step 4: Verify Installation

Run the storage example to test everything:

```bash
python memory_system/examples/storage_example.py
```

Expected output:

```
============================================================
JEBAT Memory System - Storage Backend Example
============================================================

[1] Initializing Storage Backend...
✅ Storage backend initialized successfully
   Database: healthy
   Embedding cache: 0 entries

[2] Creating and Storing Memories...
   Storing 5 memories across all layers...
✅ Stored 5 memories successfully
   - M0: User asked about the weather today...
   - M1: User prefers concise answers and dislikes verbose...
   - M2: User is a software engineer specializing in machine...
   - M3: User values efficiency and pragmatism over theoreti...
   - M4: When user asks for code examples, provide working c...

...
```

---

## 🎮 Step 5: Try Basic Operations

### Store a Memory

```python
import asyncio
from memory_system.storage import StorageBackend, DatabaseConfig, EmbeddingConfig
from memory_system.core.memory_layers import Memory, MemoryLayer, MemoryMetadata, MemoryModality, MemoryImportance, HeatScore
from datetime import datetime

async def store_memory_example():
    # Initialize backend
    backend = StorageBackend(
        db_config=DatabaseConfig(),
        embedding_config=EmbeddingConfig(),
        openai_api_key="your-key-here"
    )
    await backend.initialize()
    
    # Create a memory
    memory = Memory(
        memory_id="mem_001",
        content="User loves Python programming",
        layer=MemoryLayer.M1,
        metadata=MemoryMetadata(
            modality=MemoryModality.TEXT,
            importance=MemoryImportance.HIGH,
            tags=["preference", "programming"]
        ),
        heat=HeatScore(),
        created_at=datetime.now()
    )
    
    # Store it
    db_id = await backend.store_memory(memory, user_id="user_001")
    print(f"✅ Stored memory with ID: {db_id}")
    
    await backend.close()

asyncio.run(store_memory_example())
```

### Search Memories

```python
import asyncio
from memory_system.storage import StorageBackend, DatabaseConfig, EmbeddingConfig

async def search_example():
    backend = StorageBackend(
        db_config=DatabaseConfig(),
        embedding_config=EmbeddingConfig(),
        openai_api_key="your-key-here"
    )
    await backend.initialize()
    
    # Semantic search
    results = await backend.semantic_search(
        user_id="user_001",
        query="What programming languages does the user like?",
        limit=5
    )
    
    for memory, similarity in results:
        print(f"Similarity: {similarity:.2f}")
        print(f"Content: {memory.content}")
        print(f"Tags: {memory.metadata.tags}\n")
    
    await backend.close()

asyncio.run(search_example())
```

---

## 🧪 Step 6: Run Tests

```bash
# Install test dependencies
pip install pytest pytest-asyncio pytest-cov

# Run all tests
pytest memory_system/tests/

# Run specific test file
pytest memory_system/tests/test_storage.py

# Run with coverage
pytest --cov=memory_system memory_system/tests/

# Run only fast tests (skip slow performance tests)
pytest -m "not slow" memory_system/tests/
```

---

## 📚 Next Steps

### Explore the Examples

```bash
# Browse example files
cd memory_system/examples/

# Try different examples
python storage_example.py
python memory_layers_example.py  # (if available)
```

### Read the Documentation

- **[ARCHITECTURE.md](ARCHITECTURE.md)** - System architecture and design
- **[JEBAT.md](JEBAT.md)** - Complete feature overview
- **[DATABASE_SETUP.md](memory_system/DATABASE_SETUP.md)** - Detailed database guide
- **[JEBAT_STATUS.md](JEBAT_STATUS.md)** - Implementation roadmap

### Build Your First Agent

```python
# Coming soon: Agent integration example
from memory_system.agents import JebatAgent

agent = JebatAgent(
    name="MyAgent",
    user_id="user_001",
    storage_backend=backend
)

response = await agent.chat("Tell me what you remember about me")
```

---

## 🐛 Troubleshooting

### Database Connection Issues

```bash
# Check if PostgreSQL is running
docker ps | grep jebat-db

# Check database logs
docker logs jebat-db

# Test connection manually
docker exec -it jebat-db psql -U jebat -d jebat_memory -c "SELECT 1"
```

### OpenAI API Errors

```bash
# Verify your API key is set
echo $OPENAI_API_KEY  # Linux/macOS
echo $env:OPENAI_API_KEY  # Windows PowerShell

# Test API key
python -c "import openai; print(openai.api_key)"
```

### Import Errors

```bash
# Reinstall dependencies
pip install --upgrade -r requirements.txt

# Check Python version
python --version  # Should be 3.10+

# Verify packages
pip list | grep -E "asyncpg|openai|numpy"
```

### Port Already in Use

```bash
# Find process using port 5432
# Linux/macOS:
lsof -i :5432
# Windows:
netstat -ano | findstr :5432

# Change database port in .env or docker-compose.yml
DATABASE_PORT=5433
# Update docker command:
docker run -d ... -p 5433:5432 ...
```

---

## 💡 Common Tasks

### Reset Database

```bash
# Stop and remove container
docker stop jebat-db
docker rm jebat-db

# Remove data volume
docker volume rm jebat_data

# Start fresh
docker run -d --name jebat-db ...
```

### Backup Database

```bash
# Create backup
docker exec jebat-db pg_dump -U jebat jebat_memory > backup.sql

# Restore backup
docker exec -i jebat-db psql -U jebat jebat_memory < backup.sql
```

### View Database Contents

```bash
# Connect to database
docker exec -it jebat-db psql -U jebat -d jebat_memory

# Inside psql:
\dt                    # List tables
SELECT COUNT(*) FROM memories;  # Count memories
\q                     # Quit
```

### Clear Test Data

```bash
# Connect to database
docker exec -it jebat-db psql -U jebat -d jebat_memory

# Inside psql:
DELETE FROM memories WHERE user_id LIKE 'test_%';
DELETE FROM sessions WHERE user_id LIKE 'test_%';
```

---

## 🎓 Learning Resources

### Tutorials (Coming Soon)

- Building your first memory-augmented chatbot
- Creating custom memory layers
- Implementing agent coordination
- Optimizing vector search performance

### API Reference (Coming Soon)

- Memory Layer API
- Storage Backend API
- Agent API
- Search API

### Community

- **GitHub Issues**: Report bugs and request features
- **Discussions**: Ask questions and share ideas
- **Discord**: Join the community (link coming soon)
- **Twitter**: Follow @JebatAI for updates

---

## ✨ What's Working Now

✅ **Memory Storage Backend**
- PostgreSQL + TimescaleDB + pgvector
- Multi-layer memory system (M0-M4)
- Heat scoring and memory decay
- Automatic consolidation

✅ **Vector Search**
- OpenAI embeddings (text-embedding-3-small)
- Semantic similarity search
- Hybrid vector + keyword search
- Memory re-ranking and diversity

✅ **Database Features**
- Time-series optimization
- Vector similarity indexes
- Automatic expiration cleanup
- Session management

✅ **Developer Tools**
- Comprehensive test suite
- Docker support
- Example scripts
- Database setup automation

---

## 🚧 Coming Next

🔨 **Phase 2 Completion** (Current)
- WebSocket gateway
- Agent factory
- Basic chat interface

🔥 **Phase 3: Model Forge** (Weeks 3-4)
- Model abliteration
- Quantization
- Fine-tuning utilities

📱 **Phase 4: Multi-Channel** (Weeks 5-6)
- WhatsApp integration
- Telegram bot
- Discord bot
- Web chat UI

🛡️ **Phase 5: Sentinel** (Weeks 7-8)
- Security monitoring
- Threat detection
- Exploitation framework

---

## 🤝 Contributing

We welcome contributions! Here's how to get started:

```bash
# Fork the repository
# Clone your fork
git clone https://github.com/yourusername/jebat.git
cd jebat

# Create a branch
git checkout -b feature/your-feature

# Make your changes
# ...

# Run tests
pytest memory_system/tests/

# Commit and push
git add .
git commit -m "Add your feature"
git push origin feature/your-feature

# Open a Pull Request
```

---

## 📄 License

JEBAT is released under the MIT License. See [LICENSE](LICENSE) for details.

---

## 🗡️ "The Warrior's Memory Never Forgets"

You're now ready to build with JEBAT! Start creating intelligent, memory-augmented applications that remember, learn, and evolve.

**Need help?** Open an issue on GitHub or check the documentation.

**Built something cool?** Share it with the community!

---

**Happy Building! 🚀**