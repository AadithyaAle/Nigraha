#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

echo "🚀 Installing StackSentinel..."
sudo apt-get update
sudo apt-get install -y python3 python3-pip git espeak libnotify-bin

echo "📥 Installing Python package globally..."
sudo python3 -m pip install . --break-system-packages

echo "🔧 Marking built-in hooks as executable..."
chmod +x hooks/*.sh

echo "✅ Installation complete."
echo "Run 'stacksentinel --help' to get started."
echo "Before using AI diagnosis, set your API key:"
echo "export OPENAI_API_KEY='your_api_key_here'"
