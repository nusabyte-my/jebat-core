"""
🗡️ JEBAT DevAssistant - Main Entry Point

Usage:
    python -m jebat_dev.gateway              # Interactive mode
    python -m jebat_dev.gateway "command"    # Single command
    python -m jebat_dev.gateway -i           # Force interactive
"""

import sys

from .interactive_cli import main

if __name__ == "__main__":
    main()
