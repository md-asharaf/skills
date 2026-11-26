#!/usr/bin/env python3
import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPT = Path(__file__).with_name("check-rules.py")

CASES = [
    ("clean typescript", "a.ts", "const url = 'https://x.dev//path';\nexport const n = `a // b ${url}`;\n", []),
    ("line comment", "a.ts", "const a = 1;\n// explain\n", ["a.ts:2 comment"]),
    ("trailing comment", "a.ts", "const a = 1; // explain\n", ["a.ts:1 comment"]),
    ("block comment", "a.ts", "/**\n * doc\n */\nconst a = 1;\n", ["a.ts:1 comment"]),
    ("suppression", "a.ts", "// eslint-disable-next-line\nconst a = 1;\n", ["a.ts:1 suppression"]),
    ("ts ignore", "a.tsx", "// @ts-ignore\nconst a = 1;\n", ["a.tsx:1 suppression"]),
    ("double cast", "src/a.ts", "const a = b as unknown as C;\n", ["src/a.ts:1 type-bypass"]),
    ("as never in a test", "tests/a.spec.ts", "const a = b as never;\n", []),
    ("as never in source", "src/a.ts", "const a = b as never;\n", ["src/a.ts:1 type-bypass"]),
    ("reference directive", "env.d.ts", "/// <reference types=\"vite/client\" />\n", []),
    ("python comment", "a.py", "x = 1  # why\n", ["a.py:1 comment"]),
    ("python string hash", "a.py", "x = '#not'\ny = \"\"\"\n# inside\n\"\"\"\n", []),
    ("python noqa", "a.py", "import os  # noqa: F401\n", ["a.py:1 suppression"]),
    ("shebang", "run.sh", "#!/usr/bin/env bash\necho \"${#args[@]}\" '#x'\n", []),
    ("shell comment", "run.sh", "#!/usr/bin/env bash\n  # explain\necho hi\n", ["run.sh:2 comment"]),
    ("shell heredoc", "run.sh", "cat > f <<'EOF'\n# Heading\nEOF\necho done\n", []),
    ("go directive", "a.go", "//go:build linux\npackage a\n", []),
    ("go nolint", "a.go", "x := 1 //nolint\n", ["a.go:1 suppression"]),
    ("rust allow", "a.rs", "#[allow(dead_code)]\nfn a() {}\n", ["a.rs:1 suppression"]),
    ("sql comment", "a.sql", "select 1; -- why\n", ["a.sql:1 comment"]),
    ("html comment", "a.vue", "<template>\n<!-- note -->\n</template>\n", ["a.vue:2 comment"]),
    ("regex literal", "a.mjs", "const r = /(\\/\\/|\\/\\*)/;\nconst u = /[a-z]:\\/\\//gi;\nconst d = a / b / c;\n", []),
    ("regex with eslint text", "a.mjs", "const r = /eslint-disable/;\n", []),
    ("division then comment", "a.ts", "const d = a / 2; // why\n", ["a.ts:1 comment"]),
    ("commented-out code", "a.cjs", "module.exports = {};\n// { name: 'web' },\n", ["a.cjs:2 comment"]),
    ("drizzle marker", "0001_x.sql", "create table a ();\n--> statement-breakpoint\ncreate table b ();\n", []),
    ("allow list", "legacy/a.ts", "// kept\n", []),
]

TASK_OK = "# Active Task State\n\n## 1. Goal\nx\n## 2. Active Task\nx\n## 3. Queued Tasks\nx\n## 4. Waiting on User / Blockers\nx\n"


def run(files: dict[str, str]) -> list[str]:
    with tempfile.TemporaryDirectory() as root:
        subprocess.run(["git", "init", "-q"], cwd=root, check=True)
        for name, body in files.items():
            path = Path(root) / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(body)
        subprocess.run(["git", "add", "-A"], cwd=root, check=True)
        result = subprocess.run([sys.executable, str(SCRIPT), root], capture_output=True, text=True)
        return [line for line in result.stdout.splitlines() if not line.startswith("check-rules:")]


def matches(found: list[str], expected: list[str]) -> bool:
    return len(found) == len(expected) and all(line.startswith(prefix) for line, prefix in zip(sorted(found), sorted(expected)))


def main() -> int:
    failures: list[str] = []
    allow = {"scripts/checks/rules-allow.txt": "legacy/* comment\n"}
    for name, path, body, expected in CASES:
        found = run({path: body, **allow})
        if not matches(found, expected):
            failures.append(f"{name}: expected {expected}, got {found}")
    memory_cases = [
        ("task ok", {"TASK.md": TASK_OK}, []),
        ("task too long", {"TASK.md": TASK_OK + "x\n" * 40}, ["TASK.md: 50 lines"]),
        ("task section missing", {"TASK.md": "# Active Task State\n## 1. Goal\n"}, ["TASK.md: missing", "TASK.md: missing", "TASK.md: missing"]),
        ("loose docs file", {"docs/notes.md": "x"}, ["docs/notes.md"]),
        ("archive name", {"docs/archive/done.md": "x"}, ["docs/archive/done.md"]),
        ("audit type", {"docs/AUDIT_BACKLOG.md": "| OI-01 | risk | d | s | w | x |\n## Counts\n- FIX: 0 | VERIFY: 0 | DECIDE: 0 | WATCH: 0 | Total: 0\n"}, ["docs/AUDIT_BACKLOG.md:1"]),
        ("audit counts", {"docs/AUDIT_BACKLOG.md": "| OI-01 | FIX | d | s | w | x |\n## Counts\n- FIX: 0 | VERIFY: 0 | DECIDE: 0 | WATCH: 0 | Total: 0\n"}, ["docs/AUDIT_BACKLOG.md: Counts do not match"]),
        ("audit counts match", {"docs/AUDIT_BACKLOG.md": "| OI-01 | FIX | d | s | w | x |\n## Counts\n- FIX: 1 | VERIFY: 0 | DECIDE: 0 | WATCH: 0 | Total: 1\n"}, []),
        ("audit compact ids match", {"docs/AUDIT_BACKLOG.md": "| O2 | FIX | d | s | w | x |\n| C06 | WATCH | d | s | w | x |\n## Counts\n- FIX: 1 | VERIFY: 0 | DECIDE: 0 | WATCH: 1 | Total: 2\n"}, []),
        ("docs allowlist", {"docs/openapi.yaml": "openapi: 3.1.0\n", "scripts/checks/rules-allow.txt": "docs/openapi.yaml docs\n"}, []),
        ("task open-item count", {"TASK.md": TASK_OK + "\nOpen items (2)\n", "docs/AUDIT_BACKLOG.md": "| OI-01 | FIX | d | s | w | x |\n## Counts\n- FIX: 1 | VERIFY: 0 | DECIDE: 0 | WATCH: 0 | Total: 1\n"}, ["TASK.md: open-item count 2 does not match AUDIT_BACKLOG.md count 1"]),
        ("decision heading", {"docs/DECISIONS.md": "## ADR-001: Good (2026-01-01)\n## Notes\n"}, ["docs/DECISIONS.md:2"]),
    ]
    for name, files, expected in memory_cases:
        found = run(files)
        if not matches(found, expected):
            failures.append(f"{name}: expected {expected}, got {found}")
    rule_cases = [
        ("rule gate present", {"AGENTS.md": "## 4. Invariant Engineering Laws\n1. **Clear rules**\n*Enforced by: review.*\n### Frontend\n"}, []),
        ("rule gate missing", {"AGENTS.md": "## 4. Invariant Engineering Laws\n1. **Clear rules**\n### Frontend\n"}, ["AGENTS.md: rule 1 is missing an Enforced by annotation"]),
        ("agent file over byte limit", {"AGENTS.md": "a" * 12500}, ["AGENTS.md: 12500 bytes"]),
        ("oversized inline skill import", {"GEMINI.md": "@.skills/backend-engineering-standard/SKILL.md\n"}, ["GEMINI.md:1 oversized-inline-import"]),
        ("gemini expanded over 24k", {"AGENTS.md": "a" * 12000, "CLAUDE.md": "b" * 12000, "GEMINI.md": "@AGENTS.md\n@CLAUDE.md\n" + ("c" * 200)}, ["GEMINI.md: expanded size"]),
        (
            "codex cumulative chain over 32k",
            {
                "AGENTS.md": "a" * 11500,
                "apps/AGENTS.md": "b" * 11500,
                "apps/api/AGENTS.md": "c" * 11500,
            },
            ["apps/api/AGENTS.md: cumulative AGENTS.md chain"],
        ),
    ]
    for name, files, expected in rule_cases:
        found = run(files)
        if not matches(found, expected):
            failures.append(f"{name}: expected {expected}, got {found}")
    total = len(CASES) + len(memory_cases) + len(rule_cases)
    for failure in failures:
        print(f"FAIL {failure}")
    print(f"{total - len(failures)}/{total} passed")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
