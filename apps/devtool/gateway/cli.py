"""
JEBAT DevAssistant CLI

Command-line interface for interacting with JEBAT DevAssistant.

Usage:
    jebat <command> [options]

Commands:
    create      Create new projects/components
    modify      Modify existing code
    review      Review code for issues
    generate    Generate code or UI
    debug       Debug issues
    ui          UI generation with Stitch MCP
    help        Show this help
"""

import argparse
import asyncio
import sys
from pathlib import Path
from typing import Optional

from ..brain.dev_brain import DevBrain
from ..security_console.cli import SecurityConsoleCLI
from ..sandbox.dev_sandbox import DevSandbox


class DevCLI:
    """
    Command-line interface for JEBAT DevAssistant.

    Provides natural language interface for development tasks.
    """

    def __init__(self):
        """Initialize CLI."""
        self.brain = DevBrain()
        self.sandbox = DevSandbox()

        # Initialize skills in brain
        self.brain.initialize_skills(self.sandbox)

        self.parser = self._create_parser()

    def _create_parser(self) -> argparse.ArgumentParser:
        """Create argument parser."""
        parser = argparse.ArgumentParser(
            prog="jebat",
            description="JEBAT DevAssistant - Your Personal Development AI",
        )

        subparsers = parser.add_subparsers(dest="command", help="Commands")

        # Create command
        create_parser = subparsers.add_parser(
            "create", help="Create new projects/components"
        )
        create_parser.add_argument(
            "description", help="What to create (e.g., 'a React chat app')"
        )

        # Modify command
        modify_parser = subparsers.add_parser("modify", help="Modify existing code")
        modify_parser.add_argument("description", help="What to modify")
        modify_parser.add_argument("--path", help="Specific file/path to modify")

        # Review command
        review_parser = subparsers.add_parser("review", help="Review code for issues")
        review_parser.add_argument("path", help="File or directory to review")

        # Generate command
        generate_parser = subparsers.add_parser("generate", help="Generate code")
        generate_parser.add_argument("description", help="What to generate")

        # UI command (Stitch MCP)
        ui_parser = subparsers.add_parser("ui", help="Generate UI with Stitch MCP")
        ui_parser.add_argument(
            "description", help="UI description (e.g., 'modern login form')"
        )
        ui_parser.add_argument(
            "--framework", default="react", choices=["react", "vue", "angular"]
        )

        # Debug command
        debug_parser = subparsers.add_parser("debug", help="Debug issues")
        debug_parser.add_argument("error", help="Error message or description")
        debug_parser.add_argument("--file", help="File where error occurred")

        # Scaffold command
        scaffold_parser = subparsers.add_parser(
            "scaffold", help="Scaffold a new project"
        )
        scaffold_parser.add_argument("name", help="Project name")
        scaffold_parser.add_argument(
            "--type",
            default="python_package",
            choices=["python_package", "react_app", "nodejs_app"],
            dest="project_type",
            help="Project type",
        )

        # Git command
        git_parser = subparsers.add_parser("git", help="Git operations")
        git_parser.add_argument(
            "operation",
            choices=["init", "add", "commit", "status", "log", "push", "pull"],
            help="Git operation",
        )
        git_parser.add_argument("--path", help="Repository path")
        git_parser.add_argument("-m", "--message", help="Commit message")
        git_parser.add_argument("--files", help="Files to add", default=".")

        # Test command
        test_parser = subparsers.add_parser("test", help="Run tests")
        test_parser.add_argument("--path", help="Test path", default=".")
        test_parser.add_argument(
            "--framework",
            default="auto",
            choices=["auto", "pytest", "jest", "unittest"],
            help="Test framework",
        )

        subparsers.add_parser(
            "security",
            help="Launch Serangan Console for local security and pentest workflows",
        )

        # Help command
        subparsers.add_parser("help", help="Show help")

        return parser

    async def execute(self, args: Optional[list] = None) -> int:
        """
        Execute CLI command.

        Args:
            args: Command line arguments (defaults to sys.argv[1:])

        Returns:
            Exit code
        """
        parsed = self.parser.parse_args(args)

        if not parsed.command:
            self.parser.print_help()
            return 0

        try:
            if parsed.command == "create":
                await self.cmd_create(parsed.description)
            elif parsed.command == "modify":
                await self.cmd_modify(parsed.description, parsed.path)
            elif parsed.command == "review":
                await self.cmd_review(parsed.path)
            elif parsed.command == "generate":
                await self.cmd_generate(parsed.description)
            elif parsed.command == "ui":
                await self.cmd_ui(parsed.description, parsed.framework)
            elif parsed.command == "debug":
                await self.cmd_debug(parsed.error, parsed.file)
            elif parsed.command == "scaffold":
                await self.cmd_scaffold(parsed.name, parsed.project_type)
            elif parsed.command == "git":
                await self.cmd_git(
                    parsed.operation,
                    parsed.path,
                    parsed.message,
                    parsed.files,
                )
            elif parsed.command == "test":
                await self.cmd_test(parsed.path, parsed.framework)
            elif parsed.command == "security":
                return await self.cmd_security()
            elif parsed.command == "help":
                self.parser.print_help()
            else:
                self.parser.print_help()
                return 1

            return 0

        except Exception as e:
            print(f"[ERROR] {e}")
            return 1

    async def cmd_create(self, description: str):
        """Handle create command."""
        print(f"[JEBAT] Creating: {description}")
        result = await self.brain.execute_task(
            task_type="create",
            description=description,
            sandbox=self.sandbox,
        )
        print(f"[OK] {result.message}")

    async def cmd_modify(self, description: str, path: Optional[str] = None):
        """Handle modify command."""
        print(f"[JEBAT] Modifying: {description}")
        if path:
            print(f"   Target: {path}")
        result = await self.brain.execute_task(
            task_type="modify",
            description=description,
            path=path,
            sandbox=self.sandbox,
        )
        print(f"[OK] {result.message}")

    async def cmd_review(self, path: str):
        """Handle review command."""
        print(f"[JEBAT] Reviewing: {path}")
        result = await self.brain.execute_task(
            task_type="review",
            path=path,
            sandbox=self.sandbox,
        )
        print(f"📋 Review complete:")
        for issue in result.issues:
            print(f"  - {issue}")

    async def cmd_generate(self, description: str):
        """Handle generate command."""
        print(f"[JEBAT] Generating: {description}")
        result = await self.brain.execute_task(
            task_type="generate",
            description=description,
            sandbox=self.sandbox,
        )
        print(f"✅ {result.message}")

    async def cmd_ui(self, description: str, framework: str):
        """Handle UI command with Stitch MCP."""
        print(f"[JEBAT] Generating UI with Stitch MCP: {description}")
        print(f"   Framework: {framework}")
        result = await self.brain.execute_task(
            task_type="ui_generate",
            description=description,
            framework=framework,
            sandbox=self.sandbox,
        )
        print(f"[OK] {result.message}")
        if result.files:
            print(f"   Files created:")
            for f in result.files:
                print(f"     - {f}")

    async def cmd_debug(self, error: str, file_path: Optional[str] = None):
        """Handle debug command."""
        print(f"[JEBAT] Debugging: {error}")
        result = await self.brain.execute_task(
            task_type="debug",
            error=error,
            file_path=file_path,
            sandbox=self.sandbox,
        )
        print(f"🔍 Analysis:")
        print(f"  Type: {result.issues[0] if result.issues else 'Unknown'}")
        print(f"  Cause: {result.cause}")
        print(f"  Fix: {result.fix}")

    async def cmd_scaffold(self, name: str, project_type: str):
        """Handle scaffold command."""
        print(f"[JEBAT] Scaffolding {project_type} project: {name}")
        result = await self.brain.execute_task(
            task_type="scaffold",
            project_name=name,
            project_type=project_type,
            sandbox=self.sandbox,
        )
        if result.success:
            print(f"✅ {result.message}")
            print(f"   Location: {result.files[0]}")
        else:
            print(f"❌ {result.message}")

    async def cmd_git(
        self,
        operation: str,
        path: Optional[str],
        message: Optional[str],
        files: str,
    ):
        """Handle git command."""
        if not path:
            path = "."

        print(f"[JEBAT] Git {operation}...")
        result = await self.brain.execute_task(
            task_type="git",
            operation=operation,
            path=path,
            message=message,
            files=files,
            sandbox=self.sandbox,
        )
        print(f"✅ {result.message}")
        if result.metadata.get("status"):
            print(f"\n{result.metadata['status']}")

    async def cmd_test(self, path: str, framework: str):
        """Handle test command."""
        print(f"[JEBAT] Running tests (framework={framework})...")
        result = await self.brain.execute_task(
            task_type="test",
            path=path,
            framework=framework,
            sandbox=self.sandbox,
        )
        print(f"📊 Test Results:")
        print(f"  {result.message}")
        if result.issues:
            print(f"\n  Failures:")
            for issue in result.issues:
                print(f"    - {issue[:100]}...")
        if result.metadata.get("output"):
            print(f"\n  Output:\n{result.metadata['output'][:500]}")

    async def cmd_security(self) -> int:
        """Launch the security console."""
        console = SecurityConsoleCLI()
        return await console.run()


def main():
    """Main entry point."""
    cli = DevCLI()
    exit_code = asyncio.run(cli.execute())
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
