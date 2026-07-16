#!/bin/bash

echo "🗑️ Uninstalling StackSentinel..."

# Remove the global symlinks
sudo rm -f /usr/local/bin/stacksentinel
sudo rm -f /usr/local/bin/stacksentinel-ui

# Remove the virtual environment
rm -rf venv

echo "✅ Virtual environment and global CLI links safely removed."