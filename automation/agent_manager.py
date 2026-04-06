"""
Agent Manager
Centralized manager for orchestrating multiple agents, handling communication,
task distribution, and coordination between agents and skills.
"""

import asyncio
import json
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from ..agents.base_agent import AgentMessage, AgentResult, AgentStatus, BaseAgent
from ..skills.base_skill import BaseSkill, SkillResult


class TaskQueue:
    """Simple task queue for managing agent tasks"""

    def __init__(self):
        self.queue = asyncio.Queue()
        self.results = {}
        self.task_counter = 0

    async def add_task(
        self,
        agent_id: str,
        task: Dict[str, Any],
        priority: int = 5,
        callback: Optional[callable] = None,
    ) -> str:
        """Add task to queue"""
        self.task_counter += 1
        task_id = f"task_{self.task_counter}_{int(time.time())}"

        task_item = {
            "task_id": task_id,
            "agent_id": agent_id,
            "task": task,
            "priority": priority,
            "created_at": datetime.now(),
            "callback": callback,
        }

        await self.queue.put(task_item)
        return task_id

    async def get_task(self) -> Optional[Dict[str, Any]]:
        """Get next task from queue"""
        try:
            return await asyncio.wait_for(self.queue.get(), timeout=1.0)
        except asyncio.TimeoutError:
            return None

    def add_result(self, task_id: str, result: AgentResult):
        """Store task result"""
        self.results[task_id] = {
            "result": result,
            "completed_at": datetime.now(),
        }

    def get_result(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get task result"""
        return self.results.get(task_id)

    def get_queue_size(self) -> int:
        """Get current queue size"""
        return self.queue.qsize()


class AgentManager:
    """
    Central manager for orchestrating multiple agents and skills.
    Handles agent lifecycle, task distribution, communication, and coordination.
    """

    def __init__(
        self,
        manager_id: str = "agent_manager_001",
        config: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize the Agent Manager.

        Args:
            manager_id: Unique manager identifier
            config: Configuration parameters
        """
        self.manager_id = manager_id
        self.config = config or {}

        # Default configuration
        default_config = {
            "max_concurrent_tasks": 10,
            "task_timeout": 300,
            "heartbeat_interval": 60,
            "log_level": "INFO",
            "save_logs": True,
            "log_directory": "./logs",
            "state_file": "./agent_manager_state.json",
            "auto_save_interval": 60,
        }

        # Merge with provided config
        for key, value in default_config.items():
            if key not in self.config:
                self.config[key] = value

        # Initialize components
        self.agents: Dict[str, BaseAgent] = {}
        self.skills: Dict[str, BaseSkill] = {}
        self.task_queue = TaskQueue()
        self.active_tasks: Dict[str, Dict[str, Any]] = {}
        self.message_bus: List[AgentMessage] = []

        # Manager state
        self.is_running = False
        self.start_time = None
        self.stats = {
            "tasks_completed": 0,
            "tasks_failed": 0,
            "messages_sent": 0,
            "uptime": 0,
        }

        # Setup logging
        self.logger = self._setup_logging()

        # Background tasks
        self.background_tasks: List[asyncio.Task] = []

    def _setup_logging(self) -> logging.Logger:
        """Setup logging for the manager"""
        logger = logging.getLogger(f"agent_manager_{self.manager_id}")
        logger.setLevel(getattr(logging, self.config["log_level"]))

        if not logger.handlers:
            # Console handler
            console_handler = logging.StreamHandler()
            console_formatter = logging.Formatter(
                "[AgentManager] %(asctime)s - %(levelname)s - %(message)s"
            )
            console_handler.setFormatter(console_formatter)
            logger.addHandler(console_handler)

            # File handler (if enabled)
            if self.config["save_logs"]:
                log_dir = Path(self.config["log_directory"])
                log_dir.mkdir(exist_ok=True)

                file_handler = logging.FileHandler(
                    log_dir / f"agent_manager_{self.manager_id}.log"
                )
                file_formatter = logging.Formatter(
                    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
                )
                file_handler.setFormatter(file_formatter)
                logger.addHandler(file_handler)

        return logger

    def register_agent(self, agent: BaseAgent) -> bool:
        """
        Register an agent with the manager.

        Args:
            agent: Agent instance to register

        Returns:
            True if registration successful
        """
        try:
            if agent.agent_id in self.agents:
                self.logger.warning(f"Agent {agent.agent_id} already registered")
                return False

            self.agents[agent.agent_id] = agent
            self.logger.info(f"Registered agent: {agent.name} ({agent.agent_id})")
            return True

        except Exception as e:
            self.logger.error(f"Failed to register agent: {str(e)}")
            return False

    def unregister_agent(self, agent_id: str) -> bool:
        """
        Unregister an agent from the manager.

        Args:
            agent_id: ID of agent to unregister

        Returns:
            True if unregistration successful
        """
        try:
            if agent_id not in self.agents:
                self.logger.warning(f"Agent {agent_id} not found")
                return False

            agent = self.agents[agent_id]
            if agent.status == AgentStatus.RUNNING:
                agent.stop()

            del self.agents[agent_id]
            self.logger.info(f"Unregistered agent: {agent_id}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to unregister agent {agent_id}: {str(e)}")
            return False

    def register_skill(
        self, skill: BaseSkill, agent_ids: Optional[List[str]] = None
    ) -> bool:
        """
        Register a skill and optionally attach it to specific agents.

        Args:
            skill: Skill instance to register
            agent_ids: List of agent IDs to attach skill to (None for all)

        Returns:
            True if registration successful
        """
        try:
            self.skills[skill.skill_id] = skill
            self.logger.info(f"Registered skill: {skill.name} ({skill.skill_id})")

            # Attach to specified agents or all agents
            target_agents = agent_ids or list(self.agents.keys())
            for agent_id in target_agents:
                if agent_id in self.agents:
                    self.agents[agent_id].add_skill(skill.skill_id, skill)

            return True

        except Exception as e:
            self.logger.error(f"Failed to register skill: {str(e)}")
            return False

    async def submit_task(
        self,
        agent_id: str,
        task: Dict[str, Any],
        priority: int = 5,
        callback: Optional[callable] = None,
    ) -> str:
        """
        Submit a task for execution by a specific agent.

        Args:
            agent_id: ID of target agent
            task: Task parameters
            priority: Task priority (lower numbers = higher priority)
            callback: Optional callback function for result

        Returns:
            Task ID
        """
        if agent_id not in self.agents:
            raise ValueError(f"Agent {agent_id} not registered")

        task_id = await self.task_queue.add_task(agent_id, task, priority, callback)
        self.logger.info(f"Submitted task {task_id} to agent {agent_id}")
        return task_id

    async def submit_broadcast_task(
        self,
        task: Dict[str, Any],
        agent_filter: Optional[callable] = None,
        priority: int = 5,
    ) -> List[str]:
        """
        Submit a task to multiple agents (broadcast).

        Args:
            task: Task parameters
            agent_filter: Optional function to filter agents
            priority: Task priority

        Returns:
            List of task IDs
        """
        task_ids = []
        target_agents = self.agents.values()

        if agent_filter:
            target_agents = [agent for agent in target_agents if agent_filter(agent)]

        for agent in target_agents:
            task_id = await self.submit_task(agent.agent_id, task, priority)
            task_ids.append(task_id)

        self.logger.info(f"Broadcast task to {len(task_ids)} agents")
        return task_ids

    async def get_task_result(
        self, task_id: str, timeout: Optional[float] = None
    ) -> Optional[AgentResult]:
        """
        Get result for a specific task.

        Args:
            task_id: Task ID to get result for
            timeout: Maximum wait time for result

        Returns:
            AgentResult or None if not found/timeout
        """
        start_time = time.time()
        timeout = timeout or self.config["task_timeout"]

        while time.time() - start_time < timeout:
            result_data = self.task_queue.get_result(task_id)
            if result_data:
                return result_data["result"]

            await asyncio.sleep(0.1)

        return None

    async def send_message(
        self,
        sender_id: str,
        recipient_id: str,
        content: Any,
        message_type: str = "general",
    ) -> bool:
        """
        Send message between agents.

        Args:
            sender_id: Sender agent ID
            recipient_id: Recipient agent ID
            content: Message content
            message_type: Type of message

        Returns:
            True if message sent successfully
        """
        try:
            if sender_id in self.agents and recipient_id in self.agents:
                sender = self.agents[sender_id]
                recipient = self.agents[recipient_id]

                message = await sender.send_message(recipient_id, content, message_type)
                await recipient.receive_message(message)

                self.message_bus.append(message)
                self.stats["messages_sent"] += 1

                self.logger.debug(f"Message sent from {sender_id} to {recipient_id}")
                return True
            else:
                self.logger.error(
                    f"Invalid sender ({sender_id}) or recipient ({recipient_id})"
                )
                return False

        except Exception as e:
            self.logger.error(f"Failed to send message: {str(e)}")
            return False

    async def start(self):
        """Start the agent manager and all background processes"""
        if self.is_running:
            self.logger.warning("Agent manager already running")
            return

        self.is_running = True
        self.start_time = datetime.now()
        self.logger.info("Starting agent manager...")

        # Start background tasks
        self.background_tasks = [
            asyncio.create_task(self._task_processor()),
            asyncio.create_task(self._heartbeat_monitor()),
            asyncio.create_task(self._auto_save_state()),
        ]

        # Start all registered agents
        for agent in self.agents.values():
            agent.start()

        self.logger.info("Agent manager started successfully")

    async def stop(self):
        """Stop the agent manager and all processes"""
        if not self.is_running:
            return

        self.logger.info("Stopping agent manager...")
        self.is_running = False

        # Cancel background tasks
        for task in self.background_tasks:
            task.cancel()

        # Wait for tasks to complete
        await asyncio.gather(*self.background_tasks, return_exceptions=True)

        # Stop all agents
        for agent in self.agents.values():
            agent.stop()

        # Save final state
        await self._save_state()

        self.logger.info("Agent manager stopped")

    async def _task_processor(self):
        """Background task processor"""
        while self.is_running:
            try:
                # Process pending tasks
                active_count = len(self.active_tasks)
                if active_count < self.config["max_concurrent_tasks"]:
                    task_item = await self.task_queue.get_task()
                    if task_item:
                        await self._execute_task(task_item)

                await asyncio.sleep(0.1)

            except Exception as e:
                self.logger.error(f"Task processor error: {str(e)}")
                await asyncio.sleep(1)

    async def _execute_task(self, task_item: Dict[str, Any]):
        """Execute a single task"""
        task_id = task_item["task_id"]
        agent_id = task_item["agent_id"]
        task = task_item["task"]

        try:
            # Mark task as active
            self.active_tasks[task_id] = {
                **task_item,
                "started_at": datetime.now(),
            }

            agent = self.agents[agent_id]
            self.logger.debug(f"Executing task {task_id} on agent {agent_id}")

            # Execute task
            result = await agent.execute(task)

            # Store result
            self.task_queue.add_result(task_id, result)

            # Update stats
            if result.success:
                self.stats["tasks_completed"] += 1
            else:
                self.stats["tasks_failed"] += 1

            # Call callback if provided
            callback = task_item.get("callback")
            if callback:
                try:
                    await callback(task_id, result)
                except Exception as e:
                    self.logger.error(f"Task callback error: {str(e)}")

            self.logger.debug(f"Task {task_id} completed: {result.success}")

        except Exception as e:
            self.logger.error(f"Task execution error: {str(e)}")
            error_result = AgentResult(
                success=False,
                error=f"Task execution failed: {str(e)}",
            )
            self.task_queue.add_result(task_id, error_result)
            self.stats["tasks_failed"] += 1

        finally:
            # Remove from active tasks
            if task_id in self.active_tasks:
                del self.active_tasks[task_id]

    async def _heartbeat_monitor(self):
        """Monitor agent health and send heartbeats"""
        while self.is_running:
            try:
                for agent_id, agent in self.agents.items():
                    status = agent.get_status()
                    if status["status"] == "error":
                        self.logger.warning(f"Agent {agent_id} in error state")

                # Update uptime
                if self.start_time:
                    self.stats["uptime"] = (
                        datetime.now() - self.start_time
                    ).total_seconds()

                await asyncio.sleep(self.config["heartbeat_interval"])

            except Exception as e:
                self.logger.error(f"Heartbeat monitor error: {str(e)}")
                await asyncio.sleep(self.config["heartbeat_interval"])

    async def _auto_save_state(self):
        """Automatically save manager state"""
        while self.is_running:
            try:
                await self._save_state()
                await asyncio.sleep(self.config["auto_save_interval"])

            except Exception as e:
                self.logger.error(f"Auto-save error: {str(e)}")
                await asyncio.sleep(self.config["auto_save_interval"])

    async def _save_state(self):
        """Save current manager state to file"""
        try:
            state = {
                "manager_id": self.manager_id,
                "timestamp": datetime.now().isoformat(),
                "stats": self.stats.copy(),
                "agents": {
                    agent_id: agent.get_status()
                    for agent_id, agent in self.agents.items()
                },
                "skills": {
                    skill_id: skill.get_info()
                    for skill_id, skill in self.skills.items()
                },
                "queue_size": self.task_queue.get_queue_size(),
                "active_tasks": len(self.active_tasks),
            }

            with open(self.config["state_file"], "w") as f:
                json.dump(state, f, indent=2)

        except Exception as e:
            self.logger.error(f"Failed to save state: {str(e)}")

    def get_status(self) -> Dict[str, Any]:
        """Get comprehensive manager status"""
        return {
            "manager_id": self.manager_id,
            "is_running": self.is_running,
            "uptime": self.stats["uptime"],
            "stats": self.stats.copy(),
            "agents": {
                agent_id: agent.get_status() for agent_id, agent in self.agents.items()
            },
            "skills": list(self.skills.keys()),
            "queue_size": self.task_queue.get_queue_size(),
            "active_tasks": len(self.active_tasks),
            "message_count": len(self.message_bus),
        }

    def get_agent_capabilities(self) -> Dict[str, List[str]]:
        """Get capabilities of all registered agents"""
        return {
            agent_id: agent.get_capabilities()
            for agent_id, agent in self.agents.items()
        }

    def find_agents_by_capability(self, capability: str) -> List[str]:
        """Find agents that have a specific capability"""
        capable_agents = []
        for agent_id, agent in self.agents.items():
            if capability in agent.get_capabilities():
                capable_agents.append(agent_id)
        return capable_agents

    def clear_message_history(self):
        """Clear message bus history"""
        self.message_bus.clear()
        self.logger.info("Message history cleared")

    async def shutdown_gracefully(self, timeout: float = 30):
        """Gracefully shutdown with timeout"""
        self.logger.info(f"Graceful shutdown initiated (timeout: {timeout}s)")

        try:
            # Wait for active tasks to complete or timeout
            start_time = time.time()
            while self.active_tasks and (time.time() - start_time) < timeout:
                await asyncio.sleep(1)
                remaining_time = timeout - (time.time() - start_time)
                self.logger.info(
                    f"Waiting for {len(self.active_tasks)} active tasks... ({remaining_time:.1f}s remaining)"
                )

            # Force stop if timeout reached
            if self.active_tasks:
                self.logger.warning(
                    f"Timeout reached, {len(self.active_tasks)} tasks still active"
                )

            await self.stop()

        except Exception as e:
            self.logger.error(f"Graceful shutdown error: {str(e)}")
            await self.stop()

    def __str__(self) -> str:
        return f"AgentManager({self.manager_id}, {len(self.agents)} agents, running={self.is_running})"

    def __repr__(self) -> str:
        return f"AgentManager(manager_id='{self.manager_id}', agents={len(self.agents)}, skills={len(self.skills)})"
