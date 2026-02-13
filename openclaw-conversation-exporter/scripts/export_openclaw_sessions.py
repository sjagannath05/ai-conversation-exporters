#!/usr/bin/env python3
"""
OpenClaw Conversation Exporter
Converts OpenClaw JSONL sessions to Claude Code format and exports via claude-conversation-exporter.

Usage:
    openclaw-export                  # Export all sessions
    openclaw-export --since today    # Export today's sessions only
    openclaw-export --since 2026-02-10  # Export since date
"""

import json
import os
import sys
import glob
import subprocess
from pathlib import Path
from datetime import datetime, timedelta

OPENCLAW_DIR = Path.home() / ".openclaw"
EXPORTER = Path.home() / "ai-conversation-exporters" / "claude-conversation-exporter" / "export-conversation.py"
EXPORT_DIR = Path.home() / "openclaw-export"
CONFIG_PATH = Path.home() / ".claude" / "conversation-export-config.json"


def ensure_config():
    """Create config if it doesn't exist."""
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not CONFIG_PATH.exists():
        config = {
            "user_name": "Jagannath",
            "assistant_name": "OpenClaw",
            "user_emoji": "👤",
            "assistant_emoji": "🤖",
            "theme": "auto",
            "generate_summary": True,
            "show_statistics": True,
            "include_thinking": False,
            "central_export_location": str(EXPORT_DIR),
            "max_tool_result_length": 1000,
            "max_tool_input_length": 500
        }
        with open(CONFIG_PATH, 'w') as f:
            json.dump(config, f, indent=2)
        print(f"Created config at {CONFIG_PATH}")


def parse_openclaw_session(filepath):
    """Parse OpenClaw JSONL into Claude Code compatible message list."""
    messages = []
    session_id = Path(filepath).stem
    project_path = str(Path(filepath).parent.parent.parent)
    agent_name = Path(filepath).parent.parent.name
    first_ts = None
    last_ts = None

    with open(filepath) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except:
                continue

            if entry.get("type") == "session":
                first_ts = entry.get("timestamp")
                continue

            if entry.get("type") != "message":
                continue

            msg = entry.get("message", {})
            role = msg.get("role")
            content = msg.get("content")
            ts = entry.get("timestamp", "")
            if ts:
                last_ts = ts

            if not first_ts and ts:
                first_ts = ts

            if not role or not content:
                continue

            # Convert to Claude Code format
            claude_msg = {"role": role}

            if isinstance(content, str):
                claude_msg["content"] = content
            elif isinstance(content, list):
                claude_msg["content"] = content
            else:
                continue

            # Add usage info if present
            usage = msg.get("usage", {})
            if usage:
                claude_msg["usage"] = usage
            
            model = msg.get("model", "")
            if model:
                claude_msg["model"] = model

            messages.append(claude_msg)

    return {
        "session_id": session_id,
        "agent": agent_name,
        "project_path": project_path,
        "messages": messages,
        "first_timestamp": first_ts,
        "last_timestamp": last_ts,
    }


def export_session(session_data, export_dir):
    """Export a parsed session to HTML."""
    if not session_data["messages"]:
        return False

    agent = session_data["agent"]
    sid = session_data["session_id"]
    out_dir = export_dir / agent
    out_dir.mkdir(parents=True, exist_ok=True)

    write_simple_html(session_data, out_dir / f"{sid}.html")
    print(f"  ✅ {agent}/{sid[:8]}...")
    return True


def write_simple_html(session_data, output_path):
    """Write a self-contained HTML export."""
    import html as html_mod

    agent = session_data["agent"]
    sid = session_data["session_id"]
    first_ts = session_data.get("first_timestamp", "")
    messages = session_data["messages"]

    user_count = sum(1 for m in messages if m["role"] == "user")
    asst_count = sum(1 for m in messages if m["role"] == "assistant")

    msg_html = []
    for msg in messages:
        role = msg["role"]
        content = msg.get("content", "")
        
        if isinstance(content, list):
            text_parts = []
            tool_parts = []
            for part in content:
                if isinstance(part, dict):
                    if part.get("type") == "text":
                        text_parts.append(part.get("text", ""))
                    elif part.get("type") == "toolCall":
                        tool_parts.append(f'<details><summary>🔧 {part.get("name", "tool")}()</summary><pre>{html_mod.escape(json.dumps(part.get("arguments", {}), indent=2)[:500])}</pre></details>')
                    elif part.get("type") == "tool_use":
                        tool_parts.append(f'<details><summary>🔧 {part.get("name", "tool")}()</summary><pre>{html_mod.escape(json.dumps(part.get("input", {}), indent=2)[:500])}</pre></details>')
                    elif part.get("type") == "tool_result":
                        text_parts.append(f"[tool result: {str(part.get('content', ''))[:200]}]")
            content = "\n".join(text_parts)
            if tool_parts:
                content += "\n" + "\n".join(tool_parts)
        
        if not isinstance(content, str):
            content = str(content)

        escaped = html_mod.escape(content).replace("\n", "<br>")
        role_class = "user" if role == "user" else "assistant"
        emoji = "👤" if role == "user" else "🤖"
        name = "Jagannath" if role == "user" else "OpenClaw"
        
        msg_html.append(f'''
        <div class="message {role_class}">
            <div class="role">{emoji} {name}</div>
            <div class="content">{escaped}</div>
        </div>''')

    html_content = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>OpenClaw — {agent}/{sid[:8]}</title>
<style>
:root {{ --bg: #1a1b26; --fg: #c0caf5; --user-bg: #24283b; --asst-bg: #1a1b26; --accent: #7aa2f7; --border: #3b4261; }}
@media (prefers-color-scheme: light) {{ :root {{ --bg: #fff; --fg: #24283b; --user-bg: #f0f0f5; --asst-bg: #fff; --accent: #2e7de9; --border: #ddd; }} }}
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: var(--bg); color: var(--fg); line-height: 1.7; padding: 2rem; max-width: 960px; margin: 0 auto; }}
.header {{ border-bottom: 2px solid var(--accent); padding-bottom: 1rem; margin-bottom: 2rem; }}
.header h1 {{ color: var(--accent); font-size: 1.5rem; }}
.stats {{ color: #888; font-size: 0.85rem; margin-top: 0.5rem; }}
.message {{ padding: 1rem; margin: 0.5rem 0; border-radius: 8px; border-left: 3px solid transparent; }}
.message.user {{ background: var(--user-bg); border-left-color: var(--accent); }}
.message.assistant {{ background: var(--asst-bg); border-left-color: #9ece6a; }}
.role {{ font-weight: 600; font-size: 0.85rem; margin-bottom: 0.3rem; color: var(--accent); }}
.assistant .role {{ color: #9ece6a; }}
.content {{ font-size: 0.95rem; white-space: pre-wrap; word-wrap: break-word; }}
details {{ margin-top: 0.5rem; }}
summary {{ cursor: pointer; color: var(--accent); font-size: 0.85rem; }}
pre {{ background: #0d0d0d; padding: 0.5rem; border-radius: 4px; overflow-x: auto; font-size: 0.8rem; margin-top: 0.3rem; }}
</style>
</head>
<body>
<div class="header">
    <h1>🤖 OpenClaw — {agent}</h1>
    <div class="stats">Session: {sid[:8]}... | Started: {first_ts[:19] if first_ts else 'unknown'} | {user_count} user + {asst_count} assistant messages</div>
</div>
{"".join(msg_html)}
</body>
</html>'''

    with open(output_path, 'w') as f:
        f.write(html_content)


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Export OpenClaw conversations")
    parser.add_argument("--since", help="Export sessions since date (YYYY-MM-DD or 'today')")
    parser.add_argument("--agent", help="Filter by agent name")
    parser.add_argument("--output", help="Output directory", default=str(EXPORT_DIR))
    args = parser.parse_args()

    export_dir = Path(args.output)
    export_dir.mkdir(parents=True, exist_ok=True)

    since_dt = None
    if args.since:
        if args.since == "today":
            since_dt = datetime.now().replace(hour=0, minute=0, second=0)
        else:
            since_dt = datetime.fromisoformat(args.since)

    ensure_config()

    # Find all session files
    patterns = [str(OPENCLAW_DIR / "agents" / "*" / "sessions" / "*.jsonl")]
    session_files = []
    for pattern in patterns:
        session_files.extend(glob.glob(pattern))

    # Filter by date if specified
    if since_dt:
        filtered = []
        for f in session_files:
            mtime = datetime.fromtimestamp(os.path.getmtime(f))
            if mtime >= since_dt:
                filtered.append(f)
        session_files = filtered

    # Filter by agent if specified
    if args.agent:
        session_files = [f for f in session_files if args.agent in f]

    # Exclude topic files (compaction artifacts)
    session_files = [f for f in session_files if "-topic-" not in f]

    print(f"📦 Exporting {len(session_files)} sessions to {export_dir}")

    exported = 0
    for filepath in sorted(session_files):
        session_data = parse_openclaw_session(filepath)
        if export_session(session_data, export_dir):
            exported += 1

    print(f"\n✅ Exported {exported} sessions to {export_dir}")


if __name__ == "__main__":
    main()
