# JEBAT Project Integration

Universal integration for any development project.

## Quick Start

```bash
# Initialize JEBAT in any project
cd your-project
py -m jebat_project

# Or specify path
py -m jebat_project /path/to/project
```

## What It Does

1. **Auto-Detects Project Type**
   - React, Vue, Angular
   - Node.js, Express
   - Python, Django, Flask
   - TypeScript, JavaScript
   - Generic projects

2. **Creates Configuration**
   - `.jebatrc.json` with project settings
   - Auto-detected paths
   - Enabled features

3. **Enables JEBAT Features**
   - Ultra-Think reasoning
   - Code generation
   - Code review
   - Debugging assistance

## Usage

After initialization:

```bash
# Generate UI
py -m jebat_dev.launch ui "login form"

# Create features
py -m jebat_dev.launch create "dashboard"

# Review code
py -m jebat_dev.launch review src/App.tsx

# Debug
py -m jebat_dev.launch debug "error message"
```

## Supported Project Types

| Type | Indicators |
|------|------------|
| React | package.json, src/App.jsx |
| Vue | package.json, src/App.vue |
| Angular | angular.json |
| Node.js | package.json, server.js |
| Python | requirements.txt, main.py |
| Django | manage.py |
| Flask | app.py |
| Next.js | next.config.js |
| Nuxt | nuxt.config.js |

## Configuration

`.jebatrc.json`:

```json
{
  "projectType": "react",
  "autoDetected": true,
  "features": {
    "ultraThink": true,
    "codeGeneration": true,
    "codeReview": true,
    "debugging": true
  },
  "paths": {
    "src": "src",
    "components": "src/components"
  }
}
```

## Requirements

- Python 3.11+
- JEBAT DevAssistant installed

## License

MIT
