"""
JEBAT DevAssistant - Project Skills

Project scaffolding and structure management.
"""

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class ProjectStructure:
    """Project structure definition."""

    name: str
    type: str  # python, react, nodejs, etc.
    directories: List[str] = field(default_factory=list)
    files: Dict[str, str] = field(default_factory=dict)


class ProjectSkills:
    """
    Project scaffolding skills for DevAssistant.

    Creates project structures and manages project-level operations.
    """

    def __init__(self, sandbox):
        """
        Initialize project skills.

        Args:
            sandbox: DevSandbox for file operations
        """
        self.sandbox = sandbox
        self.templates = self._load_templates()
        logger.info("ProjectSkills initialized")

    def _load_templates(self) -> Dict[str, ProjectStructure]:
        """Load project templates."""
        return {
            "python_package": ProjectStructure(
                name="Python Package",
                type="python",
                directories=[
                    "{name}",
                    "{name}/{name}",
                    "{name}/tests",
                    "{name}/docs",
                ],
                files={
                    "{name}/setup.py": self._get_python_setup(),
                    "{name}/README.md": self._get_readme_template(),
                    "{name}/{name}/__init__.py": '__version__ = "0.1.0"\n',
                    "{name}/.gitignore": self._get_python_gitignore(),
                },
            ),
            "react_app": ProjectStructure(
                name="React Application",
                type="react",
                directories=[
                    "{name}",
                    "{name}/public",
                    "{name}/src",
                    "{name}/src/components",
                    "{name}/src/hooks",
                    "{name}/src/utils",
                ],
                files={
                    "{name}/package.json": self._get_react_package(),
                    "{name}/README.md": self._get_readme_template(),
                    "{name}/.gitignore": self._get_node_gitignore(),
                },
            ),
            "nodejs_app": ProjectStructure(
                name="Node.js Application",
                type="nodejs",
                directories=[
                    "{name}",
                    "{name}/src",
                    "{name}/tests",
                ],
                files={
                    "{name}/package.json": self._get_node_package(),
                    "{name}/README.md": self._get_readme_template(),
                    "{name}/.gitignore": self._get_node_gitignore(),
                },
            ),
        }

    async def scaffold(
        self,
        name: str,
        project_type: str = "python_package",
        base_path: str = "projects",
    ) -> bool:
        """
        Scaffold a new project.

        Args:
            name: Project name
            project_type: Type of project (python_package, react_app, nodejs_app)
            base_path: Base directory for projects

        Returns:
            True if successful
        """
        logger.info(f"Scaffolding {project_type} project: {name}")

        template = self.templates.get(project_type)
        if not template:
            logger.error(f"Unknown project type: {project_type}")
            return False

        # Create directories
        for dir_template in template.directories:
            dir_name = dir_template.format(name=name)
            full_path = f"{base_path}/{dir_name}"
            await self.sandbox.execute(f"mkdir {full_path}")
            logger.info(f"Created directory: {full_path}")

        # Create files
        for file_template, content in template.files.items():
            file_name = file_template.format(name=name)
            full_path = f"{base_path}/{file_name}"

            # Replace placeholders in content
            content = content.replace("{name}", name)

            await self.sandbox.write_file(full_path, content)
            logger.info(f"Created file: {full_path}")

        return True

    def _get_python_setup(self) -> str:
        """Get Python setup.py template."""
        return """from setuptools import setup, find_packages

setup(
    name="{name}",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[],
    python_requires=">=3.8",
)
"""

    def _get_react_package(self) -> str:
        """Get React package.json template."""
        return """{
  "name": "{name}",
  "version": "0.1.0",
  "private": true,
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-scripts": "5.0.1"
  },
  "scripts": {
    "start": "react-scripts start",
    "build": "react-scripts build",
    "test": "react-scripts test",
    "eject": "react-scripts eject"
  },
  "browserslist": {
    "production": [
      ">0.2%",
      "not dead",
      "not op_mini all"
    ],
    "development": [
      "last 1 chrome version",
      "last 1 firefox version",
      "last 1 safari version"
    ]
  }
}
"""

    def _get_node_package(self) -> str:
        """Get Node.js package.json template."""
        return """{
  "name": "{name}",
  "version": "0.1.0",
  "description": "",
  "main": "src/index.js",
  "scripts": {
    "start": "node src/index.js",
    "test": "jest",
    "dev": "nodemon src/index.js"
  },
  "keywords": [],
  "author": "",
  "license": "ISC",
  "devDependencies": {
    "jest": "^29.0.0",
    "nodemon": "^3.0.0"
  }
}
"""

    def _get_readme_template(self) -> str:
        """Get README.md template."""
        return """# {name}

## Description
TODO: Add description

## Installation
TODO: Add installation instructions

## Usage
TODO: Add usage instructions

## License
MIT
"""

    def _get_python_gitignore(self) -> str:
        """Get Python .gitignore template."""
        return """__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
ENV/
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg
.pytest_cache/
.coverage
htmlcov/
*.manifest
*.spec
"""

    def _get_node_gitignore(self) -> str:
        """Get Node.js .gitignore template."""
        return """node_modules/
dist/
.env
npm-debug.log*
yarn-debug.log*
yarn-error.log*
.DS_Store
"""

    async def add_file(
        self,
        project_path: str,
        filename: str,
        content: str,
    ) -> bool:
        """
        Add a file to an existing project.

        Args:
            project_path: Path to project
            filename: File name
            content: File content

        Returns:
            True if successful
        """
        full_path = f"{project_path}/{filename}"
        return await self.sandbox.write_file(full_path, content)

    async def add_directory(
        self,
        project_path: str,
        dirname: str,
    ) -> bool:
        """
        Add a directory to an existing project.

        Args:
            project_path: Path to project
            dirname: Directory name

        Returns:
            True if successful
        """
        full_path = f"{project_path}/{dirname}"
        result = await self.sandbox.execute(f"mkdir {full_path}")
        return result.success
