#!/bin/bash
# This script runs if "wifi" is found in the error log
echo "🔄 Running Custom WiFi Reset Hook..."
nmcli radio wifi off
sleep 1
nmcli radio wifi on
echo "✅ WiFi Reset Complete."