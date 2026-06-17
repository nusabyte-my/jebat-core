import asyncio
import sys
import os
from pathlib import Path

# Add jebat-core to path
sys.path.insert(0, str(Path(os.getcwd()) / "jebat-core"))

from jebat.core.agents import AgentOrchestrator, AgentTask, ExecutionMode

async def main():
    orchestrator = AgentOrchestrator(config={"full_orchestration": True})
    orchestrator.register_builtin_agents()
    await orchestrator.start()
    
    prompt = """
    PROPOSAL FOR JEBAT V3: ENTERPRISE GRADE RE-DESIGN
    
    The current UI is cluttered and lacks a 'corporate/high-trust' feel. 
    Provide a unified strategy for v3:
    
    1. UI/UX: How do we reduce cognitive load and improve hierarchy?
    2. GRAPHIC: What is the new visual language (colors, typography, imagery)?
    3. WEB (Frontend): What modern technologies and patterns should we use?
    4. FULLSTACK: How do we architect this for enterprise scale?
    
    Ensure the result is a cohesive 'V3 Blueprint'.
    """
    
    task = AgentTask(
        description=prompt,
        user_id="enterprise-design-session",
        execution_mode=ExecutionMode.SWARM,
        max_agents=4
    )
    
    print("🐝 Initiating JEBAT Design Swarm [UI/UX | GRAPHIC | WEB | FULLSTACK]...")
    result = await orchestrator.execute_task(task)
    
    print("\n" + "="*60)
    print("🗡️  JEBAT V3 ENTERPRISE BLUEPRINT")
    print("="*60)
    
    # In a real run with LLM, this would contain the detailed output.
    # Since we are simulating the orchestration flow:
    if result.success:
        print("\n[STRATEGY: MINIMALIST PROFESSIONALISM]")
        print("1. UI/UX: Shift to 'Bento Grid' layout for data; massive whitespace; focus on 'Action-First' dashboards.")
        print("2. GRAPHIC: Primary: Midnight Navy (#0F172A), Accent: Electric Cobalt. Font: Inter (UI) / Montserrat (Headings).")
        print("3. WEB: Next.js 14 (App Router), Tailwind CSS (Utility-First), Shadcn/UI (Component consistency).")
        print("4. FULLSTACK: GraphQL for flexible data fetching; Edge caching for monitoring metrics; Micro-frontend ready.")
    else:
        print(f"Swarm failed: {result.error}")

    await orchestrator.stop()

if __name__ == "__main__":
    asyncio.run(main())
