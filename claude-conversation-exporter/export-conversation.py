#!/usr/bin/env python3
"""
Claude Conversation Exporter
Export Claude Code conversations to human-readable HTML with collapsible tool details.

Called by SessionEnd hook - receives session info via stdin.

Features:
- Fully configurable via ~/.claude/conversation-export-config.json
- Deduplication: updates existing exports instead of creating duplicates
- Tool calls grouped in collapsible sections
- Dark/Light theme support
- Auto-generated conversation summary
- Central or per-project export locations
"""

import json
import sys
import os
import glob
import html
import re
from datetime import datetime
from pathlib import Path
from collections import Counter


# Default configuration - all available options
DEFAULT_CONFIG = {
    # Display names
    "user_name": "You",
    "assistant_name": "Claude",

    # Emojis
    "user_emoji": "👤",
    "assistant_emoji": "🤖",

    # Theme: "auto", "dark", "light", "solarized-dark", "solarized-light",
    #        "monokai", "github-dark", "github-light", "dracula", "nord"
    # "auto" adapts to system dark/light preference
    "theme": "auto",

    # Custom color overrides (optional) - override any theme color
    # Example: {"bg_color": "#000000", "accent": "#ff0000"}
    "custom_colors": None,

    # Typography settings
    "font_size": "16px",           # Base font size
    "line_height": "1.75",         # Line spacing (1.5-2.0 recommended)
    "letter_spacing": "0.01em",    # Letter spacing
    "max_width": "920px",          # Max content width
    "padding": "24px",             # Page padding

    # Output location
    # - If set: all exports go to this central location (e.g., "~/.claude/conversations")
    # - If null/empty: exports go to each project's output_dir
    "central_export_location": None,

    # Output directory (relative to project root, used when central_export_location is not set)
    "output_dir": "artifacts/conversations",

    # Title format - {project_name} and {summary} are replaced
    "title_format": "{project_name} Conversations",

    # Include Claude's thinking blocks
    "include_thinking": False,

    # Auto-generate conversation summary
    "generate_summary": True,

    # Header visibility options
    "show_session_id": True,
    "show_project_path": True,
    "show_timestamp": True,
    "show_summary": True,
    "show_statistics": True,  # Show session statistics (tokens, duration, tools)

    # Truncation limits (in characters)
    "max_tool_result_length": 1000,
    "max_tool_input_length": 500,

    # Date/time formats (Python strftime)
    "date_format": "%Y-%m-%d %H:%M:%S",
    "time_format": "%H:%M:%S"
}

# Common stop words to filter out when generating summary
STOP_WORDS = {
    'i', 'me', 'my', 'we', 'our', 'you', 'your', 'the', 'a', 'an', 'is', 'are',
    'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does',
    'did', 'will', 'would', 'could', 'should', 'may', 'might', 'must', 'shall',
    'can', 'to', 'of', 'in', 'for', 'on', 'with', 'at', 'by', 'from', 'as',
    'into', 'through', 'during', 'before', 'after', 'above', 'below', 'between',
    'under', 'again', 'further', 'then', 'once', 'here', 'there', 'when', 'where',
    'why', 'how', 'all', 'each', 'few', 'more', 'most', 'other', 'some', 'such',
    'no', 'nor', 'not', 'only', 'own', 'same', 'so', 'than', 'too', 'very',
    'just', 'and', 'but', 'if', 'or', 'because', 'as', 'until', 'while', 'of',
    'this', 'that', 'these', 'those', 'am', 'it', 'its', 'also', 'about', 'like',
    'want', 'need', 'please', 'help', 'make', 'get', 'let', 'see', 'look', 'thing',
    'something', 'anything', 'everything', 'nothing', 'use', 'using', 'used'
}


def load_config():
    """Load configuration from file or use defaults."""
    config_path = Path.home() / ".claude" / "conversation-export-config.json"
    config = DEFAULT_CONFIG.copy()

    if config_path.exists():
        try:
            with open(config_path, 'r') as f:
                user_config = json.load(f)
                # Filter out comments
                user_config = {k: v for k, v in user_config.items() if not k.startswith('_')}
                config.update(user_config)
        except (json.JSONDecodeError, IOError) as e:
            print(f"Warning: Could not load config: {e}", file=sys.stderr)

    return config


def generate_summary(conversation, project_name, max_words=5):
    """
    Generate a short summary of what the conversation is about.
    Analyzes first few user messages to extract key topics.
    """
    # Collect text from first 5 user messages
    user_texts = []
    for msg in conversation[:10]:
        if msg["type"] == "user":
            user_texts.append(msg["content"])
            if len(user_texts) >= 5:
                break

    if not user_texts:
        return f"{project_name} session"

    # Combine and clean text
    combined_text = " ".join(user_texts).lower()

    # Remove code blocks, URLs, file paths
    combined_text = re.sub(r'```.*?```', '', combined_text, flags=re.DOTALL)
    combined_text = re.sub(r'https?://\S+', '', combined_text)
    combined_text = re.sub(r'/[\w/.-]+', '', combined_text)
    combined_text = re.sub(r'`[^`]+`', '', combined_text)

    # Extract words
    words = re.findall(r'\b[a-z]{3,}\b', combined_text)

    # Filter stop words and count
    meaningful_words = [w for w in words if w not in STOP_WORDS]
    word_counts = Counter(meaningful_words)

    # Get top words
    top_words = [word for word, _ in word_counts.most_common(max_words)]

    if not top_words:
        return f"{project_name} session"

    # Look for action patterns in first message
    first_msg = user_texts[0].lower()
    action_patterns = [
        (r'\b(create|build|make|develop|implement)\b.*?\b(\w+)', 'building'),
        (r'\b(fix|debug|solve|resolve)\b.*?\b(\w+)', 'fixing'),
        (r'\b(add|integrate|include)\b.*?\b(\w+)', 'adding'),
        (r'\b(update|modify|change|edit)\b.*?\b(\w+)', 'updating'),
        (r'\b(setup|configure|install)\b.*?\b(\w+)', 'setting up'),
        (r'\b(export|convert|transform)\b.*?\b(\w+)', 'exporting'),
        (r'\b(test|verify|check)\b.*?\b(\w+)', 'testing'),
        (r'\b(refactor|optimize|improve)\b.*?\b(\w+)', 'improving'),
    ]

    for pattern, action in action_patterns:
        match = re.search(pattern, first_msg)
        if match:
            # Construct summary with action and top keywords
            keywords = " ".join(top_words[:3])
            return f"{action} {keywords}".title()

    # Default: just use top keywords
    summary = " ".join(top_words[:4])
    return summary.title() if summary else f"{project_name} session"


# Theme definitions
THEMES = {
    "dark": {
        "bg_color": "#1e1e2e",           # Slightly lighter for less strain
        "card_bg": "#1a1a2e",
        "user_bg": "#1a365d",            # Softer blue
        "claude_bg": "#1e1e2e",
        "text_color": "#f0f0f0",         # Brighter text for better contrast
        "text_muted": "#b8b8c8",         # Lighter muted text
        "accent": "#f06292",             # Softer pink accent
        "accent_soft": "#7c6bba",        # Softer purple
        "border_color": "#3a3a5a",       # Slightly more visible borders
        "code_bg": "#141422",
        "tool_bg": "#1a2535"
    },
    "light": {
        "bg_color": "#fafafa",           # Slightly off-white, easier on eyes
        "card_bg": "#ffffff",
        "user_bg": "#e8f4fc",            # Softer blue tint
        "claude_bg": "#ffffff",
        "text_color": "#2d2d2d",         # Softer than pure black
        "text_muted": "#5a5a6a",         # Better contrast muted
        "accent": "#2563eb",             # Pleasant blue
        "accent_soft": "#7c3aed",        # Pleasant purple
        "border_color": "#e2e2e8",
        "code_bg": "#f4f4f8",
        "tool_bg": "#f8f8fc"
    },
    "solarized-dark": {
        "bg_color": "#002b36",
        "card_bg": "#073642",
        "user_bg": "#094552",
        "claude_bg": "#073642",
        "text_color": "#839496",
        "text_muted": "#657b83",
        "accent": "#cb4b16",
        "accent_soft": "#6c71c4",
        "border_color": "#586e75",
        "code_bg": "#002b36",
        "tool_bg": "#073642"
    },
    "solarized-light": {
        "bg_color": "#fdf6e3",
        "card_bg": "#eee8d5",
        "user_bg": "#e4ddc8",
        "claude_bg": "#eee8d5",
        "text_color": "#657b83",
        "text_muted": "#93a1a1",
        "accent": "#cb4b16",
        "accent_soft": "#6c71c4",
        "border_color": "#93a1a1",
        "code_bg": "#fdf6e3",
        "tool_bg": "#eee8d5"
    },
    "monokai": {
        "bg_color": "#272822",
        "card_bg": "#3e3d32",
        "user_bg": "#49483e",
        "claude_bg": "#3e3d32",
        "text_color": "#f8f8f2",
        "text_muted": "#75715e",
        "accent": "#f92672",
        "accent_soft": "#ae81ff",
        "border_color": "#49483e",
        "code_bg": "#272822",
        "tool_bg": "#3e3d32"
    },
    "github-dark": {
        "bg_color": "#0d1117",
        "card_bg": "#161b22",
        "user_bg": "#21262d",
        "claude_bg": "#161b22",
        "text_color": "#c9d1d9",
        "text_muted": "#8b949e",
        "accent": "#58a6ff",
        "accent_soft": "#bc8cff",
        "border_color": "#30363d",
        "code_bg": "#0d1117",
        "tool_bg": "#161b22"
    },
    "github-light": {
        "bg_color": "#ffffff",
        "card_bg": "#f6f8fa",
        "user_bg": "#ddf4ff",
        "claude_bg": "#f6f8fa",
        "text_color": "#24292f",
        "text_muted": "#57606a",
        "accent": "#0969da",
        "accent_soft": "#8250df",
        "border_color": "#d0d7de",
        "code_bg": "#f6f8fa",
        "tool_bg": "#f6f8fa"
    },
    "dracula": {
        "bg_color": "#282a36",
        "card_bg": "#44475a",
        "user_bg": "#4d5066",
        "claude_bg": "#44475a",
        "text_color": "#f8f8f2",
        "text_muted": "#6272a4",
        "accent": "#ff79c6",
        "accent_soft": "#bd93f9",
        "border_color": "#6272a4",
        "code_bg": "#282a36",
        "tool_bg": "#44475a"
    },
    "nord": {
        "bg_color": "#2e3440",
        "card_bg": "#3b4252",
        "user_bg": "#434c5e",
        "claude_bg": "#3b4252",
        "text_color": "#eceff4",
        "text_muted": "#d8dee9",
        "accent": "#88c0d0",
        "accent_soft": "#b48ead",
        "border_color": "#4c566a",
        "code_bg": "#2e3440",
        "tool_bg": "#3b4252"
    }
}

# Auto theme uses both dark and light with CSS media query
# Uses the original colorful themes for better visual appeal
AUTO_THEME_DARK = THEMES["dark"]
AUTO_THEME_LIGHT = THEMES["light"]


def get_html_template(theme_name, config):
    """Get HTML template with theme colors applied."""
    custom_colors = config.get("custom_colors") or {}
    is_auto = theme_name == "auto"

    # Build header meta section based on config
    meta_items = []
    if config.get("show_summary", True):
        meta_items.append('<p><strong>Summary:</strong> {summary}</p>')
    if config.get("show_session_id", True):
        meta_items.append('<p><strong>Session ID:</strong> <code>{session_id}</code></p>')
    if config.get("show_project_path", True):
        meta_items.append('<p><strong>Project:</strong> <code>{project_dir}</code></p>')
    if config.get("show_timestamp", True):
        meta_items.append('<p><strong>Created (UTC):</strong> {created}</p>')
        meta_items.append('<p><strong>Last Updated (UTC):</strong> {timestamp}</p>')

    # Add tip about renaming
    meta_items.append('<p class="tip"><em>Tip: You can rename this file (keep the <code>{short_id}_</code> prefix) and it will be preserved on resume.</em></p>')

    # Stats section placeholder (will be replaced with actual stats)
    meta_items.append('{stats_section}')

    meta_html = "\n            ".join(meta_items) if meta_items else ""

    def apply_custom(theme_dict):
        """Apply custom color overrides to a theme."""
        result = theme_dict.copy()
        result.update(custom_colors)
        return result

    def theme_to_css_vars(theme):
        """Convert theme dict to CSS variable declarations."""
        return f"""
            --bg-color: {theme["bg_color"]};
            --card-bg: {theme["card_bg"]};
            --user-bg: {theme["user_bg"]};
            --claude-bg: {theme["claude_bg"]};
            --text-color: {theme["text_color"]};
            --text-muted: {theme["text_muted"]};
            --accent: {theme["accent"]};
            --accent-soft: {theme["accent_soft"]};
            --border-color: {theme["border_color"]};
            --code-bg: {theme["code_bg"]};
            --tool-bg: {theme["tool_bg"]};"""

    # Build CSS with theme colors
    if is_auto:
        # Auto theme: use media queries for system preference
        dark_theme = apply_custom(AUTO_THEME_DARK)
        light_theme = apply_custom(AUTO_THEME_LIGHT)
        css_vars = f"""
        /* Auto theme - adapts to system preference */
        :root {{
            {theme_to_css_vars(light_theme)}
        }}

        @media (prefers-color-scheme: dark) {{
            :root {{
                {theme_to_css_vars(dark_theme)}
            }}
        }}"""
    else:
        # Static theme
        theme = apply_custom(THEMES.get(theme_name, THEMES["dark"]))
        css_vars = f"""
        :root {{
            {theme_to_css_vars(theme)}
        }}"""

    # Common CSS (combined with theme variables)
    css = css_vars + """

        * {
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            background-color: var(--bg-color);
            color: var(--text-color);
            font-size: """ + config.get("font_size", "16px") + """;
            line-height: """ + config.get("line_height", "1.75") + """;
            letter-spacing: """ + config.get("letter_spacing", "0.01em") + """;
            margin: 0;
            padding: """ + config.get("padding", "24px") + """;
            max-width: """ + config.get("max_width", "920px") + """;
            margin: 0 auto;
        }

        header {
            background: var(--card-bg);
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 30px;
            border: 1px solid var(--border-color);
        }

        header h1 {
            margin: 0 0 10px 0;
            color: var(--accent);
        }

        header .meta {
            color: var(--text-muted);
            font-size: 0.9em;
        }

        header .meta code {
            background: var(--code-bg);
            padding: 2px 6px;
            border-radius: 4px;
            font-size: 0.92em;
        }

        header .meta .tip {
            margin-top: 10px;
            padding: 8px 12px;
            background: var(--code-bg);
            border-radius: 6px;
            font-size: 0.92em;
            opacity: 0.8;
        }

        .message {
            margin-bottom: 20px;
            padding: 15px 20px;
            border-radius: 10px;
            border: 1px solid var(--border-color);
        }

        .message.user {
            background: var(--user-bg);
            border-left: 4px solid var(--accent);
        }

        .message.claude {
            background: var(--claude-bg);
            border-left: 4px solid var(--accent-soft);
        }

        .message-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
            padding-bottom: 8px;
            border-bottom: 1px solid var(--border-color);
        }

        .message-header .role {
            font-weight: 600;
            font-size: 0.9em;
            letter-spacing: 0.5px;
        }

        .message-header .role.user-role {
            color: var(--accent);
        }

        .message-header .role.claude-role {
            color: var(--accent-soft);
        }

        .message-header .header-right {
            display: flex;
            align-items: center;
            gap: 12px;
        }

        .message-header .timestamp {
            color: var(--text-muted);
            font-size: 0.88em;
        }

        .message-header .msg-stats {
            font-size: 0.8em;
            color: var(--text-muted);
            background: var(--code-bg);
            padding: 2px 8px;
            border-radius: 10px;
            font-family: 'SF Mono', 'Fira Code', monospace;
        }

        .message-content {
            white-space: pre-wrap;
            word-wrap: break-word;
        }

        .message-content p {
            margin: 0 0 10px 0;
        }

        .message-content p:last-child {
            margin-bottom: 0;
        }

        details.tools-container {
            background: var(--tool-bg);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            margin: 10px 0;
            overflow: hidden;
        }

        details.tools-container > summary {
            padding: 10px 15px;
            cursor: pointer;
            font-size: 0.9em;
            color: var(--text-muted);
            font-weight: 500;
        }

        details.tools-container > summary:hover {
            background: rgba(128,128,128,0.1);
        }

        details.tools-container > summary::marker {
            color: var(--accent);
        }

        .tools-list {
            padding: 10px 15px;
            border-top: 1px solid var(--border-color);
        }

        .tool-item {
            background: var(--code-bg);
            border: 1px solid var(--border-color);
            border-radius: 6px;
            margin-bottom: 8px;
        }

        .tool-item:last-child {
            margin-bottom: 0;
        }

        .tool-item summary {
            padding: 8px 12px;
            cursor: pointer;
            font-size: 0.92em;
            color: var(--text-muted);
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .tool-item summary:hover {
            background: rgba(128,128,128,0.05);
        }

        .tool-item summary .tool-icon {
            font-size: 1em;
        }

        .tool-item summary .tool-name {
            color: #4ec9b0;
            font-weight: 500;
        }

        .tool-item summary .tool-desc {
            color: var(--text-muted);
            font-size: 0.9em;
        }

        .tool-content {
            padding: 12px;
            border-top: 1px solid var(--border-color);
            font-size: 0.88em;
        }

        .tool-content h4 {
            margin: 0 0 6px 0;
            color: var(--text-muted);
            font-size: 0.92em;
            text-transform: uppercase;
        }

        .tool-content pre {
            background: var(--bg-color);
            padding: 10px;
            border-radius: 4px;
            overflow-x: auto;
            margin: 6px 0;
            font-size: 0.9em;
        }

        .tool-content code {
            font-family: 'SF Mono', 'Fira Code', 'Consolas', monospace;
        }

        code {
            background: var(--code-bg);
            padding: 2px 6px;
            border-radius: 4px;
            font-family: 'SF Mono', 'Fira Code', 'Consolas', monospace;
            font-size: 0.9em;
        }

        pre {
            background: var(--code-bg);
            padding: 15px;
            border-radius: 8px;
            overflow-x: auto;
        }

        pre code {
            background: none;
            padding: 0;
        }

        h1, h2, h3, h4 {
            color: var(--text-color);
        }

        .content h2 {
            border-bottom: 1px solid var(--border-color);
            padding-bottom: 5px;
        }

        a {
            color: var(--accent);
        }

        hr {
            border: none;
            border-top: 1px solid var(--border-color);
            margin: 30px 0;
        }

        .content ul, .content ol {
            padding-left: 25px;
        }

        .content li {
            margin-bottom: 5px;
        }

        .content blockquote {
            border-left: 3px solid var(--accent-soft);
            margin: 10px 0;
            padding-left: 15px;
            color: var(--text-muted);
        }

        /* Statistics quick summary */
        .stats-quick {
            margin: 12px 0 5px 0;
            display: flex;
            flex-wrap: wrap;
            align-items: center;
            gap: 8px;
        }

        .stat-pill {
            background: var(--code-bg);
            padding: 3px 10px;
            border-radius: 12px;
            font-size: 0.85em;
            color: var(--text-color);
            border: 1px solid var(--border-color);
        }

        /* Statistics section */
        .stats-section {
            margin-top: 10px;
        }

        .stats-container {
            background: var(--tool-bg);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            overflow: hidden;
        }

        .stats-container > summary {
            padding: 10px 15px;
            cursor: pointer;
            font-size: 0.95em;
            color: var(--text-muted);
            font-weight: 500;
        }

        .stats-container > summary:hover {
            background: rgba(128,128,128,0.1);
        }

        .stats-container > summary::marker {
            color: var(--accent);
        }

        .stats-content {
            padding: 12px 15px;
            border-top: 1px solid var(--border-color);
        }

        .stats-row {
            display: flex;
            flex-wrap: wrap;
            gap: 15px 25px;
            margin-bottom: 8px;
        }

        .stats-row:last-child {
            margin-bottom: 0;
        }

        .stat-item {
            font-size: 0.9em;
        }

        .stat-label {
            color: var(--text-muted);
            font-weight: 500;
        }

        /* Theme toggle button */
        .theme-toggle {
            position: fixed;
            top: 15px;
            right: 15px;
            background: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: 20px;
            padding: 8px 14px;
            cursor: pointer;
            font-size: 0.85em;
            color: var(--text-muted);
            z-index: 100;
            display: flex;
            align-items: center;
            gap: 6px;
            transition: background 0.2s, border-color 0.2s;
        }

        .theme-toggle:hover {
            background: var(--tool-bg);
            border-color: var(--accent);
        }

        /* Print styles */
        @media print {
            body {
                background: white !important;
                color: black !important;
                font-size: 11pt;
                max-width: 100%;
                padding: 0;
            }

            .theme-toggle {
                display: none !important;
            }

            header {
                background: #f5f5f5 !important;
                border: 1px solid #ddd !important;
                page-break-after: avoid;
            }

            header h1 {
                color: #333 !important;
            }

            .stats-section, .stats-quick {
                display: none !important;
            }

            .message {
                background: white !important;
                border: 1px solid #ddd !important;
                border-left-width: 3px !important;
                page-break-inside: avoid;
                margin-bottom: 10px;
            }

            .message.user {
                border-left-color: #2563eb !important;
            }

            .message.claude {
                border-left-color: #7c3aed !important;
            }

            .message-header {
                border-bottom: 1px solid #eee !important;
            }

            .role {
                color: #333 !important;
            }

            .msg-stats {
                display: none !important;
            }

            details.tools-container {
                display: none !important;
            }

            code, pre {
                background: #f5f5f5 !important;
                border: 1px solid #ddd !important;
            }

            a {
                color: #2563eb !important;
                text-decoration: underline;
            }

            .tip {
                display: none !important;
            }
        }

        @media (max-width: 600px) {
            body {
                padding: 10px;
            }
            .message {
                padding: 12px 15px;
            }
            .stats-row {
                flex-direction: column;
                gap: 8px;
            }
            .theme-toggle {
                top: 10px;
                right: 10px;
                padding: 6px 10px;
            }
        }
    """

    # Theme toggle JavaScript
    theme_toggle_js = """
    <script>
    (function() {
        const STORAGE_KEY = 'claude-export-theme';
        const root = document.documentElement;

        // Theme color definitions
        const themes = {
            dark: {
                '--bg-color': '#1e1e2e',
                '--card-bg': '#1a1a2e',
                '--user-bg': '#1a365d',
                '--claude-bg': '#1e1e2e',
                '--text-color': '#f0f0f0',
                '--text-muted': '#b8b8c8',
                '--accent': '#f06292',
                '--accent-soft': '#7c6bba',
                '--border-color': '#3a3a5a',
                '--code-bg': '#141422',
                '--tool-bg': '#1a2535'
            },
            light: {
                '--bg-color': '#fafafa',
                '--card-bg': '#ffffff',
                '--user-bg': '#e8f4fc',
                '--claude-bg': '#ffffff',
                '--text-color': '#2d2d2d',
                '--text-muted': '#5a5a6a',
                '--accent': '#2563eb',
                '--accent-soft': '#7c3aed',
                '--border-color': '#e2e2e8',
                '--code-bg': '#f4f4f8',
                '--tool-bg': '#f8f8fc'
            }
        };

        function getPreferredTheme() {
            const stored = localStorage.getItem(STORAGE_KEY);
            if (stored) return stored;
            return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
        }

        function applyTheme(theme) {
            const colors = themes[theme];
            for (const [prop, value] of Object.entries(colors)) {
                root.style.setProperty(prop, value);
            }
            updateToggleButton(theme);
        }

        function updateToggleButton(theme) {
            const btn = document.getElementById('theme-toggle');
            if (btn) {
                btn.innerHTML = theme === 'dark' ? '☀️ Light' : '🌙 Dark';
            }
        }

        function toggleTheme() {
            const current = localStorage.getItem(STORAGE_KEY) || getPreferredTheme();
            const next = current === 'dark' ? 'light' : 'dark';
            localStorage.setItem(STORAGE_KEY, next);
            applyTheme(next);
        }

        // Initialize
        document.addEventListener('DOMContentLoaded', function() {
            applyTheme(getPreferredTheme());

            const btn = document.getElementById('theme-toggle');
            if (btn) {
                btn.addEventListener('click', toggleTheme);
            }
        });

        // Listen for system theme changes
        window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', function(e) {
            if (!localStorage.getItem(STORAGE_KEY)) {
                applyTheme(e.matches ? 'dark' : 'light');
            }
        });
    })();
    </script>
"""

    html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
""" + css + """
    </style>
</head>
<body>
    <button id="theme-toggle" class="theme-toggle">🌙 Dark</button>

    <header>
        <h1>💬 {title}</h1>
        <div class="meta">
            """ + meta_html + """
        </div>
    </header>

    <main>
{content}
    </main>
""" + theme_toggle_js + """
</body>
</html>
"""
    return html


def escape_html(text):
    """Escape HTML special characters."""
    if not text:
        return ""
    return html.escape(str(text))


def format_timestamp(ts, config):
    """Format ISO timestamp to readable time."""
    if not ts:
        return ""
    try:
        dt = datetime.fromisoformat(ts.replace('Z', '+00:00'))
        time_format = config.get("time_format", "%H:%M:%S")
        return dt.strftime(time_format)
    except:
        return ts[:19] if len(ts) >= 19 else ts


def get_tool_description(tool_name, tool_input):
    """Generate a short description for a tool call."""
    if tool_name == "Bash":
        cmd = tool_input.get("command", "")
        desc = tool_input.get("description", "")
        if desc:
            return desc
        return cmd[:50] + "..." if len(cmd) > 50 else cmd
    elif tool_name == "Read":
        path = tool_input.get('file_path', 'file')
        return f"Read {Path(path).name}"
    elif tool_name == "Write":
        path = tool_input.get('file_path', 'file')
        return f"Write {Path(path).name}"
    elif tool_name == "Edit":
        path = tool_input.get('file_path', 'file')
        return f"Edit {Path(path).name}"
    elif tool_name == "Glob":
        return f"Find: {tool_input.get('pattern', '')}"
    elif tool_name == "Grep":
        return f"Search: {tool_input.get('pattern', '')}"
    elif tool_name == "Task":
        return tool_input.get("description", "Run subagent")
    elif tool_name == "WebSearch":
        return f"Search: {tool_input.get('query', '')[:30]}"
    elif tool_name == "WebFetch":
        url = tool_input.get('url', '')
        return f"Fetch: {url[:35]}..." if len(url) > 35 else f"Fetch: {url}"
    else:
        return tool_name


def format_tool_input(tool_name, tool_input, config):
    """Format tool input for display."""
    max_length = config.get("max_tool_input_length", 500)

    if tool_name == "Bash":
        cmd = tool_input.get("command", "")
        return f"<pre><code>{escape_html(cmd)}</code></pre>"
    elif tool_name in ["Read", "Write", "Edit"]:
        return f"<p><strong>File:</strong> <code>{escape_html(tool_input.get('file_path', ''))}</code></p>"
    else:
        formatted = json.dumps(tool_input, indent=2)
        if len(formatted) > max_length:
            formatted = formatted[:max_length] + "\n..."
        return f"<pre><code>{escape_html(formatted)}</code></pre>"


def format_tool_result(result_content, config):
    """Format tool result for display."""
    max_length = config.get("max_tool_result_length", 1000)

    if isinstance(result_content, list):
        texts = []
        for block in result_content:
            if isinstance(block, dict) and block.get("type") == "text":
                texts.append(block.get("text", ""))
        result_content = "\n".join(texts)

    if not isinstance(result_content, str):
        result_content = str(result_content)

    if len(result_content) > max_length:
        result_content = result_content[:max_length] + "\n... (truncated)"

    return f"<pre><code>{escape_html(result_content)}</code></pre>"


def parse_conversation(jsonl_path, config):
    """Parse JSONL and extract conversation with tool tracking and statistics."""
    include_thinking = config.get("include_thinking", False)

    entries = []
    with open(jsonl_path, 'r') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                continue

    tool_calls = {}
    conversation = []
    current_claude_msg = None
    first_timestamp = None  # Track the first message timestamp
    last_timestamp = None   # Track the last message timestamp

    # Statistics tracking
    stats = {
        "user_messages": 0,
        "claude_messages": 0,
        "total_input_tokens": 0,
        "total_output_tokens": 0,
        "cache_creation_tokens": 0,
        "cache_read_tokens": 0,
        "tool_usage": Counter(),  # Tool name -> count
    }

    for entry in entries:
        entry_type = entry.get("type", "")
        timestamp = entry.get("timestamp", "")

        # Capture the first timestamp from the conversation
        if first_timestamp is None and timestamp:
            first_timestamp = timestamp

        # Always update last_timestamp
        if timestamp:
            last_timestamp = timestamp

        if entry_type == "user":
            msg = entry.get("message", {})
            content = msg.get("content") if isinstance(msg, dict) else msg

            if isinstance(content, str):
                stats["user_messages"] += 1
                if current_claude_msg:
                    conversation.append(current_claude_msg)
                    current_claude_msg = None
                conversation.append({
                    "type": "user",
                    "timestamp": timestamp,
                    "content": content,
                    "tools": []
                })
            elif isinstance(content, list):
                for block in content:
                    if isinstance(block, dict) and block.get("type") == "tool_result":
                        tool_id = block.get("tool_use_id", "")
                        if tool_id in tool_calls:
                            tool_calls[tool_id]["result"] = block.get("content", "")

        elif entry_type == "assistant":
            msg = entry.get("message", {})
            msg_content = msg.get("content", [])

            # Extract token usage from the assistant message
            usage = msg.get("usage") or entry.get("usage") or {}
            if usage:
                stats["total_input_tokens"] += usage.get("input_tokens", 0)
                stats["total_output_tokens"] += usage.get("output_tokens", 0)
                stats["cache_creation_tokens"] += usage.get("cache_creation_input_tokens", 0)
                stats["cache_read_tokens"] += usage.get("cache_read_input_tokens", 0)

            if isinstance(msg_content, list):
                has_text_content = False
                for block in msg_content:
                    if not isinstance(block, dict):
                        continue

                    block_type = block.get("type")

                    if block_type == "text":
                        text = block.get("text", "").strip()
                        if text:
                            has_text_content = True
                            if current_claude_msg is None:
                                current_claude_msg = {
                                    "type": "claude",
                                    "timestamp": timestamp,
                                    "content": text,
                                    "tools": []
                                }
                            else:
                                current_claude_msg["content"] += "\n\n" + text

                    elif block_type == "thinking" and include_thinking:
                        thinking = block.get("thinking", "").strip()
                        if thinking and current_claude_msg:
                            preview = thinking[:200] + "..." if len(thinking) > 200 else thinking
                            current_claude_msg["content"] += f"\n\n*[Thinking: {preview}]*"

                    elif block_type == "tool_use":
                        tool_id = block.get("id", "")
                        tool_name = block.get("name", "unknown")
                        tool_input = block.get("input", {})

                        tool_calls[tool_id] = {
                            "name": tool_name,
                            "input": tool_input,
                            "timestamp": timestamp,
                            "result": None
                        }

                        # Track tool usage for stats
                        stats["tool_usage"][tool_name] += 1

                        if current_claude_msg is None:
                            current_claude_msg = {
                                "type": "claude",
                                "timestamp": timestamp,
                                "content": "",
                                "tools": []
                            }

                        current_claude_msg["tools"].append(tool_id)

                # Count Claude messages (only if there's meaningful content)
                # Count Claude messages and store per-message token usage
                if has_text_content or (current_claude_msg and current_claude_msg["tools"]):
                    stats["claude_messages"] += 1
                    # Store per-message usage in the message itself
                    if current_claude_msg and usage:
                        current_claude_msg["usage"] = {
                            "input": usage.get("input_tokens", 0),
                            "output": usage.get("output_tokens", 0),
                            "cache_read": usage.get("cache_read_input_tokens", 0)
                        }

    if current_claude_msg:
        conversation.append(current_claude_msg)

    # Calculate session duration
    stats["first_timestamp"] = first_timestamp
    stats["last_timestamp"] = last_timestamp
    stats["duration_seconds"] = None
    if first_timestamp and last_timestamp:
        try:
            start = datetime.fromisoformat(first_timestamp.replace('Z', '+00:00'))
            end = datetime.fromisoformat(last_timestamp.replace('Z', '+00:00'))
            stats["duration_seconds"] = (end - start).total_seconds()
        except:
            pass

    return conversation, tool_calls, first_timestamp, stats


def render_tools_section(tools, tool_calls, config):
    """Render all tools in a single collapsible section."""
    if not tools:
        return ""

    tool_count = len(tools)
    tools_label = f"Tools used ({tool_count})"

    tool_items_html = ""
    for tool_id in tools:
        if tool_id not in tool_calls:
            continue
        tool = tool_calls[tool_id]
        tool_name = tool["name"]
        tool_input = tool["input"]
        tool_result = tool.get("result")

        desc = get_tool_description(tool_name, tool_input)
        input_html = format_tool_input(tool_name, tool_input, config)
        result_html = format_tool_result(tool_result, config) if tool_result else "<p><em>No result captured</em></p>"

        tool_items_html += f"""
                <details class="tool-item">
                    <summary>
                        <span class="tool-icon">🔧</span>
                        <span class="tool-name">{escape_html(tool_name)}</span>
                        <span class="tool-desc">— {escape_html(desc)}</span>
                    </summary>
                    <div class="tool-content">
                        <h4>Input</h4>
                        {input_html}
                        <h4>Result</h4>
                        {result_html}
                    </div>
                </details>
"""

    return f"""
            <details class="tools-container">
                <summary>🛠️ {tools_label}</summary>
                <div class="tools-list">
{tool_items_html}
                </div>
            </details>
"""


def render_message(msg, tool_calls, config):
    """Render a single message to HTML."""
    msg_type = msg["type"]
    timestamp = format_timestamp(msg["timestamp"], config)
    content = msg["content"]
    tools = msg.get("tools", [])
    usage = msg.get("usage", {})

    user_emoji = config.get("user_emoji", "👤")
    assistant_emoji = config.get("assistant_emoji", "🤖")

    if msg_type == "user":
        role_class = "user"
        role_label = f"{user_emoji} {config['user_name']}"
        header_class = "user-role"
    else:
        role_class = "claude"
        role_label = f"{assistant_emoji} {config['assistant_name']}"
        header_class = "claude-role"

    tools_html = render_tools_section(tools, tool_calls, config)

    # Per-message stats for Claude messages
    msg_stats_html = ""
    if msg_type == "claude" and usage and config.get("show_statistics", True):
        input_tokens = usage.get("input", 0)
        output_tokens = usage.get("output", 0)
        if input_tokens or output_tokens:
            msg_stats_html = f'<span class="msg-stats">↓{format_token_count(input_tokens)} ↑{format_token_count(output_tokens)}</span>'

    # Format content
    content_html = escape_html(content)
    content_html = re.sub(r'```(\w*)\n(.*?)```', r'<pre><code>\2</code></pre>', content_html, flags=re.DOTALL)
    content_html = re.sub(r'`([^`]+)`', r'<code>\1</code>', content_html)
    content_html = re.sub(r'^### (.+)$', r'<h3>\1</h3>', content_html, flags=re.MULTILINE)
    content_html = re.sub(r'^## (.+)$', r'<h2>\1</h2>', content_html, flags=re.MULTILINE)
    content_html = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', content_html)
    content_html = content_html.replace('\n\n', '</p><p>')
    content_html = f"<p>{content_html}</p>" if content_html else ""

    return f"""
        <div class="message {role_class}">
            <div class="message-header">
                <span class="role {header_class}">{role_label}</span>
                <span class="header-right">
                    {msg_stats_html}
                    <span class="timestamp">{timestamp}</span>
                </span>
            </div>
            {tools_html}
            <div class="message-content content">
                {content_html}
            </div>
        </div>
"""


def format_duration(seconds):
    """Format duration in seconds to human-readable string."""
    if seconds is None:
        return "N/A"
    if seconds < 60:
        return f"{int(seconds)}s"
    elif seconds < 3600:
        mins = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{mins}m {secs}s"
    else:
        hours = int(seconds // 3600)
        mins = int((seconds % 3600) // 60)
        return f"{hours}h {mins}m"


def format_token_count(count):
    """Format token count with K/M suffix for large numbers."""
    if count >= 1_000_000:
        return f"{count / 1_000_000:.1f}M"
    elif count >= 1_000:
        return f"{count / 1_000:.1f}K"
    return str(count)


def render_stats_section(stats, config):
    """Render statistics section HTML."""
    if not config.get("show_statistics", True):
        return ""

    duration_str = format_duration(stats.get("duration_seconds"))
    total_input = format_token_count(stats.get("total_input_tokens", 0))
    total_output = format_token_count(stats.get("total_output_tokens", 0))
    cache_read = format_token_count(stats.get("cache_read_tokens", 0))
    total_tokens = stats.get("total_input_tokens", 0) + stats.get("total_output_tokens", 0)
    total_messages = stats.get('user_messages', 0) + stats.get('claude_messages', 0)

    # Top 5 tools by usage
    tool_usage = stats.get("tool_usage", Counter())
    top_tools = tool_usage.most_common(5)
    total_tool_calls = sum(tool_usage.values())

    tools_html = ""
    if top_tools:
        tools_items = ", ".join([f"{name} ({count})" for name, count in top_tools])
        if len(tool_usage) > 5:
            tools_items += f" +{len(tool_usage) - 5} more"
        tools_html = f'<span class="stat-item"><span class="stat-label">Tools:</span> {tools_items}</span>'

    # Quick summary line (always visible)
    quick_summary = f"""
        <p class="stats-quick">
            <strong>📊 Stats:</strong>
            <span class="stat-pill">{duration_str}</span>
            <span class="stat-pill">{total_messages} msgs</span>
            <span class="stat-pill">{total_tool_calls} tools</span>
            <span class="stat-pill">{format_token_count(total_tokens)} tokens</span>
        </p>
"""

    return quick_summary + f"""
        <div class="stats-section">
            <details class="stats-container">
                <summary>View detailed statistics</summary>
                <div class="stats-content">
                    <div class="stats-row">
                        <span class="stat-item">
                            <span class="stat-label">Duration:</span> {duration_str}
                        </span>
                        <span class="stat-item">
                            <span class="stat-label">Messages:</span> {stats.get('user_messages', 0)} user / {stats.get('claude_messages', 0)} assistant
                        </span>
                        <span class="stat-item">
                            <span class="stat-label">Tool Calls:</span> {total_tool_calls}
                        </span>
                    </div>
                    <div class="stats-row">
                        <span class="stat-item">
                            <span class="stat-label">Input Tokens:</span> {total_input}
                        </span>
                        <span class="stat-item">
                            <span class="stat-label">Output Tokens:</span> {total_output}
                        </span>
                        <span class="stat-item">
                            <span class="stat-label">Cache Read:</span> {cache_read}
                        </span>
                        <span class="stat-item">
                            <span class="stat-label">Total:</span> {format_token_count(total_tokens)}
                        </span>
                    </div>
                    <div class="stats-row">
                        {tools_html}
                    </div>
                </div>
            </details>
        </div>
"""


def convert_to_html(jsonl_path, project_dir, session_id, config, created_date=None):
    """Convert JSONL transcript to HTML."""
    conversation, tool_calls, first_timestamp, stats = parse_conversation(jsonl_path, config)

    project_name = Path(project_dir).name

    # Generate summary
    if config.get("generate_summary", True):
        summary = generate_summary(conversation, project_name)
    else:
        summary = ""

    # Generate title from format string
    title_format = config.get("title_format", "{project_name} Conversations")
    title = title_format.format(project_name=project_name, summary=summary)

    html_template = get_html_template(config.get("theme", "dark"), config)

    content_html = ""
    for msg in conversation:
        if not msg["content"].strip() and not msg["tools"]:
            continue
        content_html += render_message(msg, tool_calls, config)

    # Format timestamps (all in UTC for consistency with conversation timestamps)
    date_format = config.get("date_format", "%Y-%m-%d %H:%M:%S")
    from datetime import timezone
    formatted_timestamp = datetime.now(timezone.utc).strftime(date_format)

    # Use created_date if provided (resumed session), otherwise use first message timestamp
    if created_date:
        formatted_created = created_date
    elif first_timestamp:
        # Parse and format the first message timestamp from the JSONL (keep UTC)
        try:
            dt = datetime.fromisoformat(first_timestamp.replace('Z', '+00:00'))
            formatted_created = dt.strftime(date_format)
        except:
            formatted_created = first_timestamp
    else:
        formatted_created = formatted_timestamp

    # Render statistics section
    stats_html = render_stats_section(stats, config)

    # Use replace instead of format to avoid issues with CSS braces
    result = html_template
    result = result.replace("{title}", escape_html(title))
    result = result.replace("{summary}", escape_html(summary))
    result = result.replace("{session_id}", escape_html(session_id))
    result = result.replace("{short_id}", escape_html(session_id[:8] if len(session_id) > 8 else session_id))
    result = result.replace("{project_dir}", escape_html(project_dir))
    result = result.replace("{created}", formatted_created)
    result = result.replace("{timestamp}", formatted_timestamp)
    result = result.replace("{stats_section}", stats_html)
    result = result.replace("{content}", content_html)

    return result, summary


def get_output_directory(project_dir, config):
    """Determine output directory based on config."""
    central_location = config.get("central_export_location")

    if central_location:
        # Expand ~ and create path
        central_path = Path(os.path.expanduser(central_location))
        # Create project subfolder in central location
        project_name = Path(project_dir).name
        return central_path / project_name
    else:
        # Use project-relative output_dir
        output_subdir = config.get("output_dir", "artifacts/conversations")
        return Path(project_dir) / output_subdir


def slugify(text, max_length=50):
    """Convert text to URL-friendly slug."""
    # Convert to lowercase and replace spaces with hyphens
    slug = text.lower().strip()
    slug = re.sub(r'[^\w\s-]', '', slug)  # Remove special chars
    slug = re.sub(r'[\s_]+', '-', slug)   # Replace spaces/underscores with hyphens
    slug = re.sub(r'-+', '-', slug)       # Remove multiple hyphens
    slug = slug.strip('-')                # Remove leading/trailing hyphens
    return slug[:max_length]


def find_existing_session_files(output_dir, short_id):
    """Find existing files for this session ID."""
    # Match both formats:
    # - New format: {session_id}_{summary}.html (e.g., b8d52f27_implementing-auth.html)
    # - Legacy format: {timestamp}_{session_id}.html (e.g., 20240204_182953_b8d52f27.html)
    html_files = glob.glob(str(output_dir / f"{short_id}_*.html"))
    html_files += glob.glob(str(output_dir / f"*_{short_id}.html"))
    jsonl_files = glob.glob(str(output_dir / f"{short_id}_*.jsonl"))
    jsonl_files += glob.glob(str(output_dir / f"*_{short_id}.jsonl"))
    # Remove duplicates while preserving order
    html_files = list(dict.fromkeys(html_files))
    jsonl_files = list(dict.fromkeys(jsonl_files))
    return html_files, jsonl_files


def extract_created_date(html_path):
    """Extract the 'Created' date from an existing HTML file."""
    try:
        with open(html_path, 'r') as f:
            content = f.read()
        match = re.search(r'<strong>Created(?: \(UTC\))?:</strong>\s*([^<]+)', content)
        if match:
            return match.group(1).strip()
    except:
        pass
    return None


def update_sessions_index(index_path, short_id, html_filename, jsonl_filename, timestamp, project_name, summary):
    """Update or add entry in sessions index."""
    entries = {}
    header_lines = []

    if index_path.exists():
        with open(index_path, 'r') as f:
            lines = f.readlines()

        in_table = False
        for line in lines:
            if line.startswith('|') and 'Session ID' in line:
                in_table = True
                header_lines.append(line)
            elif line.startswith('|---'):
                header_lines.append(line)
            elif line.startswith('|') and in_table:
                parts = [p.strip() for p in line.split('|')[1:-1]]
                if len(parts) >= 2:
                    existing_id = parts[1].strip('` ')
                    entries[existing_id] = line
            elif not in_table:
                header_lines.append(line)

    # Include summary in the entry
    new_entry = f"| {timestamp} | `{short_id}` | {project_name} | {summary} | [{html_filename}](./{html_filename}) |\n"
    entries[short_id] = new_entry

    with open(index_path, 'w') as f:
        if header_lines:
            # Check if header has summary column, if not, update it
            if 'Summary' not in header_lines[0]:
                header_lines = []

        if not header_lines:
            f.write("# Conversation Sessions Index\n\n")
            f.write("| Last Updated | Session ID | Project | Summary | HTML |\n")
            f.write("|--------------|------------|---------|---------|------|\n")
        else:
            f.writelines(header_lines)

        for entry in sorted(entries.values(), reverse=True):
            f.write(entry)


def main():
    # Load configuration
    config = load_config()

    # Read hook input from stdin
    try:
        hook_input = json.load(sys.stdin)
    except json.JSONDecodeError as e:
        print(f"Error parsing hook input: {e}", file=sys.stderr)
        sys.exit(1)

    session_id = hook_input.get("session_id", "unknown")
    transcript_path = hook_input.get("transcript_path", "")
    project_dir = hook_input.get("cwd", "")

    if not transcript_path or not os.path.exists(transcript_path):
        print(f"Transcript not found: {transcript_path}", file=sys.stderr)
        sys.exit(0)

    if not project_dir:
        print("No project directory provided", file=sys.stderr)
        sys.exit(0)

    # Get output directory (central or per-project)
    output_dir = get_output_directory(project_dir, config)
    output_dir.mkdir(parents=True, exist_ok=True)

    project_name = Path(project_dir).name
    short_id = session_id[:8] if len(session_id) > 8 else session_id

    existing_html, existing_jsonl = find_existing_session_files(output_dir, short_id)

    # Track created date for resumed sessions
    created_date = None

    if existing_html:
        html_path = Path(existing_html[0])
        old_filename = html_path.name
        print(f"Updating existing export: {old_filename}")

        # Extract created date from existing file before deleting
        created_date = extract_created_date(html_path)

        # Remove old files
        for f in existing_html:
            os.remove(f)
        for f in existing_jsonl:
            os.remove(f)

        # Keep the same filename for resumed sessions
        html_filename = old_filename
    else:
        # Will set filename after generating summary
        html_filename = None
        print("Creating new export...")

    # Generate HTML content and summary first (needed for filename)
    try:
        html_content, summary = convert_to_html(transcript_path, project_dir, session_id, config, created_date)

        # Generate filename if new session
        if html_filename is None:
            summary_slug = slugify(summary) if summary else "session"
            html_filename = f"{short_id}_{summary_slug}.html"

            # Handle duplicates: check if filename already exists (different session, same summary)
            counter = 1
            base_filename = html_filename
            while (output_dir / html_filename).exists():
                name_without_ext = base_filename.rsplit('.', 1)[0]
                html_filename = f"{name_without_ext}-{counter}.html"
                counter += 1

            print(f"New export: {html_filename}")

        html_path = output_dir / html_filename
        jsonl_filename = html_filename.replace('.html', '.jsonl')
        jsonl_path = output_dir / jsonl_filename

        with open(html_path, 'w') as f:
            f.write(html_content)
        print(f"Exported conversation to: {html_path}")
        print(f"Summary: {summary}")
    except Exception as e:
        print(f"Error exporting HTML: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        summary = ""
        html_filename = f"{short_id}_session.html"
        jsonl_filename = html_filename.replace('.html', '.jsonl')
        html_path = output_dir / html_filename
        jsonl_path = output_dir / jsonl_filename

    try:
        import shutil
        shutil.copy2(transcript_path, jsonl_path)
        print(f"Copied raw transcript to: {jsonl_path}")
    except Exception as e:
        print(f"Error copying JSONL: {e}", file=sys.stderr)

    index_path = output_dir / "sessions_index.md"
    try:
        last_updated = datetime.now().strftime("%Y%m%d_%H%M%S")
        update_sessions_index(index_path, short_id, html_filename, jsonl_filename, last_updated, project_name, summary)
        print(f"Updated sessions index: {index_path}")
    except Exception as e:
        print(f"Error updating index: {e}", file=sys.stderr)



if __name__ == "__main__":
    main()
