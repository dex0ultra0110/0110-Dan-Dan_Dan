#!/usr/bin/env python3
"""
king_ultra_ai.py — King Ultra with an AI Mind
All-in-one: memory brain + live Claude AI, no API key in code.

Key is loaded from:
  1. ANTHROPIC_API_KEY environment variable  (standard)
  2. ~/.king_ultra/api_key file              (saved locally on first run)

Run:  python3 king_ultra_ai.py
"""

import sys
import json
import os
import re
import stat
import datetime
import textwrap
from pathlib import Path
from collections import Counter

# ── Optional: install anthropic if missing ────────────────────────────────────
try:
    import anthropic
    _SDK_OK = True
except ImportError:
    _SDK_OK = False

# ── ANSI colors ───────────────────────────────────────────────────────────────
RED    = "\033[1;31m"
GREEN  = "\033[1;32m"
YELLOW = "\033[1;33m"
CYAN   = "\033[1;36m"
MAGENTA= "\033[1;35m"
BOLD   = "\033[1m"
DIM    = "\033[2m"
RESET  = "\033[0m"

VERSION    = "3.0.0"
BASE_DIR   = Path.home() / "king_ultra"
BRAIN_FILE = BASE_DIR / "brain.json"
KEY_FILE   = BASE_DIR / "api_key"
PAGE_SIZE  = 10
MAX_MEMORY_CONTEXT = 30   # memories sent to Claude as context

# ─────────────────────────────────────────────────────────────────────────────
# API KEY MANAGEMENT
# ─────────────────────────────────────────────────────────────────────────────

def load_api_key() -> str | None:
    """Return API key from env var or local key file, else None."""
    key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    if key:
        return key
    if KEY_FILE.exists():
        return KEY_FILE.read_text().strip()
    return None


def save_api_key(key: str) -> None:
    """Save API key to ~/.king_ultra/api_key with restricted permissions."""
    BASE_DIR.mkdir(parents=True, exist_ok=True)
    KEY_FILE.write_text(key.strip())
    KEY_FILE.chmod(stat.S_IRUSR | stat.S_IWUSR)   # owner read/write only


def prompt_for_key() -> str:
    """Interactively ask the user to paste their API key. Returns the key."""
    print(f"\n{YELLOW}{BOLD}No API key found.{RESET}")
    print(f"{DIM}Get one at: console.anthropic.com  →  API Keys{RESET}")
    print()
    try:
        key = input(f"{CYAN}Paste your Anthropic API key (sk-ant-...): {RESET}").strip()
    except (EOFError, KeyboardInterrupt):
        return ""
    if not key.startswith("sk-"):
        print(f"{RED}That doesn't look like a valid key (should start with 'sk-').{RESET}")
        return ""
    try:
        save_prompt = input(
            f"{CYAN}Save key to {KEY_FILE} for future sessions? [Y/n] {RESET}"
        ).strip().lower()
    except (EOFError, KeyboardInterrupt):
        save_prompt = "n"
    if save_prompt in ("", "y", "yes"):
        save_api_key(key)
        print(f"{GREEN}Key saved (chmod 600). It stays on your machine only.{RESET}")
    return key


# ─────────────────────────────────────────────────────────────────────────────
# BRAIN (memory) LAYER  — same v2 format as king_ultra_core.py
# ─────────────────────────────────────────────────────────────────────────────

def default_brain() -> dict:
    now = datetime.datetime.now().isoformat()
    return {"version": 2, "memories": [], "meta": {"next_id": 1, "created": now}}


def extract_tags(text: str) -> list:
    return [m.lower() for m in re.findall(r'#(\w+)', text)]


def fmt_ts(ts: str) -> str:
    return ts[:19].replace("T", " ")


def load_brain() -> dict:
    if not BRAIN_FILE.exists():
        return default_brain()
    data = json.loads(BRAIN_FILE.read_text())
    if data.get("version", 1) < 2:
        data = _migrate_v1(data)
        save_brain(data)
    return data


def save_brain(data: dict) -> None:
    BASE_DIR.mkdir(parents=True, exist_ok=True)
    tmp = BRAIN_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False))
    tmp.replace(BRAIN_FILE)


def _migrate_v1(data: dict) -> dict:
    old = data.get("memory", [])
    entries, nid = [], 1
    for e in old:
        t = e.get("text", "")
        entries.append({"id": nid, "timestamp": e.get("timestamp", datetime.datetime.now().isoformat()),
                        "text": t, "tags": extract_tags(t)})
        nid += 1
    created = old[0]["timestamp"] if old else datetime.datetime.now().isoformat()
    return {"version": 2, "memories": entries, "meta": {"next_id": nid, "created": created}}


def do_remember(text: str) -> None:
    if not text.strip():
        print(f"{RED}Nothing to remember.{RESET}")
        return
    data = load_brain()
    eid = data["meta"]["next_id"]
    tags = extract_tags(text)
    data["memories"].append({
        "id": eid, "timestamp": datetime.datetime.now().isoformat(),
        "text": text, "tags": tags
    })
    data["meta"]["next_id"] = eid + 1
    save_brain(data)
    tag_str = f"  {DIM}tags: {', '.join('#'+t for t in tags)}{RESET}" if tags else ""
    print(f"{GREEN}👑 Memory stored [ID: {eid}]{RESET}{tag_str}")


def do_recall(query: str = "") -> None:
    data = load_brain()
    mems = data["memories"]
    if not mems:
        print(f"{DIM}No memories yet. Use 'remember <text>'.{RESET}")
        return
    if query.startswith("#"):
        tag = query.lstrip("#").lower()
        filtered = [m for m in mems if tag in m.get("tags", [])]
    elif query:
        q = query.lower()
        filtered = [m for m in mems if q in m["text"].lower()]
    else:
        filtered = mems
    recent = filtered[-20:]
    if not recent:
        print(f"{YELLOW}No memories found matching '{query}'.{RESET}")
        return
    print(f"{CYAN}{BOLD}Memories{' (filtered)' if query else ''} — {len(recent)} of {len(filtered)}:{RESET}")
    for m in recent:
        tag_str = f" {DIM}[{', '.join('#'+t for t in m['tags'])}]{RESET}" if m.get("tags") else ""
        print(f"  {DIM}[{m['id']}]{RESET} {DIM}{fmt_ts(m['timestamp'])}{RESET}  {m['text']}{tag_str}")


def do_forget(id_str: str) -> None:
    try:
        tid = int(id_str)
    except ValueError:
        print(f"{RED}ID must be a number.{RESET}")
        return
    data = load_brain()
    before = len(data["memories"])
    data["memories"] = [m for m in data["memories"] if m["id"] != tid]
    if len(data["memories"]) == before:
        print(f"{RED}No memory with ID {tid}.{RESET}")
        return
    save_brain(data)
    print(f"{GREEN}Memory {tid} forgotten.{RESET}")


def do_list(page: int = 1) -> None:
    data = load_brain()
    mems = data["memories"]
    total = len(mems)
    if total == 0:
        print(f"{DIM}No memories yet.{RESET}")
        return
    total_pages = max(1, (total + PAGE_SIZE - 1) // PAGE_SIZE)
    page = max(1, min(page, total_pages))
    start = (page - 1) * PAGE_SIZE
    chunk = mems[start:start + PAGE_SIZE]
    print(f"{CYAN}{BOLD}Memories — Page {page}/{total_pages}  ({total} total){RESET}\n")
    for m in chunk:
        tag_str = f"  {DIM}[{', '.join('#'+t for t in m['tags'])}]{RESET}" if m.get("tags") else ""
        print(f"  {BOLD}[{m['id']}]{RESET}  {DIM}{fmt_ts(m['timestamp'])}{RESET}  {m['text']}{tag_str}")
    if total_pages > 1:
        nav = []
        if page > 1:  nav.append(f"'list {page-1}' ← prev")
        if page < total_pages: nav.append(f"next → 'list {page+1}'")
        print(f"\n  {DIM}{' | '.join(nav)}{RESET}")


def do_search(keyword: str) -> None:
    if not keyword.strip():
        print(f"{RED}Usage: search <keyword>{RESET}")
        return
    data = load_brain()
    mems = data["memories"]
    if keyword.startswith("#"):
        tag = keyword.lstrip("#").lower()
        results = [m for m in mems if tag in m.get("tags", [])]
        label = f"#{tag}"
    else:
        kl = keyword.lower()
        results = [m for m in mems if kl in m["text"].lower()]
        label = keyword
    if not results:
        print(f"{YELLOW}No results for '{label}'.{RESET}")
        return
    print(f"{CYAN}{BOLD}Search: '{label}' — {len(results)} result(s){RESET}\n")
    for m in results:
        text = re.sub(re.escape(keyword), lambda x: f"{YELLOW}{BOLD}{x.group()}{RESET}",
                      m["text"], flags=re.IGNORECASE) if not keyword.startswith("#") else m["text"]
        tag_str = f"  {DIM}[{', '.join('#'+t for t in m['tags'])}]{RESET}" if m.get("tags") else ""
        print(f"  {BOLD}[{m['id']}]{RESET}  {DIM}{fmt_ts(m['timestamp'])}{RESET}  {text}{tag_str}")


def do_status() -> None:
    data = load_brain()
    mems = data["memories"]
    count = len(mems)
    size = f"{BRAIN_FILE.stat().st_size / 1024:.1f} KB" if BRAIN_FILE.exists() else "—"
    last_ts, last_txt = ("—", "—") if not mems else (fmt_ts(mems[-1]["timestamp"]), mems[-1]["text"][:50])
    all_tags = [t for m in mems for t in m.get("tags", [])]
    top_tags = "  ".join(f"#{t}({n})" for t, n in Counter(all_tags).most_common(5)) or "none"
    print(f"\n{RED}{BOLD}╔══ KING ULTRA AI STATUS ══╗{RESET}")
    print(f"  {CYAN}Version      {RESET}v{VERSION}")
    print(f"  {CYAN}System       {RESET}Online ✓")
    print(f"  {CYAN}AI Mind      {RESET}{'Active ✓' if _SDK_OK else RED+'SDK not installed (pip install anthropic)'+RESET}")
    print(f"  {CYAN}Brain file   {RESET}{BRAIN_FILE}")
    print(f"  {CYAN}File size    {RESET}{size}")
    print(f"  {CYAN}Memories     {RESET}{count} stored")
    print(f"  {CYAN}Last entry   {RESET}[{last_ts}] {last_txt}")
    print(f"  {CYAN}Top tags     {RESET}{top_tags}")
    print(f"{RED}{BOLD}╚══════════════════════════╝{RESET}\n")


def do_count() -> None:
    data = load_brain()
    print(f"{CYAN}Total memories: {BOLD}{len(data['memories'])}{RESET}")


def do_export(filename: str = "") -> None:
    if not filename:
        filename = f"king_ultra_export_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    data = load_brain()
    mems = data["memories"]
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(filename, "w", encoding="utf-8") as f:
        f.write(f"King Ultra AI Memory Export\nGenerated: {now}\nTotal: {len(mems)}\n{'='*60}\n\n")
        for m in mems:
            tag_str = f"  tags: {', '.join('#'+t for t in m['tags'])}" if m.get("tags") else ""
            f.write(f"[{m['id']}] [{fmt_ts(m['timestamp'])}] {m['text']}{tag_str}\n")
    print(f"{GREEN}Exported {len(mems)} memories → {filename}{RESET}")


def do_clear() -> None:
    try:
        ans = input(f"{YELLOW}Wipe ALL memories? This cannot be undone. [y/N] {RESET}").strip().lower()
    except (EOFError, KeyboardInterrupt):
        ans = "n"
    if ans not in ("y", "yes"):
        print(f"{CYAN}Cancelled.{RESET}")
        return
    data = load_brain()
    count = len(data["memories"])
    data["memories"] = []
    save_brain(data)
    print(f"{GREEN}All {count} memories cleared.{RESET}")


# ─────────────────────────────────────────────────────────────────────────────
# AI MIND  — the "own mind and process"
# ─────────────────────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """\
You are King Ultra's AI Mind — an intelligent, self-directed process embedded \
in a personal memory and knowledge system. You have two roles:

1. THINKER: When the user asks you something, reason through it carefully and \
   give a direct, useful answer. You are not a passive assistant — you have your \
   own perspective, make judgements, and think independently.

2. MEMORY-AWARE: You are given the user's stored memories as context. Use them \
   to give personalised, relevant answers. If a memory is relevant to the \
   question, reference it explicitly.

Style:
- Be direct and concise. No filler phrases.
- When you reason, show it briefly. Don't over-explain.
- You may disagree with the user if you have good reason.
- Format with markdown only when it genuinely helps readability.

You are King Ultra's mind. Think for yourself.\
"""


def _build_memory_context(data: dict) -> str:
    """Return a compact string of recent memories for the AI's context."""
    mems = data["memories"][-MAX_MEMORY_CONTEXT:]
    if not mems:
        return "(No memories stored yet.)"
    lines = []
    for m in mems:
        tag_str = f" [{', '.join('#'+t for t in m['tags'])}]" if m.get("tags") else ""
        lines.append(f"[{m['id']}] {m['text']}{tag_str}")
    return "\n".join(lines)


class AIMind:
    """Stateful AI conversation with memory awareness."""

    def __init__(self, api_key: str):
        self._client = anthropic.Anthropic(api_key=api_key)
        self._history: list[dict] = []   # conversation turns

    def think(self, user_input: str, inject_memories: bool = True) -> None:
        """Send user_input to Claude and stream the response to stdout."""
        data = load_brain()
        mem_context = _build_memory_context(data)

        # Build the user turn — prepend memory snapshot if this is the first turn
        # or if memories changed since last turn.
        if inject_memories:
            full_input = (
                f"[Your stored memories — use these as background context]\n"
                f"{mem_context}\n\n"
                f"[User message]\n{user_input}"
            )
        else:
            full_input = user_input

        self._history.append({"role": "user", "content": full_input})

        print(f"\n{MAGENTA}{BOLD}👁  King Ultra Mind:{RESET} ", end="", flush=True)

        collected = []
        try:
            with self._client.messages.stream(
                model="claude-opus-4-6",
                max_tokens=2048,
                thinking={"type": "adaptive"},
                system=SYSTEM_PROMPT,
                messages=self._history,
            ) as stream:
                for text in stream.text_stream:
                    print(text, end="", flush=True)
                    collected.append(text)
                final = stream.get_final_message()
        except anthropic.AuthenticationError:
            print(f"\n{RED}Bad API key. Delete {KEY_FILE} and restart to re-enter.{RESET}")
            self._history.pop()
            return
        except anthropic.RateLimitError:
            print(f"\n{RED}Rate limited — wait a moment and try again.{RESET}")
            self._history.pop()
            return
        except anthropic.APIConnectionError:
            print(f"\n{RED}Network error — check your connection.{RESET}")
            self._history.pop()
            return
        except anthropic.APIStatusError as e:
            print(f"\n{RED}API error {e.status_code}: {e.message}{RESET}")
            self._history.pop()
            return

        print("\n")   # newline after streamed response

        # Record assistant turn (use full content to preserve thinking blocks)
        self._history.append({"role": "assistant", "content": final.content})

    def reset(self) -> None:
        self._history.clear()
        print(f"{GREEN}Conversation reset. Fresh context.{RESET}")


# ─────────────────────────────────────────────────────────────────────────────
# HELP
# ─────────────────────────────────────────────────────────────────────────────

def print_help() -> None:
    print(f"""
{RED}{BOLD}╔══ KING ULTRA AI v{VERSION} ══════════════════════════════════════╗{RESET}
{RED}{BOLD}║               COMMAND REFERENCE                              ║{RESET}
{RED}{BOLD}╚══════════════════════════════════════════════════════════════╝{RESET}

{CYAN}{BOLD}── AI MIND ─────────────────────────────────────────────────────{RESET}
  {MAGENTA}{BOLD}ask{RESET}  {GREEN}<question>{RESET}       Talk to the AI. It knows your memories.
  {MAGENTA}{BOLD}think{RESET} {GREEN}<topic>{RESET}         Ask the AI to reason deeply about something.
  {MAGENTA}{BOLD}reset{RESET}               Clear the current AI conversation (fresh context).

{CYAN}{BOLD}── MEMORY ──────────────────────────────────────────────────────{RESET}
  {CYAN}{BOLD}remember{RESET} {GREEN}<text>{RESET}          Store a memory. Use {YELLOW}#tags{RESET} inline.
  {CYAN}{BOLD}recall{RESET}   {GREEN}[keyword]{RESET}       Show last 20 memories, filter by word or {YELLOW}#tag{RESET}.
  {CYAN}{BOLD}search{RESET}   {GREEN}<keyword>{RESET}       Search ALL memories with highlights.
  {CYAN}{BOLD}list{RESET}     {GREEN}[page]{RESET}          List memories paginated ({PAGE_SIZE}/page).
  {CYAN}{BOLD}forget{RESET}   {GREEN}<id>{RESET}            Delete a memory by ID.
  {CYAN}{BOLD}clear{RESET}                 Wipe ALL memories (confirmation required).
  {CYAN}{BOLD}export{RESET}   {GREEN}[filename]{RESET}      Export memories to a text file.
  {CYAN}{BOLD}count{RESET}                 Show total memory count.
  {CYAN}{BOLD}status{RESET}                System status and stats.

  {CYAN}{BOLD}exit{RESET} / {CYAN}{BOLD}quit{RESET}          Shut down.

  {DIM}Tip: 'ask' and 'think' both talk to the AI.
       The AI always sees your memories as background context.
       Use 'reset' to start a fresh AI conversation.{RESET}
""")


# ─────────────────────────────────────────────────────────────────────────────
# BANNER
# ─────────────────────────────────────────────────────────────────────────────

def banner() -> None:
    os.system("clear")
    print(f"{RED}")
    print("██╗  ██╗██╗███╗   ██╗ ██████╗")
    print("██║ ██╔╝██║████╗  ██║██╔════╝")
    print("█████╔╝ ██║██╔██╗ ██║██║  ███╗")
    print("██╔═██╗ ██║██║╚██╗██║██║   ██║")
    print("██║  ██╗██║██║ ╚████║╚██████╔╝")
    print("╚═╝  ╚═╝╚═╝╚═╝  ╚═══╝ ╚═════╝")
    print(f"{RESET}")
    print(f"{CYAN}{BOLD}KING ULTRA AI :: v{VERSION} :: HAS ITS OWN MIND{RESET}")
    print(f"{DIM}  Type 'help' for commands  |  'ask <anything>' to think{RESET}")
    print()


# ─────────────────────────────────────────────────────────────────────────────
# MAIN REPL
# ─────────────────────────────────────────────────────────────────────────────

def main() -> None:
    BASE_DIR.mkdir(parents=True, exist_ok=True)

    # Ensure brain exists
    if not BRAIN_FILE.exists():
        save_brain(default_brain())

    banner()

    # ── SDK check ─────────────────────────────────────────────────────────────
    if not _SDK_OK:
        print(f"{YELLOW}Install the Anthropic SDK to enable the AI mind:{RESET}")
        print(f"  {DIM}pip install anthropic{RESET}\n")
        print(f"{GREEN}Memory commands still work without it.{RESET}\n")
        mind = None
    else:
        # ── API key resolution ─────────────────────────────────────────────────
        api_key = load_api_key()
        if not api_key:
            api_key = prompt_for_key()
        if api_key:
            mind = AIMind(api_key)
            print(f"{GREEN}AI Mind engaged 👁  (key loaded from "
                  f"{'env' if os.environ.get('ANTHROPIC_API_KEY') else KEY_FILE}){RESET}\n")
        else:
            mind = None
            print(f"{YELLOW}No API key — AI commands disabled. Memory commands work fine.{RESET}\n")

    session_history: list[str] = []

    while True:
        try:
            raw = input(f"{GREEN}{BOLD}👑 King Ultra >{RESET} ").strip()
        except (EOFError, KeyboardInterrupt):
            print(f"\n{RED}{BOLD}King Ultra standing down 👑{RESET}")
            break

        if not raw:
            continue
        session_history.append(raw)

        cmd, _, rest = raw.partition(" ")
        rest = rest.strip()

        # ── AI commands ───────────────────────────────────────────────────────
        if cmd in ("ask", "think"):
            if not mind:
                print(f"{RED}AI Mind not available. Install SDK or provide an API key.{RESET}")
            elif not rest:
                print(f"{RED}Usage: {cmd} <your question or topic>{RESET}")
            else:
                mind.think(rest)

        elif cmd == "reset":
            if mind:
                mind.reset()
            else:
                print(f"{DIM}No AI session active.{RESET}")

        # ── Memory commands ───────────────────────────────────────────────────
        elif cmd == "remember":
            do_remember(rest)

        elif cmd == "recall":
            do_recall(rest)

        elif cmd == "forget":
            do_forget(rest)

        elif cmd == "clear":
            do_clear()

        elif cmd == "list":
            try:
                page = int(rest) if rest else 1
            except ValueError:
                page = 1
            do_list(page)

        elif cmd == "export":
            do_export(rest)

        elif cmd == "search":
            do_search(rest)

        elif cmd == "count":
            do_count()

        elif cmd == "status":
            do_status()

        elif cmd == "history":
            n = 20
            if rest.isdigit():
                n = int(rest)
            recent = session_history[-n:]
            print(f"{CYAN}{BOLD}Session history ({len(recent)} commands):{RESET}")
            for i, entry in enumerate(recent, 1):
                print(f"  {DIM}{i:3}.{RESET}  {entry}")

        elif cmd in ("help", "?"):
            print_help()

        elif cmd in ("exit", "quit", "q"):
            print(f"{RED}{BOLD}King Ultra standing down 👑{RESET}")
            break

        else:
            print(f"{YELLOW}Unknown command: '{cmd}'. Type 'help' for commands.{RESET}")

        print()


if __name__ == "__main__":
    main()
