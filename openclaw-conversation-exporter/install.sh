#!/bin/bash
# Install OpenClaw Conversation Exporter
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
INSTALL_DIR="${HOME}/.local/bin"
SCRIPT_NAME="openclaw-export"

echo "🤖 Installing OpenClaw Conversation Exporter..."

# Create install directory
mkdir -p "$INSTALL_DIR"

# Copy export script
cp "$SCRIPT_DIR/scripts/export_openclaw_sessions.py" "$INSTALL_DIR/$SCRIPT_NAME"
chmod +x "$INSTALL_DIR/$SCRIPT_NAME"

# Create default config if it doesn't exist
CONFIG_DIR="${HOME}/.claude"
CONFIG_FILE="$CONFIG_DIR/conversation-export-config.json"
if [ ! -f "$CONFIG_FILE" ]; then
    mkdir -p "$CONFIG_DIR"
    cp "$SCRIPT_DIR/config.example.json" "$CONFIG_FILE"
    echo "  Created config at $CONFIG_FILE"
fi

# Create export directory
mkdir -p "${HOME}/openclaw-export"

echo ""
echo "✅ Installed! Usage:"
echo "   $SCRIPT_NAME                    # Export all sessions"
echo "   $SCRIPT_NAME --since today      # Export today's sessions"
echo "   $SCRIPT_NAME --agent main       # Export specific agent"
echo ""
echo "Make sure $INSTALL_DIR is in your PATH."
