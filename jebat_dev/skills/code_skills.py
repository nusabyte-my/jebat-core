"""
JEBAT DevAssistant - Code Skills

Code reading, writing, review, and generation capabilities.
"""

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class CodeReviewResult:
    """Result of code review."""

    issues: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    strengths: List[str] = field(default_factory=list)
    overall_score: float = 0.0


class CodeSkills:
    """
    Code manipulation skills for DevAssistant.

    Provides capabilities for reading, writing, reviewing, and generating code.
    """

    def __init__(self, sandbox):
        """
        Initialize code skills.

        Args:
            sandbox: DevSandbox for file operations
        """
        self.sandbox = sandbox
        logger.info("CodeSkills initialized")

    async def read_file(self, path: str) -> Optional[str]:
        """
        Read a code file.

        Args:
            path: File path

        Returns:
            File content or None
        """
        logger.info(f"Reading file: {path}")
        return await self.sandbox.read_file(path)

    async def write_file(self, path: str, content: str) -> bool:
        """
        Write a code file.

        Args:
            path: File path
            content: File content

        Returns:
            True if successful
        """
        logger.info(f"Writing file: {path}")
        return await self.sandbox.write_file(path, content)

    async def read_multiple_files(self, paths: List[str]) -> Dict[str, str]:
        """
        Read multiple files.

        Args:
            paths: List of file paths

        Returns:
            Dict mapping path to content
        """
        results = {}
        for path in paths:
            content = await self.read_file(path)
            if content:
                results[path] = content
        return results

    async def review_code(
        self,
        path: str,
        language: Optional[str] = None,
    ) -> CodeReviewResult:
        """
        Review code for issues and best practices.

        Args:
            path: File path to review
            language: Programming language (auto-detected if None)

        Returns:
            CodeReviewResult
        """
        logger.info(f"Reviewing code: {path}")

        content = await self.read_file(path)
        if not content:
            return CodeReviewResult(
                issues=["File not found or not readable"],
            )

        # Auto-detect language from extension
        if not language:
            ext = Path(path).suffix.lower()
            language_map = {
                ".py": "python",
                ".js": "javascript",
                ".ts": "typescript",
                ".jsx": "javascript",
                ".tsx": "typescript",
                ".java": "java",
                ".cpp": "cpp",
                ".c": "c",
                ".go": "go",
                ".rs": "rust",
            }
            language = language_map.get(ext, "unknown")

        # Analyze code based on language
        issues = []
        suggestions = []
        strengths = []

        if language == "python":
            issues, suggestions, strengths = self._review_python(content)
        elif language in ["javascript", "typescript"]:
            issues, suggestions, strengths = self._review_js_ts(content)
        else:
            suggestions.append(f"Add language-specific review rules for {language}")

        return CodeReviewResult(
            issues=issues,
            suggestions=suggestions,
            strengths=strengths,
            overall_score=self._calculate_score(issues, suggestions, strengths),
        )

    def _review_python(self, content: str) -> tuple:
        """Review Python code."""
        issues = []
        suggestions = []
        strengths = []

        lines = content.split("\n")

        # Check for docstrings
        if '"""' not in content and "'''" not in content:
            suggestions.append("Add docstrings to document code")

        # Check for type hints
        if "->" not in content and ": " not in content:
            suggestions.append("Consider adding type hints for better code clarity")

        # Check line length
        long_lines = [i for i, line in enumerate(lines) if len(line) > 100]
        if long_lines:
            issues.append(f"{len(long_lines)} lines exceed 100 characters")

        # Check for imports
        if "import" not in content and "from" not in content:
            strengths.append("No external dependencies")

        # Check for error handling
        if "try" not in content or "except" not in content:
            suggestions.append("Add error handling for robustness")

        # Check for TODO comments
        todo_count = content.lower().count("todo")
        if todo_count > 0:
            suggestions.append(f"{todo_count} TODO(s) found - consider addressing them")

        return issues, suggestions, strengths

    def _review_js_ts(self, content: str) -> tuple:
        """Review JavaScript/TypeScript code."""
        issues = []
        suggestions = []
        strengths = []

        lines = content.split("\n")

        # Check for JSDoc comments
        if "/**" not in content:
            suggestions.append("Add JSDoc comments for better documentation")

        # Check for console.log
        if "console.log" in content:
            suggestions.append("Remove console.log statements in production code")

        # Check line length
        long_lines = [i for i, line in enumerate(lines) if len(line) > 100]
        if long_lines:
            issues.append(f"{len(long_lines)} lines exceed 100 characters")

        # Check for TypeScript types
        if content.endswith(".ts") or content.endswith(".tsx"):
            if ": any" in content:
                suggestions.append("Avoid using 'any' type - use specific types")
        else:
            suggestions.append("Consider migrating to TypeScript for type safety")

        # Check for error handling
        if ".catch" not in content and "try" not in content:
            suggestions.append("Add error handling for promises/async operations")

        return issues, suggestions, strengths

    def _calculate_score(
        self,
        issues: List[str],
        suggestions: List[str],
        strengths: List[str],
    ) -> float:
        """Calculate overall code quality score."""
        # Simple scoring algorithm
        base_score = 100.0

        # Deduct for issues
        base_score -= len(issues) * 10

        # Deduct for suggestions (less severe)
        base_score -= len(suggestions) * 5

        # Add for strengths
        base_score += len(strengths) * 5

        # Clamp to 0-100
        return max(0.0, min(100.0, base_score))

    async def generate_code(
        self,
        description: str,
        language: str = "python",
        path: Optional[str] = None,
    ) -> Optional[str]:
        """
        Generate code from description.

        Args:
            description: Code description
            language: Target language
            path: Optional path to write the code

        Returns:
            Generated code or None
        """
        logger.info(f"Generating {language} code: {description}")

        # Use Ultra-Think for code generation
        try:
            from jebat.features.ultra_think import ThinkingMode, UltraThink

            thinker = UltraThink(config={"max_thoughts": 15})

            prompt = f"""
Generate {language} code for: {description}

Requirements:
- Follow best practices for {language}
- Include comments and documentation
- Add error handling
- Make it production-ready

Provide only the code without explanations.
"""

            result = await thinker.think(
                problem=prompt,
                mode=ThinkingMode.CREATIVE,
                timeout=45.0,
            )

            code = result.conclusion

            # Write to file if path provided
            if path and code:
                await self.write_file(path, code)
                logger.info(f"Code written to: {path}")

            return code

        except ImportError:
            logger.warning("Ultra-Think not available for code generation")
            return None

        except Exception as e:
            logger.error(f"Code generation failed: {e}")
            return None
