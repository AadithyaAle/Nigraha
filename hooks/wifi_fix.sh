#!/usr/bin/env bash
set -e

echo "🔄 Running custom Wi-Fi reset hook..."
nmcli radio wifi off
sleep 1
nmcli radio wifi on
echo "✅ Wi-Fi reset complete."
