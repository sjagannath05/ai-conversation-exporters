# Export Current Conversation

Export the current session conversation to a human-readable HTML file.

## Instructions

Run this command to export the current session:

```bash
~/.claude/hooks/export-current-session.sh "$(pwd)"
```

This will:
1. Find the most recent session for the current project
2. Export it to `<project>/artifacts/conversations/` as:
   - Human-readable HTML (`.html`)
   - Raw JSONL for resuming (`.jsonl`)
3. Update the sessions index

After running, confirm to the user where the files were saved.
