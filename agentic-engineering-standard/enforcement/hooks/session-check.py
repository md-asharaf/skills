#!/usr/bin/env python3
import json
import sys
from pathlib import Path

REQUIRED = [".skills", "TASK.md", "AGENTS.md", "docs/AUDIT_BACKLOG.md"]


def project_root(start: Path) -> Path | None:
    for candidate in [start, *start.parents]:
        if (candidate / ".git").exists():
            return candidate
    return None


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        payload = {}
    root = project_root(Path(payload.get("cwd") or Path.cwd()))
    if root is None or root == Path.home() / "coding" / "skills":
        return 0
    missing = [name for name in REQUIRED if not (root / name).exists()]
    if not missing:
        return 0
    message = (
        f"This project ({root}) is not set up with the owner's standards: missing {', '.join(missing)}. "
        "Before any other work, tell the owner in one line and offer to run the project-setup skill "
        "(/project-setup). Until it is set up, still follow ~/coding/skills: read the matching standard "
        "sections and the existing pattern before every edit."
    )
    print(
        json.dumps(
            {"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": message}}
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
