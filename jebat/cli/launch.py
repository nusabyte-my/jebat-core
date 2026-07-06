#!/usr/bin/env python3
"""
JEBAT CLI Launcher

Run JEBAT from the command line.

Usage:
    py -m jebat.cli.launch status
    py -m jebat.cli.launch loop start
    py -m jebat.cli.launch think "What is AI?"
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from jebat.cli.jebat_cli import main as cli_main

if __name__ == "__main__":
    result = asyncio.run(cli_main())
    sys.exit(result if result else 0)
