#!/usr/bin/env python3
"""
Deployment Script for Multi-Agent Automation System
Provides easy setup, configuration, and deployment of the agent system.
"""

import argparse
import json
import logging
import os
import shutil
import subprocess
import sys
import venv
from pathlib import Path
from typing import Dict, List, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(), logging.FileHandler("deployment.log")],
)
logger = logging.getLogger(__name__)


class DeploymentManager:
    """Manages the deployment process for the Multi-Agent System"""

    def __init__(self, base_path: Path = None):
        """Initialize deployment manager"""
        self.base_path = base_path or Path.cwd()
        self.venv_path = self.base_path / "venv"
        self.config_path = self.base_path / "config"
        self.logs_path = self.base_path / "logs"
        self.data_path = self.base_path / "data"
        self.temp_path = self.base_path / "temp"

        # Deployment configuration
        self.deployment_config = {
            "python_version": "3.8",
            "requirements_file": "requirements.txt",
            "config_templates": {
                "global": "config/global/default.json",
                "agents": "config/agents/",
                "skills": "config/skills/",
            },
            "directories": [
                "logs",
                "data",
                "temp",
                "output",
                "backup",
                "config/global",
                "config/agents",
                "config/skills",
            ],
        }

    def check_system_requirements(self) -> bool:
        """Check if system meets requirements"""
        logger.info("Checking system requirements...")

        # Check Python version
        python_version = sys.version_info
        min_version = tuple(
            map(int, self.deployment_config["python_version"].split("."))
        )

        if python_version[:2] < min_version:
            logger.error(
                f"Python {self.deployment_config['python_version']}+ required, found {python_version.major}.{python_version.minor}"
            )
            return False

        logger.info(f"✓ Python version: {python_version.major}.{python_version.minor}")

        # Check pip
        try:
            subprocess.run(
                [sys.executable, "-m", "pip", "--version"],
                check=True,
                capture_output=True,
            )
            logger.info("✓ pip is available")
        except subprocess.CalledProcessError:
            logger.error("✗ pip is not available")
            return False

        # Check venv module
        try:
            import venv

            logger.info("✓ venv module is available")
        except ImportError:
            logger.error("✗ venv module is not available")
            return False

        return True

    def create_virtual_environment(self) -> bool:
        """Create virtual environment"""
        logger.info("Creating virtual environment...")

        if self.venv_path.exists():
            logger.info("Virtual environment already exists")
            return True

        try:
            venv.create(self.venv_path, with_pip=True)
            logger.info("✓ Virtual environment created")
            return True
        except Exception as e:
            logger.error(f"✗ Failed to create virtual environment: {e}")
            return False

    def get_pip_executable(self) -> str:
        """Get pip executable path for the virtual environment"""
        if os.name == "nt":  # Windows
            return str(self.venv_path / "Scripts" / "pip.exe")
        else:  # Unix-like
            return str(self.venv_path / "bin" / "pip")

    def get_python_executable(self) -> str:
        """Get python executable path for the virtual environment"""
        if os.name == "nt":  # Windows
            return str(self.venv_path / "Scripts" / "python.exe")
        else:  # Unix-like
            return str(self.venv_path / "bin" / "python")

    def install_dependencies(self) -> bool:
        """Install required dependencies"""
        logger.info("Installing dependencies...")

        requirements_file = self.base_path / self.deployment_config["requirements_file"]

        if not requirements_file.exists():
            logger.error(f"Requirements file not found: {requirements_file}")
            return False

        try:
            pip_executable = self.get_pip_executable()

            # Upgrade pip first
            subprocess.run(
                [pip_executable, "install", "--upgrade", "pip"],
                check=True,
                capture_output=True,
            )

            # Install requirements
            result = subprocess.run(
                [pip_executable, "install", "-r", str(requirements_file)],
                check=True,
                capture_output=True,
                text=True,
            )

            logger.info("✓ Dependencies installed successfully")
            return True

        except subprocess.CalledProcessError as e:
            logger.error(f"✗ Failed to install dependencies: {e}")
            if e.stdout:
                logger.error(f"STDOUT: {e.stdout}")
            if e.stderr:
                logger.error(f"STDERR: {e.stderr}")
            return False

    def create_directory_structure(self) -> bool:
        """Create necessary directories"""
        logger.info("Creating directory structure...")

        try:
            for directory in self.deployment_config["directories"]:
                dir_path = self.base_path / directory
                dir_path.mkdir(parents=True, exist_ok=True)
                logger.info(f"✓ Created directory: {directory}")

            return True

        except Exception as e:
            logger.error(f"✗ Failed to create directories: {e}")
            return False

    def setup_configuration_files(self) -> bool:
        """Setup default configuration files"""
        logger.info("Setting up configuration files...")

        try:
            # Create global configuration
            global_config = {
                "system": {
                    "name": "Multi-Agent Automation System",
                    "version": "1.0.0",
                    "environment": "production",
                    "deployment_date": str(Path(__file__).stat().st_mtime),
                },
                "logging": {
                    "level": "INFO",
                    "file_enabled": True,
                    "console_enabled": True,
                    "log_directory": "./logs",
                    "log_rotation": True,
                    "max_log_size_mb": 50,
                },
                "performance": {
                    "max_workers": 4,
                    "timeout_default": 60,
                    "memory_limit_mb": 2048,
                    "enable_metrics": True,
                    "metrics_interval": 300,
                },
                "security": {
                    "enable_encryption": True,
                    "api_key_rotation": True,
                    "secure_communications": True,
                    "max_failed_attempts": 3,
                },
                "storage": {
                    "data_directory": "./data",
                    "temp_directory": "./temp",
                    "backup_directory": "./backup",
                    "auto_backup": True,
                    "backup_interval_hours": 24,
                },
            }

            global_config_path = self.base_path / "config" / "global" / "default.json"
            with open(global_config_path, "w") as f:
                json.dump(global_config, f, indent=2)
            logger.info("✓ Created global configuration")

            # Create sample agent configuration
            agent_config = {
                "agent_id": "sample_agent_001",
                "name": "Sample Data Agent",
                "description": "Sample agent for data processing tasks",
                "type": "data",
                "max_concurrent_tasks": 3,
                "timeout": 120,
                "retry_attempts": 3,
                "enabled": True,
                "skills": ["file_processing", "api_communication"],
                "resources": {"cpu_limit": 1.0, "memory_limit_mb": 512},
                "config": {
                    "supported_formats": ["csv", "json", "xlsx"],
                    "max_file_size_mb": 100,
                    "output_directory": "./output",
                    "temp_directory": "./temp",
                },
            }

            agent_config_path = (
                self.base_path / "config" / "agents" / "sample_agent.json"
            )
            with open(agent_config_path, "w") as f:
                json.dump(agent_config, f, indent=2)
            logger.info("✓ Created sample agent configuration")

            # Create sample skill configuration
            skill_config = {
                "skill_id": "file_processing_001",
                "name": "File Processing Skill",
                "type": "file_operations",
                "description": "Comprehensive file processing capabilities",
                "version": "1.0.0",
                "enabled": True,
                "dependencies": [],
                "parameters": {
                    "max_file_size_mb": 100,
                    "supported_formats": ["txt", "csv", "json", "xml"],
                    "backup_enabled": True,
                },
                "resources": {"memory_limit_mb": 256, "execution_timeout": 60},
            }

            skill_config_path = (
                self.base_path / "config" / "skills" / "file_processing.json"
            )
            with open(skill_config_path, "w") as f:
                json.dump(skill_config, f, indent=2)
            logger.info("✓ Created sample skill configuration")

            return True

        except Exception as e:
            logger.error(f"✗ Failed to setup configuration files: {e}")
            return False

    def create_startup_scripts(self) -> bool:
        """Create startup scripts for different platforms"""
        logger.info("Creating startup scripts...")

        try:
            # Create startup script for Windows
            windows_script = f"""@echo off
echo Starting Multi-Agent Automation System...
cd /d "{self.base_path}"
call "{self.venv_path}\\Scripts\\activate.bat"
python examples\\basic_automation.py
pause
"""

            windows_script_path = self.base_path / "start_system.bat"
            with open(windows_script_path, "w") as f:
                f.write(windows_script)
            logger.info("✓ Created Windows startup script")

            # Create startup script for Unix-like systems
            unix_script = f"""#!/bin/bash
echo "Starting Multi-Agent Automation System..."
cd "{self.base_path}"
source "{self.venv_path}/bin/activate"
python examples/basic_automation.py
"""

            unix_script_path = self.base_path / "start_system.sh"
            with open(unix_script_path, "w") as f:
                f.write(unix_script)

            # Make Unix script executable
            os.chmod(unix_script_path, 0o755)
            logger.info("✓ Created Unix startup script")

            return True

        except Exception as e:
            logger.error(f"✗ Failed to create startup scripts: {e}")
            return False

    def create_service_script(self) -> bool:
        """Create systemd service file for Linux deployment"""
        logger.info("Creating systemd service script...")

        try:
            service_content = f"""[Unit]
Description=Multi-Agent Automation System
After=network.target

[Service]
Type=simple
User={os.getenv("USER", "root")}
WorkingDirectory={self.base_path}
ExecStart={self.get_python_executable()} -m examples.basic_automation
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
"""

            service_path = self.base_path / "multi-agent-system.service"
            with open(service_path, "w") as f:
                f.write(service_content)

            logger.info("✓ Created systemd service file")
            logger.info(
                f"To install service: sudo cp {service_path} /etc/systemd/system/"
            )
            logger.info("Then run: sudo systemctl enable multi-agent-system.service")

            return True

        except Exception as e:
            logger.error(f"✗ Failed to create service script: {e}")
            return False

    def run_tests(self) -> bool:
        """Run basic system tests"""
        logger.info("Running system tests...")

        try:
            python_executable = self.get_python_executable()

            # Test imports
            test_script = """
import sys
sys.path.append('.')

try:
    from agents.data_agent import DataAgent
    from agents.web_agent import WebAgent
    from skills.file_processing_skill import FileProcessingSkill
    from skills.api_communication_skill import APICommunicationSkill
    from automation.agent_manager import AgentManager
    from config.config_manager import ConfigManager
    print("✓ All imports successful")
except ImportError as e:
    print(f"✗ Import failed: {e}")
    sys.exit(1)

# Test basic functionality
try:
    agent = DataAgent("test_agent", "Test Agent")
    skill = FileProcessingSkill()
    manager = AgentManager()
    config_mgr = ConfigManager()
    print("✓ Basic object creation successful")
except Exception as e:
    print(f"✗ Object creation failed: {e}")
    sys.exit(1)

print("✓ All tests passed")
"""

            result = subprocess.run(
                [python_executable, "-c", test_script],
                capture_output=True,
                text=True,
                cwd=self.base_path,
            )

            if result.returncode == 0:
                logger.info("✓ System tests passed")
                logger.info(result.stdout)
                return True
            else:
                logger.error("✗ System tests failed")
                logger.error(result.stderr)
                return False

        except Exception as e:
            logger.error(f"✗ Failed to run tests: {e}")
            return False

    def generate_deployment_report(self) -> Dict:
        """Generate deployment report"""
        report = {
            "deployment_status": "success",
            "timestamp": str(Path(__file__).stat().st_mtime),
            "system_info": {
                "python_version": f"{sys.version_info.major}.{sys.version_info.minor}",
                "platform": sys.platform,
                "base_path": str(self.base_path),
                "venv_path": str(self.venv_path),
            },
            "created_directories": self.deployment_config["directories"],
            "configuration_files": [
                "config/global/default.json",
                "config/agents/sample_agent.json",
                "config/skills/file_processing.json",
            ],
            "startup_scripts": [
                "start_system.bat",
                "start_system.sh",
                "multi-agent-system.service",
            ],
        }

        # Save report
        report_path = self.base_path / "deployment_report.json"
        with open(report_path, "w") as f:
            json.dump(report, f, indent=2)

        logger.info(f"Deployment report saved to: {report_path}")
        return report

    def cleanup_deployment(self) -> bool:
        """Clean up deployment artifacts"""
        logger.info("Cleaning up deployment...")

        try:
            # Remove virtual environment
            if self.venv_path.exists():
                shutil.rmtree(self.venv_path)
                logger.info("✓ Removed virtual environment")

            # Remove generated files (optional)
            generated_files = [
                "deployment.log",
                "deployment_report.json",
                "start_system.bat",
                "start_system.sh",
                "multi-agent-system.service",
            ]

            for filename in generated_files:
                file_path = self.base_path / filename
                if file_path.exists():
                    file_path.unlink()
                    logger.info(f"✓ Removed {filename}")

            # Clean up directories (keep config)
            cleanup_dirs = ["logs", "data", "temp", "output", "backup"]
            for dirname in cleanup_dirs:
                dir_path = self.base_path / dirname
                if dir_path.exists():
                    shutil.rmtree(dir_path)
                    logger.info(f"✓ Removed {dirname}/")

            return True

        except Exception as e:
            logger.error(f"✗ Cleanup failed: {e}")
            return False

    def deploy(self, skip_tests: bool = False) -> bool:
        """Run full deployment process"""
        logger.info("Starting deployment of Multi-Agent Automation System...")

        steps = [
            ("System Requirements", self.check_system_requirements),
            ("Virtual Environment", self.create_virtual_environment),
            ("Dependencies", self.install_dependencies),
            ("Directory Structure", self.create_directory_structure),
            ("Configuration Files", self.setup_configuration_files),
            ("Startup Scripts", self.create_startup_scripts),
            ("Service Script", self.create_service_script),
        ]

        if not skip_tests:
            steps.append(("System Tests", self.run_tests))

        failed_steps = []

        for step_name, step_function in steps:
            logger.info(f"\n--- {step_name} ---")
            if not step_function():
                failed_steps.append(step_name)
                logger.error(f"Step failed: {step_name}")

        if failed_steps:
            logger.error(f"\n❌ Deployment failed. Failed steps: {failed_steps}")
            return False

        # Generate deployment report
        self.generate_deployment_report()

        logger.info("\n🎉 Deployment completed successfully!")
        logger.info(f"System deployed to: {self.base_path}")
        logger.info("To start the system:")
        logger.info(f"  Windows: {self.base_path / 'start_system.bat'}")
        logger.info(f"  Unix/Linux: {self.base_path / 'start_system.sh'}")

        return True


def main():
    """Main deployment function"""
    parser = argparse.ArgumentParser(description="Deploy Multi-Agent Automation System")

    parser.add_argument(
        "--path",
        type=str,
        default=".",
        help="Base path for deployment (default: current directory)",
    )

    parser.add_argument(
        "--skip-tests", action="store_true", help="Skip running system tests"
    )

    parser.add_argument(
        "--cleanup", action="store_true", help="Clean up existing deployment"
    )

    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Initialize deployment manager
    base_path = Path(args.path).resolve()
    deployment_manager = DeploymentManager(base_path)

    try:
        if args.cleanup:
            logger.info("Running cleanup...")
            success = deployment_manager.cleanup_deployment()
            if success:
                logger.info("✓ Cleanup completed successfully")
            else:
                logger.error("✗ Cleanup failed")
                sys.exit(1)
        else:
            logger.info("Running deployment...")
            success = deployment_manager.deploy(skip_tests=args.skip_tests)
            if not success:
                logger.error("✗ Deployment failed")
                sys.exit(1)

    except KeyboardInterrupt:
        logger.info("\n⏹️ Deployment interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"\n❌ Deployment error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
