"""
Fullstack Development Skill
Comprehensive skill for fullstack web development including frontend frameworks,
backend APIs, database integration, deployment, and project management.
"""

import asyncio
import json
import os
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import requests
import yaml

from .base_skill import BaseSkill, SkillParameter, SkillResult, SkillType


class FullstackDevelopmentSkill(BaseSkill):
    """
    Comprehensive fullstack development skill.

    Capabilities:
    - Project scaffolding and setup
    - Frontend development (React, Vue, Angular)
    - Backend API development (Node.js, Python, PHP)
    - Database integration and management
    - Authentication and security
    - Testing and deployment
    - Performance optimization
    """

    def __init__(
        self,
        skill_id: str = "fullstack_dev_001",
        name: str = "Fullstack Development",
        description: str = "Comprehensive fullstack web development capabilities",
        version: str = "1.0.0",
        config: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            skill_id=skill_id,
            name=name,
            skill_type=SkillType.AUTOMATION,
            description=description,
            version=version,
            config=config or {},
        )

        # Default configuration
        default_config = {
            "supported_frameworks": {
                "frontend": {
                    "react": {
                        "versions": ["18.x", "17.x"],
                        "templates": ["cra", "next", "vite"],
                        "ui_libraries": ["material-ui", "chakra-ui", "antd"],
                    },
                    "vue": {
                        "versions": ["3.x", "2.x"],
                        "templates": ["vue-cli", "nuxt", "vite"],
                        "ui_libraries": ["vuetify", "quasar", "element-plus"],
                    },
                    "angular": {
                        "versions": ["15.x", "14.x"],
                        "templates": ["angular-cli"],
                        "ui_libraries": ["angular-material", "ng-bootstrap"],
                    },
                },
                "backend": {
                    "node": {
                        "frameworks": ["express", "fastify", "nest", "koa"],
                        "databases": ["mongodb", "postgresql", "mysql", "redis"],
                    },
                    "python": {
                        "frameworks": ["fastapi", "django", "flask", "tornado"],
                        "databases": ["postgresql", "mysql", "sqlite", "redis"],
                    },
                    "php": {
                        "frameworks": ["laravel", "symfony", "codeigniter"],
                        "databases": ["mysql", "postgresql", "sqlite"],
                    },
                },
            },
            "development_tools": {
                "package_managers": ["npm", "yarn", "pnpm", "pip", "composer"],
                "build_tools": ["webpack", "vite", "rollup", "parcel"],
                "testing": ["jest", "cypress", "playwright", "vitest"],
                "linting": ["eslint", "prettier", "stylelint"],
                "deployment": ["vercel", "netlify", "heroku", "docker"],
            },
            "project_structure": {
                "directories": [
                    "src",
                    "public",
                    "components",
                    "pages",
                    "api",
                    "utils",
                    "styles",
                    "assets",
                    "tests",
                    "docs",
                ],
                "config_files": [
                    "package.json",
                    "tsconfig.json",
                    ".env",
                    ".gitignore",
                    "README.md",
                    "docker-compose.yml",
                ],
            },
            "default_ports": {
                "frontend": 3000,
                "backend": 8000,
                "database": 5432,
                "redis": 6379,
            },
        }

        # Merge with provided config
        for key, value in default_config.items():
            if key not in self.config:
                self.config[key] = value

        # Track project state
        self.active_projects = {}
        self.build_cache = {}
        self.deployment_history = []

    async def execute(self, parameters: Dict[str, Any]) -> SkillResult:
        """Execute fullstack development operation"""
        operation = parameters.get("operation", "").lower()

        try:
            if operation == "create_project":
                return await self._create_project(parameters)
            elif operation == "setup_frontend":
                return await self._setup_frontend(parameters)
            elif operation == "setup_backend":
                return await self._setup_backend(parameters)
            elif operation == "setup_database":
                return await self._setup_database(parameters)
            elif operation == "create_api_endpoint":
                return await self._create_api_endpoint(parameters)
            elif operation == "create_component":
                return await self._create_component(parameters)
            elif operation == "setup_auth":
                return await self._setup_authentication(parameters)
            elif operation == "setup_testing":
                return await self._setup_testing(parameters)
            elif operation == "build_project":
                return await self._build_project(parameters)
            elif operation == "deploy_project":
                return await self._deploy_project(parameters)
            elif operation == "run_tests":
                return await self._run_tests(parameters)
            elif operation == "optimize_performance":
                return await self._optimize_performance(parameters)
            elif operation == "generate_docs":
                return await self._generate_documentation(parameters)
            else:
                raise ValueError(f"Unsupported operation: {operation}")

        except Exception as e:
            return SkillResult(
                success=False,
                error=f"Fullstack development operation failed: {str(e)}",
                skill_used=self.name,
            )

    async def _create_project(self, parameters: Dict[str, Any]) -> SkillResult:
        """Create a new fullstack project"""
        project_name = parameters.get("project_name")
        frontend_framework = parameters.get("frontend_framework", "react")
        backend_framework = parameters.get("backend_framework", "express")
        database_type = parameters.get("database_type", "postgresql")
        project_path = parameters.get("project_path", f"./{project_name}")

        if not project_name:
            raise ValueError("project_name is required")

        try:
            project_dir = Path(project_path)
            project_dir.mkdir(parents=True, exist_ok=True)

            created_files = []
            setup_commands = []

            # Create project structure
            directories = [
                "frontend",
                "backend",
                "database",
                "docs",
                "scripts",
                "tests",
                ".github/workflows",
            ]

            for directory in directories:
                (project_dir / directory).mkdir(parents=True, exist_ok=True)

            # Create root package.json for workspace management
            root_package = {
                "name": project_name,
                "version": "1.0.0",
                "description": f"Fullstack application: {project_name}",
                "private": True,
                "workspaces": ["frontend", "backend"],
                "scripts": {
                    "dev": 'concurrently "npm run dev:frontend" "npm run dev:backend"',
                    "dev:frontend": "cd frontend && npm run dev",
                    "dev:backend": "cd backend && npm run dev",
                    "build": "npm run build:frontend && npm run build:backend",
                    "build:frontend": "cd frontend && npm run build",
                    "build:backend": "cd backend && npm run build",
                    "test": "npm run test:frontend && npm run test:backend",
                    "test:frontend": "cd frontend && npm test",
                    "test:backend": "cd backend && npm test",
                },
                "devDependencies": {"concurrently": "^7.6.0"},
            }

            with open(project_dir / "package.json", "w") as f:
                json.dump(root_package, f, indent=2)
            created_files.append("package.json")

            # Create .env template
            env_template = f"""# Environment Configuration
NODE_ENV=development
PORT=3000
API_PORT=8000

# Database Configuration
DATABASE_URL=postgresql://username:password@localhost:5432/{project_name}
DATABASE_HOST=localhost
DATABASE_PORT=5432
DATABASE_NAME={project_name}
DATABASE_USER=username
DATABASE_PASSWORD=password

# JWT Configuration
JWT_SECRET=your-secret-key-here
JWT_EXPIRES_IN=7d

# API Configuration
API_BASE_URL=http://localhost:8000/api

# Frontend Configuration
REACT_APP_API_URL=http://localhost:8000/api
"""
            with open(project_dir / ".env.example", "w") as f:
                f.write(env_template)
            created_files.append(".env.example")

            # Create .gitignore
            gitignore_content = """# Dependencies
node_modules/
*/node_modules/

# Production builds
dist/
build/
.next/

# Environment files
.env
.env.local
.env.production

# Logs
*.log
logs/
npm-debug.log*
yarn-debug.log*

# Runtime data
pids
*.pid
*.seed

# Coverage
coverage/
*.lcov

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Database
*.sqlite
*.db

# Temporary files
tmp/
temp/
"""
            with open(project_dir / ".gitignore", "w") as f:
                f.write(gitignore_content)
            created_files.append(".gitignore")

            # Create README
            readme_content = f"""# {project_name}

A fullstack web application built with {frontend_framework.title()} and {backend_framework.title()}.

## Technology Stack

### Frontend
- **Framework**: {frontend_framework.title()}
- **Package Manager**: npm/yarn
- **Build Tool**: Vite/Webpack

### Backend
- **Framework**: {backend_framework.title()}
- **Database**: {database_type.title()}
- **Authentication**: JWT

### Development Tools
- **Testing**: Jest, Cypress
- **Linting**: ESLint, Prettier
- **CI/CD**: GitHub Actions

## Getting Started

### Prerequisites
- Node.js (v16+)
- npm or yarn
- {database_type.title()} (if using database)

### Installation

1. Clone the repository
```bash
git clone <repository-url>
cd {project_name}
```

2. Install dependencies
```bash
npm install
```

3. Set up environment variables
```bash
cp .env.example .env
# Edit .env with your configuration
```

4. Start development servers
```bash
npm run dev
```

This will start both frontend and backend development servers.

## Project Structure

```
{project_name}/
├── frontend/          # Frontend application
├── backend/           # Backend API
├── database/          # Database scripts and migrations
├── docs/             # Documentation
├── tests/            # End-to-end tests
└── scripts/          # Build and deployment scripts
```

## Development

### Frontend Development
```bash
cd frontend
npm run dev
```

### Backend Development
```bash
cd backend
npm run dev
```

### Running Tests
```bash
npm run test
```

### Building for Production
```bash
npm run build
```

## Deployment

See deployment documentation in `/docs/deployment.md`

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

[Your License Here]
"""
            with open(project_dir / "README.md", "w") as f:
                f.write(readme_content)
            created_files.append("README.md")

            # Create Docker Compose for development
            docker_compose = f"""version: '3.8'
services:
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile.dev
    ports:
      - "3000:3000"
    volumes:
      - ./frontend:/app
      - /app/node_modules
    environment:
      - REACT_APP_API_URL=http://localhost:8000/api
    depends_on:
      - backend

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile.dev
    ports:
      - "8000:8000"
    volumes:
      - ./backend:/app
      - /app/node_modules
    environment:
      - NODE_ENV=development
      - DATABASE_URL=postgresql://postgres:password@database:5432/{project_name}
    depends_on:
      - database

  database:
    image: postgres:15
    environment:
      POSTGRES_DB: {project_name}
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: password
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

volumes:
  postgres_data:
"""
            with open(project_dir / "docker-compose.yml", "w") as f:
                f.write(docker_compose)
            created_files.append("docker-compose.yml")

            # Store project information
            self.active_projects[project_name] = {
                "path": str(project_dir),
                "frontend_framework": frontend_framework,
                "backend_framework": backend_framework,
                "database_type": database_type,
                "created_at": time.time(),
                "status": "initialized",
            }

            return SkillResult(
                success=True,
                data={
                    "project_name": project_name,
                    "project_path": str(project_dir),
                    "frontend_framework": frontend_framework,
                    "backend_framework": backend_framework,
                    "database_type": database_type,
                    "created_files": created_files,
                    "next_steps": [
                        "cd " + project_name,
                        "npm install",
                        "Setup frontend: npm run setup:frontend",
                        "Setup backend: npm run setup:backend",
                        "Start development: npm run dev",
                    ],
                },
                metadata={
                    "operation": "create_project",
                    "files_created": len(created_files),
                },
            )

        except Exception as e:
            raise Exception(f"Failed to create project: {str(e)}")

    async def _setup_frontend(self, parameters: Dict[str, Any]) -> SkillResult:
        """Setup frontend application"""
        project_name = parameters.get("project_name")
        framework = parameters.get("framework", "react")
        ui_library = parameters.get("ui_library")
        features = parameters.get("features", [])

        if not project_name or project_name not in self.active_projects:
            raise ValueError("Valid project_name is required")

        try:
            project_path = Path(self.active_projects[project_name]["path"])
            frontend_path = project_path / "frontend"

            created_files = []
            commands_run = []

            if framework.lower() == "react":
                # Create React app with Vite
                cmd = [
                    "npm",
                    "create",
                    "vite@latest",
                    ".",
                    "--",
                    "--template",
                    "react-ts",
                ]
                await self._run_command(cmd, cwd=frontend_path)
                commands_run.append("Created React app with Vite")

                # Install additional dependencies
                base_deps = ["react-router-dom", "axios", "@types/react-router-dom"]

                if ui_library == "material-ui":
                    base_deps.extend(
                        [
                            "@mui/material",
                            "@emotion/react",
                            "@emotion/styled",
                            "@mui/icons-material",
                        ]
                    )
                elif ui_library == "chakra-ui":
                    base_deps.extend(
                        [
                            "@chakra-ui/react",
                            "@emotion/react",
                            "@emotion/styled",
                            "framer-motion",
                        ]
                    )

                if "authentication" in features:
                    base_deps.extend(
                        ["@auth0/auth0-react", "js-cookie", "@types/js-cookie"]
                    )

                if "state_management" in features:
                    base_deps.extend(["@reduxjs/toolkit", "react-redux", "zustand"])

                # Install dependencies
                install_cmd = ["npm", "install"] + base_deps
                await self._run_command(install_cmd, cwd=frontend_path)
                commands_run.append(f"Installed dependencies: {', '.join(base_deps)}")

            elif framework.lower() == "vue":
                # Create Vue app
                cmd = [
                    "npm",
                    "create",
                    "vue@latest",
                    ".",
                    "--",
                    "--typescript",
                    "--router",
                    "--pinia",
                ]
                await self._run_command(cmd, cwd=frontend_path)
                commands_run.append("Created Vue 3 app")

            elif framework.lower() == "angular":
                # Create Angular app
                cmd = [
                    "npx",
                    "@angular/cli@latest",
                    "new",
                    ".",
                    "--routing",
                    "--style=scss",
                    "--skip-git",
                ]
                await self._run_command(cmd, cwd=frontend_path)
                commands_run.append("Created Angular app")

            # Create common configuration files

            # Vite config (for React/Vue)
            if framework.lower() in ["react", "vue"]:
                vite_config = f"""import {{ defineConfig }} from 'vite'
import {framework} from '@vitejs/plugin-{framework}'

export default defineConfig({{
  plugins: [{framework}()],
  server: {{
    port: 3000,
    proxy: {{
      '/api': {{
        target: 'http://localhost:8000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, '/api')
      }}
    }}
  }},
  build: {{
    outDir: 'dist',
    sourcemap: true
  }}
}})
"""
                with open(frontend_path / "vite.config.ts", "w") as f:
                    f.write(vite_config)
                created_files.append("vite.config.ts")

            # ESLint config
            eslint_config = {
                "env": {"browser": True, "es2021": True},
                "extends": [
                    "eslint:recommended",
                    "@typescript-eslint/recommended",
                    f"{framework}/recommended"
                    if framework != "angular"
                    else "recommended",
                ],
                "parser": "@typescript-eslint/parser",
                "parserOptions": {"ecmaVersion": 12, "sourceType": "module"},
                "plugins": ["@typescript-eslint"],
                "rules": {
                    "semi": ["error", "always"],
                    "quotes": ["error", "single"],
                    "no-unused-vars": "warn",
                    "no-console": "warn",
                },
            }

            with open(frontend_path / ".eslintrc.json", "w") as f:
                json.dump(eslint_config, f, indent=2)
            created_files.append(".eslintrc.json")

            # Prettier config
            prettier_config = {
                "semi": True,
                "singleQuote": True,
                "tabWidth": 2,
                "trailingComma": "es5",
                "printWidth": 100,
                "bracketSpacing": True,
                "arrowParens": "avoid",
            }

            with open(frontend_path / ".prettierrc", "w") as f:
                json.dump(prettier_config, f, indent=2)
            created_files.append(".prettierrc")

            # Create basic folder structure
            directories = [
                "src/components",
                "src/pages",
                "src/utils",
                "src/hooks",
                "src/types",
            ]
            for directory in directories:
                (frontend_path / directory).mkdir(parents=True, exist_ok=True)

            # Create example component
            if framework.lower() == "react":
                component_content = """import React from 'react';

interface WelcomeProps {
  message?: string;
}

const Welcome: React.FC<WelcomeProps> = ({ message = 'Welcome to your new app!' }) => {
  return (
    <div className="welcome">
      <h1>{message}</h1>
      <p>Your fullstack application is ready!</p>
    </div>
  );
};

export default Welcome;
"""
                with open(frontend_path / "src/components/Welcome.tsx", "w") as f:
                    f.write(component_content)
                created_files.append("src/components/Welcome.tsx")

            # Update project status
            self.active_projects[project_name]["frontend_setup"] = True
            self.active_projects[project_name]["frontend_framework"] = framework

            return SkillResult(
                success=True,
                data={
                    "project_name": project_name,
                    "framework": framework,
                    "ui_library": ui_library,
                    "features": features,
                    "frontend_path": str(frontend_path),
                    "created_files": created_files,
                    "commands_run": commands_run,
                },
                metadata={"operation": "setup_frontend", "framework": framework},
            )

        except Exception as e:
            raise Exception(f"Failed to setup frontend: {str(e)}")

    async def _run_command(self, command: List[str], cwd: Path = None) -> str:
        """Execute shell command"""
        try:
            process = await asyncio.create_subprocess_exec(
                *command,
                cwd=cwd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await process.communicate()

            if process.returncode != 0:
                raise Exception(f"Command failed: {stderr.decode()}")

            return stdout.decode()

        except Exception as e:
            raise Exception(f"Failed to run command {' '.join(command)}: {str(e)}")

    def get_parameters(self) -> List[SkillParameter]:
        """Get list of parameters this skill accepts"""
        return [
            SkillParameter(
                name="operation",
                param_type=str,
                required=True,
                description="Type of fullstack operation to perform",
            ),
            SkillParameter(
                name="project_name",
                param_type=str,
                required=False,
                description="Name of the project",
            ),
            SkillParameter(
                name="frontend_framework",
                param_type=str,
                required=False,
                default="react",
                description="Frontend framework (react, vue, angular)",
            ),
            SkillParameter(
                name="backend_framework",
                param_type=str,
                required=False,
                default="express",
                description="Backend framework (express, fastapi, laravel)",
            ),
            SkillParameter(
                name="database_type",
                param_type=str,
                required=False,
                default="postgresql",
                description="Database type (postgresql, mysql, mongodb)",
            ),
            SkillParameter(
                name="features",
                param_type=list,
                required=False,
                default=[],
                description="Additional features to include",
            ),
            SkillParameter(
                name="project_path",
                param_type=str,
                required=False,
                description="Custom project path",
            ),
        ]
