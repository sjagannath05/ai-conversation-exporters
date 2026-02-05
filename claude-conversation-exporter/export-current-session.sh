#!/bin/bash
# Export current Claude Code session to artifacts/conversations/
# Usage: export-current-session.sh [project_dir]

set -e

PROJECT_DIR="${1:-$(pwd)}"
ENCODED_PATH=$(echo "$PROJECT_DIR" | tr '/' '-')
SESSIONS_DIR="$HOME/.claude/projects/$ENCODED_PATH"

if [ ! -d "$SESSIONS_DIR" ]; then
    echo "Error: No sessions found for project: $PROJECT_DIR"
    echo "Sessions dir checked: $SESSIONS_DIR"
    exit 1
fi

# Find the most recently modified session file
LATEST_SESSION=$(ls -t "$SESSIONS_DIR"/*.jsonl 2>/dev/null | head -1)

if [ -z "$LATEST_SESSION" ]; then
    echo "Error: No session files found in $SESSIONS_DIR"
    exit 1
fi

# Extract session ID from filename
SESSION_ID=$(basename "$LATEST_SESSION" .jsonl)

echo "Exporting session: $SESSION_ID"
echo "From: $LATEST_SESSION"
echo "To: $PROJECT_DIR/artifacts/conversations/"

# Determine Python path (prefer system python3, fall back to python)
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
else
    echo "Error: Python not found. Please install Python 3."
    exit 1
fi

# Find the export script
SCRIPT_DIR="$HOME/.claude/hooks"
EXPORT_SCRIPT="$SCRIPT_DIR/export-conversation.py"

if [ ! -f "$EXPORT_SCRIPT" ]; then
    echo "Error: Export script not found at $EXPORT_SCRIPT"
    echo "Please run the install script first."
    exit 1
fi

# Run the export script
echo "{\"session_id\": \"$SESSION_ID\", \"transcript_path\": \"$LATEST_SESSION\", \"cwd\": \"$PROJECT_DIR\", \"hook_event_name\": \"ManualExport\", \"reason\": \"manual\"}" | "$PYTHON_CMD" "$EXPORT_SCRIPT"
