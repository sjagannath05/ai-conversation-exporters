---
name: codex-export
description: Export the latest Codex CLI session to Markdown and HTML for archiving.
metadata:
  short-description: Export Codex sessions
---

# Codex Export

Use this skill when the user wants to export the current or latest Codex session.

## Quick use
- Run: `python3 ~/.codex/skills/codex-export/scripts/export_codex_session.py --latest`
- After export, print the output path(s) and ask if the user wants to `/exit`.

## Options
- `--session <id|path>`: export a specific session by ID or file path
- `--output <dir>`: override output directory
- `--format md|html|both`: export format (default: both)

## Config
- File: `~/.codex/conversation-export-config.json`
- Defaults are installed on first setup; edit to change theme, typography, output location, summary/statistics visibility.

## Notes
- Default output dir: `<cwd>/artifacts/conversations/codex/`
- Output file name: `YYYYMMDDTHHMMSSZ_<session_id>.<md|html>`
