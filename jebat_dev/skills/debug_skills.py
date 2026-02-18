"""
JEBAT DevAssistant - Debug Skills

Error analysis and debugging capabilities.
"""

import logging
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class DebugAnalysis:
    """Result of debug analysis."""

    error_type: str = ""
    error_message: str = ""
    location: str = ""
    cause: str = ""
    fix: str = ""
    suggestions: List[str] = field(default_factory=list)
    related_files: List[str] = field(default_factory=list)


class DebugSkills:
    """
    Debug analysis skills for DevAssistant.

    Provides capabilities for analyzing errors and suggesting fixes.
    """

    def __init__(self, sandbox):
        """
        Initialize debug skills.

        Args:
            sandbox: DevSandbox for file operations
        """
        self.sandbox = sandbox
        self.error_patterns = self._load_error_patterns()
        logger.info("DebugSkills initialized")

    def _load_error_patterns(self) -> Dict[str, Dict]:
        """Load common error patterns."""
        return {
            "python_syntax": {
                "pattern": r"SyntaxError: (.+)",
                "type": "Syntax Error",
                "common_causes": [
                    "Missing colon",
                    "Incorrect indentation",
                    "Unclosed brackets",
                    "Invalid syntax",
                ],
            },
            "python_import": {
                "pattern": r"ModuleNotFoundError: No module named '(.+)'",
                "type": "Import Error",
                "common_causes": [
                    "Module not installed",
                    "Incorrect module name",
                    "Missing __init__.py",
                ],
            },
            "python_attribute": {
                "pattern": r"AttributeError: '(.+)' object has no attribute '(.+)'",
                "type": "Attribute Error",
                "common_causes": [
                    "Typo in attribute name",
                    "Object doesn't have this method/property",
                    "Wrong object type",
                ],
            },
            "python_type": {
                "pattern": r"TypeError: (.+)",
                "type": "Type Error",
                "common_causes": [
                    "Wrong argument type",
                    "NoneType has no attribute",
                    "Unsupported operation",
                ],
            },
            "python_key": {
                "pattern": r"KeyError: '(.+)'",
                "type": "Key Error",
                "common_causes": [
                    "Dictionary key doesn't exist",
                    "Typo in key name",
                    "Case sensitivity",
                ],
            },
            "js_syntax": {
                "pattern": r"SyntaxError: (.+)",
                "type": "JavaScript Syntax Error",
                "common_causes": [
                    "Missing semicolon",
                    "Unclosed bracket",
                    "Invalid token",
                ],
            },
            "js_reference": {
                "pattern": r"ReferenceError: (.+) is not defined",
                "type": "Reference Error",
                "common_causes": [
                    "Variable not declared",
                    "Scope issue",
                    "Typo in variable name",
                ],
            },
            "js_type": {
                "pattern": r"TypeError: Cannot read propert(?:y|ies) '(.+)' of (null|undefined)",
                "type": "Type Error",
                "common_causes": [
                    "Accessing property of null/undefined",
                    "Object not initialized",
                    "Async timing issue",
                ],
            },
        }

    async def analyze_error(
        self,
        error_message: str,
        context: Optional[str] = None,
        file_path: Optional[str] = None,
    ) -> DebugAnalysis:
        """
        Analyze an error message.

        Args:
            error_message: Error message to analyze
            context: Optional context (code snippet, stack trace)
            file_path: Optional file path where error occurred

        Returns:
            DebugAnalysis
        """
        logger.info(f"Analyzing error: {error_message[:100]}...")

        analysis = DebugAnalysis(
            error_message=error_message,
        )

        # Match error pattern
        matched = False
        for pattern_name, pattern_info in self.error_patterns.items():
            match = re.search(pattern_info["pattern"], error_message)
            if match:
                matched = True
                analysis.error_type = pattern_info["type"]
                analysis.location = match.group(1) if match.groups() else ""

                if len(match.groups()) > 1:
                    analysis.location = f"{match.group(1)}.{match.group(2)}"

                # Determine cause
                analysis.cause = self._determine_cause(
                    pattern_name, error_message, context
                )

                # Suggest fix
                analysis.fix = self._suggest_fix(
                    pattern_name, analysis.cause, file_path
                )

                # Add suggestions
                analysis.suggestions = pattern_info["common_causes"]

                break

        if not matched:
            analysis.error_type = "Unknown Error"
            analysis.cause = "Unable to match error pattern"
            analysis.fix = "Please provide more context"

        # Analyze file if provided
        if file_path:
            analysis.related_files = await self._find_related_files(file_path)

        return analysis

    def _determine_cause(
        self,
        pattern_name: str,
        error_message: str,
        context: Optional[str],
    ) -> str:
        """Determine the likely cause of the error."""
        if pattern_name == "python_import":
            module = error_message.split("'")[1] if "'" in error_message else "unknown"
            return f"Module '{module}' is not installed or not found"

        elif pattern_name == "python_attribute":
            return "Attempting to access a non-existent attribute or method"

        elif pattern_name == "python_type":
            if "NoneType" in error_message:
                return "Trying to use None as if it were a valid object"
            return "Operation received an argument of incorrect type"

        elif pattern_name == "python_key":
            key = error_message.split("'")[1] if "'" in error_message else "unknown"
            return f"Dictionary key '{key}' does not exist"

        elif pattern_name == "js_reference":
            return "Variable or function is being accessed before it's defined"

        elif pattern_name == "js_type":
            return "Attempting to access a property of null or undefined"

        return "Unknown cause - more context needed"

    def _suggest_fix(
        self,
        pattern_name: str,
        cause: str,
        file_path: Optional[str],
    ) -> str:
        """Suggest a fix for the error."""
        if pattern_name == "python_import":
            module = cause.split("'")[1] if "'" in cause else "module"
            return f"Install the module: pip install {module}"

        elif pattern_name == "python_attribute":
            return "Check the object type and verify the attribute/method name"

        elif pattern_name == "python_type":
            if "NoneType" in cause:
                return "Add null check before using the object"
            return "Verify the types of arguments being passed"

        elif pattern_name == "python_key":
            return "Use .get() method or check if key exists before accessing"

        elif pattern_name == "python_syntax":
            return "Review the syntax at the indicated line"

        elif pattern_name == "js_reference":
            return "Ensure the variable is declared before use"

        elif pattern_name == "js_type":
            return "Add null/undefined check before accessing the property"

        return "Review the code and error message carefully"

    async def _find_related_files(self, file_path: str) -> List[str]:
        """Find files related to the error location."""
        related = []

        # This is a placeholder - would need actual file system access
        # to find imports, dependencies, etc.

        return related

    async def analyze_stack_trace(self, stack_trace: str) -> DebugAnalysis:
        """
        Analyze a stack trace.

        Args:
            stack_trace: Full stack trace

        Returns:
            DebugAnalysis
        """
        logger.info("Analyzing stack trace")

        analysis = DebugAnalysis()

        # Extract error from last line
        lines = stack_trace.strip().split("\n")
        if lines:
            error_line = lines[-1]
            error_analysis = await self.analyze_error(error_line)
            analysis.error_type = error_analysis.error_type
            analysis.error_message = error_analysis.error_message
            analysis.cause = error_analysis.cause
            analysis.fix = error_analysis.fix

        # Extract file locations from stack trace
        file_pattern = r'File "(.+)", line (\d+)'
        matches = re.findall(file_pattern, stack_trace)

        if matches:
            analysis.location = f"{matches[0][0]}:{matches[0][1]}"
            analysis.related_files = [m[0] for m in matches[:5]]

        return analysis
