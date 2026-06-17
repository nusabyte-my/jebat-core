#!/usr/bin/env bash
# 🗡️ JEBAT llama.cpp Build Script

set -e

LLAMA_DIR="llama.cpp"
BUILD_DIR="$LLAMA_DIR/build"

echo "🗡️ Building llama.cpp with JEBAT improvements..."

mkdir -p "$BUILD_DIR"
cd "$BUILD_DIR"

# Configure
cmake .. -DLLAMA_BUILD_EXAMPLES=ON

# Build jebat-bench and core llama.cpp
make -j$(nproc) jebat-bench llama-cli llama-server

echo ""
echo "✅ Build complete!"
echo "📍 Binaries located in: $BUILD_DIR/bin/"
echo "🚀 Try running: ./$BUILD_DIR/bin/jebat-bench --help"
