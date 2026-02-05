#!/usr/bin/env python3
"""
Codex Conversation Exporter
Export Codex CLI conversations to HTML and Markdown with collapsible tool details.
"""

import argparse
import glob
import html
import json
import os
import re
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


DEFAULT_CONFIG = {
    "user_name": "You",
    "assistant_name": "Codex",
    "user_emoji": "👤",
    "assistant_emoji": "🤖",
    "theme": "auto",
    "custom_colors": None,
    "font_size": "16px",
    "line_height": "1.75",
    "letter_spacing": "0.01em",
    "max_width": "920px",
    "padding": "24px",
    "central_export_location": None,
    "output_dir": "artifacts/conversations/codex",
    "title_format": "{project_name} Conversations",
    "include_thinking": False,
    "generate_summary": True,
    "show_session_id": True,
    "show_project_path": True,
    "show_timestamp": True,
    "show_summary": True,
    "show_statistics": True,
    "max_tool_result_length": 1000,
    "max_tool_input_length": 500,
    "date_format": "%Y-%m-%d %H:%M:%S",
    "time_format": "%H:%M:%S",
}

STOP_WORDS = {
    "i", "me", "my", "we", "our", "you", "your", "the", "a", "an", "is", "are",
    "was", "were", "be", "been", "being", "have", "has", "had", "do", "does",
    "did", "will", "would", "could", "should", "may", "might", "must", "shall",
    "can", "to", "of", "in", "for", "on", "with", "at", "by", "from", "as",
    "into", "through", "during", "before", "after", "above", "below", "between",
    "under", "again", "further", "then", "once", "here", "there", "when", "where",
    "why", "how", "all", "each", "few", "more", "most", "other", "some", "such",
    "no", "nor", "not", "only", "own", "same", "so", "than", "too", "very",
    "just", "and", "but", "if", "or", "because", "as", "until", "while", "of",
    "this", "that", "these", "those", "am", "it", "its", "also", "about", "like",
    "want", "need", "please", "help", "make", "get", "let", "see", "look", "thing",
    "something", "anything", "everything", "nothing", "use", "using", "used",
}

THEMES = {
    "dark": {
        "bg_color": "#1e1e2e",
        "card_bg": "#1a1a2e",
        "user_bg": "#1a365d",
        "assistant_bg": "#1e1e2e",
        "text_color": "#f0f0f0",
        "text_muted": "#b8b8c8",
        "accent": "#f06292",
        "accent_soft": "#7c6bba",
        "border_color": "#3a3a5a",
        "code_bg": "#141422",
        "tool_bg": "#1a2535",
    },
    "light": {
        "bg_color": "#fafafa",
        "card_bg": "#ffffff",
        "user_bg": "#e8f4fc",
        "assistant_bg": "#ffffff",
        "text_color": "#2d2d2d",
        "text_muted": "#5a5a6a",
        "accent": "#2563eb",
        "accent_soft": "#7c3aed",
        "border_color": "#e2e2e8",
        "code_bg": "#f4f4f8",
        "tool_bg": "#f8f8fc",
    },
    "solarized-dark": {
        "bg_color": "#002b36",
        "card_bg": "#073642",
        "user_bg": "#094552",
        "assistant_bg": "#073642",
        "text_color": "#839496",
        "text_muted": "#657b83",
        "accent": "#cb4b16",
        "accent_soft": "#6c71c4",
        "border_color": "#586e75",
        "code_bg": "#002b36",
        "tool_bg": "#073642",
    },
    "solarized-light": {
        "bg_color": "#fdf6e3",
        "card_bg": "#eee8d5",
        "user_bg": "#e4ddc8",
        "assistant_bg": "#eee8d5",
        "text_color": "#657b83",
        "text_muted": "#93a1a1",
        "accent": "#cb4b16",
        "accent_soft": "#6c71c4",
        "border_color": "#93a1a1",
        "code_bg": "#fdf6e3",
        "tool_bg": "#eee8d5",
    },
    "monokai": {
        "bg_color": "#272822",
        "card_bg": "#2d2e27",
        "user_bg": "#3e3d32",
        "assistant_bg": "#2d2e27",
        "text_color": "#f8f8f2",
        "text_muted": "#b9b9b0",
        "accent": "#a6e22e",
        "accent_soft": "#66d9ef",
        "border_color": "#49483e",
        "code_bg": "#1e1f1c",
        "tool_bg": "#2a2b24",
    },
    "github-dark": {
        "bg_color": "#0d1117",
        "card_bg": "#161b22",
        "user_bg": "#1f2937",
        "assistant_bg": "#161b22",
        "text_color": "#c9d1d9",
        "text_muted": "#8b949e",
        "accent": "#58a6ff",
        "accent_soft": "#79c0ff",
        "border_color": "#30363d",
        "code_bg": "#0d1117",
        "tool_bg": "#0f1520",
    },
    "github-light": {
        "bg_color": "#ffffff",
        "card_bg": "#f6f8fa",
        "user_bg": "#e7f3ff",
        "assistant_bg": "#f6f8fa",
        "text_color": "#24292f",
        "text_muted": "#57606a",
        "accent": "#0969da",
        "accent_soft": "#218bff",
        "border_color": "#d0d7de",
        "code_bg": "#f6f8fa",
        "tool_bg": "#f0f3f6",
    },
    "dracula": {
        "bg_color": "#282a36",
        "card_bg": "#2f313d",
        "user_bg": "#3b3d49",
        "assistant_bg": "#2f313d",
        "text_color": "#f8f8f2",
        "text_muted": "#bd93f9",
        "accent": "#ff79c6",
        "accent_soft": "#8be9fd",
        "border_color": "#44475a",
        "code_bg": "#21222c",
        "tool_bg": "#2b2d38",
    },
    "nord": {
        "bg_color": "#2e3440",
        "card_bg": "#3b4252",
        "user_bg": "#434c5e",
        "assistant_bg": "#3b4252",
        "text_color": "#eceff4",
        "text_muted": "#d8dee9",
        "accent": "#88c0d0",
        "accent_soft": "#81a1c1",
        "border_color": "#4c566a",
        "code_bg": "#2e3440",
        "tool_bg": "#3b4252",
    },
}

AUTO_THEME_DARK = THEMES["dark"]
AUTO_THEME_LIGHT = THEMES["light"]


def load_config():
    config_path = Path.home() / ".codex" / "conversation-export-config.json"
    config = DEFAULT_CONFIG.copy()
    if config_path.exists():
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                user_config = json.load(f)
            user_config = {k: v for k, v in user_config.items() if not k.startswith("_")}
            config.update(user_config)
        except (json.JSONDecodeError, IOError) as e:
            print(f"Warning: could not load config: {e}", file=sys.stderr)

    custom_colors = config.get("custom_colors") or {}
    if "claude_bg" in custom_colors and "assistant_bg" not in custom_colors:
        custom_colors["assistant_bg"] = custom_colors["claude_bg"]
    config["custom_colors"] = custom_colors
    return config


def generate_summary(conversation, project_name, max_words=5):
    user_texts = []
    for msg in conversation[:10]:
        if msg["type"] == "user":
            user_texts.append(msg["content"])
            if len(user_texts) >= 5:
                break

    if not user_texts:
        return f"{project_name} session"

    combined_text = " ".join(user_texts).lower()
    combined_text = re.sub(r"```.*?```", "", combined_text, flags=re.DOTALL)
    combined_text = re.sub(r"https?://\S+", "", combined_text)
    combined_text = re.sub(r"/[\w/.-]+", "", combined_text)
    combined_text = re.sub(r"`[^`]+`", "", combined_text)

    words = re.findall(r"\b[a-z]{3,}\b", combined_text)
    meaningful_words = [w for w in words if w not in STOP_WORDS]
    word_counts = Counter(meaningful_words)
    top_words = [word for word, _ in word_counts.most_common(max_words)]

    if not top_words:
        return f"{project_name} session"

    first_msg = user_texts[0].lower()
    action_patterns = [
        (r"\b(create|build|make|develop|implement)\b.*?\b(\w+)", "building"),
        (r"\b(fix|debug|solve|resolve)\b.*?\b(\w+)", "fixing"),
        (r"\b(add|integrate|include)\b.*?\b(\w+)", "adding"),
        (r"\b(update|modify|change|edit)\b.*?\b(\w+)", "updating"),
        (r"\b(setup|configure|install)\b.*?\b(\w+)", "setting up"),
        (r"\b(export|convert|transform)\b.*?\b(\w+)", "exporting"),
        (r"\b(test|verify|check)\b.*?\b(\w+)", "testing"),
        (r"\b(refactor|optimize|improve)\b.*?\b(\w+)", "improving"),
    ]

    for pattern, action in action_patterns:
        match = re.search(pattern, first_msg)
        if match:
            keywords = " ".join(top_words[:3])
            return f"{action} {keywords}".title()

    summary = " ".join(top_words[:4])
    return summary.title() if summary else f"{project_name} session"


def get_html_template(theme_name, config):
    custom_colors = config.get("custom_colors") or {}
    is_auto = theme_name == "auto"

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
    meta_items.append('<p class="tip"><em>Tip: You can rename this file (keep the <code>{short_id}_</code> prefix) and it will be preserved on resume.</em></p>')
    meta_items.append('{stats_section}')

    meta_html = "\n            ".join(meta_items) if meta_items else ""

    def apply_custom(theme_dict):
        result = theme_dict.copy()
        result.update(custom_colors)
        return result

    def theme_to_css_vars(theme):
        return f"""
            --bg-color: {theme["bg_color"]};
            --card-bg: {theme["card_bg"]};
            --user-bg: {theme["user_bg"]};
            --assistant-bg: {theme["assistant_bg"]};
            --text-color: {theme["text_color"]};
            --text-muted: {theme["text_muted"]};
            --accent: {theme["accent"]};
            --accent-soft: {theme["accent_soft"]};
            --border-color: {theme["border_color"]};
            --code-bg: {theme["code_bg"]};
            --tool-bg: {theme["tool_bg"]};"""

    if is_auto:
        dark_theme = apply_custom(AUTO_THEME_DARK)
        light_theme = apply_custom(AUTO_THEME_LIGHT)
        css_vars = f"""
        :root {{
            {theme_to_css_vars(light_theme)}
        }}

        @media (prefers-color-scheme: dark) {{
            :root {{
                {theme_to_css_vars(dark_theme)}
            }}
        }}"""
    else:
        theme = apply_custom(THEMES.get(theme_name, THEMES["dark"]))
        css_vars = f"""
        :root {{
            {theme_to_css_vars(theme)}
        }}"""

    css = css_vars + f"""
        * {{
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            background-color: var(--bg-color);
            color: var(--text-color);
            font-size: {config.get("font_size", "16px")};
            line-height: {config.get("line_height", "1.75")};
            letter-spacing: {config.get("letter_spacing", "0.01em")};
            margin: 0;
            padding: {config.get("padding", "24px")};
            max-width: {config.get("max_width", "920px")};
            margin: 0 auto;
        }}

        header {{
            background: var(--card-bg);
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 30px;
            border: 1px solid var(--border-color);
        }}

        header h1 {{
            margin: 0 0 10px 0;
            color: var(--accent);
        }}

        header .meta {{
            color: var(--text-muted);
            font-size: 0.9em;
        }}

        header .meta code {{
            background: var(--code-bg);
            padding: 2px 6px;
            border-radius: 4px;
            color: var(--accent);
        }}

        header .tip {{
            margin-top: 10px;
            font-size: 0.85em;
            color: var(--text-muted);
        }}

        .message {{
            background: var(--card-bg);
            padding: 16px 20px;
            border-radius: 12px;
            margin-bottom: 20px;
            border: 1px solid var(--border-color);
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
        }}

        .message.user {{
            background: var(--user-bg);
        }}

        .message.assistant {{
            background: var(--assistant-bg);
        }}

        .message-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 12px;
            padding-bottom: 8px;
            border-bottom: 1px solid var(--border-color);
        }}

        .message-header .role {{
            font-weight: bold;
            font-size: 0.95em;
        }}

        .message-header .user-role {{
            color: var(--accent);
        }}

        .message-header .assistant-role {{
            color: var(--accent-soft);
        }}

        .message-header .header-right {{
            display: flex;
            align-items: center;
            gap: 10px;
        }}

        .timestamp {{
            font-size: 0.85em;
            color: var(--text-muted);
        }}

        .message-content {{
            line-height: 1.6;
        }}

        .message-content code {{
            background: var(--code-bg);
            padding: 2px 6px;
            border-radius: 4px;
            font-family: 'SF Mono', Consolas, Monaco, monospace;
            font-size: 0.9em;
        }}

        .message-content pre {{
            background: var(--code-bg);
            padding: 12px;
            border-radius: 8px;
            overflow-x: auto;
            font-size: 0.9em;
        }}

        .message-content pre code {{
            background: none;
            padding: 0;
        }}

        .tools-container {{
            margin-bottom: 10px;
            background: var(--tool-bg);
            border-radius: 8px;
            border: 1px solid var(--border-color);
        }}

        .tools-container summary {{
            padding: 10px 14px;
            cursor: pointer;
            font-weight: 500;
            color: var(--accent);
        }}

        .tools-list {{
            padding: 0 14px 10px 14px;
        }}

        .tool-item {{
            margin: 8px 0;
            border-left: 3px solid var(--accent-soft);
            padding-left: 10px;
        }}

        .tool-item h4 {{
            margin: 6px 0 4px 0;
            font-size: 0.9em;
            color: var(--text-muted);
        }}

        .tool-item pre {{
            background: var(--code-bg);
            padding: 8px;
            border-radius: 6px;
            font-size: 0.85em;
            overflow-x: auto;
        }}

        .stats-quick {{
            margin-top: 12px;
            padding: 10px;
            background: var(--tool-bg);
            border-radius: 8px;
            border: 1px solid var(--border-color);
        }}

        .stat-pill {{
            display: inline-block;
            background: var(--card-bg);
            border: 1px solid var(--border-color);
            padding: 4px 8px;
            border-radius: 999px;
            margin-right: 6px;
        }}

        .stats-container summary {{
            cursor: pointer;
            padding: 10px 14px;
            color: var(--accent);
        }}

        .stats-content {{
            padding: 10px 14px 14px 14px;
        }}

        .stats-row {{
            display: flex;
            flex-wrap: wrap;
            gap: 12px;
            margin-bottom: 8px;
            color: var(--text-muted);
        }}

        .stat-item {{
            background: var(--tool-bg);
            border-radius: 6px;
            padding: 6px 10px;
            border: 1px solid var(--border-color);
        }}

        .theme-toggle {{
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 8px 14px;
            border: 1px solid var(--border-color);
            background: var(--card-bg);
            color: var(--text-color);
            border-radius: 20px;
            cursor: pointer;
            font-size: 0.9em;
        }}

        @media print {{
            .theme-toggle,
            .tools-container,
            details,
            .stats-quick,
            .stats-section,
            .tip {{
                display: none;
            }}
        }}
    """

    theme_toggle_js = """
    <script>
    (function() {
        const root = document.documentElement;
        const STORAGE_KEY = 'codex-theme';

        const themes = {
            dark: {
                'bg-color': '#1e1e2e',
                'card-bg': '#1a1a2e',
                'user-bg': '#1a365d',
                'assistant-bg': '#1e1e2e',
                'text-color': '#f0f0f0',
                'text-muted': '#b8b8c8',
                'accent': '#f06292',
                'accent-soft': '#7c6bba',
                'border-color': '#3a3a5a',
                'code-bg': '#141422',
                'tool-bg': '#1a2535'
            },
            light: {
                'bg-color': '#fafafa',
                'card-bg': '#ffffff',
                'user-bg': '#e8f4fc',
                'assistant-bg': '#ffffff',
                'text-color': '#2d2d2d',
                'text-muted': '#5a5a6a',
                'accent': '#2563eb',
                'accent-soft': '#7c3aed',
                'border-color': '#e2e2e8',
                'code-bg': '#f4f4f8',
                'tool-bg': '#f8f8fc'
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
                root.style.setProperty(`--${prop}`, value);
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

        document.addEventListener('DOMContentLoaded', function() {
            applyTheme(getPreferredTheme());
            const btn = document.getElementById('theme-toggle');
            if (btn) {
                btn.addEventListener('click', toggleTheme);
            }
        });

        window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', function(e) {
            if (!localStorage.getItem(STORAGE_KEY)) {
                applyTheme(e.matches ? 'dark' : 'light');
            }
        });
    })();
    </script>
    """

    html_tpl = """<!DOCTYPE html>
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
    return html_tpl


def escape_html(text):
    if not text:
        return ""
    return html.escape(str(text))


def format_timestamp(ts, config):
    if not ts:
        return ""
    try:
        dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        return dt.strftime(config.get("time_format", "%H:%M:%S"))
    except ValueError:
        return ts[:19] if len(ts) >= 19 else ts


def format_tool_call(tool_name, tool_input, config):
    max_length = config.get("max_tool_input_length", 500)
    content = tool_input
    if len(content) > max_length:
        content = content[:max_length] + "..."
    return f"<pre><code>{escape_html(content)}</code></pre>"


def format_tool_output(tool_output, config):
    max_length = config.get("max_tool_result_length", 1000)
    content = tool_output
    if len(content) > max_length:
        content = content[:max_length] + "..."
    return f"<pre><code>{escape_html(content)}</code></pre>"


def render_tools_section(tools, config):
    if not tools:
        return ""

    tool_items_html = ""
    for tool in tools:
        label = tool.get("label", "tool")
        tool_items_html += f"""
                <div class="tool-item">
                    <h4>{escape_html(label)}</h4>
                    {tool.get("input_html", "")}
                    {tool.get("output_html", "")}
                </div>
"""

    return f"""
            <details class="tools-container">
                <summary>🛠️ Tools</summary>
                <div class="tools-list">
{tool_items_html}
                </div>
            </details>
"""


def render_message(msg, config):
    msg_type = msg["type"]
    timestamp = format_timestamp(msg["timestamp"], config)
    content = msg["content"]
    tools = msg.get("tools", [])

    user_emoji = config.get("user_emoji", "👤")
    assistant_emoji = config.get("assistant_emoji", "🤖")

    if msg_type == "user":
        role_class = "user"
        role_label = f"{user_emoji} {config['user_name']}"
        header_class = "user-role"
    else:
        role_class = "assistant"
        role_label = f"{assistant_emoji} {config['assistant_name']}"
        header_class = "assistant-role"

    tools_html = render_tools_section(tools, config)

    content_html = escape_html(content)
    content_html = re.sub(r"```(\w*)\n(.*?)```", r"<pre><code>\2</code></pre>", content_html, flags=re.DOTALL)
    content_html = re.sub(r"`([^`]+)`", r"<code>\1</code>", content_html)
    content_html = re.sub(r"^### (.+)$", r"<h3>\1</h3>", content_html, flags=re.MULTILINE)
    content_html = re.sub(r"^## (.+)$", r"<h2>\1</h2>", content_html, flags=re.MULTILINE)
    content_html = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", content_html)
    content_html = content_html.replace("\n\n", "</p><p>")
    content_html = f"<p>{content_html}</p>" if content_html else ""

    return f"""
        <div class="message {role_class}">
            <div class="message-header">
                <span class="role {header_class}">{role_label}</span>
                <span class="header-right">
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
    if seconds is None:
        return "N/A"
    if seconds < 60:
        return f"{int(seconds)}s"
    if seconds < 3600:
        mins = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{mins}m {secs}s"
    hours = int(seconds // 3600)
    mins = int((seconds % 3600) // 60)
    return f"{hours}h {mins}m"


def format_token_count(count):
    if count >= 1_000_000:
        return f"{count / 1_000_000:.1f}M"
    if count >= 1_000:
        return f"{count / 1_000:.1f}K"
    return str(count)


def render_stats_section(stats, config):
    if not config.get("show_statistics", True):
        return ""

    duration_str = format_duration(stats.get("duration_seconds"))
    total_input = format_token_count(stats.get("total_input_tokens", 0))
    total_output = format_token_count(stats.get("total_output_tokens", 0))
    cache_read = format_token_count(stats.get("cache_read_tokens", 0))
    total_tokens = stats.get("total_input_tokens", 0) + stats.get("total_output_tokens", 0)
    total_messages = stats.get("user_messages", 0) + stats.get("assistant_messages", 0)

    tool_usage = stats.get("tool_usage", Counter())
    top_tools = tool_usage.most_common(5)
    total_tool_calls = sum(tool_usage.values())

    tools_html = ""
    if top_tools:
        tools_items = ", ".join([f"{name} ({count})" for name, count in top_tools])
        if len(tool_usage) > 5:
            tools_items += f" +{len(tool_usage) - 5} more"
        tools_html = f'<span class="stat-item"><span class="stat-label">Tools:</span> {tools_items}</span>'

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
                            <span class="stat-label">Messages:</span> {stats.get('user_messages', 0)} user / {stats.get('assistant_messages', 0)} assistant
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


def parse_session(jsonl_path, config):
    meta = {}
    events = []
    conversation = []
    tool_by_call_id = {}
    pending_tools = []
    last_assistant_index = None
    token_totals = {}

    with open(jsonl_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue

            ts = obj.get("timestamp")
            entry_type = obj.get("type")
            payload = obj.get("payload", {})

            if entry_type == "session_meta":
                meta = payload
                continue

            if entry_type == "event_msg":
                if isinstance(payload, dict) and payload.get("type") == "token_count":
                    info = payload.get("info") or {}
                    if isinstance(info, dict):
                        totals = info.get("total_token_usage") or {}
                        if isinstance(totals, dict):
                            token_totals = totals
                continue

            if entry_type != "response_item":
                continue

            if not isinstance(payload, dict):
                continue

            payload_type = payload.get("type")
            if payload_type == "message":
                role = payload.get("role", "unknown")
                text = "".join(
                    [item.get("text", "") for item in payload.get("content", []) if item.get("type") in ("input_text", "output_text")]
                ).strip()
                if text:
                    events.append({"kind": "message", "role": role, "text": text, "ts": ts})
                    msg_type = "assistant" if role != "user" else "user"
                    msg = {"type": msg_type, "timestamp": ts, "content": text, "tools": []}
                    conversation.append(msg)
                    if msg_type == "assistant":
                        last_assistant_index = len(conversation) - 1
                        if pending_tools:
                            conversation[last_assistant_index]["tools"].extend(pending_tools)
                            pending_tools = []

            elif payload_type == "function_call":
                call_id = payload.get("call_id")
                name = payload.get("name", "tool")
                args = payload.get("arguments", "")
                events.append({"kind": "tool_call", "name": name, "args": args, "ts": ts, "call_id": call_id})

                tool_obj = {
                    "label": name,
                    "input_html": format_tool_call(name, args, config),
                    "output_html": "",
                }
                if call_id:
                    tool_by_call_id[call_id] = tool_obj

                if last_assistant_index is not None:
                    conversation[last_assistant_index]["tools"].append(tool_obj)
                else:
                    pending_tools.append(tool_obj)

            elif payload_type == "function_call_output":
                call_id = payload.get("call_id")
                output = payload.get("output", "")
                if output and len(output) > config.get("max_tool_result_length", 1000):
                    output = output[: config.get("max_tool_result_length", 1000)] + "..."
                events.append({"kind": "tool_output", "call_id": call_id, "output": output, "ts": ts})

                if call_id and call_id in tool_by_call_id:
                    tool_by_call_id[call_id]["output_html"] = format_tool_output(output, config)
                else:
                    tool_obj = {
                        "label": "tool_output",
                        "input_html": "",
                        "output_html": format_tool_output(output, config),
                    }
                    if last_assistant_index is not None:
                        conversation[last_assistant_index]["tools"].append(tool_obj)
                    else:
                        pending_tools.append(tool_obj)

    if pending_tools and conversation:
        conversation[-1]["tools"].extend(pending_tools)

    return meta, events, conversation, token_totals


def compute_stats(events, token_totals):
    user_messages = 0
    assistant_messages = 0
    tool_usage = Counter()
    first_ts = None
    last_ts = None

    for ev in events:
        ts = ev.get("ts")
        if ts and first_ts is None:
            first_ts = ts
        if ts:
            last_ts = ts
        if ev["kind"] == "message":
            if ev.get("role") == "user":
                user_messages += 1
            else:
                assistant_messages += 1
        if ev["kind"] == "tool_call":
            tool_usage[ev.get("name", "tool")] += 1

    duration_seconds = None
    if first_ts and last_ts:
        try:
            start = datetime.fromisoformat(first_ts.replace("Z", "+00:00"))
            end = datetime.fromisoformat(last_ts.replace("Z", "+00:00"))
            duration_seconds = (end - start).total_seconds()
        except ValueError:
            duration_seconds = None

    return {
        "duration_seconds": duration_seconds,
        "user_messages": user_messages,
        "assistant_messages": assistant_messages,
        "tool_usage": tool_usage,
        "total_input_tokens": token_totals.get("input_tokens", 0),
        "total_output_tokens": token_totals.get("output_tokens", 0),
        "cache_read_tokens": token_totals.get("cached_input_tokens", 0),
    }


def convert_to_html(jsonl_path, project_dir, session_id, config):
    meta, events, conversation, token_totals = parse_session(jsonl_path, config)
    stats = compute_stats(events, token_totals)

    project_name = Path(project_dir).name
    summary = generate_summary(conversation, project_name) if config.get("generate_summary", True) else ""
    title_format = config.get("title_format", "{project_name} Conversations")
    title = title_format.format(project_name=project_name, summary=summary)

    html_template = get_html_template(config.get("theme", "auto"), config)

    content_html = ""
    for msg in conversation:
        if not msg["content"].strip() and not msg["tools"]:
            continue
        content_html += render_message(msg, config)

    date_format = config.get("date_format", "%Y-%m-%d %H:%M:%S")
    formatted_timestamp = datetime.now(timezone.utc).strftime(date_format)

    created = formatted_timestamp
    if meta.get("timestamp"):
        try:
            dt = datetime.fromisoformat(meta["timestamp"].replace("Z", "+00:00"))
            created = dt.strftime(date_format)
        except ValueError:
            created = meta.get("timestamp")

    stats_html = render_stats_section(stats, config)

    result = html_template
    result = result.replace("{title}", escape_html(title))
    result = result.replace("{summary}", escape_html(summary))
    result = result.replace("{session_id}", escape_html(session_id))
    result = result.replace("{short_id}", escape_html(session_id[:8] if session_id else "session"))
    result = result.replace("{project_dir}", escape_html(project_dir))
    result = result.replace("{created}", created)
    result = result.replace("{timestamp}", formatted_timestamp)
    result = result.replace("{stats_section}", stats_html)
    result = result.replace("{content}", content_html)

    return result


def render_markdown(meta, events, jsonl_path):
    session_id = meta.get("id")
    cwd = meta.get("cwd")
    started_at = meta.get("timestamp")

    lines = ["# Codex Conversation Export", ""]
    if session_id:
        lines.append(f"Session ID: {session_id}")
    if started_at:
        lines.append(f"Started: {started_at}")
    if cwd:
        lines.append(f"CWD: {cwd}")
    lines.append(f"Source: {jsonl_path}")
    lines.append("")
    lines.append("---")
    lines.append("")

    for ev in events:
        if ev["kind"] == "message":
            role = ev.get("role", "unknown")
            ts = ev.get("ts") or ""
            lines.append(f"## {role} {ts}")
            lines.append("")
            lines.append(ev.get("text", ""))
            lines.append("")
        elif ev["kind"] == "tool_call":
            name = ev.get("name", "unknown")
            ts = ev.get("ts") or ""
            lines.append(f"### tool_call {name} {ts}")
            lines.append("")
            lines.append("```json")
            lines.append(ev.get("args", ""))
            lines.append("```")
            lines.append("")
        elif ev["kind"] == "tool_output":
            ts = ev.get("ts") or ""
            lines.append(f"### tool_output {ts}")
            lines.append("")
            lines.append("```")
            lines.append(ev.get("output", ""))
            lines.append("```")
            lines.append("")

    return "\n".join(lines).strip() + "\n"


def find_latest_session(root):
    pattern = os.path.join(root, "**", "rollout-*.jsonl")
    candidates = glob.glob(pattern, recursive=True)
    if not candidates:
        return None
    return max(candidates, key=os.path.getmtime)


def find_session_by_id(root, session_id):
    pattern = os.path.join(root, "**", f"*{session_id}*.jsonl")
    matches = glob.glob(pattern, recursive=True)
    if not matches:
        return None
    return max(matches, key=os.path.getmtime)


def get_output_directory(project_dir, config):
    central_location = config.get("central_export_location")
    if central_location:
        central_path = Path(os.path.expanduser(central_location))
        project_name = Path(project_dir).name
        return central_path / project_name
    output_subdir = config.get("output_dir", "artifacts/conversations/codex")
    return Path(project_dir) / output_subdir


def build_output_path(output_dir, session_id, started_at, ext):
    output_dir.mkdir(parents=True, exist_ok=True)
    if started_at:
        ts = datetime.fromisoformat(started_at.replace("Z", "+00:00")).strftime("%Y%m%dT%H%M%SZ")
    else:
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    filename = f"{ts}_{session_id}.{ext}" if session_id else f"{ts}_session.{ext}"
    return output_dir / filename


def main():
    parser = argparse.ArgumentParser(description="Export a Codex session to Markdown/HTML")
    parser.add_argument("--latest", action="store_true", help="Export the latest session")
    parser.add_argument("--session", help="Session ID or full path to a session JSONL file")
    parser.add_argument("--output", help="Output directory (overrides config/output_dir)")
    parser.add_argument("--format", choices=["md", "html", "both"], help="Export format")
    args = parser.parse_args()

    config = load_config()

    sessions_root = os.path.expanduser("~/.codex/sessions")
    if args.session:
        if os.path.isfile(args.session):
            session_path = args.session
        else:
            session_path = find_session_by_id(sessions_root, args.session)
    else:
        session_path = find_latest_session(sessions_root)

    if not session_path:
        print("No session file found.")
        return 1

    meta, events, conversation, token_totals = parse_session(session_path, config)
    session_id = meta.get("id")
    cwd = meta.get("cwd") or os.getcwd()

    output_dir = Path(args.output) if args.output else get_output_directory(cwd, config)
    output_format = args.format or os.getenv("CODEX_EXPORT_FORMAT") or "both"

    written = []

    if output_format in ("md", "both"):
        md_path = build_output_path(output_dir, session_id, meta.get("timestamp"), "md")
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(render_markdown(meta, events, session_path))
        written.append(str(md_path))

    if output_format in ("html", "both"):
        html_content = convert_to_html(session_path, cwd, session_id, config)
        html_path = build_output_path(output_dir, session_id, meta.get("timestamp"), "html")
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html_content)
        written.append(str(html_path))

    for path in written:
        print(path)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
