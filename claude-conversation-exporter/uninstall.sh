#!/bin/bash
# Claude Conversation Exporter - Uninstallation Script
# Removes hooks and commands installed by the exporter

set -e

echo "🗑️  Uninstalling Claude Conversation Exporter..."
echo ""

CLAUDE_DIR="$HOME/.claude"
HOOKS_DIR="$CLAUDE_DIR/hooks"
COMMANDS_DIR="$CLAUDE_DIR/commands"
CONFIG_FILE="$CLAUDE_DIR/conversation-export-config.json"
SETTINGS_FILE="$CLAUDE_DIR/settings.json"

# Remove scripts
echo "📝 Removing scripts..."
rm -f "$HOOKS_DIR/export-conversation.py"
rm -f "$HOOKS_DIR/export-current-session.sh"
rm -f "$COMMANDS_DIR/export-conversation.md"

# Ask about config
if [ -f "$CONFIG_FILE" ]; then
    read -p "Remove configuration file? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm -f "$CONFIG_FILE"
        echo "   Removed $CONFIG_FILE"
    else
        echo "   Keeping $CONFIG_FILE"
    fi
fi

# Remove ONLY our SessionEnd hook from settings.json (preserve other hooks)
echo "🔧 Removing conversation exporter hook from settings..."
if [ -f "$SETTINGS_FILE" ]; then
    python3 << 'EOF'
import json
import os

settings_file = os.path.expanduser("~/.claude/settings.json")

try:
    with open(settings_file, 'r') as f:
        settings = json.load(f)

    if 'hooks' in settings and 'SessionEnd' in settings['hooks']:
        # Filter out only our hook, keep others
        original_count = len(settings['hooks']['SessionEnd'])
        settings['hooks']['SessionEnd'] = [
            hook for hook in settings['hooks']['SessionEnd']
            if 'export-conversation.py' not in str(hook)
        ]
        new_count = len(settings['hooks']['SessionEnd'])

        # Remove empty SessionEnd array
        if not settings['hooks']['SessionEnd']:
            del settings['hooks']['SessionEnd']

        # Remove empty hooks section
        if not settings['hooks']:
            del settings['hooks']

        with open(settings_file, 'w') as f:
            json.dump(settings, f, indent=2)
            f.write('\n')

        if original_count > new_count:
            print("   Conversation exporter hook removed")
            if new_count > 0:
                print(f"   (kept {new_count} other SessionEnd hook(s))")
        else:
            print("   Hook not found in settings")
    else:
        print("   No SessionEnd hooks found")
except Exception as e:
    print(f"   Warning: Could not update settings.json: {e}")
EOF
fi

# Remove self
rm -f "$HOOKS_DIR/uninstall-conversation-exporter.sh"

echo ""
echo "✅ Uninstallation complete!"
echo ""
echo "Notes:"
echo "  • Existing conversation exports in your projects are preserved."
echo "    Delete them manually if needed: rm -rf <project>/artifacts/conversations/"
echo ""
echo "  • Backups of your original settings are in: ~/.claude/backups/"
echo "    To restore: cp ~/.claude/backups/settings.json.backup_* ~/.claude/settings.json"
echo ""
