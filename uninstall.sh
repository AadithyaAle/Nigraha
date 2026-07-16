#!/usr/bin/env bash
set -e

echo "🗑️ Uninstalling StackSentinel..."
sudo python3 -m pip uninstall -y stacksentinel --break-system-packages || true
echo "✅ Global StackSentinel package removed."
