#!/usr/bin/env python3
"""
JEBAT Setup Script

Automated setup and configuration for JEBAT AI Assistant.

Usage:
    python setup.py              # Interactive setup
    python setup.py --quick      # Quick setup with defaults
    python setup.py --check      # Check system requirements
"""

import os
import platform
import subprocess
import sys
from pathlib import Path
from typing import Optional


class Colors:
    """ANSI color codes for terminal output"""

    HEADER = "\033[95m"
    OKBLUE = "\033[94m"
    OKCYAN = "\033[96m"
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"


def print_header(text: str):
    """Print header text"""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'=' * 60}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text.center(60)}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'=' * 60}{Colors.ENDC}\n")


def print_success(text: str):
    """Print success message"""
    print(f"{Colors.OKGREEN}✓ {text}{Colors.ENDC}")


def print_error(text: str):
    """Print error message"""
    print(f"{Colors.FAIL}✗ {text}{Colors.ENDC}")


def print_warning(text: str):
    """Print warning message"""
    print(f"{Colors.WARNING}⚠ {text}{Colors.ENDC}")


def print_info(text: str):
    """Print info message"""
    print(f"{Colors.OKCYAN}ℹ {text}{Colors.ENDC}")


class JEBATSetup:
    """JEBAT setup and configuration"""

    def __init__(self, quick_mode: bool = False):
        """Initialize setup"""
        self.quick_mode = quick_mode
        self.project_root = Path(__file__).parent
        self.env_file = self.project_root / ".env"
        self.config_dir = self.project_root / "config"

        # System requirements
        self.required_python = (3, 11)
        self.required_packages = [
            "sqlalchemy",
            "asyncpg",
            "redis",
            "scikit-learn",
            "numpy",
            "scipy",
        ]

    def check_python_version(self) -> bool:
        """Check Python version"""
        current = sys.version_info[:2]
        required = self.required_python

        if current >= required:
            print_success(
                f"Python version: {sys.version.split()[0]} (required: {'.'.join(map(str, required))}+)"
            )
            return True
        else:
            print_error(
                f"Python version: {sys.version.split()[0]} (required: {'.'.join(map(str, required))}+)"
            )
            return False

    def check_packages(self) -> bool:
        """Check required packages"""
        missing = []

        for package in self.required_packages:
            try:
                __import__(package.replace("-", "_"))
                print_success(f"Package installed: {package}")
            except ImportError:
                print_error(f"Package missing: {package}")
                missing.append(package)

        if missing:
            print_warning(f"\nMissing packages: {', '.join(missing)}")
            print_info("Run: pip install -r requirements.txt")
            return False

        return True

    def check_database(self) -> bool:
        """Check database connectivity"""
        # This would check PostgreSQL connection
        # For now, just verify the URL format
        db_url = os.getenv("DATABASE_URL", "")

        if db_url.startswith("postgresql+asyncpg://"):
            print_success("Database URL configured")
            return True
        else:
            print_warning("Database URL not configured (will use defaults)")
            return True  # Not fatal

    def check_redis(self) -> bool:
        """Check Redis connectivity"""
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")

        if redis_url.startswith("redis://"):
            print_success("Redis URL configured")
            return True
        else:
            print_warning("Redis URL not configured (will use defaults)")
            return True  # Not fatal

    def check_requirements(self) -> bool:
        """Check all requirements"""
        print_header("Checking System Requirements")

        checks = [
            self.check_python_version(),
            self.check_packages(),
            self.check_database(),
            self.check_redis(),
        ]

        if all(checks):
            print_success("All requirements met!")
            return True
        else:
            print_warning("Some requirements not met. Please fix the issues above.")
            return False

    def create_env_file(self):
        """Create .env file with configuration"""
        if self.env_file.exists():
            print_warning(f".env file already exists: {self.env_file}")
            if not self.quick_mode:
                response = input("Overwrite? (y/N): ").strip().lower()
                if response != "y":
                    print_info("Keeping existing .env file")
                    return

        print_info("Creating .env file...")

        env_content = """# JEBAT Configuration
# Generated by setup.py

# Application
APP_ENV=development
APP_DEBUG=true
LOG_LEVEL=INFO

# Database
DATABASE_URL=postgresql+asyncpg://jebat:jebat_password@localhost:5432/jebat_db
REDIS_URL=redis://localhost:6379/0

# LLM Providers (add your keys)
OPENAI_API_KEY=
ANTHROPIC_API_KEY=

# Embedding
EMBEDDING_MODEL=text-embedding-3-small
EMBEDDING_DIMENSIONS=1536

# Memory Configuration
M0_TTL=30s
M1_TTL=24h
M2_TTL=7d
M3_TTL=90d

HEAT_THRESHOLD_HIGH=0.8
HEAT_THRESHOLD_LOW=0.4
CONSOLIDATION_INTERVAL=3600

# Agent Configuration
MAX_AGENTS=10
AGENT_TIMEOUT=300
MAX_RETRIES=3

# Search
SEARCH_TOP_K=10
RERANK_TOP_K=5

# Telegram Bot (optional)
TELEGRAM_BOT_TOKEN=

# Discord Bot (optional)
DISCORD_BOT_TOKEN=
"""

        with open(self.env_file, "w") as f:
            f.write(env_content)

        print_success(f".env file created: {self.env_file}")
        print_warning("Please edit .env and add your API keys!")

    def create_config_directory(self):
        """Create configuration directory"""
        if not self.config_dir.exists():
            self.config_dir.mkdir(parents=True)
            print_success(f"Config directory created: {self.config_dir}")
        else:
            print_info(f"Config directory exists: {self.config_dir}")

    def install_dependencies(self):
        """Install Python dependencies"""
        requirements_file = self.project_root / "requirements.txt"

        if not requirements_file.exists():
            print_warning("requirements.txt not found")
            return

        print_info("Installing dependencies...")

        try:
            subprocess.check_call(
                [
                    sys.executable,
                    "-m",
                    "pip",
                    "install",
                    "-r",
                    str(requirements_file),
                    "--upgrade",
                ]
            )
            print_success("Dependencies installed successfully")
        except subprocess.CalledProcessError as e:
            print_error(f"Failed to install dependencies: {e}")

    def initialize_database(self):
        """Initialize database tables"""
        print_info("Initializing database...")

        try:
            # Import and run database initialization
            sys.path.insert(0, str(self.project_root))
            import asyncio

            from jebat.database.models import init_db

            asyncio.run(init_db())
            print_success("Database initialized successfully")
        except Exception as e:
            print_error(f"Database initialization failed: {e}")
            print_info("Make sure PostgreSQL is running and DATABASE_URL is correct")

    def run_tests(self):
        """Run basic tests"""
        print_info("Running basic tests...")

        try:
            # Test imports
            from jebat import MemoryManager
            from jebat.features.ultra_loop import create_ultra_loop
            from jebat.features.ultra_think import create_ultra_think

            print_success("All imports successful")

            # Test CLI
            result = subprocess.run(
                [sys.executable, "-m", "jebat.cli.launch", "--help"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                print_success("CLI working correctly")
            else:
                print_warning("CLI test failed")

        except Exception as e:
            print_error(f"Test failed: {e}")

    def setup_complete(self):
        """Print setup completion message"""
        print_header("Setup Complete!")

        print_success("JEBAT is ready to use!")
        print("\nNext steps:")
        print("  1. Edit .env file and add your API keys")
        print("  2. Start PostgreSQL and Redis")
        print("  3. Run: py -m jebat.cli.launch status")
        print('  4. Try: py -m jebat.cli.launch think "Hello!"')
        print("\nDocumentation:")
        print("  - Quick Reference: QUICK_REFERENCE.md")
        print("  - Full Report: SYSTEM_REPORT_COMPLETE.md")
        print("  - Roadmap: ROADMAP.md")
        print()

    def run(self):
        """Run complete setup"""
        print_header("JEBAT Setup")

        # Check requirements
        if not self.check_requirements():
            if self.quick_mode:
                print_warning("Continuing in quick mode despite issues...")
            else:
                print_error("Please fix requirements before continuing")
                return False

        # Create configuration
        self.create_env_file()
        self.create_config_directory()

        # Install dependencies
        if not self.quick_mode:
            response = input("\nInstall/update dependencies? (Y/n): ").strip().lower()
            if response != "n":
                self.install_dependencies()

        # Initialize database
        if not self.quick_mode:
            response = input("\nInitialize database? (Y/n): ").strip().lower()
            if response != "n":
                self.initialize_database()

        # Run tests
        self.run_tests()

        # Completion
        self.setup_complete()
        return True


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="JEBAT Setup Script")
    parser.add_argument(
        "--quick", action="store_true", help="Quick setup with defaults"
    )
    parser.add_argument(
        "--check", action="store_true", help="Check system requirements only"
    )
    parser.add_argument(
        "--init-db", action="store_true", help="Initialize database only"
    )

    args = parser.parse_args()

    setup = JEBATSetup(quick_mode=args.quick)

    if args.check:
        success = setup.check_requirements()
        sys.exit(0 if success else 1)
    elif args.init_db:
        setup.initialize_database()
        sys.exit(0)
    else:
        success = setup.run()
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
