# AI Conversation Exporters

A collection of tools to export conversations from AI coding assistants to beautiful, readable HTML files with syntax highlighting, collapsible tool details, and session statistics.

## Supported Platforms

| Tool | AI Assistant | Export Method |
|------|--------------|---------------|
| [Claude Conversation Exporter](./claude-conversation-exporter/) | Claude Code CLI | **Automatic** (SessionEnd hook) + Manual |
| [Codex Conversation Exporter](./codex-conversation-exporter/) | OpenAI Codex CLI | **Manual** (skill/CLI) |
| [OpenClaw Conversation Exporter](./openclaw-conversation-exporter/) | OpenClaw Agents | **Manual** + Cron automation |

### Feature Comparison

| Feature | Claude | Codex | OpenClaw |
|---------|:------:|:-----:|:--------:|
| Auto-export on session end | Yes | - | Cron |
| Manual export command | `/export-conversation` | `$codex-export` | `openclaw-export` |
| Batch export all sessions | Yes | - | Yes |
| Output formats | HTML | MD, HTML, or both | HTML |
| Multi-agent support | - | - | Yes |
| Session resumption tracking | Yes | - | - |
| Session index file | Yes | - | - |
| Token usage statistics | Yes | Yes | Yes |
| 10 built-in themes | Yes | Yes | Auto dark/light |

## Features

Both exporters share a consistent feature set:

- **Beautiful HTML exports** with syntax highlighting and responsive design
- **10 built-in themes** - Auto, Dark, Light, Solarized, Monokai, Dracula, Nord, GitHub
- **Dark/Light toggle** - Switch themes with one click (preference saved in browser)
- **Auto-generated summaries** - Intelligent conversation summarization from keywords
- **Session statistics** - Duration, message counts, token usage, tool breakdown
- **Per-message token stats** - See input/output tokens on each assistant response
- **Collapsible tool sections** - See what tools were used without clutter
- **Print-friendly** - Clean output when printing (hides interactive elements)
- **25+ configuration options** - Names, labels, emojis, colors, typography, and more
- **Central or per-project exports** - Choose where to store conversations

### Claude-Specific Features

- **Session deduplication** - Updates existing exports instead of creating duplicates
- **Session continuity** - Preserves original creation date when resuming sessions
- **Batch export** - Export all historical sessions with filtering options
- **Session index** - Maintains `sessions_index.md` for easy browsing

## Quick Start

### Claude Code CLI

```bash
cd claude-conversation-exporter
./install.sh
```

Conversations **auto-export** when you exit Claude Code (`Ctrl+C`, `/exit`). You can also manually export anytime with `/export-conversation`.

**Batch export** all historical sessions:

```bash
python claude-conversation-exporter/export-all-sessions.py --list        # List sessions
python claude-conversation-exporter/export-all-sessions.py --skip-existing  # Export new only
```

### OpenAI Codex CLI

```bash
cd codex-conversation-exporter
./install.sh
```

**Manual export only** - use the skill in Codex:

```
$codex-export
```

Or run directly from CLI:

```bash
python3 ~/.codex/skills/codex-export/scripts/export_codex_session.py --latest
```

Options: `--format md|html|both`, `--output <dir>`, `--session <id|path>`

## Configuration

Both tools use JSON configuration files for customization:

| Tool | Config Location |
|------|-----------------|
| Claude | `~/.claude/conversation-export-config.json` |
| Codex | `~/.codex/conversation-export-config.json` |

### Example Configuration

```json
{
  "user_name": "You",
  "assistant_name": "Claude",
  "user_emoji": "👤",
  "assistant_emoji": "🤖",
  "theme": "auto",
  "generate_summary": true,
  "show_statistics": true,
  "central_export_location": null
}
```

### Available Themes

- `auto` - Adapts to system dark/light preference
- `dark` / `light` - Standard themes
- `github-dark` / `github-light` - GitHub-style
- `solarized-dark` / `solarized-light` - Solarized palette
- `monokai` - Monokai editor theme
- `dracula` - Dracula dark theme
- `nord` - Nord arctic palette

### Custom Colors

Override any theme color:

```json
{
  "theme": "dark",
  "custom_colors": {
    "bg_color": "#000000",
    "accent": "#ff6b6b",
    "user_bg": "#1a365d"
  }
}
```

## Export Output

### Directory Structure

```
your-project/
└── artifacts/
    └── conversations/
        ├── sessions_index.md           # Index of all sessions (Claude only)
        └── b8d52f27_auth-feature.html  # Session export
```

### HTML Export Contents

Each export includes:
- Session metadata (ID, project, timestamps)
- Auto-generated summary
- Statistics (duration, messages, tokens, tools)
- Full conversation with collapsible tool details
- Theme toggle button

## Architecture

```
┌─────────────────┐     ┌──────────────┐     ┌─────────────────┐
│   AI CLI Tool   │────▶│  Hook/Skill  │────▶│  Export Script  │
│ (Claude/Codex)  │     │   Trigger    │     │    (Python)     │
└─────────────────┘     └──────────────┘     └─────────────────┘
                                                      │
                                                      ▼
                                             ┌─────────────────┐
                                             │   HTML Output   │
                                             │  with Themes    │
                                             └─────────────────┘
```

### Claude Exporter
- **Automatic**: SessionEnd hook triggers export on session close
- **Manual**: `/export-conversation` slash command
- Reads JSONL transcripts from `~/.claude/projects/`
- Maintains session index for easy browsing

### Codex Exporter
- **Manual only**: `$codex-export` skill or CLI script
- Reads JSONL transcripts from `~/.codex/sessions/`
- Supports multiple output formats (HTML, Markdown, or both)

## Requirements

- Python 3.7+
- Bash shell
- Claude Code CLI or OpenAI Codex CLI

## Uninstalling

### Claude

```bash
~/.claude/hooks/uninstall-conversation-exporter.sh
```

### Codex

```bash
cd codex-conversation-exporter
./uninstall.sh
```

## Contributing

Issues and PRs welcome! When contributing:

1. Test changes with both dark and light themes
2. Ensure print styles remain clean
3. Keep configuration options backward-compatible
4. Update documentation for new features

## License

MIT License - see [LICENSE](./claude-conversation-exporter/LICENSE)
