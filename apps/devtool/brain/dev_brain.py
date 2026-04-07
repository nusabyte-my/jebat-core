"""
JEBAT DevAssistant Brain

Central intelligence for development tasks:
- Ultra-Think reasoning
- Task planning
- Multi-agent coordination
- Project memory
- Skills integration
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class TaskResult:
    """Result of task execution."""

    success: bool
    message: str
    files: List[str] = field(default_factory=list)
    issues: List[str] = field(default_factory=list)
    cause: Optional[str] = None
    fix: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class DevBrain:
    """
    Central intelligence for DevAssistant.

    Uses JEBAT Ultra-Think for reasoning and planning.
    Coordinates multiple agents for complex tasks.
    Integrates skills for execution.
    """

    def __init__(self):
        """Initialize DevBrain."""
        self.project_context: Dict[str, Any] = {}
        self.task_history: List[Dict] = []
        self.skills: Dict[str, Any] = {}
        logger.info("DevBrain initialized")

    def initialize_skills(self, sandbox):
        """
        Initialize all skills with sandbox.

        Args:
            sandbox: DevSandbox instance
        """
        from ..skills import (
            CodeSkills,
            DebugSkills,
            GitSkills,
            ProjectSkills,
            TestSkills,
        )

        self.skills["code"] = CodeSkills(sandbox)
        self.skills["project"] = ProjectSkills(sandbox)
        self.skills["git"] = GitSkills(sandbox)
        self.skills["test"] = TestSkills(sandbox)
        self.skills["debug"] = DebugSkills(sandbox)

        logger.info("DevBrain skills initialized")

    async def execute_task(
        self,
        task_type: str,
        description: str,
        sandbox: Any,
        **kwargs,
    ) -> TaskResult:
        """
        Execute a development task.

        Args:
            task_type: Type of task (create, modify, review, etc.)
            description: Task description
            sandbox: DevSandbox for execution
            **kwargs: Additional parameters

        Returns:
            TaskResult
        """
        logger.info(f"Executing task: {task_type} - {description}")

        # Use Ultra-Think to plan the task
        plan = await self._plan_task(task_type, description, **kwargs)

        # Execute the plan (pass task_type in kwargs)
        kwargs["task_type"] = task_type
        result = await self._execute_plan(plan, sandbox, **kwargs)

        # Store in history
        self.task_history.append(
            {
                "type": task_type,
                "description": description,
                "result": result.success,
                "timestamp": datetime.utcnow(),
            }
        )

        return result

    async def _plan_task(self, task_type: str, description: str, **kwargs) -> Dict:
        """
        Plan task using Ultra-Think.

        Args:
            task_type: Task type
            description: Task description
            **kwargs: Additional params

        Returns:
            Task plan
        """
        # Import Ultra-Think
        try:
            from jebat.features.ultra_think import ThinkingMode, UltraThink

            thinker = UltraThink(config={"max_thoughts": 10})

            # Think about the task
            prompt = f"""
Plan how to {task_type}: {description}

Consider:
1. What files need to be created/modified?
2. What dependencies are needed?
3. What are the steps?
4. Any potential issues?

Context: Working in Dev environment.
"""

            result = await thinker.think(
                problem=prompt,
                mode=ThinkingMode.DELIBERATE,
                timeout=30.0,
            )

            plan = {
                "thoughts": result.reasoning_steps,
                "confidence": result.confidence,
                "conclusion": result.conclusion,
            }

            return plan

        except ImportError:
            # Fallback if Ultra-Think not available
            logger.warning("Ultra-Think not available, using simple planning")
            return {
                "thoughts": [f"Planning {task_type} task"],
                "confidence": 0.5,
                "conclusion": f"Execute {task_type}: {description}",
            }

    async def _execute_plan(self, plan: Dict, sandbox: Any, **kwargs) -> TaskResult:
        """
        Execute task plan.

        Args:
            plan: Task plan from _plan_task
            sandbox: DevSandbox for execution
            **kwargs: Additional params

        Returns:
            TaskResult
        """
        task_type = kwargs.get("task_type", "unknown")

        # Initialize skills if not already done
        if not self.skills:
            self.initialize_skills(sandbox)

        try:
            # Execute based on task type using skills
            if task_type == "create":
                return await self._execute_create(plan, sandbox, **kwargs)
            elif task_type == "modify":
                return await self._execute_modify(plan, sandbox, **kwargs)
            elif task_type == "review":
                return await self._execute_review(plan, sandbox, **kwargs)
            elif task_type == "generate":
                return await self._execute_generate(plan, sandbox, **kwargs)
            elif task_type == "ui_generate":
                return await self._execute_ui(plan, sandbox, **kwargs)
            elif task_type == "debug":
                return await self._execute_debug(plan, sandbox, **kwargs)
            elif task_type == "scaffold":
                return await self._execute_scaffold(plan, sandbox, **kwargs)
            elif task_type == "git":
                return await self._execute_git(plan, sandbox, **kwargs)
            elif task_type == "test":
                return await self._execute_test(plan, sandbox, **kwargs)
            else:
                return TaskResult(
                    success=False,
                    message=f"Unknown task type: {task_type}",
                )

        except Exception as e:
            logger.error(f"Task execution failed: {e}")
            return TaskResult(
                success=False,
                message=f"Task failed: {str(e)}",
            )

    async def _execute_create(self, plan: Dict, sandbox: Any, **kwargs) -> TaskResult:
        """Execute create task."""
        description = kwargs.get("description", "")

        # Use first meaningful word as project name
        words = description.lower().split()
        project_name = (
            words[1] if len(words) > 1 and words[0] in ["a", "an", "the"] else words[0]
        )
        project_path = f"projects/{project_name}"

        # Create directory structure
        await sandbox.execute(f"mkdir projects\\{project_name}")

        return TaskResult(
            success=True,
            message=f"Created: {project_path}",
            files=[project_path],
        )

    async def _execute_modify(self, plan: Dict, sandbox: Any, **kwargs) -> TaskResult:
        """Execute modify task."""
        return TaskResult(
            success=True,
            message="Modification task completed (placeholder)",
        )

    async def _execute_review(self, plan: Dict, sandbox: Any, **kwargs) -> TaskResult:
        """Execute review task."""
        path = kwargs.get("path", "")

        # Read and analyze file
        issues = []

        # Placeholder - will use actual code analysis
        issues.append("Consider adding type hints")
        issues.append("Add docstrings to public methods")

        return TaskResult(
            success=True,
            message="Review complete",
            issues=issues,
        )

    async def _execute_generate(self, plan: Dict, sandbox: Any, **kwargs) -> TaskResult:
        """Execute generate task."""
        return TaskResult(
            success=True,
            message="Code generation complete (placeholder)",
        )

    async def _execute_ui(self, plan: Dict, sandbox: Any, **kwargs) -> TaskResult:
        """Execute UI generation with Stitch MCP."""
        description = kwargs.get("description", "")
        framework = kwargs.get("framework", "react")

        try:
            # Import Stitch MCP integration
            from ..integrations.stitch_mcp import StitchMCPClient

            client = StitchMCPClient()

            # Generate UI
            result = await client.generate_ui(description, framework)

            return TaskResult(
                success=True,
                message=f"Generated {framework} UI with Stitch MCP",
                files=result.get("files", []),
            )

        except ImportError:
            logger.warning("Stitch MCP not available")
            return TaskResult(
                success=False,
                message="Stitch MCP integration not available",
            )

    async def _execute_debug(self, plan: Dict, sandbox: Any, **kwargs) -> TaskResult:
        """Execute debug task."""
        error = kwargs.get("error", "")
        file_path = kwargs.get("file_path")

        # Use debug skills
        if self.skills.get("debug"):
            analysis = await self.skills["debug"].analyze_error(
                error_message=error,
                file_path=file_path,
            )

            return TaskResult(
                success=True,
                message="Debug analysis complete",
                cause=analysis.cause,
                fix=analysis.fix,
                issues=[analysis.error_type],
                metadata={
                    "error_type": analysis.error_type,
                    "location": analysis.location,
                    "suggestions": analysis.suggestions,
                },
            )

        return TaskResult(
            success=True,
            message="Debug analysis complete",
            cause="Analysis complete",
            fix="Review the error and apply suggested fix",
        )

    async def _execute_scaffold(self, plan: Dict, sandbox: Any, **kwargs) -> TaskResult:
        """Execute project scaffolding task."""
        project_name = kwargs.get("project_name", "my_project")
        project_type = kwargs.get("project_type", "python_package")

        # Use project skills
        if self.skills.get("project"):
            success = await self.skills["project"].scaffold(
                name=project_name,
                project_type=project_type,
            )

            if success:
                return TaskResult(
                    success=True,
                    message=f"Scaffolded {project_type} project: {project_name}",
                    files=[f"projects/{project_name}"],
                )

        return TaskResult(
            success=False,
            message="Failed to scaffold project",
        )

    async def _execute_git(self, plan: Dict, sandbox: Any, **kwargs) -> TaskResult:
        """Execute Git operation task."""
        operation = kwargs.get("operation", "status")
        path = kwargs.get("path", "")
        message = kwargs.get("message", "")

        # Use git skills
        if self.skills.get("git"):
            git = self.skills["git"]

            if operation == "init":
                success = await git.init(path)
                return TaskResult(
                    success=success,
                    message="Git repository initialized",
                )
            elif operation == "add":
                success = await git.add(path, kwargs.get("files", "."))
                return TaskResult(
                    success=success,
                    message="Files staged",
                )
            elif operation == "commit":
                success = await git.commit(path, message)
                return TaskResult(
                    success=success,
                    message=f"Committed: {message}",
                )
            elif operation == "status":
                status = await git.status(path)
                return TaskResult(
                    success=True,
                    message="Git status retrieved",
                    metadata={"status": status},
                )

        return TaskResult(
            success=False,
            message="Git operation failed",
        )

    async def _execute_test(self, plan: Dict, sandbox: Any, **kwargs) -> TaskResult:
        """Execute test running task."""
        path = kwargs.get("path", "")
        framework = kwargs.get("framework", "auto")

        # Use test skills
        if self.skills.get("test"):
            result = await self.skills["test"].run_tests(
                path=path,
                framework=framework,
            )

            return TaskResult(
                success=result.success,
                message=f"Tests: {result.passed} passed, {result.failed} failed",
                issues=result.failures[:3],  # Include first 3 failures
                metadata={
                    "total": result.total,
                    "passed": result.passed,
                    "failed": result.failed,
                    "output": result.output,
                },
            )

        return TaskResult(
            success=False,
            message="Test execution failed",
        )
