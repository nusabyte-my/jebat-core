# 🤝 Contributing to JEBAT

**Welcome to the JEBAT community!**

Thank you for your interest in contributing to JEBAT. This document provides guidelines and instructions for contributing.

---

## 📖 Table of Contents

1. [Code of Conduct](#code-of-conduct)
2. [How to Contribute](#how-to-contribute)
3. [Getting Started](#getting-started)
4. [Development Workflow](#development-workflow)
5. [Coding Standards](#coding-standards)
6. [Testing](#testing)
7. [Documentation](#documentation)
8. [Pull Request Guidelines](#pull-request-guidelines)
9. [Issue Guidelines](#issue-guidelines)
10. [Community](#community)

---

## 🎯 Code of Conduct

### Our Pledge

We pledge to make participation in JEBAT a harassment-free experience for everyone. We welcome contributors of all backgrounds and identities.

### Our Standards

Examples of behavior that contributes to a positive environment:

- ✅ Using welcoming and inclusive language
- ✅ Being respectful of differing viewpoints
- ✅ Gracefully accepting constructive criticism
- ✅ Focusing on what is best for the community
- ✅ Showing empathy towards other community members

Examples of unacceptable behavior:

- ❌ Trolling, insulting/derogatory comments
- ❌ Personal or political attacks
- ❌ Public or private harassment
- ❌ Publishing others' private information
- ❌ Other conduct inappropriate in a professional setting

---

## 🚀 How to Contribute

### Ways to Help

1. **Report Bugs** - Open an issue with detailed description
2. **Fix Bugs** - Submit a PR with fix
3. **Add Features** - Propose feature, then implement
4. **Improve Docs** - Fix typos, add examples, clarify
5. **Review PRs** - Provide constructive feedback
6. **Answer Questions** - Help in discussions/issues
7. **Spread the Word** - Star the repo, share on social media

---

## 🛠️ Getting Started

### 1. Fork the Repository

```bash
# Fork on GitHub, then clone
git clone https://github.com/YOUR_USERNAME/jebat-core.git
cd jebat-core

# Add upstream remote
git remote add upstream https://github.com/nusabyte-my/jebat-core.git
```

### 2. Set Up Development Environment

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate     # Windows

# Install dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install
```

### 3. Create a Branch

```bash
# Get latest changes
git checkout main
git pull upstream main

# Create feature branch
git checkout -b feature/your-feature-name
```

---

## 📝 Development Workflow

### 1. Make Changes

- Write clean, readable code
- Add tests for new features
- Update documentation
- Follow existing patterns

### 2. Test Locally

```bash
# Run tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=jebat --cov-report=html

# Check code quality
black jebat/ --check
flake8 jebat/
mypy jebat/
```

### 3. Commit Changes

```bash
# Stage changes
git add .

# Commit with clear message
git commit -m "feat: add your feature

- Description of what was added
- Why it was added
- Any breaking changes"
```

### 4. Push & Create PR

```bash
# Push to your fork
git push origin feature/your-feature-name

# Create Pull Request on GitHub
# - Go to your fork
# - Click "Compare & pull request"
# - Fill out PR template
```

---

## 📏 Coding Standards

### Python Style Guide

We follow **PEP 8** with these conventions:

#### Code Formatting

```python
# Use 4 spaces for indentation (no tabs)
def my_function():
    """Docstring"""
    return True

# Maximum line length: 88 characters
# Use type hints
def greet(name: str, age: int) -> str:
    return f"Hello {name}, you are {age} years old"

# Use f-strings for string formatting
name = "JEBAT"
print(f"Welcome to {name}")
```

#### Naming Conventions

```python
# Classes: PascalCase
class MemoryManager:
    pass

# Functions/variables: snake_case
def store_memory():
    user_id = "123"

# Constants: UPPER_CASE
MAX_RETRIES = 3

# Private: leading underscore
def _internal_function():
    pass
```

#### Docstrings

```python
def complex_function(param1: str, param2: int) -> dict:
    """
    Brief description of function.

    Extended description if needed.

    Args:
        param1: Description of param1
        param2: Description of param2

    Returns:
        dict: Description of return value

    Raises:
        ValueError: When param1 is empty
    """
    pass
```

### Code Quality Tools

```bash
# Install quality tools
pip install black flake8 mypy pylint isort

# Format code
black jebat/
isort jebat/

# Check quality
flake8 jebat/
mypy jebat/
pylint jebat/
```

---

## 🧪 Testing

### Writing Tests

```python
"""Test module for feature"""

import pytest
from jebat.feature import my_function

def test_my_function():
    """Test basic functionality"""
    result = my_function("input")
    assert result == "expected"

@pytest.mark.asyncio
async def test_async_function():
    """Test async function"""
    result = await async_function()
    assert result is not None
```

### Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_feature.py -v

# Run with coverage
pytest tests/ --cov=jebat --cov-report=html

# Run specific test
pytest tests/test_feature.py::test_my_function -v
```

### Test Coverage

We aim for **80%+ coverage** on core modules.

```bash
# Check coverage
pytest tests/ --cov=jebat --cov-report=term-missing

# View HTML report
start htmlcov/index.html  # Windows
open htmlcov/index.html   # macOS
```

---

## 📚 Documentation

### Code Comments

```python
# Good comment - explains WHY
# Using async here to avoid blocking the event loop
await asyncio.sleep(1)

# Bad comment - explains WHAT (obvious from code)
# Increment counter
counter += 1
```

### Docstrings

All public functions/classes should have docstrings:

```python
class MemoryManager:
    """
    Manages JEBAT's 5-layer memory system.
    
    Handles storage, retrieval, and consolidation
    of memories across different layers.
    """
    
    async def store(self, content: str, layer: str) -> Memory:
        """
        Store a memory in specified layer.
        
        Args:
            content: Memory content
            layer: Target layer (M0-M4)
            
        Returns:
            Stored Memory object
            
        Raises:
            ValueError: If layer is invalid
        """
        pass
```

### README Updates

When adding features, update:

- Main README.md
- Relevant documentation files
- Code examples
- API reference

---

## 📥 Pull Request Guidelines

### PR Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix (non-breaking change)
- [ ] New feature (non-breaking change)
- [ ] Breaking change (fix/feature causing existing functionality to break)
- [ ] Documentation update

## Testing
- [ ] Tests pass locally
- [ ] New tests added for new functionality
- [ ] Test coverage maintained or improved

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] No new warnings
- [ ] Tests pass locally
```

### Before Submitting

- [ ] Code is formatted (black, isort)
- [ ] Tests pass (`pytest tests/`)
- [ ] Linting passes (`flake8`, `mypy`)
- [ ] Documentation updated
- [ ] Commit messages are clear
- [ ] Branch is up to date with main

### Review Process

1. **Automated Checks** - CI/CD runs tests
2. **Code Review** - Maintainer reviews code
3. **Feedback** - Address any comments
4. **Approval** - PR is approved
5. **Merge** - Changes merged to main

---

## 🐛 Issue Guidelines

### Bug Report Template

```markdown
## Bug Description
Clear description of the bug

## To Reproduce
Steps to reproduce:
1. Run command '...'
2. See error

## Expected Behavior
What should happen

## Screenshots
If applicable

## Environment
- OS: [e.g., Windows 11]
- Python: [e.g., 3.11.5]
- JEBAT: [e.g., 2.0.0]

## Additional Context
Any other details
```

### Feature Request Template

```markdown
## Problem Statement
What problem does this solve?

## Proposed Solution
How should it work?

## Alternatives Considered
Other approaches

## Use Cases
Who will use this and how?

## Additional Context
Mockups, examples, etc.
```

---

## 🌟 Community

### Get Involved

- **GitHub Discussions** - Share ideas, ask questions
- **Discord Server** - Chat with community (coming soon)
- **Twitter** - Follow @JEBAT_AI (placeholder)
- **Blog** - Read tutorials and updates

### Recognition

Contributors are recognized in:

- **README.md** - Top contributors section
- **CONTRIBUTORS.md** - Full list of contributors
- **Release Notes** - Mentioned in changelog
- **Social Media** - Shoutouts on Twitter/Discord

---

## 📜 License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

## 🙏 Thank You!

Every contribution, no matter how small, helps make JEBAT better.

**Together, we're building the future of AI assistants!** 🗡️

---

**Questions?** Open an issue or join our discussions!
