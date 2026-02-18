# 🚀 JEBAT - Quick Start Examples

**Version**: 1.0.0  
**Last Updated**: 2026-02-18

---

## 📋 Example Projects

### 1. Basic Chatbot

**File**: `examples/chatbot/basic_bot.py`

```python
"""
Simple JEBAT-powered chatbot

Run: py examples/chatbot/basic_bot.py
"""

import asyncio
from jebat_sdk import JEBATClient

async def main():
    print("🗡️  JEBAT Chatbot")
    print("Type 'quit' to exit\n")
    
    async with JEBATClient(base_url="http://localhost:8000") as client:
        while True:
            # Get user input
            user_input = input("You: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'bye']:
                print("JEBAT: Goodbye! 👋")
                break
            
            if not user_input:
                continue
            
            # Get response from JEBAT
            response = await client.chat(
                message=user_input,
                mode="deliberate",
                timeout=30
            )
            
            print(f"JEBAT: {response.response}")
            print(f"Confidence: {response.confidence:.1%}\n")

if __name__ == "__main__":
    asyncio.run(main())
```

---

### 2. Memory-Enhanced Assistant

**File**: `examples/memory/memory_assistant.py`

```python
"""
Memory-enhanced personal assistant

Run: py examples/memory/memory_assistant.py
"""

import asyncio
from jebat_sdk import JEBATClient

async def main():
    print("🗡️  JEBAT Memory-Enhanced Assistant")
    print("I'll remember what you tell me!\n")
    
    async with JEBATClient(base_url="http://localhost:8000") as client:
        user_id = "user_demo"
        
        while True:
            user_input = input("You: ").strip()
            
            if user_input.lower() in ['quit', 'exit']:
                # Show remembered facts
                memories = await client.search_memories(
                    query="user facts",
                    user_id=user_id
                )
                
                print("\n📚 What I remember about you:")
                for mem in memories[:5]:
                    print(f"  - {mem.content}")
                
                print("\nGoodbye! 👋")
                break
            
            if not user_input:
                continue
            
            # Store as memory if it's a fact
            if any(kw in user_input.lower() for kw in ['i am', 'i like', 'my name', 'i prefer']):
                await client.store_memory(
                    content=user_input,
                    user_id=user_id,
                    layer="M1_EPISODIC"
                )
                print("JEBAT: I'll remember that! 💾\n")
            
            # Get response with memory context
            response = await client.chat(
                message=user_input,
                user_id=user_id,
                mode="deliberate"
            )
            
            print(f"JEBAT: {response.response}\n")

if __name__ == "__main__":
    asyncio.run(main())
```

---

### 3. Multi-Agent Research System

**File**: `examples/agents/research_team.py`

```python
"""
Multi-agent research team

Run: py examples/agents/research_team.py
"""

import asyncio
from jebat.orchestration import AgentOrchestrator

async def main():
    print("🗡️  JEBAT Multi-Agent Research Team")
    print("Assembling research team...\n")
    
    orchestrator = AgentOrchestrator()
    
    topic = input("Research topic: ").strip()
    
    if not topic:
        topic = "Artificial Intelligence trends"
    
    # Define research workflow
    tasks = [
        {
            "agent_type": "research",
            "task": f"Research latest developments in {topic}",
            "description": "Gather information"
        },
        {
            "agent_type": "analysis",
            "task": "Analyze the research findings for patterns and insights",
            "description": "Analyze findings"
        },
        {
            "agent_type": "writing",
            "task": "Write a comprehensive research report",
            "description": "Write report"
        },
        {
            "agent_type": "review",
            "task": "Review and fact-check the report",
            "description": "Quality review"
        }
    ]
    
    print(f"\n📋 Research Plan:")
    for i, task in enumerate(tasks, 1):
        print(f"  {i}. {task['agent_type']}: {task['description']}")
    
    print("\n🚀 Starting research...\n")
    
    # Execute multi-agent workflow
    results = await orchestrator.execute_multi_agent(tasks=tasks)
    
    # Display results
    print("\n" + "="*60)
    print("📊 RESEARCH RESULTS")
    print("="*60)
    
    for i, result in enumerate(results, 1):
        print(f"\n{i}. {result.agent_type.upper()}")
        print(f"   Duration: {result.duration:.2f}s")
        print(f"   Output:\n{result.output}")
    
    print("\n✅ Research complete!")

if __name__ == "__main__":
    asyncio.run(main())
```

---

### 4. Ultra-Think Analysis

**File**: `examples/thinking/deep_analysis.py`

```python
"""
Deep thinking analysis with Ultra-Think

Run: py examples/thinking/deep_analysis.py
"""

import asyncio
from jebat.ultra_think import create_ultra_think, ThinkingMode

async def main():
    print("🗡️  JEBAT Ultra-Think Deep Analysis")
    print("Enter a complex question for deep analysis\n")
    
    think = await create_ultra_think()
    
    question = input("Your question: ").strip()
    
    if not question:
        question = "What is the future of artificial intelligence?"
    
    print(f"\n🤔 Thinking about: {question}")
    print("This may take a moment...\n")
    
    # Run deep thinking
    result = await think.think(
        question=question,
        mode=ThinkingMode.DEEP,
        timeout=60,
        max_thoughts=20
    )
    
    # Display results
    print("="*60)
    print("💭 THINKING PROCESS")
    print("="*60)
    
    print(f"\n📊 Statistics:")
    print(f"   Thoughts: {result.thought_count}")
    print(f"   Duration: {result.duration:.2f}s")
    print(f"   Confidence: {result.confidence:.1%}")
    
    print(f"\n🔍 Thought Chain:")
    for i, thought in enumerate(result.thoughts[:10], 1):
        print(f"   {i}. {thought}")
    
    if len(result.thoughts) > 10:
        print(f"   ... and {len(result.thoughts) - 10} more thoughts")
    
    print("\n" + "="*60)
    print("🎯 CONCLUSION")
    print("="*60)
    print(f"\n{result.conclusion}")
    
    print("\n✅ Analysis complete!")

if __name__ == "__main__":
    asyncio.run(main())
```

---

### 5. Plugin Development Example

**File**: `examples/plugins/weather_plugin/manifest.json`

```json
{
  "name": "weather_plugin",
  "version": "1.0.0",
  "description": "Weather information plugin",
  "author": "JEBAT Team",
  "type": "tool",
  "entry_point": "plugin.py",
  "dependencies": ["requests"],
  "permissions": ["network"],
  "config_schema": {
    "api_key": {
      "type": "string",
      "required": true,
      "description": "OpenWeatherMap API key"
    }
  }
}
```

**File**: `examples/plugins/weather_plugin/plugin.py`

```python
"""
Weather Plugin for JEBAT

Get current weather information for any city.
"""

import requests
from typing import Any, Dict

# Plugin state
_config = {}

async def init(config: Dict[str, Any]):
    """Initialize weather plugin"""
    global _config
    _config = config
    print(f"Weather plugin initialized (API key: {_config.get('api_key', 'N/A')[:8]}...)")

async def execute(data: Any, **kwargs) -> Any:
    """
    Execute weather lookup.
    
    Args:
        data: City name or {"city": "London"}
    
    Returns:
        Weather information
    """
    city = data if isinstance(data, str) else data.get("city", "")
    
    if not city:
        return {"error": "City name required"}
    
    api_key = _config.get("api_key")
    if not api_key:
        return {"error": "API key not configured"}
    
    try:
        # Call OpenWeatherMap API
        url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        weather_data = response.json()
        
        # Format response
        return {
            "city": weather_data["name"],
            "country": weather_data["sys"]["country"],
            "temperature": weather_data["main"]["temp"],
            "feels_like": weather_data["main"]["feels_like"],
            "description": weather_data["weather"][0]["description"],
            "humidity": weather_data["main"]["humidity"],
            "wind_speed": weather_data["wind"]["speed"],
        }
        
    except requests.exceptions.Timeout:
        return {"error": "Weather service timeout"}
    except requests.exceptions.RequestException as e:
        return {"error": f"Weather service error: {str(e)}"}

async def cleanup():
    """Cleanup plugin resources"""
    global _config
    _config = {}
    print("Weather plugin cleanup complete")
```

**Usage Example**:

```python
from jebat.plugins import PluginManager

async def main():
    manager = PluginManager(plugins_dir="examples/plugins")
    
    # Load weather plugin
    await manager.load_plugin(
        "weather_plugin",
        config={"api_key": "YOUR_OPENWEATHER_API_KEY"}
    )
    
    # Get weather
    result = await manager.execute_plugin("weather_plugin", "London")
    
    if "error" in result:
        print(f"Error: {result['error']}")
    else:
        print(f"🌤️  Weather in {result['city']}, {result['country']}:")
        print(f"   Temperature: {result['temperature']}°C (feels like {result['feels_like']}°C)")
        print(f"   Conditions: {result['description']}")
        print(f"   Humidity: {result['humidity']}%")
        print(f"   Wind: {result['wind_speed']} m/s")

# asyncio.run(main())
```

---

### 6. Analytics Dashboard Example

**File**: `examples/analytics/track_usage.py`

```python
"""
Analytics tracking example

Run: py examples/analytics/track_usage.py
"""

import asyncio
import random
from datetime import datetime
from jebat.analytics import AnalyticsEngine

async def main():
    print("🗡️  JEBAT Analytics Tracking Demo")
    print("Simulating user activity...\n")
    
    engine = AnalyticsEngine()
    
    # Simulate users and activities
    users = ["user1", "user2", "user3", "user4", "user5"]
    features = ["chat", "memory", "search", "agents", "thinking"]
    
    # Generate 50 random events
    for i in range(50):
        user = random.choice(users)
        feature = random.choice(features)
        duration = random.uniform(0.5, 5.0)
        
        await engine.track_event(
            event_type=f"{feature}_usage",
            metadata={
                "feature": feature,
                "duration": duration,
                "timestamp": datetime.utcnow().isoformat()
            },
            user_id=user
        )
    
    print(f"✅ Tracked 50 events")
    
    # Get insights
    print("\n📊 Analytics Insights:")
    print("="*40)
    
    insights = await engine.get_insights(period="day")
    for insight in insights:
        delta = f"{insight.change:+.1f}%" if insight.change != 0 else "0%"
        print(f"{insight.metric}: {insight.value} ({delta})")
    
    # Get usage report
    print("\n📈 Usage Report:")
    print("="*40)
    
    report = await engine.get_usage_report(period="day")
    print(f"Total Events: {report['total_events']}")
    print(f"Unique Users: {report['unique_users']}")
    print(f"Avg Duration: {report['avg_duration']:.2f}s")
    print(f"Peak Hour: {report['peak_hour']}:00")
    
    # Get user analytics
    print("\n👥 User Analytics:")
    print("="*40)
    
    for user in users:
        analytics = await engine.get_user_analytics(user)
        print(f"\n{user}:")
        print(f"  Interactions: {analytics['total_interactions']}")
        print(f"  Retention: {analytics['retention_score']:.1%}")
        if analytics['favorite_features']:
            print(f"  Top Feature: {analytics['favorite_features'][0]}")

if __name__ == "__main__":
    asyncio.run(main())
```

---

### 7. Multi-Tenancy Example

**File**: `examples/multitenancy/saas_demo.py`

```python
"""
Multi-tenancy SaaS demo

Run: py examples/multitenancy/saas_demo.py
"""

import asyncio
from jebat.multitenancy import TenantManager, PlanType

async def main():
    print("🗡️  JEBAT Multi-Tenancy SaaS Demo")
    print("Setting up tenants...\n")
    
    manager = TenantManager()
    
    # Create different tenant tiers
    tenants = [
        {
            "name": "startup-inc",
            "display_name": "Startup Inc",
            "plan": PlanType.FREE,
        },
        {
            "name": "growth-co",
            "display_name": "Growth Co",
            "plan": PlanType.PRO,
        },
        {
            "name": "enterprise-corp",
            "display_name": "Enterprise Corp",
            "plan": PlanType.ENTERPRISE,
        },
    ]
    
    # Create tenants
    created = []
    for t in tenants:
        tenant = await manager.create_tenant(**t)
        created.append(tenant)
        print(f"✅ Created: {tenant.display_name} ({tenant.plan.value})")
    
    # Set quotas
    print("\n📊 Setting quotas...")
    
    quotas = {
        "startup-inc": {"api_calls_per_day": 100, "storage_gb": 1},
        "growth-co": {"api_calls_per_day": 10000, "storage_gb": 10},
        "enterprise-corp": {"api_calls_per_day": 1000000, "storage_gb": 100},
    }
    
    for tenant_name, limits in quotas.items():
        for quota_name, limit in limits.items():
            await manager.set_quota(tenant_name, quota_name_name, limit)
    
    # Simulate usage
    print("\n🔄 Simulating API usage...")
    
    for tenant_name in quotas.keys():
        # Consume some quota
        for _ in range(10):
            await manager.consume_quota(tenant_name, "api_calls_per_day", 1)
        
        # Check remaining
        remaining = await manager.check_quota(tenant_name, "api_calls_per_day")
        print(f"  {tenant_name}: {remaining} API calls remaining")
    
    # Get usage summaries
    print("\n📈 Usage Summaries:")
    print("="*40)
    
    for tenant in created:
        usage = await manager.get_usage_summary(tenant.id, period="day")
        print(f"\n{tenant.display_name}:")
        print(f"  Plan: {tenant.plan.value}")
        print(f"  API Calls Used: {usage.get('api_calls_per_day', 0)}")
        print(f"  Storage Used: {usage.get('storage_gb', 0):.2f} GB")

if __name__ == "__main__":
    asyncio.run(main())
```

---

### 8. Knowledge Graph Example

**File**: `examples/ml/knowledge_graph.py`

```python
"""
Knowledge Graph example

Run: py examples/ml/knowledge_graph.py
"""

import asyncio
from jebat.ml import AdvancedMLEngine

async def main():
    print("🗡️  JEBAT Knowledge Graph Demo")
    print("Building knowledge graph...\n")
    
    engine = AdvancedMLEngine()
    
    # Add concept nodes
    print("📚 Adding concepts...")
    
    ai_id = await engine.add_knowledge_node(
        label="Artificial Intelligence",
        node_type="field",
        properties={"established": 1956}
    )
    
    ml_id = await engine.add_knowledge_node(
        label="Machine Learning",
        node_type="subfield",
        properties={}
    )
    
    dl_id = await engine.add_knowledge_node(
        label="Deep Learning",
        node_type="technique",
        properties={}
    )
    
    nn_id = await engine.add_knowledge_node(
        label="Neural Networks",
        node_type="model",
        properties={}
    )
    
    # Add relationships
    print("🔗 Adding relationships...")
    
    await engine.add_knowledge_edge(
        source_id=ml_id,
        target_id=ai_id,
        relation="subset_of"
    )
    
    await engine.add_knowledge_edge(
        source_id=dl_id,
        target_id=ml_id,
        relation="subset_of"
    )
    
    await engine.add_knowledge_edge(
        source_id=nn_id,
        target_id=dl_id,
        relation="foundation_of"
    )
    
    # Query graph
    print("\n🔍 Querying knowledge graph...")
    
    result = await engine.query_knowledge_graph()
    print(f"Total Nodes: {result['total_nodes']}")
    print(f"Total Edges: {result['total_edges']}")
    
    # Get related concepts
    print("\n🔗 Related to Machine Learning:")
    
    related = await engine.get_related_nodes(ml_id)
    for node in related:
        print(f"  - {node.label} ({node.node_type})")
    
    # Export graph
    print("\n💾 Exporting knowledge graph...")
    
    json_export = await engine.export_knowledge_graph()
    print(f"Exported {len(json_export)} bytes")

if __name__ == "__main__":
    asyncio.run(main())
```

---

## 🏃 Running Examples

### Prerequisites

```bash
# Install JEBAT SDK
pip install -e .

# Or install from PyPI (when published)
pip install jebat-sdk
```

### Run Any Example

```bash
# Chatbot
py examples/chatbot/basic_bot.py

# Memory assistant
py examples/memory/memory_assistant.py

# Research team
py examples/agents/research_team.py

# Deep thinking
py examples/thinking/deep_analysis.py

# Analytics
py examples/analytics/track_usage.py

# Multi-tenancy
py examples/multitenancy/saas_demo.py

# Knowledge graph
py examples/ml/knowledge_graph.py
```

---

## 📁 Example Structure

```
examples/
├── chatbot/
│   └── basic_bot.py
├── memory/
│   └── memory_assistant.py
├── agents/
│   └── research_team.py
├── thinking/
│   └── deep_analysis.py
├── plugins/
│   └── weather_plugin/
│       ├── manifest.json
│       └── plugin.py
├── analytics/
│   └── track_usage.py
├── multitenancy/
│   └── saas_demo.py
└── ml/
    └── knowledge_graph.py
```

---

**JEBAT** - *Because warriors remember everything that matters.* 🗡️
