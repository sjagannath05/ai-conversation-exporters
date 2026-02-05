#!/bin/bash
# Claude Conversation Exporter - Installation Script
# Installs hooks and commands for automatic conversation export

set -e

echo "🚀 Installing Claude Conversation Exporter..."
echo ""

# Determine script directory (works for both local and curl installs)
if [ -n "$BASH_SOURCE" ] && [ -f "${BASH_SOURCE[0]}" ]; then
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
else
    # Running from curl - download files to temp directory
    SCRIPT_DIR=$(mktemp -d)
    echo "📥 Downloading files..."

    BASE_URL="https://raw.githubusercontent.com/YOUR_USERNAME/claude-conversation-exporter/main"
    curl -fsSL "$BASE_URL/export-conversation.py" -o "$SCRIPT_DIR/export-conversation.py"
    curl -fsSL "$BASE_URL/export-current-session.sh" -o "$SCRIPT_DIR/export-current-session.sh"
    curl -fsSL "$BASE_URL/export-conversation.md" -o "$SCRIPT_DIR/export-conversation.md"
    curl -fsSL "$BASE_URL/config.example.json" -o "$SCRIPT_DIR/config.example.json"
    curl -fsSL "$BASE_URL/uninstall.sh" -o "$SCRIPT_DIR/uninstall.sh"
fi

# Define paths
CLAUDE_DIR="$HOME/.claude"
HOOKS_DIR="$CLAUDE_DIR/hooks"
COMMANDS_DIR="$CLAUDE_DIR/commands"
CONFIG_FILE="$CLAUDE_DIR/conversation-export-config.json"
SETTINGS_FILE="$CLAUDE_DIR/settings.json"

# Create directories
echo "📁 Creating directories..."
mkdir -p "$HOOKS_DIR"
mkdir -p "$COMMANDS_DIR"

# Copy scripts
echo "📝 Installing scripts..."
cp "$SCRIPT_DIR/export-conversation.py" "$HOOKS_DIR/"
cp "$SCRIPT_DIR/export-current-session.sh" "$HOOKS_DIR/"
chmod +x "$HOOKS_DIR/export-current-session.sh"

# Copy command definition
cp "$SCRIPT_DIR/export-conversation.md" "$COMMANDS_DIR/"

# Copy uninstall script
cp "$SCRIPT_DIR/uninstall.sh" "$HOOKS_DIR/uninstall-conversation-exporter.sh"
chmod +x "$HOOKS_DIR/uninstall-conversation-exporter.sh"

# Create config if not exists
if [ ! -f "$CONFIG_FILE" ]; then
    echo "⚙️  Creating default configuration..."
    cp "$SCRIPT_DIR/config.example.json" "$CONFIG_FILE"
    echo "   Edit $CONFIG_FILE to customize names and theme"
fi

# Detect Python path
if command -v python3 &> /dev/null; then
    PYTHON_PATH=$(which python3)
elif command -v python &> /dev/null; then
    PYTHON_PATH=$(which python)
else
    echo "⚠️  Warning: Python not found. Please install Python 3."
    PYTHON_PATH="python3"
fi

# Backup existing settings.json before modifying
echo "💾 Backing up existing configuration..."
BACKUP_DIR="$CLAUDE_DIR/backups"
mkdir -p "$BACKUP_DIR"
BACKUP_TIMESTAMP=$(date +%Y%m%d_%H%M%S)

if [ -f "$SETTINGS_FILE" ]; then
    cp "$SETTINGS_FILE" "$BACKUP_DIR/settings.json.backup_$BACKUP_TIMESTAMP"
    echo "   Backed up settings.json to $BACKUP_DIR/settings.json.backup_$BACKUP_TIMESTAMP"
fi

if [ -f "$CONFIG_FILE" ]; then
    cp "$CONFIG_FILE" "$BACKUP_DIR/conversation-export-config.json.backup_$BACKUP_TIMESTAMP"
    echo "   Backed up existing config to $BACKUP_DIR/"
fi

# Update settings.json to add SessionEnd hook
echo "🔧 Configuring SessionEnd hook..."

if [ -f "$SETTINGS_FILE" ]; then
    # Check if hooks section exists and SessionEnd is configured
    if grep -q '"SessionEnd"' "$SETTINGS_FILE" 2>/dev/null; then
        echo "   SessionEnd hook already configured, skipping..."
    else
        # Use Python to safely modify JSON
        python3 << EOF
import json
import os

settings_file = "$SETTINGS_FILE"
hooks_dir = "$HOOKS_DIR"
python_path = "$PYTHON_PATH"

with open(settings_file, 'r') as f:
    settings = json.load(f)

# Add hooks section if not exists
if 'hooks' not in settings:
    settings['hooks'] = {}

# Add SessionEnd hook - new format with matcher string and hooks array
new_hook = {
    "matcher": "",
    "hooks": [
        {
            "type": "command",
            "command": f"{python_path} {hooks_dir}/export-conversation.py"
        }
    ]
}

if 'SessionEnd' not in settings['hooks']:
    settings['hooks']['SessionEnd'] = [new_hook]
else:
    # Check if our hook already exists
    our_command = f"{hooks_dir}/export-conversation.py"
    hook_exists = any(
        our_command in str(hook)
        for hook in settings['hooks']['SessionEnd']
    )
    if not hook_exists:
        settings['hooks']['SessionEnd'].append(new_hook)

with open(settings_file, 'w') as f:
    json.dump(settings, f, indent=2)
    f.write('\n')

print("   Hook configured successfully")
EOF
    fi
else
    # Create new settings file with new hook format
    cat > "$SETTINGS_FILE" << EOF
{
  "\$schema": "https://json.schemastore.org/claude-code-settings.json",
  "hooks": {
    "SessionEnd": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "$PYTHON_PATH $HOOKS_DIR/export-conversation.py"
          }
        ]
      }
    ]
  }
}
EOF
    echo "   Created settings.json with SessionEnd hook"
fi

# Cleanup temp directory if used
if [ "$SCRIPT_DIR" != "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd 2>/dev/null)" ]; then
    rm -rf "$SCRIPT_DIR"
fi

echo ""
echo "✅ Installation complete!"
echo ""
echo "📖 Usage:"
echo "   • Conversations auto-export when you exit Claude Code (Ctrl+C, /exit)"
echo "   • Manual export: /export-conversation"
echo ""
echo "⚙️  Configuration:"
echo "   Edit: $CONFIG_FILE"
echo ""
echo "🗑️  To uninstall:"
echo "   $HOOKS_DIR/uninstall-conversation-exporter.sh"
echo ""
