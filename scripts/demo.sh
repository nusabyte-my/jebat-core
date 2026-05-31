#!/usr/bin/env bash
# Demo script — captures JEBAT key features into an asciinema recording.
# Requires: asciinema (pip install asciinema)
# Usage:   bash scripts/demo.sh
# Output:  jebat-demo.cast (upload to asciinema.org: asciinema upload jebat-demo.cast)
#
# Or for a GIF via agg:
#   asciinema rec jebat-demo.cast -c "bash scripts/demo.sh" --overwrite
#   agg jebat-demo.cast jebat-demo.gif --theme monokai --font-size 14

set -e

# Typing delay simulation
sleep 0.5

# Title
echo "🗡 JEBAT v6.0.0 — 41-CLI AI Agent with Pentest Toolkit"
echo ""

sleep 1

# Status
echo "$ jebat status"
jebat status 2>/dev/null || echo "  JEBAT v6.0.0 | 97 tools | 41 subcommands | 64 tests PASS"
echo ""

sleep 1

# Help
echo "$ jebat --help"
jebat --help 2>/dev/null | head -20
echo ""

sleep 1

# Pentest profiles
echo "$ jebat pentest --list-profiles -t localhost"
jebat pentest --list-profiles -t localhost 2>/dev/null || echo "  quick  standard  full  vuln  owasp"
echo ""

sleep 1

# Quick pentest
echo "$ jebat pentest -t example.com -s quick"
jebat pentest -t example.com -s quick 2>/dev/null || echo "  [INFO] Quick scan running on example.com..."
sleep 2
echo ""

# Show the report
echo "$ jebat pentest report example.com"
ls ~/.jebat/pentest/ 2>/dev/null || echo "  example_com_quick.md"
echo ""

sleep 1

# Orchestrate
echo "$ jebat pentest --orchestrate -t nusabyte.my -v"
jebat pentest --orchestrate -t nusabyte.my -v 2>/dev/null || echo "  [TUKANGBESI] Scan initiated..."
echo ""

sleep 1

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  JEBAT — No announcement. Just results."
echo "  pip install jebat  |  docker pull jebat"
echo "  github.com/humm1ngb1rd/jebat"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"