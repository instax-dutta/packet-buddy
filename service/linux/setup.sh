#!/bin/bash

# PacketBuddy Linux Service Installer
# Installs a user-level Systemd service for network monitoring

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${PURPLE}═══════════════════════════════════════════════════${NC}"
echo -e "${PURPLE}  PacketBuddy - Linux Service Installer${NC}"
echo -e "${PURPLE}═══════════════════════════════════════════════════${NC}"
echo ""

# Get directory where script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/../.." && pwd )"

# Step 1: Check Python
echo -e "${YELLOW}[1/6]${NC} Checking Python installation..."
PYTHON_PATH=$(which python3)
if [ -z "$PYTHON_PATH" ]; then
    echo -e "${RED}❌ Python 3 not found. Please install Python 3.11+ first.${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Python found: $PYTHON_PATH${NC}"

# Step 2: Virtual Environment
echo -e "${YELLOW}[2/6]${NC} Setting up virtual environment..."
cd "$PROJECT_ROOT"
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo -e "${GREEN}✓ Virtual environment created${NC}"
else
    echo -e "${CYAN}ℹ️  Virtual environment already exists${NC}"
fi

# Step 3: Dependencies
echo -e "${YELLOW}[3/6]${NC} Installing dependencies..."
./venv/bin/pip install --quiet --upgrade pip
./venv/bin/pip install --quiet -r requirements.txt
echo -e "${GREEN}✓ Dependencies installed${NC}"

# Step 4: Configuration
echo -e "${YELLOW}[4/6]${NC} Setting up configuration..."
mkdir -p "$HOME/.packetbuddy"
if [ ! -f "$HOME/.packetbuddy/config.toml" ]; then
    cp config.example.toml "$HOME/.packetbuddy/config.toml"
    echo -e "${GREEN}✓ Configuration file created${NC}"
fi

# Initialize database
./venv/bin/python -c "from src.core.storage import storage; storage.get_device_id()" >/dev/null 2>&1
echo -e "${GREEN}✓ Database initialized${NC}"

# Step 5: Systemd Service
echo -e "${YELLOW}[5/6]${NC} Configuring systemd service..."
SERVICE_PATH="$HOME/.config/systemd/user/packetbuddy.service"
mkdir -p "$(dirname "$SERVICE_PATH")"

# Replace placeholders in template
# Note: We use the venv python for the service
VENV_PYTHON="$PROJECT_ROOT/venv/bin/python"
sed "s|{{PROJECT_ROOT}}|$PROJECT_ROOT|g; s|{{PYTHON_PATH}}|$VENV_PYTHON|g; s|{{HOME}}|$HOME|g" \
    "$SCRIPT_DIR/packetbuddy.service.template" > "$SERVICE_PATH"

echo -e "${GREEN}✓ Systemd service file created at $SERVICE_PATH${NC}"

# Reload systemd and enable service
echo -e "${YELLOW}[6/6]${NC} Starting service..."
systemctl --user daemon-reload
systemctl --user enable packetbuddy.service
systemctl --user restart packetbuddy.service

echo ""
echo -e "${GREEN}═══════════════════════════════════════════════════${NC}"
echo -e "${GREEN}  ✓ PacketBuddy installed successfully!${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════${NC}"
echo ""
echo -e "${CYAN}Dashboard: http://127.0.0.1:7373/dashboard${NC}"
echo ""
echo -e "${YELLOW}To check status:${NC}"
echo "  systemctl --user status packetbuddy.service"
echo ""
echo -e "${YELLOW}To see logs:${NC}"
echo "  tail -f \$HOME/.packetbuddy/stderr.log"
echo ""
