"""
🗡️ JEBAT DevAssistant - Interactive Launcher

Launch the interactive DevAssistant CLI.

Usage:
    py -m jebat_dev.launch                    # Interactive mode
    py -m jebat_dev.launch "command"          # Single command
    py -m jebat_dev.launch -i                 # Force interactive

Or directly:
    jebat [command] [options]
"""

import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from jebat_dev.gateway.interactive_cli import main

if __name__ == "__main__":
    main()
