#!/bin/bash
# generate-og-image.sh — Generate OG image for jebat.online
# Requires: python3 with Pillow installed
# Output: /var/www/jebat.online/og-image.png

set -e

OUTPUT="${1:-/var/www/jebat.online/og-image.png}"
WIDTH=1200
HEIGHT=630

python3 - "$WIDTH" "$HEIGHT" "$OUTPUT" << 'PY'
from PIL import Image, ImageDraw, ImageFont
import os, sys

W = int(sys.argv[1])
H = int(sys.argv[2])
OUT = sys.argv[3]

img = Image.new('RGB', (W, H), color=(3, 3, 3))
draw = ImageDraw.Draw(img)

# Accent bar at top
draw.rectangle([0, 0, W, 4], fill=(0, 240, 255))

# Grid lines (subtle)
for x in range(0, W, 60):
    draw.line([(x, 0), (x, H)], fill=(15, 15, 25), width=1)
for y in range(0, H, 60):
    draw.line([(0, y), (W, y)], fill=(15, 15, 25), width=1)

# Terminal frame
margin = 60
draw.rectangle(
    [margin, margin, W - margin, H - margin],
    outline=(26, 26, 36), width=2
)

# Title
try:
    font_title = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 56)
    font_body = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 24)
    font_mono = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 18)
except:
    font_title = ImageFont.load_default()
    font_body = ImageFont.load_default()
    font_mono = ImageFont.load_default()

draw.text((100, 110), "JEBAT v7.5", fill=(0, 240, 255), font=font_title)
draw.text((100, 190), "Sovereign AI Platform", fill=(200, 200, 200), font=font_body)

# Product list
products = [
    ("JEBAT Core", "Hang Jebat", "Inference Router + Multi-Agent Swarm"),
    ("Sentinel", "Keris", "Autonomous Security Orchestrator"),
    ("Developer Suite", "Pandai", "MCP-Native Dev Environment"),
    ("Companion", "Sahabat", "Conversational AI with Memory"),
    ("Nexus", "Perisai", "Multi-Channel Bot Orchestrator"),
]
y = 260
for name, code, desc in products:
    draw.text((100, y), f"  {name}", fill=(0, 240, 255), font=font_body)
    draw.text((360, y), f"{desc}", fill=(140, 140, 160), font=font_body)
    y += 40

# Bottom bar
draw.rectangle([margin, H - 80, W - margin, H - margin], outline=(26, 26, 36), width=1)
draw.text((100, H - 64), "npx @nusabyte/jebat  |  47 MCP Tools  |  17 Providers  |  MIT License", fill=(80, 80, 100), font=font_mono)

os.makedirs(os.path.dirname(OUT), exist_ok=True)
img.save(OUT)
print(f"OG image saved: {OUT}  ({W}x{H})")
PY
