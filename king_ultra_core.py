#!/usr/bin/env python3
"""
king_ultra_core.py — King Ultra Brain v2.0
CLI: python3 king_ultra_core.py <command> [brain_file] [args...]

Commands:
  init <brain_file>
  remember <brain_file> <text...>
  recall <brain_file> [query...]
  forget <brain_file> <id>
  clear <brain_file>
  list <brain_file> [page] [page_size]
  export <brain_file> <output_path>
  search <brain_file> <keyword...>
  count <brain_file>
  status <brain_file>
  help
"""

import sys
import json
import os
import datetime
import re
from pathlib import Path
from collections import Counter

# ── ANSI colors ──────────────────────────────────────────────────────────────
RED    = "\033[1;31m"
GREEN  = "\033[1;32m"
YELLOW = "\033[1;33m"
CYAN   = "\033[1;36m"
BOLD   = "\033[1m"
DIM    = "\033[2m"
RESET  = "\033[0m"

# ── Utilities ─────────────────────────────────────────────────────────────────

def highlight(text: str, keyword: str) -> str:
    """Wrap all case-insensitive occurrences of keyword in YELLOW BOLD."""
    if not keyword:
        return text
    pattern = re.compile(re.escape(keyword), re.IGNORECASE)
    return pattern.sub(lambda m: f"{YELLOW}{BOLD}{m.group()}{RESET}", text)


def extract_tags(text: str) -> list:
    """Return list of lowercase tag names from #word tokens in text."""
    return [m.lower() for m in re.findall(r'#(\w+)', text)]


def fmt_ts(ts: str) -> str:
    """Shorten ISO timestamp for display."""
    return ts[:19].replace("T", " ")


def default_brain() -> dict:
    """Return a fresh v2 brain structure."""
    now = datetime.datetime.now().isoformat()
    return {
        "version": 2,
        "memories": [],
        "meta": {
            "next_id": 1,
            "created": now
        }
    }


def migrate_v1_to_v2(data: dict) -> dict:
    """Upgrade v1 {memory: [...]} format to v2 {memories: [...], meta: {...}}."""
    old_entries = data.get("memory", [])
    new_entries = []
    next_id = 1
    for entry in old_entries:
        text = entry.get("text", "")
        new_entries.append({
            "id": next_id,
            "timestamp": entry.get("timestamp", datetime.datetime.now().isoformat()),
            "text": text,
            "tags": extract_tags(text)
        })
        next_id += 1

    # Determine created time from oldest entry or now
    created = old_entries[0]["timestamp"] if old_entries else datetime.datetime.now().isoformat()

    return {
        "version": 2,
        "memories": new_entries,
        "meta": {
            "next_id": next_id,
            "created": created
        }
    }


def load_brain(path: str) -> dict:
    """Load and return brain.json, migrating v1 format if needed."""
    if not os.path.exists(path):
        return default_brain()

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Detect v1 format (missing version key or version < 2)
    if data.get("version", 1) < 2:
        data = migrate_v1_to_v2(data)
        save_brain(path, data)

    return data


def save_brain(path: str, data: dict) -> None:
    """Atomically write brain.json using temp file + rename."""
    tmp_path = path + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    os.replace(tmp_path, path)


# ── Subcommand functions ──────────────────────────────────────────────────────

def cmd_init(brain_file: str) -> int:
    """Create brain.json if absent; migrate if v1. Silent on success."""
    os.makedirs(os.path.dirname(brain_file), exist_ok=True)
    if not os.path.exists(brain_file):
        save_brain(brain_file, default_brain())
    else:
        # load_brain handles migration and re-saves if needed
        load_brain(brain_file)
    return 0


def cmd_remember(brain_file: str, text: str) -> int:
    """Store a new memory entry."""
    if not text.strip():
        print(f"{RED}Error: nothing to remember. Provide some text.{RESET}", file=sys.stderr)
        return 1

    data = load_brain(brain_file)
    entry_id = data["meta"]["next_id"]
    tags = extract_tags(text)

    entry = {
        "id": entry_id,
        "timestamp": datetime.datetime.now().isoformat(),
        "text": text,
        "tags": tags
    }
    data["memories"].append(entry)
    data["meta"]["next_id"] = entry_id + 1
    save_brain(brain_file, data)

    tag_str = f"  {DIM}tags: {', '.join('#'+t for t in tags)}{RESET}" if tags else ""
    print(f"{GREEN}👑 Memory stored [ID: {entry_id}]{RESET}{tag_str}")
    return 0


def cmd_recall(brain_file: str, query: str = "") -> int:
    """Show last 20 memories, optionally filtered by keyword or #tag."""
    data = load_brain(brain_file)
    memories = data["memories"]

    if not memories:
        print(f"{DIM}No memories yet. Use 'remember <text>' to store one.{RESET}")
        return 0

    if query:
        # Tag filter: #tagname
        if query.startswith("#"):
            tag = query.lstrip("#").lower()
            filtered = [m for m in memories if tag in m.get("tags", [])]
        else:
            q = query.lower()
            filtered = [m for m in memories if q in m["text"].lower()]
    else:
        filtered = memories

    recent = filtered[-20:]
    if not recent:
        print(f"{YELLOW}No memories found matching '{query}'.{RESET}")
        return 0

    print(f"{CYAN}{BOLD}Recent memories{' (filtered)' if query else ''} — showing {len(recent)} of {len(filtered)}:{RESET}")
    for m in recent:
        ts = fmt_ts(m["timestamp"])
        tag_str = f" {DIM}[{', '.join('#'+t for t in m['tags'])}]{RESET}" if m.get("tags") else ""
        print(f"  {DIM}[{m['id']}]{RESET} {DIM}{ts}{RESET}  {m['text']}{tag_str}")
    return 0


def cmd_forget(brain_file: str, id_str: str) -> int:
    """Delete a memory by its integer ID."""
    if not id_str:
        print(f"{RED}Usage: forget <id>{RESET}", file=sys.stderr)
        return 1

    try:
        target_id = int(id_str)
    except ValueError:
        print(f"{RED}Error: ID must be a number, got '{id_str}'.{RESET}", file=sys.stderr)
        return 1

    data = load_brain(brain_file)
    original_count = len(data["memories"])
    data["memories"] = [m for m in data["memories"] if m["id"] != target_id]

    if len(data["memories"]) == original_count:
        print(f"{RED}Error: no memory with ID {target_id}.{RESET}", file=sys.stderr)
        return 1

    save_brain(brain_file, data)
    print(f"{GREEN}Memory {target_id} forgotten.{RESET}")
    return 0


def cmd_clear(brain_file: str) -> int:
    """Wipe all memories (confirmation handled in bash)."""
    data = load_brain(brain_file)
    count = len(data["memories"])
    data["memories"] = []
    # Preserve meta.next_id so IDs continue incrementing after clear
    save_brain(brain_file, data)
    print(f"{GREEN}All {count} memories cleared.{RESET}")
    return 0


def cmd_list(brain_file: str, page: int = 1, page_size: int = 10) -> int:
    """List all memories paginated."""
    data = load_brain(brain_file)
    memories = data["memories"]
    total = len(memories)

    if total == 0:
        print(f"{DIM}No memories yet.{RESET}")
        return 0

    total_pages = max(1, (total + page_size - 1) // page_size)
    page = max(1, min(page, total_pages))
    start = (page - 1) * page_size
    end = start + page_size
    page_entries = memories[start:end]

    print(f"{CYAN}{BOLD}Memories — Page {page}/{total_pages}  ({total} total){RESET}")
    print()
    for m in page_entries:
        ts = fmt_ts(m["timestamp"])
        tag_str = f"  {DIM}[{', '.join('#'+t for t in m['tags'])}]{RESET}" if m.get("tags") else ""
        print(f"  {BOLD}[{m['id']}]{RESET}  {DIM}{ts}{RESET}  {m['text']}{tag_str}")

    if total_pages > 1:
        print()
        nav = []
        if page > 1:
            nav.append(f"'list {page-1}' ← prev")
        if page < total_pages:
            nav.append(f"next → 'list {page+1}'")
        print(f"  {DIM}{' | '.join(nav)}{RESET}")
    return 0


def cmd_export(brain_file: str, output_path: str) -> int:
    """Export all memories to a plain-text file."""
    data = load_brain(brain_file)
    memories = data["memories"]
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(f"King Ultra Memory Export\n")
        f.write(f"Generated: {now}\n")
        f.write(f"Total memories: {len(memories)}\n")
        f.write("=" * 60 + "\n\n")
        for m in memories:
            ts = fmt_ts(m["timestamp"])
            tag_str = f"  tags: {', '.join('#'+t for t in m['tags'])}" if m.get("tags") else ""
            f.write(f"[{m['id']}] [{ts}] {m['text']}{tag_str}\n")

    print(f"{GREEN}Exported {len(memories)} memories → {output_path}{RESET}")
    return 0


def cmd_search(brain_file: str, keyword: str) -> int:
    """Search all memories with highlighted matches. No count cap."""
    if not keyword.strip():
        print(f"{RED}Usage: search <keyword>{RESET}", file=sys.stderr)
        return 1

    data = load_brain(brain_file)
    memories = data["memories"]

    # Tag search
    if keyword.startswith("#"):
        tag = keyword.lstrip("#").lower()
        results = [m for m in memories if tag in m.get("tags", [])]
        label = f"#{tag}"
    else:
        kw_lower = keyword.lower()
        results = [m for m in memories if kw_lower in m["text"].lower()]
        label = keyword

    if not results:
        print(f"{YELLOW}No results for '{label}'.{RESET}")
        return 0

    print(f"{CYAN}{BOLD}Search: '{label}' — {len(results)} result(s){RESET}")
    print()
    for m in results:
        ts = fmt_ts(m["timestamp"])
        displayed_text = highlight(m["text"], keyword if not keyword.startswith("#") else "")
        tag_str = f"  {DIM}[{', '.join('#'+t for t in m['tags'])}]{RESET}" if m.get("tags") else ""
        print(f"  {BOLD}[{m['id']}]{RESET}  {DIM}{ts}{RESET}  {displayed_text}{tag_str}")
    return 0


def cmd_count(brain_file: str) -> int:
    """Print total memory count."""
    data = load_brain(brain_file)
    count = len(data["memories"])
    print(f"{CYAN}Total memories: {BOLD}{count}{RESET}")
    return 0


def cmd_status(brain_file: str) -> int:
    """Show system status: count, file size, last entry, top tags."""
    data = load_brain(brain_file)
    memories = data["memories"]
    count = len(memories)

    # File size
    try:
        size_bytes = os.path.getsize(brain_file)
        if size_bytes >= 1024:
            size_str = f"{size_bytes / 1024:.1f} KB"
        else:
            size_str = f"{size_bytes} B"
    except OSError:
        size_str = "unknown"

    # Last entry
    if memories:
        last = memories[-1]
        last_ts = fmt_ts(last["timestamp"])
        last_text = last["text"][:50] + ("…" if len(last["text"]) > 50 else "")
    else:
        last_ts = "—"
        last_text = "—"

    # Top tags
    all_tags = []
    for m in memories:
        all_tags.extend(m.get("tags", []))
    top_tags = Counter(all_tags).most_common(5)
    tag_str = "  ".join(f"#{t}({n})" for t, n in top_tags) if top_tags else "none"

    # Created time
    created = fmt_ts(data["meta"].get("created", "unknown"))
    next_id = data["meta"].get("next_id", "?")

    print(f"\n{RED}{BOLD}╔══ KING ULTRA STATUS ══╗{RESET}")
    print(f"  {CYAN}System       {RESET}Online ✓")
    print(f"  {CYAN}Brain file   {RESET}{brain_file}")
    print(f"  {CYAN}File size    {RESET}{size_str}")
    print(f"  {CYAN}Memories     {RESET}{count} stored  (next ID: {next_id})")
    print(f"  {CYAN}Created      {RESET}{created}")
    print(f"  {CYAN}Last entry   {RESET}[{last_ts}] {last_text}")
    print(f"  {CYAN}Top tags     {RESET}{tag_str}")
    print(f"{RED}{BOLD}╚═══════════════════════╝{RESET}\n")
    return 0


def cmd_help() -> int:
    """Print the formatted help menu."""
    print(f"""
{RED}{BOLD}╔══ KING ULTRA v2.0 ═══════════════════════════════════════════╗{RESET}
{RED}{BOLD}║                    COMMAND REFERENCE                         ║{RESET}
{RED}{BOLD}╚══════════════════════════════════════════════════════════════╝{RESET}

  {CYAN}{BOLD}remember{RESET} {GREEN}<text>{RESET}        Store a memory. Use {YELLOW}#tags{RESET} inline.
  {CYAN}{BOLD}recall{RESET}   {GREEN}[keyword]{RESET}     Show last 20 memories, filtered by word or {YELLOW}#tag{RESET}.
  {CYAN}{BOLD}search{RESET}   {GREEN}<keyword>{RESET}     Search ALL memories with highlighted matches.
  {CYAN}{BOLD}list{RESET}     {GREEN}[page]{RESET}        List memories paginated (10 per page).
  {CYAN}{BOLD}forget{RESET}   {GREEN}<id>{RESET}          Delete a memory by its ID number.
  {CYAN}{BOLD}clear{RESET}                 Wipe ALL memories (asks for confirmation).
  {CYAN}{BOLD}export{RESET}   {GREEN}[filename]{RESET}    Export all memories to a plain-text file.
  {CYAN}{BOLD}count{RESET}                 Show total number of stored memories.
  {CYAN}{BOLD}status{RESET}                Show system status, file size, top tags.
  {CYAN}{BOLD}history{RESET}  {GREEN}[n]{RESET}           Show last N commands from this session.
  {CYAN}{BOLD}help{RESET}                  Show this command reference.
  {CYAN}{BOLD}exit{RESET} / {CYAN}{BOLD}quit{RESET}          Shut down King Ultra.

  {DIM}Tip: Use #tags in your memories to organize them.
       'remember buy milk #shopping #groceries'
       'recall #shopping' → shows all shopping memories{RESET}
""")
    return 0


# ── Main dispatcher ───────────────────────────────────────────────────────────

def main():
    if len(sys.argv) < 2:
        cmd_help()
        sys.exit(0)

    command = sys.argv[1]

    # Commands that don't need brain_file
    if command == "help":
        sys.exit(cmd_help())

    # init needs brain_file
    if command == "init":
        brain_file = sys.argv[2] if len(sys.argv) > 2 else None
        if not brain_file:
            print(f"{RED}Error: brain file path required for init.{RESET}", file=sys.stderr)
            sys.exit(1)
        sys.exit(cmd_init(brain_file))

    # All other commands require brain_file as argv[2]
    if len(sys.argv) < 3:
        print(f"{RED}Error: brain file path required.{RESET}", file=sys.stderr)
        sys.exit(1)

    brain_file = sys.argv[2]

    def get_text():
        return " ".join(sys.argv[3:])

    dispatch = {
        "remember": lambda: cmd_remember(brain_file, get_text()),
        "recall":   lambda: cmd_recall(brain_file, get_text()),
        "forget":   lambda: cmd_forget(brain_file, sys.argv[3] if len(sys.argv) > 3 else ""),
        "clear":    lambda: cmd_clear(brain_file),
        "list":     lambda: cmd_list(
                        brain_file,
                        int(sys.argv[3]) if len(sys.argv) > 3 and sys.argv[3].isdigit() else 1,
                        int(sys.argv[4]) if len(sys.argv) > 4 and sys.argv[4].isdigit() else 10,
                    ),
        "export":   lambda: cmd_export(
                        brain_file,
                        sys.argv[3] if len(sys.argv) > 3 else "king_ultra_export.txt"
                    ),
        "search":   lambda: cmd_search(brain_file, get_text()),
        "count":    lambda: cmd_count(brain_file),
        "status":   lambda: cmd_status(brain_file),
    }

    handler = dispatch.get(command)
    if handler is None:
        print(f"{RED}Unknown command: '{command}'. Run 'help' for usage.{RESET}", file=sys.stderr)
        sys.exit(1)

    try:
        sys.exit(handler())
    except FileNotFoundError as e:
        print(f"{RED}File error: {e}{RESET}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"{RED}Brain file corrupted: {e}\nTry deleting {brain_file} to reset.{RESET}", file=sys.stderr)
        sys.exit(1)
    except PermissionError as e:
        print(f"{RED}Permission denied: {e}{RESET}", file=sys.stderr)
        sys.exit(1)
    except (ValueError, KeyError) as e:
        print(f"{RED}Data error: {e}{RESET}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
