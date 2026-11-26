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
    ("echo x >> AGENTS.md", "ask"),
    ("cat AGENTS.md | head", "allow"),
    ("sed -i s/a/b/ apps/api/CLAUDE.md", "ask"),
    ("echo x > .cursor/rules/standards.mdc", "ask"),
    ("echo x > docs/AGENTS-notes.md", "allow"),
    ("git diff --stat; git status -s", "allow"),
    ("rm -rf node_modules", "ask"),
    ("grep -n psql docs/notes.md", "allow"),
    ("psql postgres://x", "ask"),
    ("npx prisma migrate deploy", "deny"),
    ("alembic upgrade head", "deny"),
    ("python manage.py migrate", "deny"),
    ("python manage.py makemigrations --check", "allow"),
    ("bin/rails db:migrate", "deny"),
    ("goose -dir migrations postgres x up", "deny"),
    ("php artisan migrate --force", "deny"),
    ("dotnet ef database update", "deny"),
    ("SKIP=ruff git commit -m x", "deny"),
    ("pnpm add zod", "ask"),
    ("pnpm --filter @ws/api add zod", "ask"),
    ("pnpm install --frozen-lockfile", "allow"),
    ("pip install requests", "ask"),
    ("pip install -r requirements.txt", "allow"),
    ("go get github.com/x/y", "ask"),
    ("cargo add serde", "ask"),
    ("go test ./...", "allow"),
    ("sed -i s/a/b/ package.json", "ask"),
    ("cat package.json | jq .scripts", "allow"),
    ("echo x >> .pre-commit-config.yaml", "ask"),
    ("sed -i s/x/y/ .golangci.yml", "ask"),
    ("cp a tsconfig.json", "ask"),
    ("echo x > .github/workflows/ci.yml", "ask"),
    ("redis-cli FLUSHALL", "ask"),
]

FILE_CASES = [
    ("/x/eslint.config.ts", "ask"),
    ("/x/.github/workflows/verify.yml", "ask"),
    ("/x/apps/api/src/a.ts", "allow"),
    ("/x/pyproject.toml", "ask"),
    ("/x/go.mod", "ask"),
    ("/x/apps/web/package.json", "ask"),
    ("/x/src/package_json.py", "allow"),
    ("/x/.claude/agents/reviewer.md", "ask"),
    ("/x/analysis_options.yaml", "ask"),
    ("/x/scripts/checks/side-effects.mjs", "ask"),
    ("/x/src/services/checkout.service.ts", "allow"),
    ("/x/AGENTS.md", "ask"),
    ("/x/apps/web/CLAUDE.md", "ask"),
    ("/x/GEMINI.md", "ask"),
    ("/x/.cursor/rules/standards.mdc", "ask"),
    ("/x/docs/DECISIONS.md", "allow"),
    ("/x/TASK.md", "allow"),
    ("/x/.gitleaksignore", "ask"),
    ("/x/scripts/checks/rules-allow.txt", "ask"),
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
