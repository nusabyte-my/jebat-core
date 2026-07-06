"""
🗡️ JEBAT MCP Server

Model Context Protocol Server for JEBAT.

Provides AI capabilities to IDEs via MCP:
- Code reading/writing
- Code generation
- Code review
- Project scaffolding
- Git operations
- Test running
- Debug analysis

Usage:
    python -m jebat.mcp.server
    python -m jebat.mcp.server --port 8787
"""

import asyncio
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# MCP Protocol imports
try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import (
        Resource,
        ResourceTemplate,
        TextContent,
        Tool,
    )

    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    print("MCP library not installed. Install with: pip install mcp")

from jebat_dev.brain import DevBrain
from jebat_dev.sandbox import DevSandbox

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("jebat.mcp.server")


class JEBATMCPServer:
    """
    JEBAT MCP Server Implementation.

    Exposes JEBAT capabilities via Model Context Protocol.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize JEBAT MCP Server.

        Args:
            config: Server configuration
        """
        self.config = config or {}
        self.brain = DevBrain()
        self.sandbox = DevSandbox()
        self.brain.initialize_skills(self.sandbox)

        # MCP Server instance
        if MCP_AVAILABLE:
            self.server = Server("jebat")
            self._register_tools()
            self._register_resources()
        else:
            self.server = None

        logger.info("JEBAT MCP Server initialized")

    def _register_tools(self):
        """Register MCP tools."""

        @self.server.list_tools()
        async def list_tools() -> List[Tool]:
            """List available JEBAT tools."""
            return [
                Tool(
                    name="code.read",
                    description="Read and analyze code files",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "path": {
                                "type": "string",
                                "description": "File path to read",
                            },
                        },
                        "required": ["path"],
                    },
                ),
                Tool(
                    name="code.write",
                    description="Create or modify code files",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "path": {
                                "type": "string",
                                "description": "File path to write",
                            },
                            "content": {
                                "type": "string",
                                "description": "File content",
                            },
                        },
                        "required": ["path", "content"],
                    },
                ),
                Tool(
                    name="code.generate",
                    description="Generate code from description",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "description": {
                                "type": "string",
                                "description": "What to generate",
                            },
                            "language": {
                                "type": "string",
                                "description": "Programming language",
                            },
                            "path": {
                                "type": "string",
                                "description": "Optional file path",
                            },
                        },
                        "required": ["description"],
                    },
                ),
                Tool(
                    name="code.review",
                    description="Review code for issues and best practices",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "path": {
                                "type": "string",
                                "description": "File path to review",
                            },
                        },
                        "required": ["path"],
                    },
                ),
                Tool(
                    name="project.scaffold",
                    description="Create a new project from template",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "name": {
                                "type": "string",
                                "description": "Project name",
                            },
                            "type": {
                                "type": "string",
                                "description": "Project type (python_package, react_app, nodejs_app)",
                                "enum": ["python_package", "react_app", "nodejs_app"],
                            },
                        },
                        "required": ["name", "type"],
                    },
                ),
                Tool(
                    name="git.operation",
                    description="Perform Git operations",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "operation": {
                                "type": "string",
                                "description": "Git operation (init, add, commit, status, log)",
                                "enum": ["init", "add", "commit", "status", "log"],
                            },
                            "path": {
                                "type": "string",
                                "description": "Repository path",
                            },
                            "message": {
                                "type": "string",
                                "description": "Commit message (for commit operation)",
                            },
                        },
                        "required": ["operation", "path"],
                    },
                ),
                Tool(
                    name="test.run",
                    description="Run tests in a project",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "path": {
                                "type": "string",
                                "description": "Test path",
                            },
                            "framework": {
                                "type": "string",
                                "description": "Test framework (auto, pytest, jest, unittest)",
                                "enum": ["auto", "pytest", "jest", "unittest"],
                            },
                        },
                        "required": ["path"],
                    },
                ),
                Tool(
                    name="debug.analyze",
                    description="Analyze errors and debug issues",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "error": {
                                "type": "string",
                                "description": "Error message to analyze",
                            },
                            "file_path": {
                                "type": "string",
                                "description": "File where error occurred",
                            },
                        },
                        "required": ["error"],
                    },
                ),
            ]

        @self.server.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
            """Execute a tool."""
            try:
                result = await self._execute_tool(name, arguments)
                return [TextContent(type="text", text=json.dumps(result, indent=2))]
            except Exception as e:
                logger.error(f"Tool execution failed: {e}")
                return [TextContent(type="text", text=f"Error: {str(e)}")]

    async def _execute_tool(
        self,
        name: str,
        arguments: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Execute a specific tool."""

        if name == "code.read":
            content = await self.sandbox.read_file(arguments["path"])
            return {
                "success": content is not None,
                "content": content or "File not found",
            }

        elif name == "code.write":
            success = await self.sandbox.write_file(
                arguments["path"],
                arguments["content"],
            )
            return {"success": success, "path": arguments["path"]}

        elif name == "code.generate":
            if self.brain.skills.get("code"):
                code = await self.brain.skills["code"].generate_code(
                    description=arguments.get("description", ""),
                    language=arguments.get("language", "python"),
                    path=arguments.get("path"),
                )
                return {"success": code is not None, "code": code or ""}
            return {"success": False, "error": "Code skills not available"}

        elif name == "code.review":
            if self.brain.skills.get("code"):
                result = await self.brain.skills["code"].review_code(arguments["path"])
                return {
                    "success": True,
                    "issues": result.issues,
                    "suggestions": result.suggestions,
                    "score": result.overall_score,
                }
            return {"success": False, "error": "Code skills not available"}

        elif name == "project.scaffold":
            if self.brain.skills.get("project"):
                success = await self.brain.skills["project"].scaffold(
                    name=arguments["name"],
                    project_type=arguments["type"],
                )
                return {"success": success, "project": arguments["name"]}
            return {"success": False, "error": "Project skills not available"}

        elif name == "git.operation":
            if self.brain.skills.get("git"):
                git = self.brain.skills["git"]
                op = arguments["operation"]
                path = arguments["path"]

                if op == "init":
                    success = await git.init(path)
                elif op == "status":
                    status = await git.status(path)
                    return {"success": True, "status": status}
                elif op == "commit":
                    success = await git.commit(path, arguments.get("message", ""))
                else:
                    return {"success": False, "error": f"Unknown operation: {op}"}

                return {"success": success}

            return {"success": False, "error": "Git skills not available"}

        elif name == "test.run":
            if self.brain.skills.get("test"):
                result = await self.brain.skills["test"].run_tests(
                    path=arguments["path"],
                    framework=arguments.get("framework", "auto"),
                )
                return {
                    "success": result.success,
                    "total": result.total,
                    "passed": result.passed,
                    "failed": result.failed,
                    "output": result.output[:1000] if result.output else "",
                }
            return {"success": False, "error": "Test skills not available"}

        elif name == "debug.analyze":
            if self.brain.skills.get("debug"):
                analysis = await self.brain.skills["debug"].analyze_error(
                    error_message=arguments["error"],
                    file_path=arguments.get("file_path"),
                )
                return {
                    "success": True,
                    "error_type": analysis.error_type,
                    "cause": analysis.cause,
                    "fix": analysis.fix,
                    "suggestions": analysis.suggestions,
                }
            return {"success": False, "error": "Debug skills not available"}

        else:
            return {"success": False, "error": f"Unknown tool: {name}"}

    def _register_resources(self):
        """Register MCP resources."""

        @self.server.list_resources()
        async def list_resources() -> List[Resource]:
            """List available resources."""
            return [
                Resource(
                    uri="jebat://status",
                    name="JEBAT Status",
                    description="Current JEBAT server status",
                    mimeType="application/json",
                ),
                Resource(
                    uri="jebat://capabilities",
                    name="JEBAT Capabilities",
                    description="Available JEBAT capabilities",
                    mimeType="application/json",
                ),
            ]

        @self.server.read_resource()
        async def read_resource(uri: str) -> str:
            """Read a resource."""
            if uri == "jebat://status":
                return json.dumps(
                    {
                        "status": "online",
                        "timestamp": datetime.now().isoformat(),
                        "version": "2.0.0",
                    },
                    indent=2,
                )

            elif uri == "jebat://capabilities":
                return json.dumps(
                    {
                        "tools": [
                            "code.read",
                            "code.write",
                            "code.generate",
                            "code.review",
                            "project.scaffold",
                            "git.operation",
                            "test.run",
                            "debug.analyze",
                        ],
                        "resources": [
                            "jebat://status",
                            "jebat://capabilities",
                        ],
                    },
                    indent=2,
                )

            else:
                raise ValueError(f"Unknown resource: {uri}")

    async def run_stdio(self):
        """Run server using stdio transport."""
        if not self.server:
            print("MCP library not available")
            return

        logger.info("Starting JEBAT MCP Server (stdio)")

        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                self.server.create_initialization_options(),
            )

    async def run_http(self, host: str = "localhost", port: int = 8787):
        """Run server using HTTP transport."""
        logger.info(f"Starting JEBAT MCP Server (http://{host}:{port})")

        # HTTP server implementation would go here
        # For now, use stdio
        await self.run_stdio()


async def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="JEBAT MCP Server")
    parser.add_argument(
        "--port",
        type=int,
        default=8787,
        help="Server port (for HTTP mode)",
    )
    parser.add_argument(
        "--mode",
        choices=["stdio", "http"],
        default="stdio",
        help="Server mode",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging",
    )

    args = parser.parse_args()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    server = JEBATMCPServer()

    if args.mode == "stdio":
        await server.run_stdio()
    else:
        await server.run_http(port=args.port)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
