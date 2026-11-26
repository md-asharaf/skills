#!/usr/bin/env python3
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

HOOK = Path(__file__).with_name("session-check.py")


def run_hook(cwd: Path, home: Path) -> str:
    result = subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps({"cwd": str(cwd)}),
        capture_output=True,
        text=True,
        check=True,
        env={**os.environ, "HOME": str(home)},
    )
    if not result.stdout.strip():
        return ""
    return json.loads(result.stdout)["hookSpecificOutput"]["additionalContext"]


def setup_repo(root: Path, include: tuple[str, ...] = (".skills", "TASK.md", "AGENTS.md", "docs/AUDIT_BACKLOG.md")) -> None:
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    for rel in include:
        target = root / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("ok\n")


def main() -> int:
    failures: list[str] = []
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        home = base / "home"
        home.mkdir()

        missing_repo = base / "missing"
        missing_repo.mkdir()
        setup_repo(missing_repo, (".skills", "AGENTS.md"))
        out = run_hook(missing_repo, home)
        if "missing TASK.md, docs/AUDIT_BACKLOG.md" not in out or "/project-setup" not in out:
            failures.append(f"missing setup files: got {out!r}")

        stale_repo = base / "stale"
        stale_repo.mkdir()
        setup_repo(stale_repo)
        (stale_repo / "TASK.md").write_text("line\n" * 45)
        checker = stale_repo / "scripts" / "checks" / "check-rules.py"
        checker.parent.mkdir(parents=True, exist_ok=True)
        checker.write_text("old\n")
        out = run_hook(stale_repo, home)
        if "differs from the skills copy" not in out:
            failures.append(f"stale check-rules drift: got {out!r}")
        if "TASK.md is over 40 lines" not in out:
            failures.append(f"overlong TASK.md: got {out!r}")

        outside = base / "outside"
        outside.mkdir()
        out = run_hook(outside, home)
        if "not set up" in out:
            failures.append(f"outside git repo flagged setup: got {out!r}")

    total = 4
    for failure in failures:
        print(f"FAIL {failure}")
    print(f"{total - len(failures)}/{total} passed")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
