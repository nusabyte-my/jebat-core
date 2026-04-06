"""
🗡️ JEBAT Project Integration - Universal

Drop-in integration for ANY project.
Automatically detects project type and configures accordingly.

Usage:
    py -m jebat_project [command]

Works with:
- React/Vue/Angular projects
- Node.js/Express backends
- Python/Django/Flask projects
- TypeScript/JavaScript projects
- Any codebase
"""

import json
import sys
from pathlib import Path

# Add Dev directory to path for jebat_dev imports
dev_path = Path(__file__).parent.parent
if dev_path.exists():
    sys.path.insert(0, str(dev_path))


class JEBATProjectIntegration:
    """
    Universal JEBAT integration for any project.

    Auto-detects project type and configures JEBAT accordingly.
    """

    # Project type indicators
    PROJECT_TYPES = {
        "react": ["package.json", "src/App.jsx", "src/App.tsx"],
        "vue": ["package.json", "src/App.vue", "vite.config.js"],
        "angular": ["package.json", "angular.json", "src/app/app.component.ts"],
        "node": ["package.json", "server.js", "index.js"],
        "python": ["requirements.txt", "main.py", "app.py"],
        "django": ["manage.py", "requirements.txt"],
        "flask": ["app.py", "requirements.txt", "wsgi.py"],
        "typescript": ["tsconfig.json"],
        "nextjs": ["package.json", "next.config.js", "pages/"],
        "nuxt": ["package.json", "nuxt.config.js"],
    }

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.project_type = self._detect_project_type()
        self.config = self._load_or_create_config()

    def _detect_project_type(self) -> str:
        """Auto-detect project type from file structure."""
        detected = []

        for ptype, indicators in self.PROJECT_TYPES.items():
            matches = sum(1 for f in indicators if (self.project_root / f).exists())
            if matches > 0:
                detected.append((ptype, matches))

        if not detected:
            return "generic"

        # Return best match
        detected.sort(key=lambda x: x[1], reverse=True)
        return detected[0][0]

    def _load_or_create_config(self) -> dict:
        """Load existing config or create default."""
        config_path = self.project_root / ".jebatrc.json"

        if config_path.exists():
            with open(config_path) as f:
                return json.load(f)

        # Create default config
        config = {
            "projectType": self.project_type,
            "autoDetected": True,
            "features": {
                "ultraThink": True,
                "codeGeneration": True,
                "codeReview": True,
                "debugging": True,
            },
            "paths": self._detect_paths(),
        }

        # Save config
        with open(config_path, "w") as f:
            json.dump(config, f, indent=2)

        return config

    def _detect_paths(self) -> dict:
        """Detect common project paths."""
        paths = {}

        # Source directories
        for src in ["src", "app", "lib", "components", "pages"]:
            if (self.project_root / src).exists():
                paths[src] = src

        # Common patterns
        if (self.project_root / "src" / "components").exists():
            paths["components"] = "src/components"
        if (self.project_root / "src" / "pages").exists():
            paths["pages"] = "src/pages"
        if (self.project_root / "server").exists():
            paths["server"] = "server"

        return paths

    def get_status(self) -> dict:
        """Get integration status."""
        return {
            "projectType": self.project_type,
            "configExists": (self.project_root / ".jebatrc.json").exists(),
            "features": self.config.get("features", {}),
            "paths": self.config.get("paths", {}),
        }

    def print_status(self):
        """Print integration status."""
        print("=" * 60)
        print("JEBAT Project Integration")
        print("=" * 60)
        print()
        print(f"Project Type: {self.project_type.upper()}")
        print(f"Location: {self.project_root}")
        print()

        print("Detected Structure:")
        for name, path in self.config.get("paths", {}).items():
            exists = "✓" if (self.project_root / path).exists() else "✗"
            print(f"  [{exists}] {name}: {path}")

        print()
        print("Enabled Features:")
        features = self.config.get("features", {})
        for feature, enabled in features.items():
            status = "✓" if enabled else "✗"
            print(f"  [{status}] {feature}")

        print()
        print("=" * 60)
        print("Quick Start:")
        print()
        print(f'  py -m jebat_dev.launch ui "component description"')
        print(f'  py -m jebat_dev.launch create "feature description"')
        print(f"  py -m jebat_dev.launch review {self._get_sample_path()}")
        print(f'  py -m jebat_dev.launch debug "error message"')
        print()
        print("=" * 60)

    def _get_sample_path(self) -> str:
        """Get a sample file path for the project type."""
        samples = {
            "react": "src/App.tsx",
            "vue": "src/App.vue",
            "angular": "src/app/app.component.ts",
            "node": "server.js",
            "python": "main.py",
            "django": "views.py",
            "flask": "app.py",
            "typescript": "index.ts",
            "nextjs": "pages/index.tsx",
            "generic": "src/index.ts",
        }
        return samples.get(self.project_type, "src/index.ts")


def main():
    """Main entry point."""
    # Get current directory or provided path
    if len(sys.argv) > 1:
        project_root = Path(sys.argv[1]).resolve()
    else:
        project_root = Path.cwd()

    # Check if it's a valid project
    if not project_root.exists():
        print(f"Error: Path not found: {project_root}")
        sys.exit(1)

    # Initialize integration
    integration = JEBATProjectIntegration(project_root)

    # Show status
    integration.print_status()

    # Save config
    config_path = project_root / ".jebatrc.json"
    print(f"\nConfiguration saved to: {config_path}")
    print("\nTo use JEBAT with this project:")
    print("  1. Navigate to project: cd <project_path>")
    print("  2. Run JEBAT: py -m jebat_dev.launch <command>")
    print("  3. Or use global: jebat <command>")


if __name__ == "__main__":
    main()
