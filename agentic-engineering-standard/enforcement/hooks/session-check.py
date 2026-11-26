#!/usr/bin/env python3
import json
import subprocess
import sys
from pathlib import Path

REQUIRED = [".skills", "TASK.md", "AGENTS.md", "docs/AUDIT_BACKLOG.md"]
SKILLS = Path.home() / "coding" / "skills"
STANDARD = SKILLS / "agentic-engineering-standard"
MANAGED = Path("/Library/Application Support/ClaudeCode") if sys.platform == "darwin" else Path("/etc/claude-code")
HOOKS = ["guard.py", "session-check.py", "inspection-log.py"]
TASK_LIMIT = 40


def project_root(start: Path) -> Path | None:
    for candidate in [start, *start.parents]:
        if (candidate / ".git").exists():
            return candidate
    return None


def same(source: Path, copy: Path, replace: tuple[str, str] | None = None) -> bool:
    if not source.is_file() or not copy.is_file():
        return False
    text = source.read_text()
    if replace:
        text = text.replace(*replace)
    return text == copy.read_text()


def machine_drift() -> list[str]:
    if not STANDARD.is_dir():
        return []
    notes: list[str] = []
    stale = [name for name in HOOKS if not same(STANDARD / "enforcement" / "hooks" / name, MANAGED / "hooks" / name)]
    if not same(STANDARD / "enforcement" / "managed-settings.json", MANAGED / "managed-settings.json", ("/etc/claude-code", str(MANAGED))):
        stale.append("managed-settings.json")
    if stale:
        notes.append(
            f"The owner's managed layer in {MANAGED} is out of date ({', '.join(stale)}). Tell the owner to run "
            f"{STANDARD / 'scripts' / 'install-machine.sh'} and the sudo lines it prints."
        )
    ahead = subprocess.run(["git", "-C", str(SKILLS), "rev-list", "--count", "@{u}..HEAD"], capture_output=True, text=True)
    if ahead.returncode == 0 and ahead.stdout.strip() not in ("", "0"):
        notes.append(f"The skills repository has {ahead.stdout.strip()} unpushed commit(s); remind the owner to push it so other machines get them.")
    return notes


def project_drift(root: Path) -> list[str]:
    notes: list[str] = []
    copy = root / "scripts" / "checks" / "check-rules.py"
    if copy.is_file() and not same(STANDARD / "scripts" / "check-rules.py", copy):
        notes.append("scripts/checks/check-rules.py differs from the skills copy; offer /project-setup to refresh it.")
    task = root / "TASK.md"
    if task.is_file() and len(task.read_text().splitlines()) > TASK_LIMIT:
        notes.append(f"TASK.md is over {TASK_LIMIT} lines; move finished work to docs/archive before new work.")
    return notes


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        payload = {}
    notes = machine_drift()
    root = project_root(Path(payload.get("cwd") or Path.cwd()))
    if root is not None and root != SKILLS:
        missing = [name for name in REQUIRED if not (root / name).exists()]
        if missing:
            notes.append(
                f"This project ({root}) is not set up with the owner's standards: missing {', '.join(missing)}. "
                "Before any other work, tell the owner in one line and offer to run the project-setup skill "
                "(/project-setup). Until it is set up, still follow ~/coding/skills: read the matching standard "
                "sections and the existing pattern before every edit."
            )
        else:
            notes.extend(project_drift(root))
    if not notes:
        return 0
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": " ".join(notes)}}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
