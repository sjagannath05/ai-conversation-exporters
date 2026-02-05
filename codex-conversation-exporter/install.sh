#!/bin/bash
# Codex Conversation Exporter - Installation Script

set -e

echo "Installing Codex Conversation Exporter..."

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CODEX_DIR="$HOME/.codex"
SKILLS_DIR="$CODEX_DIR/skills"
TARGET_DIR="$SKILLS_DIR/codex-export"
CONFIG_FILE="$CODEX_DIR/conversation-export-config.json"
BACKUP_DIR="$CODEX_DIR/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

mkdir -p "$TARGET_DIR/scripts"
mkdir -p "$BACKUP_DIR"

if [ -d "$TARGET_DIR" ]; then
  cp -R "$TARGET_DIR" "$BACKUP_DIR/codex-export.backup_$TIMESTAMP"
  echo "Backed up existing skill to $BACKUP_DIR/codex-export.backup_$TIMESTAMP"
fi

if [ -f "$CONFIG_FILE" ]; then
  cp "$CONFIG_FILE" "$BACKUP_DIR/conversation-export-config.json.backup_$TIMESTAMP"
  echo "Backed up existing config to $BACKUP_DIR/conversation-export-config.json.backup_$TIMESTAMP"
fi

cp "$SCRIPT_DIR/SKILL.md" "$TARGET_DIR/SKILL.md"
cp "$SCRIPT_DIR/export_codex_session.py" "$TARGET_DIR/scripts/export_codex_session.py"
chmod +x "$TARGET_DIR/scripts/export_codex_session.py"

if [ ! -f "$CONFIG_FILE" ]; then
  cat > "$CONFIG_FILE" << 'CONFIG'
{
  "user_name": "Jagannath",
  "assistant_name": "Jagan's coding partner",
  "user_emoji": "👤",
  "assistant_emoji": "🤖",
  "theme": "auto",
  "custom_colors": {
    "_comment": "Optimized for readability",
    "text_color": "#e8eaed",
    "text_muted": "#9aa0a6",
    "bg_color": "#202124",
    "card_bg": "#292a2d",
    "user_bg": "#1a3a5c",
    "claude_bg": "#2d2e31",
    "accent": "#8ab4f8",
    "accent_soft": "#c58af9",
    "border_color": "#3c4043",
    "code_bg": "#1a1a1d",
    "tool_bg": "#25262a"
  },
  "generate_summary": true,
  "show_summary": true,
  "show_session_id": true,
  "show_project_path": true,
  "show_timestamp": true
}
CONFIG
  echo "Created config at $CONFIG_FILE"
fi

echo ""
echo "Installation complete."
echo "Restart Codex to see $codex-export in /skills."
echo ""
