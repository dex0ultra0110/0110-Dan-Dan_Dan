#!/usr/bin/env bash
# ╔══════════════════════════════════════════════════════════════╗
# ║             KING ULTRA — Terminal Brain v2.0                 ║
# ║  Requires: python3 in PATH, king_ultra_core.py alongside     ║
# ╚══════════════════════════════════════════════════════════════╝

VERSION="2.0.0"

# ── Resolve script directory so core.py is always found ──────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CORE_PY="$SCRIPT_DIR/king_ultra_core.py"

# ── Brain data lives in home dir (persists across reinstalls) ─────────────────
BASE_DIR="$HOME/king_ultra"
BRAIN_FILE="$BASE_DIR/brain.json"

PAGE_SIZE=10    # memories shown per 'list' page

# ── ANSI colors ───────────────────────────────────────────────────────────────
RED="\033[1;31m"
GREEN="\033[1;32m"
YELLOW="\033[1;33m"
CYAN="\033[1;36m"
BOLD="\033[1m"
DIM="\033[2m"
RESET="\033[0m"

# ── Session command history (bash array, in-memory only) ──────────────────────
SESSION_HISTORY=()

# ── Core dispatcher ───────────────────────────────────────────────────────────
run_core() {
    python3 "$CORE_PY" "$@"
}

# ── Initialise ────────────────────────────────────────────────────────────────
init() {
    # Verify python3
    if ! command -v python3 &>/dev/null; then
        echo -e "${RED}Error: python3 is not installed or not in PATH.${RESET}" >&2
        exit 1
    fi

    # Verify core module
    if [ ! -f "$CORE_PY" ]; then
        echo -e "${RED}Error: king_ultra_core.py not found at:${RESET}" >&2
        echo -e "  $CORE_PY" >&2
        echo -e "${YELLOW}Make sure king_ultra_core.py is in the same directory as this script.${RESET}" >&2
        exit 1
    fi

    mkdir -p "$BASE_DIR"

    # Delegate brain.json creation / migration to Python
    run_core init "$BRAIN_FILE"
}

# ── Banner ────────────────────────────────────────────────────────────────────
banner() {
    clear
    echo -e "${RED}"
    echo "██╗  ██╗██╗███╗   ██╗ ██████╗"
    echo "██║ ██╔╝██║████╗  ██║██╔════╝"
    echo "█████╔╝ ██║██╔██╗ ██║██║  ███╗"
    echo "██╔═██╗ ██║██║╚██╗██║██║   ██║"
    echo "██║  ██╗██║██║ ╚████║╚██████╔╝"
    echo "╚═╝  ╚═╝╚═╝╚═╝  ╚═══╝ ╚═════╝"
    echo -e "${RESET}"
    echo -e "${CYAN}${BOLD}KING ULTRA :: v${VERSION} :: UPGRADED${RESET}"
    echo -e "${DIM}  Type 'help' for commands${RESET}"
    echo
}

# ── Confirmation prompt ───────────────────────────────────────────────────────
confirm() {
    local prompt="$1"
    echo -ne "${YELLOW}${prompt} [y/N] ${RESET}"
    read -r answer
    [[ "$answer" =~ ^[Yy]$ ]]
}

# ── Command handlers ──────────────────────────────────────────────────────────

cmd_remember() {
    if [ -z "$*" ]; then
        echo -e "${RED}Usage: remember <text>   (use #tags inline)${RESET}"
        return 1
    fi
    run_core remember "$BRAIN_FILE" "$@"
}

cmd_recall() {
    run_core recall "$BRAIN_FILE" "$@"
}

cmd_forget() {
    if [ -z "$1" ]; then
        echo -e "${RED}Usage: forget <id>${RESET}"
        return 1
    fi
    run_core forget "$BRAIN_FILE" "$1"
}

cmd_clear() {
    if confirm "Wipe ALL memories? This cannot be undone."; then
        run_core clear "$BRAIN_FILE"
    else
        echo -e "${CYAN}Cancelled.${RESET}"
    fi
}

cmd_list() {
    local page="${1:-1}"
    run_core list "$BRAIN_FILE" "$page" "$PAGE_SIZE"
}

cmd_export() {
    # Default filename includes timestamp so exports never overwrite each other
    local filename="${1:-king_ultra_export_$(date +%Y%m%d_%H%M%S).txt}"
    run_core export "$BRAIN_FILE" "$filename"
}

cmd_search() {
    if [ -z "$*" ]; then
        echo -e "${RED}Usage: search <keyword>   or   search #tag${RESET}"
        return 1
    fi
    run_core search "$BRAIN_FILE" "$@"
}

cmd_count() {
    run_core count "$BRAIN_FILE"
}

cmd_status() {
    run_core status "$BRAIN_FILE"
}

cmd_history() {
    local n="${1:-20}"
    local total="${#SESSION_HISTORY[@]}"

    if [ "$total" -eq 0 ]; then
        echo -e "${DIM}No session history yet.${RESET}"
        return 0
    fi

    local start=$(( total - n ))
    (( start < 0 )) && start=0

    echo -e "${CYAN}${BOLD}Session history (${n} most recent):${RESET}"
    for (( i=start; i<total; i++ )); do
        printf "  ${DIM}%3d.${RESET}  %s\n" "$((i+1))" "${SESSION_HISTORY[$i]}"
    done
}

cmd_help() {
    run_core help
}

# ── Main REPL loop ────────────────────────────────────────────────────────────
main_loop() {
    banner
    echo -e "${GREEN}Ultra brain engaged 👁${RESET}"
    echo

    while true; do
        # Prompt
        echo -ne "${GREEN}${BOLD}👑 King Ultra >${RESET} "
        read -r input

        # Skip blank lines
        [ -z "$input" ] && continue

        # Append to session history
        SESSION_HISTORY+=("$input")

        # Split into command and remainder
        cmd=$(awk '{print $1}' <<< "$input")
        rest="${input#"$cmd"}"
        rest="${rest# }"   # strip one leading space

        case "$cmd" in
            remember)
                # Pass $rest unquoted so each word becomes a separate argv —
                # Python joins them. This is intentional (see architecture notes).
                # shellcheck disable=SC2086
                cmd_remember $rest
                ;;
            recall)
                # shellcheck disable=SC2086
                cmd_recall $rest
                ;;
            forget)
                cmd_forget "$rest"
                ;;
            clear)
                cmd_clear
                ;;
            list)
                # shellcheck disable=SC2086
                cmd_list $rest
                ;;
            export)
                cmd_export "$rest"
                ;;
            search)
                # shellcheck disable=SC2086
                cmd_search $rest
                ;;
            count)
                cmd_count
                ;;
            status)
                cmd_status
                ;;
            history)
                cmd_history "$rest"
                ;;
            help|"?")
                cmd_help
                ;;
            exit|quit|q)
                echo -e "${RED}${BOLD}King Ultra standing down 👑${RESET}"
                exit 0
                ;;
            *)
                echo -e "${YELLOW}Unknown command: '${cmd}'. Type 'help' for available commands.${RESET}"
                ;;
        esac

        echo
    done
}

# ── Entry point ───────────────────────────────────────────────────────────────
init
main_loop
