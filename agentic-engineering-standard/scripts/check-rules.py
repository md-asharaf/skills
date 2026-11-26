#!/usr/bin/env python3
import argparse
import fnmatch
import os
import re
import subprocess
import sys
from pathlib import Path

SLASH = {".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs", ".go", ".rs", ".java", ".kt", ".kts", ".scala", ".cs", ".dart", ".swift", ".c", ".h", ".cc", ".cpp", ".hpp", ".php"}
HASH = {".py", ".rb", ".sh", ".bash", ".zsh", ".ex", ".exs", ".php"}
DASH = {".sql"}
BLOCK = SLASH | {".css", ".scss", ".less", ".sql"}
MARKUP = {".vue", ".svelte", ".html", ".astro"}
TYPESCRIPT = {".ts", ".tsx", ".vue", ".svelte", ".astro"}
SOURCE = SLASH | HASH | DASH | BLOCK | MARKUP
SKIP_DIRS = {"node_modules", "dist", "build", ".next", "vendor", "target", ".venv", "venv", "__pycache__", "coverage", ".turbo", ".git", ".skills"}
ALLOWED_COMMENTS = [re.compile(p) for p in [r"^#!", r"^///\s*<reference", r"^//go:", r"^#\s*-\*-.*coding", r"^/\*!?\s*@vite-ignore\s*\*/$", r"^--> statement-breakpoint$"]]
SCRIPT_SUFFIXES = {".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs", ".vue", ".svelte", ".astro"}
REGEX_BEFORE = set("(,=:[!&|?{};+-*%<>~^") | {""}
REGEX_KEYWORDS = ("return", "typeof", "case", "in", "of", "delete", "void", "throw", "yield", "await")
SUPPRESSIONS = re.compile(
    r"eslint-disable|@ts-ignore|@ts-expect-error|@ts-nocheck|biome-ignore|\bnoqa\b|type:\s*ignore|pragma:\s*no cover"
    r"|//\s*nolint|@SuppressWarnings|#\[allow\(|#!\[allow\(|@phpstan-ignore|@psalm-suppress|#pragma warning disable"
    r"|\[SuppressMessage|//\s*ignore(_for_file)?:|istanbul ignore|c8 ignore|prettier-ignore|rubocop:disable|deno-lint-ignore"
)
TYPE_BYPASS = re.compile(r"\bas\s+unknown\s+as\b|\bas\s+any\b|:\s*any\b|<any>|\bas\s+never\b")
DOCS_ROOT = {"README.md", "BACKLOG.md", "AUDIT_BACKLOG.md", "DECISIONS.md", "designs", "reports", "archive"}
AUDIT_TYPES = {"FIX", "VERIFY", "DECIDE", "WATCH"}
TASK_SECTIONS = ["## 1. Goal", "## 2. Active Task", "## 3. Queued Tasks", "## 4. Waiting on User / Blockers"]
AGENT_FILE_NAMES = {"AGENTS.md", "CLAUDE.md", "GEMINI.md"}
AT_INCLUDE = re.compile(r"^\s*@(?:(?:\[[^\]]*\]\(([^)]+)\))|(\S+))\s*$")
LARGE_INLINE_TARGET = re.compile(r"(?:^|/)[^/\s]+/SKILL\.md$|(?:^|/)enforcement/REVIEW\.md$")
GEMINI_MAX_BYTES = 24000
CODEX_MAX_BYTES = 32768
CLAUDE_MAX_BYTES = 40000


def starts_regex(before: str) -> bool:
    stripped = before.rstrip()
    return (stripped[-1:] in REGEX_BEFORE and not stripped.endswith(("++", "--"))) or stripped.endswith(REGEX_KEYWORDS)


SHELL = {".sh", ".bash", ".zsh"}
HEREDOC = re.compile(r"<<-?\s*(['\"]?)([A-Za-z_]\w*)\1")


def split_code(text: str, suffix: str) -> list[tuple[int, str, str]]:
    pieces: list[tuple[int, str, str]] = []
    code: list[str] = []
    line, i, size = 1, 0, len(text)
    slash = suffix in SLASH or suffix in MARKUP
    hashes = suffix in HASH
    blocks = suffix in BLOCK or suffix in MARKUP
    quotes = "\"'" if suffix in HASH | DASH else "\"'`"
    heredoc: str | None = None

    def flush() -> None:
        if "".join(code).strip():
            pieces.append((line, "code", "".join(code)))
        code.clear()

    def skip_to(end: int, kind: str | None) -> None:
        nonlocal i, line
        if kind:
            pieces.append((line, kind, text[i:end]))
        else:
            code.append("\"\"")
        line += text.count("\n", i, end)
        i = end

    while i < size:
        char = text[i]
        if char == "\n":
            flush()
            line += 1
            i += 1
            if heredoc:
                stop = re.compile(rf"^\t*{re.escape(heredoc)}$", re.MULTILINE).search(text, i)
                end = size if stop is None else stop.end()
                line += text.count("\n", i, end)
                i = end
                heredoc = None
            continue
        if suffix in SHELL and (match := HEREDOC.match(text, i)):
            heredoc = match.group(2)
            code.append(match.group(0))
            i = match.end()
        elif suffix == ".py" and text.startswith(('"""', "'''"), i):
            end = text.find(text[i:i + 3], i + 3)
            skip_to(size if end < 0 else end + 3, None)
        elif suffix in SCRIPT_SUFFIXES and char == "/" and text[i + 1:i + 2] not in ("/", "*") and starts_regex("".join(code)):
            j, in_class = i + 1, False
            while j < size and text[j] != "\n" and (in_class or text[j] != "/"):
                in_class = (in_class or text[j] == "[") and text[j] != "]"
                j += 2 if text[j] == "\\" else 1
            skip_to(min(j + 1, size), None)
        elif char in quotes and not (suffix in SHELL and text[i - 1:i] == "\\"):
            j = i + 1
            while j < size and text[j] != char and not (text[j] == "\n" and char != "`" and suffix not in SHELL):
                j += 2 if text[j] == "\\" and not (suffix in SHELL and char == "'") else 1
            skip_to(min(j + 1, size), None)
        elif blocks and text.startswith("/*", i):
            end = text.find("*/", i + 2)
            skip_to(size if end < 0 else end + 2, "comment")
        elif suffix in MARKUP and text.startswith("<!--", i):
            end = text.find("-->", i + 4)
            skip_to(size if end < 0 else end + 3, "comment")
        elif (
            (slash and text.startswith("//", i) and text[i - 1:i] != ":")
            or (hashes and char == "#" and not text.startswith("#[", i) and (i == 0 or text[i - 1] in " \t\n;(") and not (suffix in SHELL and text[i - 1:i] == "$"))
            or (suffix in DASH and text.startswith("--", i))
        ):
            end = text.find("\n", i)
            skip_to(size if end < 0 else end, "comment")
        else:
            code.append(char)
            i += 1
    flush()
    return pieces


def tracked_files(root: Path, staged: bool) -> list[Path]:
    command = ["git", "diff", "--cached", "--name-only", "--diff-filter=ACMR"] if staged else ["git", "ls-files"]
    output = subprocess.run(command, cwd=root, capture_output=True, text=True, check=True).stdout
    return [root / name for name in output.splitlines() if name and not set(Path(name).parts) & SKIP_DIRS]


def allowed(path: str, rule: str, allow: list[str]) -> bool:
    return any(fnmatch.fnmatch(path, entry.split(" ")[0]) and (len(entry.split(" ")) == 1 or entry.split(" ")[1] == rule) for entry in allow)


def check_code(root: Path, files: list[Path], allow: list[str]) -> list[str]:
    problems: list[str] = []
    for path in files:
        suffix = path.suffix.lower()
        if suffix not in SOURCE or not path.is_file():
            continue
        relative = path.relative_to(root).as_posix()
        is_test = bool(re.search(r"(^|/)(tests?|__tests__|spec)/|[._-](test|spec)\.", relative))
        for line, kind, piece in split_code(path.read_text(errors="replace"), suffix):
            stripped = piece.strip()
            if kind == "comment":
                if SUPPRESSIONS.search(stripped):
                    rule = "suppression"
                elif any(pattern.search(stripped) for pattern in ALLOWED_COMMENTS) or (line == 1 and stripped.startswith("#!")):
                    continue
                else:
                    rule = "comment"
                if not allowed(relative, rule, allow):
                    problems.append(f"{relative}:{line} {rule}: {stripped.splitlines()[0][:80]}")
            elif SUPPRESSIONS.search(piece) and not allowed(relative, "suppression", allow):
                problems.append(f"{relative}:{line} suppression: {stripped[:80]}")
            elif suffix in TYPESCRIPT and (match := TYPE_BYPASS.search(piece)) and not (is_test and "never" in match.group(0)) and not allowed(relative, "type-bypass", allow):
                problems.append(f"{relative}:{line} type-bypass: {stripped[:80]}")
    return problems


def check_task(root: Path, task_max: int) -> list[str]:
    task = root / "TASK.md"
    if not task.is_file():
        return []
    lines = task.read_text().splitlines()
    problems = [f"TASK.md: {len(lines)} lines, the limit is {task_max} (move done work to docs/archive)"] if len(lines) > task_max else []
    problems += [f"TASK.md: missing section '{section}'" for section in TASK_SECTIONS if section not in lines]
    return problems


def check_agent_rules(root: Path) -> list[str]:
    agents = root / "AGENTS.md"
    if not agents.is_file():
        return []
    lines = agents.read_text().splitlines()
    section = next((i for i, line in enumerate(lines) if re.fullmatch(r"## \d+\. Invariant Engineering Laws", line)), None)
    if section is None:
        return []
    end = next((i for i in range(section + 1, len(lines)) if lines[i] == "### Frontend"), None)
    if end is None:
        end = next((i for i in range(section + 1, len(lines)) if re.match(r"^## ", lines[i])), len(lines))
    rules = [i for i in range(section + 1, end) if re.match(r"^\d+\. \*\*", lines[i])]
    problems = []
    for index, start in enumerate(rules):
        stop = rules[index + 1] if index + 1 < len(rules) else end
        number = re.match(r"^(\d+)", lines[start]).group(1)
        if not any("Enforced by:" in line for line in lines[start:stop]):
            problems.append(f"AGENTS.md: rule {number} is missing an Enforced by annotation")
    return problems


def iter_agent_files(root: Path) -> list[Path]:
    found: list[Path] = []
    for current, dirs, files in os.walk(root):
        dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS)
        current_path = Path(current)
        for name in sorted(files):
            path = current_path / name
            relative = path.relative_to(root)
            posix = relative.as_posix()
            if name in AGENT_FILE_NAMES or posix == ".github/copilot-instructions.md" or (relative.parts[:2] == (".cursor", "rules") and path.suffix == ".mdc"):
                found.append(path)
    return found


def expanded_bytes(root: Path, path: Path, seen: set[Path] | None = None) -> tuple[int, list[tuple[int, str]]]:
    seen = seen if seen is not None else set()
    resolved = path.resolve()
    if resolved in seen or not path.is_file():
        return 0, []
    seen.add(resolved)
    raw = path.read_text(errors="replace")
    total = len(raw.encode("utf-8"))
    bad_includes: list[tuple[int, str]] = []
    in_fence = False
    for number, line in enumerate(raw.splitlines(), 1):
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        match = AT_INCLUDE.match(line)
        if not match:
            continue
        target_text = (match.group(1) or match.group(2) or "").strip()
        if LARGE_INLINE_TARGET.search(target_text):
            bad_includes.append((number, target_text))
        candidate = (path.parent / target_text).resolve()
        if candidate.is_file() and (candidate.is_relative_to(root) or ".skills" in target_text):
            sub_bytes, sub_bad = expanded_bytes(root, candidate, seen)
            total += sub_bytes
            bad_includes.extend(sub_bad)
    return total, bad_includes


def check_agent_files(root: Path, agents_max: int, allow: list[str]) -> list[str]:
    problems: list[str] = []
    files = iter_agent_files(root)
    raw_sizes: dict[Path, int] = {}
    for path in files:
        relative = path.relative_to(root).as_posix()
        size = path.stat().st_size
        raw_sizes[path] = size
        if not allowed(relative, "agent-size", allow) and size > agents_max:
            problems.append(f"{relative}: {size} bytes, the limit is {agents_max} (move details to docs/ or pointer links)")
        expanded, bad_includes = expanded_bytes(root, path)
        for line, target in bad_includes:
            if not allowed(relative, "agent-inline", allow):
                problems.append(f"{relative}:{line} oversized-inline-import: '{target}' must be a path pointer, not an @ inline expansion")
        if path.name == "GEMINI.md" and expanded > GEMINI_MAX_BYTES and not allowed(relative, "agent-size", allow):
            problems.append(f"{relative}: expanded size {expanded} bytes exceeds Antigravity limit {GEMINI_MAX_BYTES}")
        if path.name == "CLAUDE.md" and expanded > CLAUDE_MAX_BYTES and not allowed(relative, "agent-size", allow):
            problems.append(f"{relative}: expanded size {expanded} bytes exceeds Claude Code limit {CLAUDE_MAX_BYTES}")
    for path in files:
        if path.name != "AGENTS.md":
            continue
        relative = path.relative_to(root).as_posix()
        if allowed(relative, "agent-size", allow):
            continue
        chain_bytes = 0
        cursor = path.parent
        while True:
            candidate = cursor / "AGENTS.md"
            if candidate in raw_sizes:
                chain_bytes += raw_sizes[candidate]
            if cursor == root:
                break
            cursor = cursor.parent
        if chain_bytes > CODEX_MAX_BYTES:
            problems.append(f"{relative}: cumulative AGENTS.md chain is {chain_bytes} bytes, exceeding Codex limit {CODEX_MAX_BYTES}")
    return problems


def check_docs(root: Path, allow: list[str]) -> list[str]:
    docs = root / "docs"
    if not docs.is_dir():
        return []
    problems = [
        f"docs/{entry.name}: not allowed at the docs root (agentic standard §9.2)"
        for entry in docs.iterdir()
        if entry.name not in DOCS_ROOT and not entry.name.startswith(".") and not allowed(f"docs/{entry.name}", "docs", allow)
    ]
    for entry in (docs / "archive").glob("*") if (docs / "archive").is_dir() else []:
        if not re.fullmatch(r"COMPLETED_\d{4}_\d{2}\.md|\..*", entry.name):
            problems.append(f"docs/archive/{entry.name}: archive files are COMPLETED_YYYY_MM.md")
    for entry in (docs / "reports").glob("*") if (docs / "reports").is_dir() else []:
        if not re.fullmatch(r"\d{4}_\d{2}_[a-z0-9_]+\.md|benchmarks|\..*", entry.name):
            problems.append(f"docs/reports/{entry.name}: reports are YYYY_MM_<topic>.md")
    audit = docs / "AUDIT_BACKLOG.md"
    if audit.is_file():
        text = audit.read_text()
        if "## Counts" not in text:
            problems.append("docs/AUDIT_BACKLOG.md: missing '## Counts'")
        counts = {kind: 0 for kind in AUDIT_TYPES}
        for number, row in enumerate(text.splitlines(), 1):
            cells = [cell.strip() for cell in row.strip().strip("|").split("|")]
            if row.startswith("|") and len(cells) > 1 and re.fullmatch(r"[A-Z]+-?\d+", cells[0]):
                if cells[1] not in AUDIT_TYPES:
                    problems.append(f"docs/AUDIT_BACKLOG.md:{number} type '{cells[1]}' is not one of FIX, VERIFY, DECIDE, WATCH")
                else:
                    counts[cells[1]] += 1
        counts_line = next((line for line in text.splitlines() if line.startswith("- FIX:")), None)
        count_match = re.fullmatch(r"- FIX: (\d+) \| VERIFY: (\d+) \| DECIDE: (\d+) \| WATCH: (\d+) \| Total: (\d+)", counts_line or "")
        if counts_line is None or count_match is None:
            problems.append("docs/AUDIT_BACKLOG.md: invalid or missing count line")
        else:
            reported = dict(zip(("FIX", "VERIFY", "DECIDE", "WATCH"), map(int, count_match.groups()[:4])))
            total = sum(counts.values())
            if reported != counts or int(count_match.group(5)) != total:
                problems.append("docs/AUDIT_BACKLOG.md: Counts do not match the open items table")
            task = root / "TASK.md"
            task_count = re.search(r"Open items \((\d+)\)", task.read_text()) if task.is_file() else None
            if task_count and int(task_count.group(1)) != total:
                problems.append(f"TASK.md: open-item count {task_count.group(1)} does not match AUDIT_BACKLOG.md count {total}")
    decisions = docs / "DECISIONS.md"
    if decisions.is_file():
        for number, row in enumerate(decisions.read_text().splitlines(), 1):
            if row.startswith("## ") and not re.match(r"## ADR-\d{3,}: .+", row):
                problems.append(f"docs/DECISIONS.md:{number} headings are '## ADR-NNN: <title> (YYYY-MM-DD)'")
    return problems


def main() -> int:
    parser = argparse.ArgumentParser(description="Language-independent checks of the agentic standard (§9, §13).")
    parser.add_argument("--staged", action="store_true", help="check only staged files")
    parser.add_argument("--skip-code", action="store_true", help="skip comments, suppressions and type bypasses (the project's own gate covers them)")
    parser.add_argument("--task-max", type=int, default=40)
    parser.add_argument("--agents-max-bytes", type=int, default=12000)
    parser.add_argument("--allow", default="scripts/checks/rules-allow.txt", help="lines of '<glob> [rule]'; a gate file")
    parser.add_argument("root", nargs="?", default=".")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    allow_file = root / args.allow
    allow = [line.strip() for line in allow_file.read_text().splitlines() if line.strip()] if allow_file.is_file() else []
    problems = [] if args.skip_code else check_code(root, tracked_files(root, args.staged), allow)
    problems += check_agent_rules(root) + check_agent_files(root, args.agents_max_bytes, allow) + check_task(root, args.task_max) + check_docs(root, allow)
    for problem in problems:
        print(problem)
    print(f"check-rules: {len(problems)} problem(s)")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
