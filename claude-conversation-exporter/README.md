# Claude Conversation Exporter

Export your Claude Code conversations to beautiful, readable HTML files with collapsible tool details and auto-generated summaries.

![Example](https://img.shields.io/badge/Claude_Code-Compatible-blue)

## Features

- **Automatic export** when sessions end (via SessionEnd hook)
- **Manual export** anytime with `/export-conversation` command
- **Auto-generated summaries** based on conversation content
- **Dark/Light themes** with syntax highlighting
- **Collapsible tool sections** - see what tools were used without clutter
- **Session statistics** - duration, message counts, token usage, tool breakdown
- **Per-message token stats** - see input/output tokens for each Claude response
- **Dark/Light toggle** - switch themes with one click (preference saved in browser)
- **Print-friendly** - clean output when printing (hides tools, stats, toggle)
- **Session continuity** - updates existing exports instead of creating duplicates
- **Central or per-project exports** - choose where to store conversations
- **Safe installation** - backs up existing settings, only adds our hook
- **Dynamic configuration** - changes apply immediately, no restart needed
- **Customizable** names, labels, emojis, and appearance

## Installation

### Quick Install

```bash
curl -fsSL https://raw.githubusercontent.com/YOUR_USERNAME/claude-conversation-exporter/main/install.sh | bash
```

### Manual Install

1. Clone this repository:
   ```bash
   git clone https://github.com/YOUR_USERNAME/claude-conversation-exporter.git
   cd claude-conversation-exporter
   ```

2. Run the install script:
   ```bash
   ./install.sh
   ```

The installer will:
- Create backup of your existing `settings.json` in `~/.claude/backups/`
- Add the SessionEnd hook without modifying other hooks
- Install the `/export-conversation` skill
- Create default configuration file

## Configuration

After installation, customize your export by editing `~/.claude/conversation-export-config.json`:

```json
{
  "user_name": "Your Name",
  "assistant_name": "Your coding partner",
  "user_emoji": "👤",
  "assistant_emoji": "🤖",
  "theme": "dark",
  "generate_summary": true,
  "show_summary": true,
  "show_session_id": true,
  "show_project_path": true,
  "show_timestamp": true
}
```

**Note:** Configuration changes are loaded dynamically - no need to restart Claude Code!

### All Available Options

| Option | Description | Default |
|--------|-------------|---------|
| `user_name` | Display name for your messages | `"You"` |
| `assistant_name` | Display name for Claude's messages | `"Claude"` |
| `user_emoji` | Emoji prefix for user messages | `"👤"` |
| `assistant_emoji` | Emoji prefix for assistant messages | `"🤖"` |
| `theme` | Color theme (see [Themes](#themes) below) | `"auto"` |
| `custom_colors` | Override specific theme colors (see [Custom Colors](#custom-colors)) | `null` |
| `font_size` | Base font size | `"16px"` |
| `line_height` | Line spacing (1.5-2.0 recommended for readability) | `"1.75"` |
| `letter_spacing` | Letter spacing | `"0.01em"` |
| `max_width` | Max content width | `"920px"` |
| `padding` | Page padding | `"24px"` |
| `central_export_location` | Absolute path to store all exports centrally (overrides per-project) | `null` |
| `output_dir` | Subdirectory for per-project exports | `"artifacts/conversations"` |
| `title_format` | Title format for HTML (use `{project_name}`) | `"{project_name} Conversations"` |
| `include_thinking` | Include Claude's thinking blocks | `false` |
| `generate_summary` | Auto-generate conversation summary from content | `true` |
| `show_summary` | Display summary in HTML header | `true` |
| `show_session_id` | Display session ID in HTML header | `true` |
| `show_project_path` | Display project path in HTML header | `true` |
| `show_timestamp` | Display timestamps in HTML header | `true` |
| `show_statistics` | Display session statistics (duration, tokens, tools) | `true` |
| `max_tool_result_length` | Max characters to show in tool results | `1000` |
| `max_tool_input_length` | Max characters to show in tool inputs | `500` |
| `date_format` | Date format for timestamps | `"%Y-%m-%d %H:%M:%S"` |
| `time_format` | Time format for message timestamps | `"%H:%M:%S"` |

### Central Export Location

By default, exports are saved per-project in `<project>/artifacts/conversations/`. To store all conversations in one central location:

```json
{
  "central_export_location": "/Users/yourname/Documents/claude-conversations"
}
```

When using central location, files are organized by project name in subdirectories.

### Themes

Available built-in themes:

| Theme | Description |
|-------|-------------|
| `auto` | **Default** - Adapts to system dark/light preference |
| `dark` | Dark blue theme |
| `light` | Light gray theme |
| `github-dark` | GitHub's dark mode colors |
| `github-light` | GitHub's light mode colors |
| `solarized-dark` | Solarized dark palette |
| `solarized-light` | Solarized light palette |
| `monokai` | Monokai editor theme |
| `dracula` | Dracula dark theme |
| `nord` | Nord arctic color palette |

### Custom Colors

Override any theme color by providing a `custom_colors` object:

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

Available color keys:
- `bg_color` - Page background
- `card_bg` - Card/container background
- `user_bg` - User message background
- `claude_bg` - Claude message background
- `text_color` - Main text color
- `text_muted` - Secondary/muted text
- `accent` - Primary accent color (links, highlights)
- `accent_soft` - Secondary accent color
- `border_color` - Border colors
- `code_bg` - Code block background
- `tool_bg` - Tool section background

Custom colors are applied on top of the selected theme, so you only need to specify the colors you want to change.

## Usage

### Automatic Export (Recommended)

Conversations are automatically exported when you:
- Press `Ctrl+C` to exit
- Type `/exit`
- Close the terminal

### Manual Export

Run the command anytime during a session:
```
/export-conversation
```

### Batch Export All Sessions

Export all existing sessions on your system at once:

```bash
# List all sessions
python export-all-sessions.py --list

# Export all sessions
python export-all-sessions.py

# Preview without exporting
python export-all-sessions.py --dry-run

# Only export new sessions (skip already exported)
python export-all-sessions.py --skip-existing

# Filter by project name
python export-all-sessions.py --project wireless

# Filter by date
python export-all-sessions.py --since 2024-01-01
python export-all-sessions.py --before 2024-02-01

# Export to central location
python export-all-sessions.py --central ~/Documents/claude-exports
```

### Viewing Exports

```bash
# Open the latest export
open <project>/artifacts/conversations/*.html

# Or check the index
cat <project>/artifacts/conversations/sessions_index.md
```

## Output Structure

```
your-project/
└── artifacts/
    └── conversations/
        ├── sessions_index.md                              # Index of all sessions
        └── b8d52f27_implementing-user-authentication.html # Session export
```

### Filename Format

Files are named: `{session_id}_{summary-slug}.html`

- `session_id`: First 8 characters of the Claude session UUID
- `summary-slug`: Auto-generated summary converted to URL-friendly format

Example: `b8d52f27_implementing-user-authentication.html`

### Custom Filenames

You can rename exported files to something more memorable. Just keep the session ID prefix (first 8 characters + underscore) and the exporter will preserve your custom name on resume:

```bash
# Original auto-generated name
b8d52f27_implementing-user-authentication.html

# Rename to something custom (keep the prefix!)
mv b8d52f27_implementing-user-authentication.html b8d52f27_oauth-feature-work.html

# On resume, your custom name is preserved
b8d52f27_oauth-feature-work.html  # Updated in place
```

This tip is also shown at the top of each exported HTML file.

### HTML Export Contents

Each export includes:
- **Created**: When the session first started
- **Last Updated**: When the export was last updated
- **Session ID**: Unique identifier for resuming
- **Project Path**: Working directory
- **Summary**: Auto-generated description of the conversation
- **Statistics**: Quick summary (duration, messages, tools, tokens) + detailed breakdown
- **Per-message stats**: Token usage (↓input ↑output) shown on each Claude response
- **Full conversation**: All messages with collapsible tool details
- **Theme toggle**: Switch between dark/light modes (top-right button)

### Printing

The HTML is print-friendly. When printing:
- Theme toggle button is hidden
- Statistics sections are hidden
- Tool details are hidden
- Clean black/white formatting for readability

## Session Continuity

When you resume a session, the exporter:
1. Detects the existing export by session ID
2. Updates the same file (preserving the original "Created" timestamp)
3. Updates "Last Updated" timestamp
4. Regenerates summary if conversation changed significantly

This means resumed sessions don't create duplicate files.

## Resuming Sessions

The raw `.jsonl` transcripts are preserved by Claude Code so you can resume sessions:

```bash
claude --resume  # Interactive picker
```

## Uninstalling

Run from anywhere:
```bash
~/.claude/hooks/uninstall-conversation-exporter.sh
```

The uninstaller will:
- Remove only our SessionEnd hook (preserves other hooks you may have)
- Ask before removing configuration file
- Preserve existing conversation exports
- Display location of settings backup for recovery

### Manual Removal

If needed, manually remove:
- `~/.claude/hooks/export-conversation.py`
- `~/.claude/hooks/export-current-session.sh`
- `~/.claude/commands/export-conversation.md`
- `~/.claude/conversation-export-config.json`
- Remove only our hook from `SessionEnd` in `~/.claude/settings.json`

### Restoring Settings

If something goes wrong, restore from backup:
```bash
cp ~/.claude/backups/settings.json.backup_YYYYMMDD_HHMMSS ~/.claude/settings.json
```

## How It Works

1. **SessionEnd Hook**: When a session ends, Claude Code triggers the export script
2. **Transcript Parsing**: The script reads the raw JSONL transcript from `~/.claude/projects/`
3. **Summary Generation**: Extracts keywords from user messages to create a summary
4. **HTML Generation**: Converts to formatted HTML with collapsible tool sections
5. **Deduplication**: Checks for existing exports of the same session and updates instead of duplicating
6. **Index Update**: Adds/updates entry in `sessions_index.md`

## Requirements

- Claude Code CLI
- Python 3.7+
- Bash shell

## License

MIT License - feel free to modify and share!

## Contributing

Issues and PRs welcome!
