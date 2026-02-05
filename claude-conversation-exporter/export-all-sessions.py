#!/usr/bin/env python3
"""
Batch export all Claude Code sessions to HTML.

Scans ~/.claude/projects/ for all session transcripts and exports them
using the same logic as the SessionEnd hook.

Usage:
    python export-all-sessions.py                    # Export all sessions
    python export-all-sessions.py --dry-run          # Preview without exporting
    python export-all-sessions.py --skip-existing    # Skip already exported sessions
    python export-all-sessions.py --project wireless # Filter by project name
    python export-all-sessions.py --since 2024-01-01 # Filter by date
    python export-all-sessions.py --central ~/exports # Override central location
"""

import os
import sys
import json
import glob
import argparse
import subprocess
from pathlib import Path
from datetime import datetime


def load_config():
    """Load configuration from user's config file."""
    config_path = Path.home() / ".claude" / "conversation-export-config.json"

    default_config = {
        "central_export_location": None,
        "output_dir": "artifacts/conversations",
    }

    if config_path.exists():
        try:
            with open(config_path, 'r') as f:
                user_config = json.load(f)
                default_config.update(user_config)
        except Exception as e:
            print(f"Warning: Could not load config: {e}", file=sys.stderr)

    return default_config


def decode_project_path(encoded_name):
    """
    Convert encoded project folder name back to actual path.
    Example: -Users-jagannath-Downloads-coding-wireless-epc
             -> /Users/jagannath/Downloads/coding/wireless-epc

    The challenge: Claude encodes paths by replacing '/' with '-', but folder names
    can also contain '-'. We solve this by testing which decoded path actually exists.
    """
    if encoded_name.startswith('-'):
        # Remove leading dash and split into parts
        parts = encoded_name[1:].split('-')
    else:
        parts = encoded_name.split('-')

    # Try to reconstruct the path by finding which combination of parts exists
    # Start from the beginning and greedily match existing directories
    result_parts = []
    i = 0

    while i < len(parts):
        # Try progressively longer combinations of remaining parts joined with dashes
        # Start with longest possible to prefer paths with dashes in folder names
        found = False

        for j in range(len(parts), i, -1):
            candidate_segment = '-'.join(parts[i:j])
            candidate_path = '/' + '/'.join(result_parts + [candidate_segment])

            if os.path.exists(candidate_path):
                result_parts.append(candidate_segment)
                i = j
                found = True
                break

        if not found:
            # No existing path found, just use single part
            result_parts.append(parts[i])
            i += 1

    return '/' + '/'.join(result_parts)


def get_session_modified_time(jsonl_path):
    """Get the last modified time of a session file."""
    try:
        return datetime.fromtimestamp(os.path.getmtime(jsonl_path))
    except:
        return None


def get_session_created_time(jsonl_path):
    """Get the creation time from the first entry in the JSONL file."""
    try:
        with open(jsonl_path, 'r') as f:
            first_line = f.readline()
            if first_line:
                data = json.loads(first_line)
                if 'timestamp' in data:
                    return datetime.fromisoformat(data['timestamp'].replace('Z', '+00:00'))
    except:
        pass
    return get_session_modified_time(jsonl_path)


def find_all_sessions(projects_dir):
    """
    Find all session files across all projects.
    Returns list of dicts with session info.
    """
    sessions = []

    if not projects_dir.exists():
        print(f"Projects directory not found: {projects_dir}", file=sys.stderr)
        return sessions

    for project_folder in projects_dir.iterdir():
        if not project_folder.is_dir():
            continue

        # Decode the project path
        project_path = decode_project_path(project_folder.name)
        project_name = Path(project_path).name

        # Find all JSONL files in this project
        for jsonl_file in project_folder.glob("*.jsonl"):
            session_id = jsonl_file.stem  # filename without extension

            sessions.append({
                'session_id': session_id,
                'short_id': session_id[:8] if len(session_id) > 8 else session_id,
                'transcript_path': str(jsonl_file),
                'cwd': project_path,
                'project_name': project_name,
                'project_folder': str(project_folder),
                'modified_time': get_session_modified_time(jsonl_file),
                'file_size': jsonl_file.stat().st_size,
            })

    # Sort by modified time, newest first
    sessions.sort(key=lambda x: x['modified_time'] or datetime.min, reverse=True)

    return sessions


def check_existing_export(session, config, central_location=None):
    """Check if a session has already been exported."""
    short_id = session['short_id']

    # Determine output directory
    if central_location:
        output_dir = Path(central_location) / session['project_name']
    elif config.get('central_export_location'):
        output_dir = Path(config['central_export_location']) / session['project_name']
    else:
        output_dir = Path(session['cwd']) / config.get('output_dir', 'artifacts/conversations')

    if not output_dir.exists():
        return None

    # Check both filename formats
    patterns = [
        str(output_dir / f"{short_id}_*.html"),
        str(output_dir / f"*_{short_id}.html"),
    ]

    for pattern in patterns:
        matches = glob.glob(pattern)
        if matches:
            return matches[0]

    return None


def export_session(session, export_script_path, dry_run=False):
    """Export a single session using the export script."""
    hook_input = {
        'session_id': session['session_id'],
        'transcript_path': session['transcript_path'],
        'cwd': session['cwd'],
    }

    if dry_run:
        return True, "Dry run - would export"

    try:
        result = subprocess.run(
            [sys.executable, str(export_script_path)],
            input=json.dumps(hook_input),
            capture_output=True,
            text=True,
            timeout=60,
        )

        if result.returncode == 0:
            return True, result.stdout.strip()
        else:
            return False, result.stderr.strip() or "Unknown error"

    except subprocess.TimeoutExpired:
        return False, "Export timed out"
    except Exception as e:
        return False, str(e)


def format_size(size_bytes):
    """Format file size in human-readable format."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"


def main():
    parser = argparse.ArgumentParser(
        description='Batch export all Claude Code sessions to HTML',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python export-all-sessions.py                      # Export all sessions
  python export-all-sessions.py --dry-run            # Preview what would be exported
  python export-all-sessions.py --skip-existing      # Only export new sessions
  python export-all-sessions.py --project wireless   # Filter by project name
  python export-all-sessions.py --since 2024-01-01   # Only sessions after date
  python export-all-sessions.py --list               # Just list sessions, don't export
  python export-all-sessions.py --central ~/exports  # Export all to central location
        """
    )

    parser.add_argument('--dry-run', '-n', action='store_true',
                        help='Preview exports without actually running them')
    parser.add_argument('--skip-existing', '-s', action='store_true',
                        help='Skip sessions that have already been exported')
    parser.add_argument('--project', '-p', type=str,
                        help='Filter by project name (partial match)')
    parser.add_argument('--since', type=str,
                        help='Only export sessions modified after this date (YYYY-MM-DD)')
    parser.add_argument('--before', type=str,
                        help='Only export sessions modified before this date (YYYY-MM-DD)')
    parser.add_argument('--list', '-l', action='store_true',
                        help='List all sessions without exporting')
    parser.add_argument('--central', type=str,
                        help='Override central export location')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='Show detailed output')

    args = parser.parse_args()

    # Load config
    config = load_config()

    # Find export script (in same directory as this script)
    script_dir = Path(__file__).parent
    export_script = script_dir / "export-conversation.py"

    if not export_script.exists():
        # Try the installed location
        export_script = Path.home() / ".claude" / "hooks" / "export-conversation.py"

    if not export_script.exists() and not args.list:
        print(f"Error: Export script not found at {export_script}", file=sys.stderr)
        print("Make sure export-conversation.py is in the same directory or installed.", file=sys.stderr)
        sys.exit(1)

    # Find all sessions
    projects_dir = Path.home() / ".claude" / "projects"
    sessions = find_all_sessions(projects_dir)

    if not sessions:
        print("No sessions found.")
        sys.exit(0)

    # Apply filters
    if args.project:
        sessions = [s for s in sessions if args.project.lower() in s['project_name'].lower()]

    if args.since:
        try:
            since_date = datetime.strptime(args.since, '%Y-%m-%d')
            sessions = [s for s in sessions if s['modified_time'] and s['modified_time'] >= since_date]
        except ValueError:
            print(f"Invalid date format: {args.since}. Use YYYY-MM-DD", file=sys.stderr)
            sys.exit(1)

    if args.before:
        try:
            before_date = datetime.strptime(args.before, '%Y-%m-%d')
            sessions = [s for s in sessions if s['modified_time'] and s['modified_time'] < before_date]
        except ValueError:
            print(f"Invalid date format: {args.before}. Use YYYY-MM-DD", file=sys.stderr)
            sys.exit(1)

    # List mode
    if args.list:
        print(f"\nFound {len(sessions)} session(s):\n")
        print(f"{'Session ID':<12} {'Project':<30} {'Modified':<20} {'Size':<10} {'Exported?':<10}")
        print("-" * 90)

        for session in sessions:
            existing = check_existing_export(session, config, args.central)
            exported = "Yes" if existing else "No"
            modified = session['modified_time'].strftime('%Y-%m-%d %H:%M') if session['modified_time'] else 'Unknown'
            size = format_size(session['file_size'])

            print(f"{session['short_id']:<12} {session['project_name']:<30} {modified:<20} {size:<10} {exported:<10}")

        print()
        sys.exit(0)

    # Check for existing exports if skip-existing
    if args.skip_existing:
        original_count = len(sessions)
        sessions = [s for s in sessions if not check_existing_export(s, config, args.central)]
        skipped = original_count - len(sessions)
        if skipped > 0:
            print(f"Skipping {skipped} already exported session(s)")

    if not sessions:
        print("No sessions to export after applying filters.")
        sys.exit(0)

    # Export sessions
    print(f"\n{'[DRY RUN] ' if args.dry_run else ''}Exporting {len(sessions)} session(s)...\n")

    success_count = 0
    fail_count = 0

    for i, session in enumerate(sessions, 1):
        prefix = f"[{i}/{len(sessions)}]"
        project_info = f"{session['project_name']} ({session['short_id']})"

        print(f"{prefix} {project_info}...", end=' ', flush=True)

        success, message = export_session(session, export_script, args.dry_run)

        if success:
            success_count += 1
            if args.verbose:
                print(f"OK\n    {message}")
            else:
                print("OK")
        else:
            fail_count += 1
            print(f"FAILED\n    {message}")

    # Summary
    print(f"\n{'[DRY RUN] ' if args.dry_run else ''}Complete: {success_count} exported, {fail_count} failed")

    if args.dry_run:
        print("\nRun without --dry-run to actually export.")


if __name__ == "__main__":
    main()
