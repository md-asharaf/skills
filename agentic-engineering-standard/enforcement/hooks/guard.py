#!/usr/bin/env python3
import json
import re
import sys
from pathlib import Path

PROTECTED_PATHS = [
    r"/etc/claude-code",
    r"managed-settings\.json",
    r"agentic-engineering-standard/enforcement/",
    r"HARD-RULES\.md",
    r"(^|/)\.claude/",
    r"(^|/)(AGENTS|CLAUDE|GEMINI)\.md$",
    r"(^|/)\.cursor/rules/",
    r"(^|/)\.cursorrules$|(^|/)\.windsurfrules$",
    r"(^|/)\.husky/",
    r"(^|/)\.git/hooks/",
    r"(^|/)\.pre-commit-config\.ya?ml",
    r"(^|/)lefthook\.ya?ml",
    r"(^|/)\.github/",
    r"(^|/)\.gitlab-ci\.ya?ml",
    r"(^|/)\.circleci/",
    r"(^|/)Jenkinsfile",
    r"(^|/)azure-pipelines\.ya?ml",
    r"(^|/)bitbucket-pipelines\.ya?ml",
    r"(^|/)scripts/(verify|checks|gates)",
    r"(^|/)eslint\.config\.|(^|/)\.eslintrc",
    r"(^|/)biome\.jsonc?",
    r"(^|/)\.?stylelintrc|(^|/)stylelint\.config\.",
    r"(^|/)\.?cspell\.json|(^|/)cspell\.config\.",
    r"(^|/)tsconfig[\w.-]*\.json",
    r"(^|/)\.dependency-cruiser",
    r"(^|/)(\.)?ruff\.toml|(^|/)mypy\.ini|(^|/)pyrightconfig\.json|(^|/)\.importlinter|(^|/)setup\.cfg",
    r"(^|/)\.golangci\.ya?ml",
    r"(^|/)clippy\.toml|(^|/)deny\.toml|(^|/)rustfmt\.toml",
    r"(^|/)phpstan\.neon|(^|/)psalm\.xml|(^|/)deptrac\.ya?ml",
    r"(^|/)analysis_options\.yaml",
    r"(^|/)Directory\.Build\.props|(^|/)\.editorconfig",
    r"(^|/)(package\.json|pyproject\.toml|requirements[\w.-]*\.txt|go\.mod|Cargo\.toml|composer\.json|pubspec\.yaml|Gemfile|pom\.xml|build\.gradle(\.kts)?|[\w.-]+\.csproj)$",
]

PROTECTED_PATHS = [
    pattern.replace("(^|/)", r"(^|[\s/'\"=:])").replace(")$", r")(?=$|[\s'\";|&)])")
    for pattern in PROTECTED_PATHS
]

PROJECT_PROTECTED_FILE = ".claude/protected-paths.txt"

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

GIT_COMMAND = re.compile(
    r"^\s*(?:\w+=\S*\s+)*git(?:\s+-[Cc]\s+\S+|\s+--\S+=\S+)*\s+(?P<rest>.*)$"
)

GIT_DENY = [
    (r"^push\b", "Pushing is done by the user after reviewing the diff. Ask the user to run `! git push`."),
    (r"^commit\b.*\s-[a-zA-Z]*n[a-zA-Z]*(\s|$)", "`git commit -n` skips hooks; hooks are never bypassed."),
    (r"^filter-(branch|repo)\b", "Rewriting history needs the user."),
    (r"^config\b.*\bcore\.hooksPath\b", "Hooks are never redirected."),
]

GIT_ASK = [
    (r"^reset\b.*--hard", "Discards work."),
    (r"^rebase\b", "Rewrites history."),
    (r"^clean\b.*\s-[a-zA-Z]*f", "Deletes untracked files."),
    (r"^checkout\b\s+(--\s|\.\s*$)", "Discards changes."),
    (r"^restore\b", "Discards changes."),
    (r"^branch\b.*\s-D\b", "Deletes a branch."),
]

MIGRATIONS = (
    r"drizzle-kit\s+(migrate|push|drop)"
    r"|\bdb:(migrate|push|rollback|reset|drop|seed)"
    r"|prisma\s+(migrate\s+(deploy|dev|reset|resolve)|db\s+(push|execute))"
    r"|alembic\s+(upgrade|downgrade|stamp)"
    r"|manage\.py\s+(migrate|flush|sqlflush)"
    r"|\brake\s+db:|\brails\s+db:"
    r"|\bgoose\b.*\b(up|down|redo|reset)\b"
    r"|\bflyway\b.*\b(migrate|clean|undo|repair)\b"
    r"|\bliquibase\b.*\b(update|rollback|drop-all)\b"
    r"|sqlx\s+(migrate\s+(run|revert)|database\s+(drop|reset))"
    r"|diesel\s+(migration\s+(run|revert|redo)|database\s+reset)"
    r"|artisan\s+(migrate|db:wipe)"
    r"|knex\s+migrate:|sequelize(-cli)?\s+db:|typeorm\s+(migration:(run|revert)|schema:(drop|sync))"
    r"|dotnet\s+ef\s+database\s+(update|drop)"
    r"|mix\s+ecto\.(migrate|rollback|drop|reset)"
)

DENY = [
    (r"--no-verify", "Hooks are never bypassed."),
    (r"(^|\s)HUSKY=0\b|\bHUSKY_SKIP|\bSKIP=\S|\bPRE_COMMIT_ALLOW_NO_CONFIG|\bLEFTHOOK=0\b", "Hooks are never bypassed."),
    (MIGRATIONS, "Migrations and schema changes against a database are applied by the user."),
    (r"--dangerously-skip-permissions", "Permission checks are never bypassed."),
]

ASK = [
    (r"\brm\s+-[a-zA-Z]*r[a-zA-Z]*f|\brm\s+-[a-zA-Z]*f[a-zA-Z]*r", "Deletes files recursively."),
    (r"(^|[;&|]\s*)(psql|pg_restore|dropdb|mysql|mongosh|mongo|redis-cli|sqlcmd|sqlite3)\b", "Runs commands against a database."),
    (
        r"(^|[;&|]\s*)("
        r"(npm|pnpm|yarn|bun)\s+(add|install|i)\s+[^-\s]"
        r"|(pnpm|npm)\s+.*\s(add|install)\s+[^-\s]"
        r"|pip3?\s+install\s+(?!-r\b|-e\s+\.)[^-\s]|uv\s+(add|pip\s+install)|poetry\s+add|pipenv\s+install\s+[^-\s]"
        r"|go\s+get\s|cargo\s+(add|install)\s|composer\s+require\s|bundle\s+add\s|gem\s+install\s"
        r"|dotnet\s+add\s.*package|flutter\s+pub\s+add|dart\s+pub\s+add"
        r")",
        "Adds a dependency; new dependencies need the user's approval.",
    ),
]

SEGMENT_SPLIT = re.compile(r"\n|;|&&|\|\||\||\$\(|`")


def project_paths(cwd: str | None) -> list[str]:
    start = Path(cwd) if cwd else Path.cwd()
    for candidate in [start, *start.parents]:
        listing = candidate / PROJECT_PROTECTED_FILE
        if listing.is_file():
            lines = listing.read_text().splitlines()
            return [re.escape(line.strip()) for line in lines if line.strip() and not line.startswith("#")]
        if (candidate / ".git").exists():
            return []
    return []


def git_verdict(command: str, rules: list[tuple[str, str]]) -> str | None:
    for segment in SEGMENT_SPLIT.split(command):
        match = GIT_COMMAND.match(segment)
        if not match:
            continue
        rest = match.group("rest")
        for pattern, reason in rules:
            if re.search(pattern, rest):
                return reason
    return None


def decide(command: str, protected: list[str]) -> tuple[str, str] | None:
    reason = git_verdict(command, GIT_DENY)
    if reason:
        return "deny", reason
    for pattern, reason in DENY:
        if re.search(pattern, command):
            return "deny", reason
    if any(re.search(path, command) for path in protected) and any(
        re.search(marker, command) for marker in WRITE_MARKERS
    ):
        return "ask", "This command may change a gate, hook, lint, CI, dependency or permission file. Only the user approves such changes."
    reason = git_verdict(command, GIT_ASK)
    if reason:
        return "ask", reason
    for pattern, reason in ASK:
        if re.search(pattern, command):
            return "ask", reason
    return None


def decide_file(file_path: str, protected: list[str]) -> tuple[str, str] | None:
    if any(re.search(path, file_path) for path in protected):
        return "ask", "This file is a gate, hook, lint, CI, dependency or permission file. Only the user approves changes to it."
    return None


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0
    protected = PROTECTED_PATHS + project_paths(payload.get("cwd"))
    tool_input = payload.get("tool_input", {})
    command = tool_input.get("command")
    file_path = tool_input.get("file_path") or tool_input.get("notebook_path")
    if isinstance(command, str):
        verdict = decide(command, protected)
    elif isinstance(file_path, str):
        verdict = decide_file(file_path, protected)
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
