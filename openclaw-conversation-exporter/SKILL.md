---
name: openclaw-export
description: Export OpenClaw conversations to beautiful HTML files with dark/light themes, syntax highlighting, and session statistics.
author: Jagannath S
version: 1.0.0
metadata:
  short-description: Export OpenClaw sessions to HTML
---

# OpenClaw Conversation Exporter

Export your OpenClaw agent conversations to self-contained HTML files with dark/light theme support, collapsible tool calls, and session statistics.

## Quick Use

```bash
# Export all sessions
python3 <skill-dir>/scripts/export_openclaw_sessions.py

# Export today's sessions only
python3 <skill-dir>/scripts/export_openclaw_sessions.py --since today

# Export specific agent's sessions
python3 <skill-dir>/scripts/export_openclaw_sessions.py --agent go-tester-v2

# Export since a date
python3 <skill-dir>/scripts/export_openclaw_sessions.py --since 2026-02-10
```

## Options

| Flag | Description | Default |
|------|-------------|---------|
| `--since` | Export sessions modified since date (`YYYY-MM-DD` or `today`) | All sessions |
| `--agent` | Filter by agent name | All agents |
| `--output` | Output directory | `~/openclaw-export` |

## Output

- **Location**: `~/openclaw-export/{agent}/{session-id}.html`
- **Format**: Self-contained HTML with embedded CSS
- **Theme**: Auto dark/light based on system preference
- **Features**: Collapsible tool calls, message stats, timestamps

## Automation

Set up a daily cron job to export conversations automatically:

```
Schedule: 0 23 * * * (11 PM daily)
Task: openclaw-export --since today
```

Or via OpenClaw cron:
```json
{
  "name": "openclaw-export-daily",
  "schedule": {"kind": "cron", "expr": "0 23 * * *", "tz": "Asia/Calcutta"},
  "payload": {"kind": "agentTurn", "message": "Run openclaw-export --since today"},
  "sessionTarget": "isolated"
}
```

## Notes

- Parses OpenClaw's native JSONL session format (`~/.openclaw/agents/*/sessions/*.jsonl`)
- Skips compaction topic files automatically
- Each agent's sessions are organized in separate subdirectories
- No external dependencies — pure Python 3
