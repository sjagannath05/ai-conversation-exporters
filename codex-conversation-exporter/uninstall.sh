#!/bin/bash
# Codex Conversation Exporter - Uninstall Script

set -e

CODEX_DIR="$HOME/.codex"
TARGET_DIR="$CODEX_DIR/skills/codex-export"

if [ -d "$TARGET_DIR" ]; then
  rm -rf "$TARGET_DIR"
  echo "Removed skill: $TARGET_DIR"
else
  echo "Skill not found: $TARGET_DIR"
fi

echo "Config preserved at $CODEX_DIR/conversation-export-config.json"
