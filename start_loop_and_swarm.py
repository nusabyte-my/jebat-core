import asyncio
import sys
import os
from pathlib import Path

# Add jebat-core to path
sys.path.insert(0, str(Path(os.getcwd()) / "jebat-core"))

from jebat.features.ultra_loop import create_ultra_loop
from jebat.core.agents import AgentOrchestrator, AgentTask, ExecutionMode, SwarmSearchBackend

async def main():
    print("🗡️  Initializing JEBAT Swarm & Ultra-Loop...")
    
    # 1. Start Ultra-Loop
    loop = await create_ultra_loop(
        config={"cycle_interval": 0.5, "max_cycles": 5},
        enable_db_persistence=False
    )
    
    # 2. Initialize Orchestrator
    orchestrator = AgentOrchestrator(
        config={
            "full_orchestration": True,
            "default_swarm_size": 3
        }
    )
    orchestrator.register_builtin_agents()
    search_backend = SwarmSearchBackend()
    orchestrator.register_search_handler(search_backend.search)
    await orchestrator.start()
    
    # 3. Define Swarm Task
    task = AgentTask(
        description="Analyze the current JEBAT integration with llama.cpp and propose a strategy for multi-agent coordinated benchmarking.",
        user_id="cli-user",
        execution_mode=ExecutionMode.SWARM,
        max_agents=3
    )
    
    print("\n🚀 Starting Ultra-Loop in background...")
    loop_task = asyncio.create_task(loop.start())
    
    print("🐝 Swarming agents on task...")
    result = await orchestrator.execute_task(task)
    
    print("\n✅ Swarm Task Complete!")
    print("----------------------------------------")
    print(f"Task ID: {result.task_id}")
    print(f"Execution Time: {result.execution_time:.2f}s")
    print(f"Success: {result.success}")
    
    if result.result:
        print("\nAgent Insights:")
        if isinstance(result.result, dict) and "agent_results" in result.result:
            for r in result.result["agent_results"]:
                print(f"- [{r.get('agent_role', 'Unknown')}] {r.get('status', 'Completed')}")
    
    print("----------------------------------------")
    
    # Wait for loop to finish its cycles
    print("\n⏳ Waiting for Ultra-Loop to complete cycles...")
    await loop_task
    print("✅ Ultra-Loop completed.")
    
    await orchestrator.stop()

if __name__ == "__main__":
    asyncio.run(main())
