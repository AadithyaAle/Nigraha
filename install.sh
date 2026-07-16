#!/bin/bash

echo "🚀 Initiating StackSentinel Installation..."
APP_DIR=$(pwd)

echo "📦 Setting up Python Virtual Environment..."
python3 -m venv venv
source venv/bin/activate

echo "🔊 Installing Linux Audio Dependencies..."
sudo apt-get update && sudo apt-get install -y espeak alsa-utils

echo "📥 Installing dependencies and native CLI tools..."
pip install -r requirements.txt
pip install .

echo "🔗 Linking commands to global system path..."
# This makes the commands work in ANY terminal instantly
sudo ln -sf "$APP_DIR/venv/bin/stacksentinel" /usr/local/bin/stacksentinel
sudo ln -sf "$APP_DIR/venv/bin/stacksentinel-ui" /usr/local/bin/stacksentinel-ui

echo "✅ Installation Complete!"
echo "------------------------------------------------------"
echo "🛡️  StackSentinel is now installed as a native global app."
echo "💻 You can now safely open a new terminal and run 'stacksentinel'."
echo "------------------------------------------------------"