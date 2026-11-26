#!/usr/bin/env python3
import json
import os
import runpy
import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPT = Path(__file__).with_name("setup-project.sh")
SKILLS_SOURCE = Path(__file__).resolve().parents[2]
DETECTOR = runpy.run_path(str(SCRIPT.with_name("detect-project.py")))
TASK = "# Active Task State\n\n## 1. Goal\nx\n## 2. Active Task\nx\n## 3. Queued Tasks\nx\n## 4. Waiting on User / Blockers\nx\n"


def run(files: dict[str, str], check: bool = True) -> tuple[int, str]:
    with tempfile.TemporaryDirectory() as root:
        subprocess.run(["git", "init", "-q"], cwd=root, check=True)
        for name, body in files.items():
            path = Path(root) / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(body)
        environment = os.environ | {"SKILLS_SOURCE": str(SKILLS_SOURCE), "HOME": root}
        command = ["bash", str(SCRIPT)]
        if check:
            command.append("--check")
        command.append(root)
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            env=environment,
        )
        return result.returncode, result.stdout


def created_pointers() -> tuple[int, str, dict[str, str]]:
    with tempfile.TemporaryDirectory() as root:
        subprocess.run(["git", "init", "-q"], cwd=root, check=True)
        environment = os.environ | {"SKILLS_SOURCE": str(SKILLS_SOURCE), "HOME": root}
        result = subprocess.run(
            ["bash", str(SCRIPT), root],
            capture_output=True,
            text=True,
            env=environment,
        )
        files = {
            "AGENTS.md": Path(root, "AGENTS.md").read_text(),
            "CLAUDE.md": Path(root, "CLAUDE.md").read_text(),
            "GEMINI.md": Path(root, "GEMINI.md").read_text(),
            ".github/copilot-instructions.md": Path(root, ".github/copilot-instructions.md").read_text(),
            ".cursor/rules/standards.mdc": Path(root, ".cursor/rules/standards.mdc").read_text(),
        }
        return result.returncode, result.stdout, files


def configured_setup_check(mode: str) -> tuple[int, str]:
    with tempfile.TemporaryDirectory() as root:
        subprocess.run(["git", "init", "-q"], cwd=root, check=True)
        environment = os.environ | {"SKILLS_SOURCE": str(SKILLS_SOURCE), "HOME": root}
        subprocess.run(
            ["bash", str(SCRIPT), root],
            capture_output=True,
            text=True,
            env=environment,
            check=True,
        )
        Path(root, "package.json").write_text('{"dependencies":{"express":"1"}}\n')
        subprocess.run(
            ["bash", str(SCRIPT), root],
            capture_output=True,
            text=True,
            env=environment,
            check=True,
        )
        Path(root, "scripts").mkdir(exist_ok=True)
        gate = ""
        if mode == "valid":
            gate = (
                "#!/usr/bin/env bash\n"
                "case \"${1:-staged}\" in\n"
                "  staged)\n"
                "    gitleaks git --staged\n"
                "    python3 scripts/checks/check-rules.py --staged\n"
                "    ;;\n"
                "  ci)\n"
                "    python3 scripts/checks/check-rules.py\n"
                "    ;;\n"
                "  *) exit 2 ;;\n"
                "esac\n"
            )
        elif mode == "decoy":
            gate = (
                "#!/usr/bin/env bash\n"
                "case \"${1:-staged}\" in\n"
                "  staged)\n"
                "    echo 'gitleaks git --staged'\n"
                "    echo 'python3 scripts/checks/check-rules.py'\n"
                "    ;;\n"
                "  ci)\n"
                "    echo 'python3 scripts/checks/check-rules.py'\n"
                "    ;;\n"
                "  *) exit 2 ;;\n"
                "esac\n"
            )
        Path(root, "scripts/gates.sh").write_text(gate)
        Path(root, "scripts/gates.sh").chmod(0o755)
        Path(root, ".husky").mkdir(exist_ok=True)
        if mode == "inert":
            hook = "#!/bin/sh\nexit 0\n"
        elif mode == "decoy":
            hook = "#!/bin/sh\necho 'scripts/gates.sh staged'\n"
        else:
            hook = "#!/bin/sh\n./scripts/gates.sh staged\n"
        Path(root, ".husky/pre-commit").write_text(hook)
        Path(root, ".husky/commit-msg").write_text("#!/bin/sh\nexit 0\n")
        Path(root, ".github/workflows").mkdir(parents=True, exist_ok=True)
        if mode == "inert":
            workflow = "gitleaks\n"
        elif mode == "decoy":
            workflow = (
                "name: verify\njobs:\n  verify:\n    steps:\n"
                "      - run: echo 'gitleaks git'\n"
                "      - run: echo 'scripts/gates.sh ci'\n"
            )
        else:
            workflow = (
            "name: verify\njobs:\n  verify:\n    steps:\n"
            "      - run: gitleaks git --redact --no-banner .\n"
            "      - run: ./scripts/gates.sh ci\n"
            )
        Path(root, ".github/workflows/verify.yml").write_text(workflow)
        Path(root, "cspell.json").write_text("{}\n" if mode == "inert" else '{"flagWords":[]}\n')
        Path(root, ".eslintrc.json").write_text('{"note":"catch-or-return"}\n')
        result = subprocess.run(
            ["bash", str(SCRIPT), "--check", root],
            capture_output=True,
            text=True,
            env=environment,
        )
        return result.returncode, result.stdout


def detect_profile(files: dict[str, str]) -> tuple[set[str], set[str]]:
    with tempfile.TemporaryDirectory() as root:
        for name, body in files.items():
            path = Path(root, name)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(body)
        return DETECTOR["classify"](Path(root))


def main() -> int:
    cases = [
        (
            "detects a single CI file",
            {".github/workflows/verify.yml": "name: Verify\n"},
            "CI that runs the gates",
            False,
        ),
        (
            "rejects cspell config without flagWords",
            {"cspell.json": "{}\n"},
            "cspell configuration is missing flagWords",
            True,
        ),
        (
            "detects a supported app profile",
            {
                "apps/api/package.json": '{"dependencies":{"@nestjs/core":"1","typescript":"1"}}\n',
                "apps/web/package.json": '{"dependencies":{"next":"1","typescript":"1"}}\n',
            },
            "server parts: apps/api",
            True,
        ),
        (
            "rejects an unknown app profile",
            {"package.json": '{"dependencies":{"custom-server-framework":"1","typescript":"1"}}\n'},
            "unverified application profile",
            True,
        ),
        (
            "rejects an incomplete Ruby profile",
            {"Gemfile": "source 'https://rubygems.org'\n"},
            "unverified language profile",
            True,
        ),
        (
            "rejects an incomplete Swift profile",
            {"Package.swift": "let package = Package(name: \"Example\")\n"},
            "unverified language profile",
            True,
        ),
        (
            "detects a Python backend",
            {"requirements.txt": "fastapi\n", "mypy.ini": "[mypy]\nstrict = True\n"},
            "Detected: python; server parts: .",
            True,
        ),
        (
            "detects a Go backend",
            {"go.mod": "module example\n", ".golangci.yml": "linters:\n"},
            "Detected: go; server parts: .",
            True,
        ),
        (
            "detects a Rust backend",
            {"Cargo.toml": "[package]\nname = \"example\"\nclippy = true\n"},
            "Detected: rust; server parts: .",
            True,
        ),
        (
            "detects a JVM backend",
            {"pom.xml": "<project><artifactId>errorprone</artifactId></project>\n"},
            "Detected: jvm; server parts: .",
            True,
        ),
        (
            "detects a .NET backend",
            {"api.csproj": "<Project />\n", "Directory.Build.props": "<TreatWarningsAsErrors>true</TreatWarningsAsErrors>\n"},
            "Detected: dotnet; server parts: .",
            True,
        ),
        (
            "detects a PHP backend",
            {"composer.json": "{}\n", "phpstan.neon": "parameters:\n"},
            "Detected: php; server parts: .",
            True,
        ),
        (
            "detects a Flutter frontend",
            {"pubspec.yaml": "dependencies:\n  flutter:\n", "analysis_options.yaml": "analyzer:\n  language:\n    strict-casts: true\n"},
            "Detected: dart; server parts: none; UI parts: .",
            True,
        ),
    ]
    failures: list[str] = []
    for name, files, expected_text, should_be_present in cases:
        status, output = run(files)
        if status == 0 or (expected_text in output) != should_be_present:
            failures.append(f"{name}: exit {status}, expected presence {should_be_present} for '{expected_text}'")
    status, output = run({})
    if status == 0 or "setup check failed" not in output.lower():
        failures.append(f"missing controls: expected a failing check, got exit {status}")
    if "unverified stack" not in output:
        failures.append("unknown stack: expected an explicit unverified result")
    for path in ("AGENTS.md", "CLAUDE.md", "GEMINI.md", ".github/copilot-instructions.md", ".cursor/rules/standards.mdc"):
        if path not in output:
            failures.append(f"missing pointer: expected {path} in the setup report")
    _, output = run({".gitignore": "*.md\n", "AGENTS.md": "rules\n", "TASK.md": TASK})
    if "cross-device continuity is unverified" not in output:
        failures.append("local-only files: expected an explicit unverified sharing warning")
    status, _, pointers = created_pointers()
    if status != 0:
        failures.append(f"pointer creation: expected setup mode to complete, got exit {status}")
    if "HARD-RULES.md" not in pointers["AGENTS.md"]:
        failures.append("AGENTS pointer: expected the universal standard link")
    if "@AGENTS.md" not in pointers["CLAUDE.md"]:
        failures.append("Claude pointer: expected the project rules import")
    if "@AGENTS.md" not in pointers["GEMINI.md"] or "HARD-RULES.md" not in pointers["GEMINI.md"]:
        failures.append("Gemini pointer: expected project rules and universal standard links")
    if "backend-engineering-standard" not in pointers["GEMINI.md"] or "frontend-engineering-standard" not in pointers["GEMINI.md"]:
        failures.append("Gemini pointer: expected conditional backend and frontend standard links")
    if "enforcement/REVIEW.md" not in pointers["GEMINI.md"]:
        failures.append("Gemini pointer: expected the review checklist")
    if "@.skills/backend-engineering-standard/SKILL.md" in pointers["GEMINI.md"] or "@.skills/frontend-engineering-standard/SKILL.md" in pointers["GEMINI.md"]:
        failures.append("Gemini pointer: must not @-expand full SKILL.md manuals inline")
    if "backend-engineering-standard" not in pointers[".github/copilot-instructions.md"] or "frontend-engineering-standard" not in pointers[".github/copilot-instructions.md"]:
        failures.append("Copilot pointer: expected conditional backend and frontend standard links")
    if "AGENTS.md" not in pointers[".github/copilot-instructions.md"] or "HARD-RULES.md" not in pointers[".github/copilot-instructions.md"]:
        failures.append("Copilot pointer: expected project rules and universal hard rules")
    if "enforcement/REVIEW.md" not in pointers[".github/copilot-instructions.md"]:
        failures.append("Copilot pointer: expected the review checklist")
    if "alwaysApply: true" not in pointers[".cursor/rules/standards.mdc"]:
        failures.append("Cursor pointer: expected always-on project rules")
    if "backend-engineering-standard" not in pointers[".cursor/rules/standards.mdc"] or "frontend-engineering-standard" not in pointers[".cursor/rules/standards.mdc"]:
        failures.append("Cursor pointer: expected conditional backend and frontend standard links")
    if "enforcement/REVIEW.md" not in pointers[".cursor/rules/standards.mdc"]:
        failures.append("Cursor pointer: expected the review checklist")
    incomplete_pointers = [
        ("GEMINI.md", "@AGENTS.md\n", "backend-engineering-standard"),
        (".github/copilot-instructions.md", "AGENTS.md\n", "HARD-RULES.md"),
        (".cursor/rules/standards.mdc", "alwaysApply: true\n", "frontend-engineering-standard"),
    ]
    for path, body, expected in incomplete_pointers:
        status, output = run({path: body})
        if status == 0 or path not in output or expected not in output:
            failures.append(f"existing incomplete pointer: {path} should report missing {expected}")
    status, output = configured_setup_check("inert")
    if status == 0 or "pre-commit hook does not run scripts/gates.sh staged" not in output:
        failures.append("inert pre-commit hook: expected setup check failure")
    if "CI does not run scripts/gates.sh ci" not in output:
        failures.append("inert CI workflow: expected setup check failure")
    if "scripts/gates.sh is missing staged or ci modes" not in output:
        failures.append("inert gate runner: expected setup check failure")
    status, output = configured_setup_check("decoy")
    if status == 0 or "scripts/gates.sh staged mode does not run gitleaks git --staged" not in output:
        failures.append("decoy gate commands: expected setup check failure")
    if "pre-commit hook does not run scripts/gates.sh staged" not in output:
        failures.append("decoy hook command: expected setup check failure")
    if "CI does not run scripts/gates.sh ci" not in output or "CI does not run gitleaks git" not in output:
        failures.append("decoy CI commands: expected setup check failure")
    status, output = configured_setup_check("valid")
    if status != 0 or "Setup check passed" not in output:
        failures.append(f"configured gates: expected setup check success, got exit {status}")
    profile_cases = [
        ("Rust UI", {"Cargo.toml": "[dependencies]\nyew = \"1\"\n"}, {"frontend"}, {"rust"}),
        ("Android Gradle UI", {"build.gradle.kts": "plugins { id(\"com.android.application\") }"}, {"frontend"}, {"jvm"}),
        ("JVM Gradle server", {"build.gradle": "plugins { id 'java' }"}, {"backend"}, {"jvm"}),
        (".NET solution", {"Example.sln": ""}, {"backend"}, {"dotnet"}),
        ("plain Dart server", {"pubspec.yaml": "name: example\n"}, {"backend"}, {"dart"}),
        ("Python server", {"pyproject.toml": "[project]\nname = 'example'\n"}, {"backend"}, {"python"}),
        ("unknown JavaScript framework", {"package.json": '{"dependencies":{"unknown-ui":"1"}}'}, set(), {"javascript"}),
    ]
    for marker in sorted(DETECTOR["FRONTEND_JS"]):
        profile_cases.append(
            (f"JavaScript UI {marker}", {"package.json": json.dumps({"dependencies": {marker: "1"}})}, {"frontend"}, {"javascript"})
        )
    for marker in sorted(DETECTOR["BACKEND_JS"]):
        profile_cases.append(
            (f"JavaScript server {marker}", {"package.json": json.dumps({"dependencies": {marker: "1"}})}, {"backend"}, {"javascript"})
        )
    for name, files, expected_roles, expected_ecosystems in profile_cases:
        roles, ecosystems = detect_profile(files)
        if roles != expected_roles or ecosystems != expected_ecosystems:
            failures.append(f"profile detection: {name} expected {expected_roles}/{expected_ecosystems}, got {roles}/{ecosystems}")
    ignored_case = {
        "go.mod": "module example\n",
        ".gitignore": "legacy/\n",
        "legacy/package.json": '{"dependencies":{"next":"1","typescript":"1"}}\n',
    }
    with tempfile.TemporaryDirectory() as root:
        subprocess.run(["git", "init", "-q"], cwd=root, check=True)
        for name, body in ignored_case.items():
            path = Path(root, name)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(body)
        detected = subprocess.run(
            [sys.executable, str(SCRIPT.with_name("detect-project.py")), root],
            capture_output=True,
            text=True,
            check=True,
        )
        parsed = json.loads(detected.stdout)
        if parsed["parts"] != [{"dir": ".", "roles": ["backend"]}] or parsed["ecosystems"] != ["go"]:
            failures.append(f"ignored subfolder detection: expected Go backend only, got {parsed}")
    for failure in failures:
        print(f"FAIL {failure}")
    total = len(cases) + 1 + 24 + len(profile_cases)
    print(f"{total - len(failures)}/{total} passed")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
