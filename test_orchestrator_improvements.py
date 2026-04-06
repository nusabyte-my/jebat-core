#!/usr/bin/env python3
"""
Test script to verify orchestrator improvements
"""

import asyncio
import sys
import os

# Add the jebat-core to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'jebat-core'))

from jebat.core.agents.orchestrator import AgentOrchestrator, AgentTask, TaskPriority
from jebat.core.agents.factory import AgentFactory, AgentTemplate, AgentType, AgentPersonality


async def test_intelligent_agent_selection():
    """Test that the orchestrator can select agents intelligently"""
    print("Testing intelligent agent selection...")
    
    # Create orchestrator
    orchestrator = AgentOrchestrator()
    
    # Create factory
    factory = AgentFactory()
    
    # Create agents with different capabilities
    analytical_template = AgentTemplate(
        agent_type=AgentType.ANALYTICAL,
        name="AnalystAgent",
        description="Data analysis agent",
        personality=AgentPersonality.TECHNICAL,
        capabilities=["analysis", "insights", "data_processing"],
    )
    
    creative_template = AgentTemplate(
        agent_type=AgentType.CREATIVE,
        name="CreativeAgent",
        description="Creative content agent",
        personality=AgentPersonality.CREATIVE,
        capabilities=["creation", "brainstorming", "design"],
    )
    
    conversational_template = AgentTemplate(
        agent_type=AgentType.CONVERSATIONAL,
        name="ChatAgent",
        description="Friendly conversational agent",
        personality=AgentPersonality.FRIENDLY,
        capabilities=["conversation", "context", "support"],
    )
    
    # Register agents
    analyst_id = factory.create(analytical_template, "analyst_001")
    creative_id = factory.create(creative_template, "creative_001")
    chat_id = factory.create(conversational_template, "chat_001")
    
    # Add agents to orchestrator
    orchestrator.agents[analyst_id] = factory.get(analyst_id)
    orchestrator.agents[creative_id] = factory.get(creative_id)
    orchestrator.agents[chat_id] = factory.get(chat_id)
    
    print(f"Registered agents: {list(orchestrator.agents.keys())}")
    
    # Test task that requires analysis
    analysis_task = AgentTask(
        description="Analyze sales data for Q4 trends",
        parameters={"type": "analytical"}
    )
    
    selected_agent = orchestrator._select_agent(analysis_task)
    print(f"Analysis task selected agent: {selected_agent}")
    print(f"Expected: analyst_001, Got: {selected_agent}")
    
    # Test task that requires creativity
    creative_task = AgentTask(
        description="Create a marketing campaign for new product",
        parameters={"type": "creative"}
    )
    
    selected_agent = orchestrator._select_agent(creative_task)
    print(f"Creative task selected agent: {selected_agent}")
    print(f"Expected: creative_001, Got: {selected_agent}")
    
    # Test task that requires conversation
    conversation_task = AgentTask(
        description="Have a conversation with the user about their day",
        parameters={"type": "conversational"}
    )
    
    selected_agent = orchestrator._select_agent(conversation_task)
    print(f"Conversation task selected agent: {selected_agent}")
    print(f"Expected: chat_001, Got: {selected_agent}")
    
    # Test task with no specific capabilities
    generic_task = AgentTask(
        description="Do something",
        parameters={}
    )
    
    selected_agent = orchestrator._select_agent(generic_task)
    print(f"Generic task selected agent: {selected_agent}")
    
    print("Intelligent agent selection test completed!")
    

async def test_performance_tracking():
    """Test that performance tracking works"""
    print("\nTesting performance tracking...")
    
    orchestrator = AgentOrchestrator()
    
    # Add a mock agent
    orchestrator.agents["test_agent_001"] = {
        "id": "test_agent_001",
        "name": "TestAgent",
        "type": "task_executor",
        "capabilities": ["testing"],
    }
    
    # Check initial stats
    stats = orchestrator.get_stats()
    print(f"Initial stats: {stats}")
    
    # Simulate some task executions by updating performance directly
    orchestrator._update_agent_performance("test_agent_001", 1.5, True)
    orchestrator._update_agent_performance("test_agent_001", 2.0, True)
    orchestrator._update_agent_performance("test_agent_001", 1.0, False)
    
    # Check updated stats
    stats = orchestrator.get_stats()
    print(f"Updated stats: {stats}")
    
    # Verify performance data
    perf = stats["agent_performance"]["test_agent_001"]
    assert perf["total_tasks"] == 3
    assert perf["success_rate"] == 2/3
    assert perf["avg_execution_time"] == (1.5 + 2.0 + 1.0) / 3
    
    print("Performance tracking test completed!")


async def main():
    """Run all tests"""
    print("Running orchestrator improvements tests...\n")
    
    await test_intelligent_agent_selection()
    await test_performance_tracking()
    
    print("\nAll tests completed!")


if __name__ == "__main__":
    asyncio.run(main())