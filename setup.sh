#!/bin/bash
# PacketBuddy - Root Setup Redirector

# Detect OS
OS="$(uname)"
if [ "$OS" == "Darwin" ]; then
    echo "Detected macOS. Launching setup..."
    chmod +x service/macos/setup.sh
    ./service/macos/setup.sh
elif [ "$OS" == "Linux" ]; then
    echo "Detected Linux. Launching setup..."
    chmod +x service/linux/setup.sh
    ./service/linux/setup.sh
else
    echo "Unsupported OS: $OS"
    exit 1
fi
