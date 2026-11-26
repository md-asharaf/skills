#!/usr/bin/env python3
import json
import re
import sys

PROTECTED_PATHS = [
    r"\.husky/",
    r"eslint\.config\.",
    r"biome\.jsonc?",
    r"\.github/workflows/",
    r"scripts/verify",
    r"\.claude/settings",
    r"managed-settings\.json",
    r"/etc/claude-code",
    r"agentic-engineering-standard/enforcement/",
    r"HARD-RULES\.md",
]

WRITE_MARKERS = [
    r"(^|\s)-i(\s|$)",
    r"--in-place",
    r"(?<![<>&0-9])>{1,2}(?!&)",
    r"\btee\b",
    r"\bmv\b",
    r"\bcp\b",
    r"\brm\b",
    r"\bchmod\b",
    r"\btruncate\b",
    r"\bln\b",
    r"\bgit\s+(checkout|restore|apply|am|stash)\b",
    r"open\([^)]*['\"][wa]",
    r"write_text|write_bytes|writeFile|\.write\(",
]

DENY = [
    (r"\bgit\b[^|;&]*\bpush\b", "Pushing is done by the user after reviewing the diff. Ask the user to run `! git push`."),
    (r"--no-verify", "Hooks are never bypassed."),
    (r"\bHUSKY=0\b|\bHUSKY_SKIP", "Hooks are never bypassed."),
    (r"\bgit\b[^|;&]*\bcommit\b[^|;&]*\s-[a-zA-Z]*n[a-zA-Z]*(\s|$)", "`git commit -n` skips hooks; hooks are never bypassed."),
    (r"\bgit\b[^|;&]*\bfilter-(branch|repo)\b", "Rewriting history needs the user."),
    (r"\bdrizzle-kit\s+(migrate|push)\b|\bdb:(migrate|push)\b", "Migrations are applied by the user."),
    (r"--dangerously-skip-permissions|bypassPermissions", "Permission checks are never bypassed."),
    (r"\bcore\.hooksPath\b", "Hooks are never redirected."),
]

ASK = [
    (r"\bgit\b[^|;&]*\breset\b[^|;&]*--hard", "Discards work."),
    (r"\bgit\b[^|;&]*\brebase\b", "Rewrites history."),
    (r"\bgit\b[^|;&]*\bclean\b[^|;&]*-[a-zA-Z]*f", "Deletes untracked files."),
    (r"\bgit\b[^|;&]*\bcheckout\b\s+(--\s|\.\s*$)", "Discards changes."),
    (r"\bgit\b[^|;&]*\brestore\b", "Discards changes."),
    (r"\bgit\b[^|;&]*\bbranch\b[^|;&]*\s-D\b", "Deletes a branch."),
    (r"\brm\s+-[a-zA-Z]*r[a-zA-Z]*f|\brm\s+-[a-zA-Z]*f[a-zA-Z]*r", "Deletes files recursively."),
    (r"\bpsql\b|\bpg_restore\b|\bdropdb\b", "Runs SQL against a database."),
]


def decide(command: str) -> tuple[str, str] | None:
    for pattern, reason in DENY:
        if re.search(pattern, command):
            return "deny", reason
    if any(re.search(path, command) for path in PROTECTED_PATHS) and any(
        re.search(marker, command) for marker in WRITE_MARKERS
    ):
        return "ask", "This command may change a gate, hook, lint, CI or permission file. Only the user approves such changes."
    for pattern, reason in ASK:
        if re.search(pattern, command):
            return "ask", reason
    return None


def decide_file(file_path: str) -> tuple[str, str] | None:
    if any(re.search(path, file_path) for path in PROTECTED_PATHS):
        return "ask", "This file is a gate, hook, lint, CI or permission file. Only the user approves changes to it."
    return None


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0
    tool_input = payload.get("tool_input", {})
    command = tool_input.get("command")
    file_path = tool_input.get("file_path") or tool_input.get("notebook_path")
    if isinstance(command, str):
        verdict = decide(command)
    elif isinstance(file_path, str):
        verdict = decide_file(file_path)
    else:
        return 0
    if verdict is None:
        return 0
    decision, reason = verdict
    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": decision,
                    "permissionDecisionReason": f"Guard: {reason}",
                }
            }
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
