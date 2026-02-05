# Codex Conversation Exporter

Exports Codex CLI sessions to Markdown and HTML with Claude-style formatting.

## Installation

```bash
cd /Users/jagannath/Downloads/coding/local_testing/codex-conversation-exporter
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

- `--format md|html|both`
- `--output <dir>`
- `--session <id|path>`

Config:

- `~/.codex/conversation-export-config.json`
- Customize names, theme, colors, and display toggles

## Uninstall

```bash
./uninstall.sh
```

Config is preserved at `~/.codex/conversation-export-config.json`.
