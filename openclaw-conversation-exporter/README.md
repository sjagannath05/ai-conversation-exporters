# OpenClaw Conversation Exporter

Export your [OpenClaw](https://github.com/openclaw/openclaw) agent conversations to beautiful, self-contained HTML files.

![OpenClaw](https://img.shields.io/badge/OpenClaw-Compatible-green)

## Features

- **Self-contained HTML** — no external dependencies, open anywhere
- **Auto dark/light theme** — adapts to system preference with one-click toggle
- **Collapsible tool calls** — see tool usage without clutter
- **Session statistics** — message counts, timestamps, agent info
- **Multi-agent support** — exports from all configured agents (main, subagents, etc.)
- **Date filtering** — export all sessions or just today's
- **Agent filtering** — export specific agent's sessions only
- **No dependencies** — pure Python 3, nothing to install

## Installation

```bash
cd openclaw-conversation-exporter
./install.sh
```

This installs `openclaw-export` to `~/.local/bin/`.

## Usage

```bash
# Export all sessions
openclaw-export

# Export today's sessions
openclaw-export --since today

# Export since a specific date
openclaw-export --since 2026-02-10

# Export specific agent only
openclaw-export --agent go-tester-v2

# Custom output directory
openclaw-export --output ~/Documents/conversations
```

## Output

Sessions are exported to `~/openclaw-export/{agent}/{session-id}.html`:

```
~/openclaw-export/
├── main/
│   ├── a36ff9c4-49f4-423b-94b5-67c269295f7a.html
│   └── f09ba930-4bc3-4022-93c2-c274a62e4b4f.html
├── go-architect/
│   └── ae13d42a-d373-4d44-9b9d-0a70f26bc934.html
└── go-tester-v2/
    └── ...
```

Each HTML file includes:
- Session metadata (agent, session ID, timestamps)
- Message count statistics
- Full conversation with user/assistant messages
- Collapsible tool call details with arguments
- Responsive dark/light theme

## Automation

### OpenClaw Cron (recommended)

Add a daily export job via OpenClaw:

```json
{
  "name": "openclaw-export-daily",
  "schedule": { "kind": "cron", "expr": "0 23 * * *", "tz": "Asia/Calcutta" },
  "payload": { "kind": "agentTurn", "message": "Run openclaw-export --since today" },
  "sessionTarget": "isolated",
  "delivery": { "mode": "none" }
}
```

### macOS launchd

```bash
# Create a launchd plist for daily exports at 11 PM
cat > ~/Library/LaunchAgents/com.openclaw.export.plist << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key><string>com.openclaw.export</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/python3</string>
        <string>~/.local/bin/openclaw-export</string>
        <string>--since</string>
        <string>today</string>
    </array>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key><integer>23</integer>
        <key>Minute</key><integer>0</integer>
    </dict>
</dict>
</plist>
EOF
launchctl load ~/Library/LaunchAgents/com.openclaw.export.plist
```

## Configuration

Edit `~/.claude/conversation-export-config.json`:

```json
{
  "user_name": "Your Name",
  "assistant_name": "OpenClaw",
  "user_emoji": "👤",
  "assistant_emoji": "🤖",
  "theme": "auto",
  "generate_summary": true,
  "show_statistics": true,
  "include_thinking": false,
  "central_export_location": "~/openclaw-export"
}
```

## OpenClaw Skill

This exporter also works as an OpenClaw skill. See [SKILL.md](SKILL.md) for integration details.

## How It Works

1. Reads OpenClaw's JSONL session transcripts from `~/.openclaw/agents/*/sessions/`
2. Parses the OpenClaw message format (type: "message" → message.role + message.content)
3. Generates self-contained HTML with embedded CSS and dark/light theme support
4. Organizes exports by agent name

## License

MIT
