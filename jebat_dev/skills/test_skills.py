"""
JEBAT DevAssistant - Test Skills

Test running and analysis capabilities.
"""

import logging
from dataclasses import dataclass, field
from typing import List, Optional

logger = logging.getLogger(__name__)


@dataclass
class TestResult:
    """Result of test execution."""

    success: bool
    total: int = 0
    passed: int = 0
    failed: int = 0
    errors: int = 0
    skipped: int = 0
    output: str = ""
    failures: List[str] = field(default_factory=list)


class TestSkills:
    """
    Test running skills for DevAssistant.

    Provides capabilities for running and analyzing tests.
    """

    def __init__(self, sandbox):
        """
        Initialize test skills.

        Args:
            sandbox: DevSandbox for command execution
        """
        self.sandbox = sandbox
        logger.info("TestSkills initialized")

    async def run_tests(
        self,
        path: str,
        framework: str = "auto",
        test_path: str = "",
    ) -> TestResult:
        """
        Run tests.

        Args:
            path: Project path
            framework: Test framework (auto, pytest, jest, unittest)
            test_path: Specific test file or directory

        Returns:
            TestResult
        """
        logger.info(f"Running tests in {path} (framework={framework})")

        # Auto-detect framework
        if framework == "auto":
            framework = await self._detect_framework(path)
            logger.info(f"Auto-detected framework: {framework}")

        # Run tests based on framework
        if framework == "pytest":
            return await self._run_pytest(path, test_path)
        elif framework == "jest":
            return await self._run_jest(path, test_path)
        elif framework == "unittest":
            return await self._run_unittest(path, test_path)
        else:
            return TestResult(
                success=False,
                output="No test framework detected",
            )

    async def _detect_framework(self, path: str) -> Optional[str]:
        """Detect test framework from project."""
        # Check for pytest
        content = await self.sandbox.read_file(f"{path}/pyproject.toml")
        if content and ("pytest" in content or "testpaths" in content):
            return "pytest"

        # Check for requirements.txt
        content = await self.sandbox.read_file(f"{path}/requirements.txt")
        if content and "pytest" in content:
            return "pytest"

        # Check for package.json (Jest)
        content = await self.sandbox.read_file(f"{path}/package.json")
        if content and ("jest" in content or "@types/jest" in content):
            return "jest"

        # Default to unittest for Python
        return "unittest"

    async def _run_pytest(self, path: str, test_path: str) -> TestResult:
        """Run pytest tests."""
        cmd = f"pytest {test_path} -v --tb=short"
        result = await self.sandbox.execute(cmd, cwd=path)

        return self._parse_pytest_output(result)

    async def _run_jest(self, path: str, test_path: str) -> TestResult:
        """Run Jest tests."""
        cmd = f"npx jest {test_path} --verbose"
        result = await self.sandbox.execute(cmd, cwd=path)

        return self._parse_jest_output(result)

    async def _run_unittest(self, path: str, test_path: str) -> TestResult:
        """Run unittest tests."""
        cmd = f"python -m unittest discover {test_path} -v"
        result = await self.sandbox.execute(cmd, cwd=path)

        return self._parse_unittest_output(result)

    def _parse_pytest_output(self, result) -> TestResult:
        """Parse pytest output."""
        output = result.output + result.error
        lines = output.split("\n")

        test_result = TestResult(
            success=result.success,
            output=output,
        )

        # Parse summary line
        for line in lines:
            if "passed" in line or "failed" in line:
                # Example: "2 passed, 1 failed, 1 error in 0.50s"
                parts = line.split(",")
                for part in parts:
                    part = part.strip()
                    if "passed" in part:
                        test_result.passed = int(part.split()[0])
                    elif "failed" in part:
                        test_result.failed = int(part.split()[0])
                    elif "error" in part:
                        test_result.errors = int(part.split()[0])
                    elif "skipped" in part:
                        test_result.skipped = int(part.split()[0])

        test_result.total = (
            test_result.passed
            + test_result.failed
            + test_result.errors
            + test_result.skipped
        )

        # Extract failures
        test_result.failures = self._extract_failures(output)

        return test_result

    def _parse_jest_output(self, result) -> TestResult:
        """Parse Jest output."""
        output = result.output + result.error
        lines = output.split("\n")

        test_result = TestResult(
            success=result.success,
            output=output,
        )

        # Parse summary
        for line in lines:
            if "Tests:" in line:
                # Example: "Tests:       5 passed, 2 failed, 7 total"
                if "passed" in line:
                    test_result.passed = int(
                        line.split("passed")[0].split(":")[-1].strip()
                    )
                if "failed" in line:
                    test_result.failed = int(
                        line.split("failed")[0].split(":")[-1].strip()
                    )

        test_result.total = test_result.passed + test_result.failed
        test_result.failures = self._extract_failures(output)

        return test_result

    def _parse_unittest_output(self, result) -> TestResult:
        """Parse unittest output."""
        output = result.output + result.error
        lines = output.split("\n")

        test_result = TestResult(
            success=result.success,
            output=output,
        )

        # Parse summary
        for line in lines:
            if "OK" in line or "FAILED" in line:
                # Example: "OK (tests=10)" or "FAILED (failures=2, errors=1)"
                if "tests=" in line:
                    test_result.total = int(line.split("tests=")[1].split(")")[0])
                if "failures=" in line:
                    test_result.failed = int(line.split("failures=")[1].split(",")[0])
                if "errors=" in line:
                    test_result.errors = int(line.split("errors=")[1].split(",")[0])

        test_result.passed = test_result.total - test_result.failed - test_result.errors
        test_result.failures = self._extract_failures(output)

        return test_result

    def _extract_failures(self, output: str) -> List[str]:
        """Extract failure messages from output."""
        failures = []
        in_failure = False
        current_failure = []

        for line in output.split("\n"):
            if "FAILED" in line or "ERROR" in line or "FAIL:" in line:
                in_failure = True
                current_failure = [line]
            elif in_failure:
                if line.startswith("=") or line.startswith("-"):
                    failures.append("\n".join(current_failure))
                    in_failure = False
                    current_failure = []
                else:
                    current_failure.append(line)

        return failures[:5]  # Limit to first 5 failures
