"""
JEBAT DevAssistant - Git Skills

Git operations for version control.
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


class GitSkills:
    """
    Git operations skills for DevAssistant.

    Provides capabilities for common Git operations.
    """

    def __init__(self, sandbox):
        """
        Initialize Git skills.

        Args:
            sandbox: DevSandbox for command execution
        """
        self.sandbox = sandbox
        logger.info("GitSkills initialized")

    async def init(self, path: str) -> bool:
        """
        Initialize a Git repository.

        Args:
            path: Directory path

        Returns:
            True if successful
        """
        logger.info(f"Initializing Git repo: {path}")
        result = await self.sandbox.execute(f"git init", cwd=path)
        return result.success

    async def add(self, path: str, files: str = ".") -> bool:
        """
        Add files to staging.

        Args:
            path: Repository path
            files: Files to add (default: all)

        Returns:
            True if successful
        """
        logger.info(f"Adding files: {files}")
        result = await self.sandbox.execute(f"git add {files}", cwd=path)
        return result.success

    async def commit(self, path: str, message: str) -> bool:
        """
        Commit staged changes.

        Args:
            path: Repository path
            message: Commit message

        Returns:
            True if successful
        """
        logger.info(f"Committing: {message}")
        result = await self.sandbox.execute(f'git commit -m "{message}"', cwd=path)
        return result.success

    async def status(self, path: str) -> Optional[str]:
        """
        Get Git status.

        Args:
            path: Repository path

        Returns:
            Status output or None
        """
        result = await self.sandbox.execute("git status --short", cwd=path)
        if result.success:
            return result.output
        return None

    async def log(self, path: str, limit: int = 5) -> Optional[str]:
        """
        Get Git log.

        Args:
            path: Repository path
            limit: Number of commits to show

        Returns:
            Log output or None
        """
        result = await self.sandbox.execute(f"git log -{limit} --oneline", cwd=path)
        if result.success:
            return result.output
        return None

    async def branch(self, path: str, name: str, create: bool = False) -> bool:
        """
        Create or switch to branch.

        Args:
            path: Repository path
            name: Branch name
            create: If True, create new branch

        Returns:
            True if successful
        """
        if create:
            logger.info(f"Creating branch: {name}")
            result = await self.sandbox.execute(f"git checkout -b {name}", cwd=path)
        else:
            logger.info(f"Switching to branch: {name}")
            result = await self.sandbox.execute(f"git checkout {name}", cwd=path)
        return result.success

    async def push(
        self, path: str, remote: str = "origin", branch: str = "main"
    ) -> bool:
        """
        Push changes to remote.

        Args:
            path: Repository path
            remote: Remote name
            branch: Branch name

        Returns:
            True if successful
        """
        logger.info(f"Pushing to {remote}/{branch}")
        result = await self.sandbox.execute(f"git push {remote} {branch}", cwd=path)
        return result.success

    async def pull(
        self, path: str, remote: str = "origin", branch: str = "main"
    ) -> bool:
        """
        Pull changes from remote.

        Args:
            path: Repository path
            remote: Remote name
            branch: Branch name

        Returns:
            True if successful
        """
        logger.info(f"Pulling from {remote}/{branch}")
        result = await self.sandbox.execute(f"git pull {remote} {branch}", cwd=path)
        return result.success

    async def clone(self, url: str, path: str) -> bool:
        """
        Clone a repository.

        Args:
            url: Repository URL
            path: Destination path

        Returns:
            True if successful
        """
        logger.info(f"Cloning: {url} -> {path}")
        result = await self.sandbox.execute(f"git clone {url} {path}")
        return result.success

    async def diff(self, path: str) -> Optional[str]:
        """
        Get diff of unstaged changes.

        Args:
            path: Repository path

        Returns:
            Diff output or None
        """
        result = await self.sandbox.execute("git diff", cwd=path)
        if result.success:
            return result.output
        return None
