# Codex Conversation Exporter

Exports Codex CLI sessions to Markdown and HTML with Claude-style formatting.

## Installation

```bash
cd codex-conversation-exporter
./install.sh
```

- Installs the `codex-export` skill under `~/.codex/skills/codex-export`
- Creates `~/.codex/conversation-export-config.json` if it does not exist
- Backs up any existing skill/config to `~/.codex/backups/`

Restart Codex after install so the new skill appears in `/skills`.

## Usage

In Codex:

```
$codex-export
```

This exports the latest session to:

```
<cwd>/artifacts/conversations/codex/
```

Manual CLI run:

```bash
python3 ~/.codex/skills/codex-export/scripts/export_codex_session.py --latest
```

Options:

| Flag | Description |
|------|-------------|
| `--format md\|html\|both` | Output format (default: `html`) |
| `--output <dir>` | Custom output directory |
| `--session <id\|path>` | Export specific session by ID or file path |
| `--latest` | Export most recent session |

## Configuration

Edit `~/.codex/conversation-export-config.json` to customize:

```json
{
  "user_name": "You",
  "assistant_name": "Codex",
  "theme": "auto",
  "generate_summary": true,
  "show_statistics": true
}
```

### Available Themes

`auto`, `dark`, `light`, `github-dark`, `github-light`, `solarized-dark`, `solarized-light`, `monokai`, `dracula`, `nord`

See the [main README](../README.md) for full configuration options and custom colors

## Uninstall

```bash
./uninstall.sh
```

Config is preserved at `~/.codex/conversation-export-config.json`.
