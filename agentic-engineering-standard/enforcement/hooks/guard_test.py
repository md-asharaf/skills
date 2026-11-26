#!/usr/bin/env python3
import json
import subprocess
import sys
from pathlib import Path

GUARD = Path(__file__).with_name("guard.py")

CASES = [
    ("git push origin main", "deny"),
    ("git -C /x push", "deny"),
    ("cd x && git push", "deny"),
    ("python3 - <<EOF\ns = 'refuse git push to the agent'\nEOF", "allow"),
    ('git commit -m "docs: never git push"', "allow"),
    ('git commit -m "feat: x"', "allow"),
    ("git commit -n -m x", "deny"),
    ("git commit --no-verify -m x", "deny"),
    ("HUSKY=0 git commit -m x", "deny"),
    ("git config core.hooksPath /dev/null", "deny"),
    ("git filter-branch --all", "deny"),
    ("pnpm --filter @ws/db exec drizzle-kit migrate", "deny"),
    ("pnpm --filter @ws/db exec drizzle-kit check 2>&1 | tail", "allow"),
    ("sed -i s/a/b/ scripts/verify-all.mjs", "ask"),
    ("sed -n 1,20p scripts/verify-all.mjs", "allow"),
    ("cat eslint.config.ts | head", "allow"),
    ("echo x > .husky/pre-commit", "ask"),
    ("git reset --hard HEAD", "ask"),
    ("git reset --soft HEAD~1", "allow"),
    ("git rebase main", "ask"),
    ("git log --oneline -3 2>/dev/null", "allow"),
    ("git diff --stat; git status -s", "allow"),
    ("rm -rf node_modules", "ask"),
    ("grep -n psql docs/notes.md", "allow"),
    ("psql postgres://x", "ask"),
]

FILE_CASES = [
    ("/x/eslint.config.ts", "ask"),
    ("/x/.github/workflows/verify.yml", "ask"),
    ("/x/apps/api/src/a.ts", "allow"),
]


def verdict(payload: dict) -> str:
    out = subprocess.run(
        [sys.executable, str(GUARD)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    return json.loads(out)["hookSpecificOutput"]["permissionDecision"] if out else "allow"


def main() -> int:
    failures = 0
    cases = [({"tool_name": "Bash", "tool_input": {"command": c}}, w, c) for c, w in CASES]
    cases += [({"tool_name": "Edit", "tool_input": {"file_path": f}}, w, f) for f, w in FILE_CASES]
    for payload, want, label in cases:
        got = verdict(payload)
        if got != want:
            failures += 1
            print(f"FAIL want={want} got={got}: {label!r}")
    print(f"{len(cases) - failures}/{len(cases)} passed")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
