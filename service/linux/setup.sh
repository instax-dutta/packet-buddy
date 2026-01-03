#!/bin/bash

# PacketBuddy Linux Service Installer
# Installs a user-level Systemd service for network monitoring

set -e

echo "═══════════════════════════════════════════════════"
echo "  PacketBuddy - Linux Service Installer"
echo "═══════════════════════════════════════════════════"
echo ""

# Get directory where script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/../.." && pwd )"

# Check if Python is installed
PYTHON_PATH=$(which python3)
if [ -z "$PYTHON_PATH" ]; then
    echo "❌ Python 3 not found. Please install Python 3.11+ first."
    exit 1
fi

echo "✓ Python found: $PYTHON_PATH"
echo "✓ Project root: $PROJECT_ROOT"

# Create logs directory
mkdir -p "$HOME/.packetbuddy"

# Prepare Systemd service file
SERVICE_PATH="$HOME/.config/systemd/user/packetbuddy.service"
mkdir -p "$(dirname "$SERVICE_PATH")"

# Replace placeholders in template
sed "s|{{PROJECT_ROOT}}|$PROJECT_ROOT|g; s|{{PYTHON_PATH}}|$PYTHON_PATH|g; s|{{HOME}}|$HOME|g" \
    "$SCRIPT_DIR/packetbuddy.service.template" > "$SERVICE_PATH"

echo "✓ Systemd service file created at $SERVICE_PATH"

# Reload systemd and enable service
systemctl --user daemon-reload
systemctl --user enable packetbuddy.service
systemctl --user restart packetbuddy.service

echo ""
echo "═══════════════════════════════════════════════════"
echo "  ✓ PacketBuddy installed successfully!"
echo "═══════════════════════════════════════════════════"
echo ""
echo "Dashboard: http://127.0.0.1:7373/dashboard"
echo ""
echo "To check status:"
echo "  systemctl --user status packetbuddy.service"
echo ""
echo "To see logs:"
echo "  tail -f \$HOME/.packetbuddy/stdout.log"
echo ""
