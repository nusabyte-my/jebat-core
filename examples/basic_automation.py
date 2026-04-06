"""
Basic Automation Example
Demonstrates how to set up and run multiple agents with skills for automated tasks.
This example shows data processing, web scraping, and API integration workflows.
"""

import asyncio
import logging
import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from agents.data_agent import DataAgent
from agents.web_agent import WebAgent
from automation.agent_manager import AgentManager
from config.config_manager import ConfigManager
from skills.api_communication_skill import APICommunicationSkill
from skills.file_processing_skill import FileProcessingSkill


async def setup_logging():
    """Setup logging for the automation example"""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler("automation_example.log"),
        ],
    )


async def create_sample_data():
    """Create sample data files for testing"""
    sample_data = [
        {"name": "Alice", "age": 30, "city": "New York", "salary": 75000},
        {"name": "Bob", "age": 25, "city": "San Francisco", "salary": 80000},
        {"name": "Charlie", "age": 35, "city": "Boston", "salary": 70000},
        {"name": "Diana", "age": 28, "city": "Seattle", "salary": 85000},
        {"name": "Eve", "age": 32, "city": "Austin", "salary": 72000},
    ]

    os.makedirs("sample_data", exist_ok=True)

    # Create CSV file
    import csv

    with open("sample_data/employees.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["name", "age", "city", "salary"])
        writer.writeheader()
        writer.writerows(sample_data)

    # Create JSON file
    import json

    with open("sample_data/employees.json", "w") as f:
        json.dump(sample_data, f, indent=2)

    print("Sample data files created in 'sample_data/' directory")


async def basic_data_processing_workflow():
    """Demonstrate basic data processing workflow"""
    print("\n=== Basic Data Processing Workflow ===")

    # Create data agent
    data_agent = DataAgent(
        agent_id="data_processor_001",
        name="Data Processor",
        config={"output_directory": "./output", "max_file_size_mb": 50},
    )

    # Add file processing skill
    file_skill = FileProcessingSkill()
    data_agent.add_skill("file_processing", file_skill)

    try:
        # Read CSV file
        read_task = {"action": "read_file", "file_path": "sample_data/employees.csv"}

        result = await data_agent.execute(read_task)
        if result.success:
            print(f"✓ Successfully read CSV file with {len(result.data)} rows")

            # Process data - calculate average salary by city
            process_task = {
                "action": "aggregate_data",
                "data": result.data,
                "group_by": ["city"],
                "aggregations": {"salary": ["mean", "count"]},
            }

            agg_result = await data_agent.execute(process_task)
            if agg_result.success:
                print("✓ Data aggregation completed")
                print(f"Results shape: {agg_result.data.shape}")

                # Export results
                export_task = {
                    "action": "export_data",
                    "data": agg_result.data,
                    "file_path": "./output/salary_by_city.json",
                    "format": "json",
                }

                export_result = await data_agent.execute(export_task)
                if export_result.success:
                    print("✓ Results exported successfully")
                    print(f"File saved: {export_result.data['file_path']}")

    except Exception as e:
        print(f"✗ Data processing workflow failed: {e}")


async def web_scraping_workflow():
    """Demonstrate web scraping workflow"""
    print("\n=== Web Scraping Workflow ===")

    # Create web agent
    web_agent = WebAgent(
        agent_id="web_scraper_001",
        name="Web Scraper",
        config={"headless": True, "timeout": 30},
    )

    try:
        # Scrape a sample website (using httpbin.org for testing)
        scrape_task = {
            "action": "scrape_page",
            "url": "https://httpbin.org/json",
            "extract_text": True,
            "extract_links": False,
        }

        result = await web_agent.execute(scrape_task)
        if result.success:
            print("✓ Successfully scraped web page")
            print(f"Page title: {result.data.get('title', 'N/A')}")

            # Make API call
            api_task = {
                "action": "api_call",
                "url": "https://httpbin.org/get",
                "method": "GET",
                "params": {"test": "automation_example"},
            }

            api_result = await web_agent.execute(api_task)
            if api_result.success:
                print("✓ API call completed successfully")
                print(f"Status code: {api_result.data['status_code']}")

    except Exception as e:
        print(f"✗ Web scraping workflow failed: {e}")
    finally:
        # Cleanup browser resources
        web_agent.cleanup()


async def api_integration_workflow():
    """Demonstrate API integration workflow"""
    print("\n=== API Integration Workflow ===")

    # Create API communication skill
    api_skill = APICommunicationSkill(config={"timeout": 30, "max_retries": 3})

    try:
        # Test basic API request
        request_params = {
            "operation": "request",
            "url": "https://jsonplaceholder.typicode.com/posts/1",
            "method": "GET",
        }

        result = await api_skill.safe_execute(request_params)
        if result.success:
            print("✓ Basic API request successful")
            data = result.data.get("data", {})
            if isinstance(data, dict) and "title" in data:
                print(f"Post title: {data['title']}")

            # Test batch requests
            batch_params = {
                "operation": "batch_requests",
                "requests": [
                    {
                        "url": "https://jsonplaceholder.typicode.com/posts/1",
                        "method": "GET",
                    },
                    {
                        "url": "https://jsonplaceholder.typicode.com/posts/2",
                        "method": "GET",
                    },
                    {
                        "url": "https://jsonplaceholder.typicode.com/posts/3",
                        "method": "GET",
                    },
                ],
                "max_concurrent": 2,
            }

            batch_result = await api_skill.safe_execute(batch_params)
            if batch_result.success:
                print(
                    f"✓ Batch requests completed: {batch_result.data['successful_requests']} successful"
                )

    except Exception as e:
        print(f"✗ API integration workflow failed: {e}")


async def multi_agent_coordination():
    """Demonstrate multi-agent coordination using AgentManager"""
    print("\n=== Multi-Agent Coordination ===")

    # Create agent manager
    manager = AgentManager(
        manager_id="coordination_manager",
        config={"max_concurrent_tasks": 5, "task_timeout": 60},
    )

    try:
        # Create and register agents
        data_agent = DataAgent(agent_id="data_001", name="Data Agent 1")
        web_agent = WebAgent(agent_id="web_001", name="Web Agent 1")

        manager.register_agent(data_agent)
        manager.register_agent(web_agent)

        # Create and register skills
        file_skill = FileProcessingSkill()
        api_skill = APICommunicationSkill()

        manager.register_skill(file_skill, ["data_001"])
        manager.register_skill(api_skill, ["web_001"])

        # Start manager
        await manager.start()

        print("✓ Agent manager started with registered agents and skills")

        # Submit coordinated tasks
        tasks = []

        # Task 1: Data processing
        data_task_id = await manager.submit_task(
            "data_001",
            {"action": "read_file", "file_path": "sample_data/employees.json"},
        )
        tasks.append(("data", data_task_id))

        # Task 2: Web API call
        web_task_id = await manager.submit_task(
            "web_001",
            {"action": "api_call", "url": "https://httpbin.org/uuid", "method": "GET"},
        )
        tasks.append(("web", web_task_id))

        # Wait for results
        print("Waiting for task results...")
        for task_type, task_id in tasks:
            result = await manager.get_task_result(task_id, timeout=30)
            if result and result.success:
                print(f"✓ {task_type.title()} task completed successfully")
            else:
                print(f"✗ {task_type.title()} task failed")

        # Get manager status
        status = manager.get_status()
        print(f"Manager status: {status['stats']['tasks_completed']} tasks completed")

    except Exception as e:
        print(f"✗ Multi-agent coordination failed: {e}")
    finally:
        # Clean shutdown
        if manager.is_running:
            await manager.shutdown_gracefully(timeout=10)


async def configuration_management_demo():
    """Demonstrate configuration management"""
    print("\n=== Configuration Management Demo ===")

    # Create config manager
    config_manager = ConfigManager(config_directory="./config_demo")

    try:
        # Create sample agent configuration
        agent_config = {
            "agent_id": "demo_agent_001",
            "name": "Demo Agent",
            "description": "Agent for demonstration purposes",
            "max_concurrent_tasks": 3,
            "timeout": 45,
            "enabled": True,
            "skills": ["file_processing", "api_communication"],
            "resources": {"cpu_limit": 0.5, "memory_limit_mb": 256},
        }

        # Save configuration
        success = config_manager.save_config(
            "agent",
            "demo_agent",
            agent_config,
            format_type=config_manager.ConfigFormat.JSON,
        )

        if success:
            print("✓ Agent configuration saved")

            # Load and verify
            loaded_config = config_manager.get_config("agent", "demo_agent")
            if loaded_config:
                print(f"✓ Configuration loaded: {loaded_config['name']}")

                # Merge with global config
                merged_config = config_manager.get_merged_config("agent", "demo_agent")
                print(f"✓ Merged configuration has {len(merged_config)} keys")

        # List all configurations
        all_configs = config_manager.list_configs()
        print(f"Available configurations: {all_configs}")

    except Exception as e:
        print(f"✗ Configuration management failed: {e}")


async def cleanup_demo_files():
    """Clean up demo files and directories"""
    print("\n=== Cleanup ===")

    import shutil

    cleanup_paths = [
        "sample_data",
        "output",
        "config_demo",
        "web_output",
        "downloads",
        "screenshots",
        "logs",
        "temp",
        "backup",
    ]

    for path in cleanup_paths:
        if os.path.exists(path):
            if os.path.isdir(path):
                shutil.rmtree(path)
                print(f"✓ Removed directory: {path}")
            else:
                os.remove(path)
                print(f"✓ Removed file: {path}")

    # Remove log files
    for log_file in ["automation_example.log", "agent_manager_001.log"]:
        if os.path.exists(log_file):
            os.remove(log_file)
            print(f"✓ Removed log file: {log_file}")


async def main():
    """Main automation example function"""
    print("🚀 Multi-Agent Automation System - Basic Example")
    print("=" * 55)

    # Setup
    await setup_logging()

    try:
        # Create sample data
        await create_sample_data()

        # Run workflows
        await basic_data_processing_workflow()
        await web_scraping_workflow()
        await api_integration_workflow()
        await multi_agent_coordination()
        await configuration_management_demo()

        print("\n🎉 All workflows completed successfully!")

    except KeyboardInterrupt:
        print("\n⏹️  Automation interrupted by user")
    except Exception as e:
        print(f"\n❌ Automation failed: {e}")
        logging.exception("Automation error")
    finally:
        # Optional cleanup (uncomment to clean up demo files)
        # await cleanup_demo_files()
        print("\n✨ Automation example finished")


if __name__ == "__main__":
    # Run the automation example
    asyncio.run(main())
