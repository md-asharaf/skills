#!/usr/bin/env bash
set -euo pipefail

SKILLS_SOURCE="${SKILLS_SOURCE:-${HOME}/coding/skills}"
ENFORCEMENT="${SKILLS_SOURCE}/agentic-engineering-standard/enforcement"
SCRIPTS="${SKILLS_SOURCE}/agentic-engineering-standard/scripts"
MODE="setup"
TARGET_DIR="."
FORCED_BACKEND=()
FORCED_FRONTEND=()
while [ $# -gt 0 ]; do
  case "$1" in
    --check) MODE="check" ;;
    --backend) FORCED_BACKEND+=("$2"); shift ;;
    --frontend) FORCED_FRONTEND+=("$2"); shift ;;
    *) TARGET_DIR="$1" ;;
  esac
  shift
done
cd "$TARGET_DIR"

if [ ! -d .git ] && ! git rev-parse --git-dir >/dev/null 2>&1; then
  CHILD_REPOS=()
  for child in */; do
    [ -d "${child}.git" ] && CHILD_REPOS+=("${child%/}")
  done
  if [ ${#CHILD_REPOS[@]} -gt 0 ]; then
    echo "$(pwd) is a folder of ${#CHILD_REPOS[@]} separate repositories: ${CHILD_REPOS[*]}. Setting up each one on its own; nothing is created in this folder."
    echo
    for child in "${CHILD_REPOS[@]}"; do
      args=()
      [ "$MODE" = "check" ] && args+=(--check)
      "$0" "${args[@]}" "$(pwd)/${child}"
      echo
    done
    exit 0
  fi
fi

MONTH=$(date +"%Y_%m")
MONTH_DASH=$(date +"%Y-%m")
TODAY=$(date +"%Y-%m-%d")
CREATED=()
MISSING=()
OWNER=()
LOCAL_ONLY=0

create() {
  local path="$1"
  if [ -e "$path" ]; then return 1; fi
  if [ "$MODE" = "check" ]; then MISSING+=("$path"); return 1; fi
  mkdir -p "$(dirname "$path")"
  cat > "$path"
  CREATED+=("$path")
}

any_file_exists() {
  local path
  for path in "$@"; do
    [ -f "$path" ] && return 0
  done
  return 1
}

file_contains() {
  local text="$1"
  shift
  local path
  for path in "$@"; do
    [ -f "$path" ] && grep -Fq -- "$text" "$path" && return 0
  done
  return 1
}

has_gate_invocation() {
  local mode="$1"
  shift
  local path
  local pattern="^[[:space:]]*(-[[:space:]]+)?(run:|script:|command:|entry:)?[[:space:]]*(exec[[:space:]]+)?(\\./)?scripts/gates\\.sh[[:space:]]+${mode}([[:space:]]|$)"
  local shell_pattern="^[[:space:]]*sh[[:space:]]+['\"](\\./)?scripts/gates\\.sh[[:space:]]+${mode}['\"]"
  for path in "$@"; do
    [ -f "$path" ] || continue
    if grep -Eqs "$pattern" "$path" || grep -Eqs "$shell_pattern" "$path"; then
      return 0
    fi
  done
  return 1
}

has_secret_scan() {
  local path
  for path in "$@"; do
    [ -f "$path" ] || continue
    if grep -Eqs '^[[:space:]]*(-[[:space:]]+)?(run:|script:|command:)?[[:space:]]*(\./)?gitleaks[[:space:]]+git([[:space:]]|$)' "$path"; then
      return 0
    fi
  done
  if has_gate_invocation ci "$@" && [ -x scripts/gates.sh ] && grep -Eq '^[[:space:]]*gitleaks[[:space:]]+git([[:space:]]|$)' scripts/gates.sh; then
    return 0
  fi
  return 1
}

if [ ! -d .git ]; then
  if [ "$MODE" = "check" ]; then MISSING+=("git repository"); else git init -q; CREATED+=("git repository"); fi
fi

if [ ! -e .skills ]; then
  if [ "$MODE" = "check" ]; then MISSING+=(".skills link"); else ln -s "$SKILLS_SOURCE" .skills; CREATED+=(".skills -> $SKILLS_SOURCE"); fi
fi
if ! grep -qxE '\.skills/?' .gitignore 2>/dev/null; then
  if [ "$MODE" = "check" ]; then MISSING+=(".skills in .gitignore"); else printf '\n.skills\n' >> .gitignore; CREATED+=(".skills in .gitignore"); fi
fi

create AGENTS.md <<'EOF' || true
# AGENTS.md

Single entry point for every agent and contributor. Read once per session, then only the slices it points to.

## 1. Sources of truth (highest first)
1. `SPEC.md`: the product and system specification. Wins every conflict.
2. This file and `.skills/` (agentic, backend, frontend, monorepo standards).
3. Existing code: a pattern source only where it follows 1 and 2; code that breaks them is a defect, never a pattern.

Live state is `TASK.md`; read it first in every session.

Every agent (Claude Code, Codex, Cursor, Copilot, Gemini and others) follows `.skills/agentic-engineering-standard/HARD-RULES.md` and, before committing, reviews its diff against `.skills/agentic-engineering-standard/enforcement/REVIEW.md`.

## 2. Project commands
- Format and lint: <fill in>
- Typecheck: <fill in>
- Tests: <fill in>
- Pre-commit gate: <fill in>

## 3. Patterns to copy
| The change needs | Copy this file |
| :--- | :--- |
| <fill in as the project grows> | |

## 4. Stop and ask
Destructive data or schema actions, public contract changes, new dependencies or infrastructure, conflicting rules, gates that cannot both pass.

## 5. Memory
`TASK.md` (hot, at most 30 lines), `docs/BACKLOG.md`, `docs/AUDIT_BACKLOG.md`, `docs/DECISIONS.md`, `docs/designs/`, `docs/reports/`, `docs/archive/COMPLETED_YYYY_MM.md`, in the schemas of the agentic standard §9.2.
EOF

create CLAUDE.md <<'EOF' || true
@AGENTS.md

# Claude Code in this repository

Rules: `AGENTS.md`, `SPEC.md` and the standards in `.skills/`. Enforcement layers: `.skills/agentic-engineering-standard/enforcement/README.md`.
EOF

POINTER="Read and follow AGENTS.md and .skills/agentic-engineering-standard/HARD-RULES.md before any change. Server code also follows .skills/backend-engineering-standard/SKILL.md, UI code .skills/frontend-engineering-standard/SKILL.md (read the matching sections before the first edit). Before committing, review the diff against .skills/agentic-engineering-standard/enforcement/REVIEW.md. Never push; the owner pushes."

create GEMINI.md <<'EOF' || true
@AGENTS.md
@.skills/agentic-engineering-standard/HARD-RULES.md

Read matching sections with `grep -n '^##'` before editing (never inline-expand full manuals with `@`):
- Server code: `.skills/backend-engineering-standard/SKILL.md`
- UI code: `.skills/frontend-engineering-standard/SKILL.md`
- Monorepo layout: `.skills/universal-enterprise-monorepo/SKILL.md`
- Before commit: `.skills/agentic-engineering-standard/enforcement/REVIEW.md`
EOF

create .github/copilot-instructions.md <<EOF || true
${POINTER}
EOF

create .cursor/rules/standards.mdc <<EOF || true
---
description: Owner standards for every change
alwaysApply: true
---
${POINTER}
EOF

require_pointer() {
  local path="$1"
  local text="$2"
  if [ -f "$path" ] && ! grep -Fq -- "$text" "$path"; then
    MISSING+=("${path} is missing required instruction: ${text}")
  fi
}

require_pointer AGENTS.md "SPEC.md"
require_pointer AGENTS.md ".skills/agentic-engineering-standard/HARD-RULES.md"
require_pointer CLAUDE.md "@AGENTS.md"
require_pointer GEMINI.md "@AGENTS.md"
require_pointer GEMINI.md ".skills/agentic-engineering-standard/HARD-RULES.md"
require_pointer GEMINI.md ".skills/backend-engineering-standard/SKILL.md"
require_pointer GEMINI.md ".skills/frontend-engineering-standard/SKILL.md"
require_pointer GEMINI.md ".skills/agentic-engineering-standard/enforcement/REVIEW.md"
require_pointer .github/copilot-instructions.md "AGENTS.md"
require_pointer .github/copilot-instructions.md "HARD-RULES.md"
require_pointer .github/copilot-instructions.md ".skills/backend-engineering-standard/SKILL.md"
require_pointer .github/copilot-instructions.md ".skills/frontend-engineering-standard/SKILL.md"
require_pointer .github/copilot-instructions.md ".skills/agentic-engineering-standard/enforcement/REVIEW.md"
require_pointer .cursor/rules/standards.mdc "alwaysApply: true"
require_pointer .cursor/rules/standards.mdc "AGENTS.md"
require_pointer .cursor/rules/standards.mdc "HARD-RULES.md"
require_pointer .cursor/rules/standards.mdc ".skills/backend-engineering-standard/SKILL.md"
require_pointer .cursor/rules/standards.mdc ".skills/frontend-engineering-standard/SKILL.md"
require_pointer .cursor/rules/standards.mdc ".skills/agentic-engineering-standard/enforcement/REVIEW.md"

create TASK.md <<EOF || true
# Active Task State

**Last Updated:** ${TODAY}

## 1. Goal
<one line, from SPEC.md>

## 2. Active Task
- [ ] <step>

## 3. Queued Tasks
- Full backlog: \`docs/BACKLOG.md\`
- Open items: \`docs/AUDIT_BACKLOG.md\`

## 4. Waiting on User / Blockers
- None.
EOF

if [ ! -f SPEC.md ] && [ ! -f SPECS.md ]; then
  create SPEC.md <<EOF || true
# System Specification

**Version:** 0.1.0 (${TODAY})

## 1. Product overview
- Problem, users, core workflows

## 2. Architecture invariants
- Runtime and language
- Data persistence and transaction rules
- Public API contract and error envelope
EOF
fi

create docs/README.md <<'EOF' || true
# Project knowledge base

`BACKLOG.md` features and roadmap, `AUDIT_BACKLOG.md` open items, `DECISIONS.md` decisions, `designs/` blueprints, `reports/` point-in-time audits, `archive/` completed work by month.
EOF

create docs/BACKLOG.md <<'EOF' || true
# Product Backlog & Roadmap

## 1. Scheduled Phases
| Phase | Target | Scope | Design Doc |
| :--- | :--- | :--- | :--- |

## 2. Queued Features

## 3. Parked Ideas
EOF

create docs/AUDIT_BACKLOG.md <<'EOF' || true
# Audit Backlog

| ID | Type | Date | Source | Where | Summary |
| :--- | :--- | :--- | :--- | :--- | :--- |

## Counts
- FIX: 0 | VERIFY: 0 | DECIDE: 0 | WATCH: 0 | Total: 0
EOF

create docs/DECISIONS.md <<EOF || true
# Architecture Decision Records (ADRs)

## ADR-001: Agent rules and enforcement layers (${TODAY})
- **Context:** Agents skip written rules unless something outside them checks.
- **Decision:** Follow \`.skills\` standards; enforce through managed settings, directory imports, project gates, CI and owner review before push.
- **Rejected:** Rules in documents only.
- **Status:** Approved
EOF

create "docs/archive/COMPLETED_${MONTH}.md" <<EOF || true
# Completed Tasks — ${MONTH_DASH}

## 1. Completed Milestones & Commits

## 2. Closed Audit Items
| ID | Closed | Outcome | Commit | Summary |
| :--- | :--- | :--- | :--- | :--- |
EOF

if [ ! -f scripts/checks/check-rules.py ]; then
  if [ "$MODE" = "check" ]; then MISSING+=("scripts/checks/check-rules.py (language-independent rule check)"); else mkdir -p scripts/checks; cp "${SCRIPTS}/check-rules.py" scripts/checks/check-rules.py; chmod +x scripts/checks/check-rules.py; CREATED+=("scripts/checks/check-rules.py"); fi
elif ! cmp -s "${SCRIPTS}/check-rules.py" scripts/checks/check-rules.py; then
  MISSING+=("scripts/checks/check-rules.py is older than the skills copy: cp ${SCRIPTS}/check-rules.py scripts/checks/ (a gate file: the owner approves)")
fi
if [ -f AGENTS.md ] && ! grep -qs "HARD-RULES.md" AGENTS.md; then
  MISSING+=("AGENTS.md does not point other agents to .skills/agentic-engineering-standard/HARD-RULES.md and enforcement/REVIEW.md")
fi

for dir in docs/designs docs/reports; do
  if [ ! -d "$dir" ]; then
    if [ "$MODE" = "check" ]; then MISSING+=("$dir/"); else mkdir -p "$dir"; touch "$dir/.gitkeep"; CREATED+=("$dir/"); fi
  fi
done

link_into() {
  local file="$1" rel="$2" title="$3" standard="$4"
  local line="Read matching sections of \`${rel}\` (locate with \`grep -n '^##'\`) before the first edit."
  if [ -f "$file" ] && grep -qF "${standard}/SKILL.md" "$file"; then return 0; fi
  if [ "$MODE" = "check" ]; then MISSING+=("${file} pointer to ${standard}"); return 0; fi
  if [ -f "$file" ]; then
    python3 - "$file" "$line" <<'PY'
import sys
path, line = sys.argv[1], sys.argv[2]
lines = open(path).read().splitlines(True)
at = 1 if lines and lines[0].startswith("#") else 0
block = (["\n"] if at else []) + [line + "\n"]
if at >= len(lines) or lines[at].strip():
    block.append("\n")
lines[at:at] = block
open(path, "w").write("".join(lines))
PY
  else
    printf '# %s\n\n%s\n\nBefore the first edit of a task here, write the Primary Source Inspection Log in chat: the standard sections read and the existing file followed.\n' "$title" "$line" > "$file"
  fi
  CREATED+=("${file} pointer to ${standard}")
}

link_standard() {
  local dir="$1" standard="$2" title="$3"
  [ -d "$dir" ] || return 0
  local rel
  rel=$(python3 -c "import os,sys;print(os.path.relpath(sys.argv[1],sys.argv[2]))" "$(pwd)/.skills/${standard}/SKILL.md" "$(pwd)/${dir}")
  link_into "${dir}/CLAUDE.md" "$rel" "$title" "$standard"
  if [ "$dir" != "." ]; then
    link_into "${dir}/AGENTS.md" "$rel" "$title" "$standard"
  fi
}

DETECTED=$(python3 "${SCRIPTS}/detect-project.py" .)
ECOSYSTEMS=$(python3 -c "import json,sys;print(', '.join(json.loads(sys.argv[1])['ecosystems']) or 'none detected')" "$DETECTED")
if [ ${#FORCED_BACKEND[@]} -gt 0 ] || [ ${#FORCED_FRONTEND[@]} -gt 0 ]; then
  BACKEND_DIRS=("${FORCED_BACKEND[@]}")
  FRONTEND_DIRS=("${FORCED_FRONTEND[@]}")
else
  mapfile -t BACKEND_DIRS < <(python3 -c "import json,sys;[print(p['dir']) for p in json.loads(sys.argv[1])['parts'] if 'backend' in p['roles']]" "$DETECTED")
  mapfile -t FRONTEND_DIRS < <(python3 -c "import json,sys;[print(p['dir']) for p in json.loads(sys.argv[1])['parts'] if 'frontend' in p['roles']]" "$DETECTED")
fi
for dir in "${BACKEND_DIRS[@]}"; do
  [ -n "$dir" ] && link_standard "$dir" backend-engineering-standard "Server rules"
done
for dir in "${FRONTEND_DIRS[@]}"; do
  [ -n "$dir" ] && link_standard "$dir" frontend-engineering-standard "UI rules"
done
if python3 -c "import json,sys;sys.exit(0 if json.loads(sys.argv[1])['workspace'] else 1)" "$DETECTED"; then
  link_standard . universal-enterprise-monorepo "Repository rules"
fi
if [ ${#BACKEND_DIRS[@]} -eq 0 ] && [ ${#FRONTEND_DIRS[@]} -eq 0 ]; then
  MISSING+=("unverified application profile: no supported server or UI framework was detected; add and test a profile before setup can pass")
fi
if [ "$ECOSYSTEMS" = "none detected" ]; then
  MISSING+=("unverified stack: no supported language profile was detected; add and test a profile before treating setup as complete")
fi
case "$ECOSYSTEMS" in
  *ruby*|*swift*) MISSING+=("unverified language profile: Ruby and Swift are detected but have no complete gate matrix in ${ENFORCEMENT}/GATES.md");;
esac

CI_FILES=(.github/workflows/*.y*ml .gitlab-ci.yml .gitlab-ci.yaml .circleci/config.yml Jenkinsfile azure-pipelines.yml bitbucket-pipelines.yml)
if any_file_exists "${CI_FILES[@]}"; then :; else
  MISSING+=("CI that runs the gates (templates in ${ENFORCEMENT}/ci: verify.yml for GitHub, gitlab-ci.yml, bitbucket-pipelines.yml, Jenkinsfile)")
fi
if grep -rqs "REPLACE_WITH_TOOLCHAIN\|Replace this step with the setup actions" .github .gitlab-ci.yml bitbucket-pipelines.yml Jenkinsfile 2>/dev/null; then
  MISSING+=("CI still has the template Toolchain step: replace it with the project's language setup")
fi
if [ ! -x scripts/gates.sh ]; then
  MISSING+=("scripts/gates.sh with 'staged' and 'ci' modes, called by both the pre-commit hook and CI (template: ${ENFORCEMENT}/templates/gates.sh)")
elif ! grep -Eq '^[[:space:]]*staged\)' scripts/gates.sh || ! grep -Eq '^[[:space:]]*ci\)' scripts/gates.sh; then
  MISSING+=("scripts/gates.sh is missing staged or ci modes")
elif grep -Eq 'fill_in|REPLACE_WITH_TOOLCHAIN|Replace this step' scripts/gates.sh; then
  MISSING+=("scripts/gates.sh still contains an unfilled gate placeholder")
fi
if [ -x scripts/gates.sh ] && ! grep -Eq '^[[:space:]]*gitleaks[[:space:]]+git([[:space:]]+--pre-commit)?[[:space:]]+--staged([[:space:]]|$)' scripts/gates.sh; then
  MISSING+=("scripts/gates.sh staged mode does not run gitleaks git --staged")
fi
if [ -x scripts/gates.sh ] && ! grep -Eq '^[[:space:]]*python3([[:space:]]+-[A-Za-z]+)*[[:space:]]+scripts/checks/check-rules\.py([[:space:]]|$)' scripts/gates.sh; then
  MISSING+=("scripts/gates.sh does not run scripts/checks/check-rules.py")
fi
HOOK_FILES=(.husky/pre-commit lefthook.yml lefthook.yaml .pre-commit-config.yaml .git/hooks/pre-commit)
if any_file_exists "${HOOK_FILES[@]}"; then
  if ! has_gate_invocation staged "${HOOK_FILES[@]}"; then
    MISSING+=("pre-commit hook does not run scripts/gates.sh staged")
  fi
else
  MISSING+=("pre-commit hook running ./scripts/gates.sh staged (template: ${ENFORCEMENT}/templates/pre-commit)")
fi
if [ -f .husky/commit-msg ] || grep -qs "commit-msg" lefthook.y*ml .pre-commit-config.yaml 2>/dev/null || [ -x .git/hooks/commit-msg ]; then :; else
  MISSING+=("commit-msg hook, single-line Conventional Commit (template: ${ENFORCEMENT}/templates/commit-msg)")
fi
if any_file_exists "${CI_FILES[@]}" && ! has_gate_invocation ci "${CI_FILES[@]}"; then
  MISSING+=("CI does not run scripts/gates.sh ci")
fi
if any_file_exists "${CI_FILES[@]}" && ! has_secret_scan "${CI_FILES[@]}"; then
  MISSING+=("CI does not run gitleaks git")
fi
SPELL_CONFIGS=(cspell.json .cspell.json cspell.config.*)
if ! any_file_exists "${SPELL_CONFIGS[@]}"; then
  MISSING+=("jargon check: cspell with flagWords in the hook and CI (template: ${ENFORCEMENT}/templates/cspell.json; run with --report flagged)")
elif ! file_contains "flagWords" "${SPELL_CONFIGS[@]}"; then
  MISSING+=("cspell configuration is missing flagWords")
fi
has_eslint_rule() {
  local pattern="$1"
  if grep -rqs "$pattern" --include='eslint.config.*' --include='.eslintrc*' --exclude-dir=node_modules --exclude-dir=.skills --exclude-dir=dist . 2>/dev/null; then
    return 0
  fi
  if [ -d packages ] && grep -rqs "$pattern" --include='*.js' --include='*.mjs' --include='*.ts' --exclude-dir=node_modules --exclude-dir=dist packages/*eslint* 2>/dev/null; then
    return 0
  fi
  return 1
}

case ",${ECOSYSTEMS}," in *typescript*)
  has_eslint_rule "no-floating-promises" || MISSING+=("typescript: @typescript-eslint/no-floating-promises (ignoreVoid false) and no-misused-promises");;
esac
case ",${ECOSYSTEMS}," in *python*)
  any_file_exists mypy.ini pyrightconfig.json || grep -qs "tool.mypy\|tool.pyright" pyproject.toml \
    || MISSING+=("python: strict type checking (mypy --strict or pyright strict)");;
esac
case ",${ECOSYSTEMS}," in *go*)
  any_file_exists .golangci.y*ml || MISSING+=("go: golangci-lint with errcheck, depguard, forbidigo, noctx");;
esac
case ",${ECOSYSTEMS}," in *javascript*)
  has_eslint_rule "catch-or-return\|no-floating-promises" || MISSING+=("javascript: eslint-plugin-promise catch-or-return and no-console (or move to TypeScript for no-floating-promises)");;
esac
case ",${ECOSYSTEMS}," in *rust*)
  grep -rqs "unused_must_use\|clippy" Cargo.toml clippy.toml .cargo/config.toml src/lib.rs src/main.rs 2>/dev/null \
    || MISSING+=("rust: clippy with -D warnings, #![deny(unused_must_use)], #![forbid(unsafe_code)]");;
esac
case ",${ECOSYSTEMS}," in *jvm*)
  grep -rqs "errorprone\|detekt\|archunit" --include='*.gradle*' --include='pom.xml' . 2>/dev/null \
    || MISSING+=("jvm: Error Prone or detekt with warnings as errors, ArchUnit for layers");;
esac
case ",${ECOSYSTEMS}," in *dotnet*)
  grep -rqs "TreatWarningsAsErrors" --include='*.csproj' --include='Directory.Build.props' . 2>/dev/null \
    || MISSING+=("dotnet: <TreatWarningsAsErrors>, <Nullable>enable</Nullable>, CS4014 as error, NetArchTest");;
esac
case ",${ECOSYSTEMS}," in *php*)
  any_file_exists phpstan.neon* psalm.xml || MISSING+=("php: PHPStan or Psalm at max level, deptrac for layers");;
esac
case ",${ECOSYSTEMS}," in *ruby*)
  any_file_exists .rubocop.yml || MISSING+=("ruby: rubocop with no disabled cops, strong_migrations, bullet for N+1");;
esac
case ",${ECOSYSTEMS}," in *dart*)
  grep -qs "strict-casts" analysis_options.yaml || MISSING+=("dart: analysis_options.yaml with strict-casts, strict-inference, unawaited_futures, avoid_print");;
esac
case ",${ECOSYSTEMS}," in *swift*)
  any_file_exists .swiftlint.yml || MISSING+=("swift: SwiftLint with warnings as errors");;
esac
if [ -f AGENTS.md ]; then
  if ! RULE_OUTPUT=$(python3 "${SCRIPTS}/check-rules.py" --skip-code . 2>&1); then
    printf '%s\n' "$RULE_OUTPUT"
    MISSING+=("project rules or memory checks failed (see check-rules.py output above)")
  fi
fi
for path in AGENTS.md TASK.md SPEC.md docs/AUDIT_BACKLOG.md; do
  if [ -e "$path" ] && git check-ignore -q "$path"; then
    LOCAL_ONLY=1
  fi
done
if [ "$LOCAL_ONLY" -eq 1 ]; then
  OWNER+=("Key guidance or memory files are ignored by Git; cross-device continuity is unverified until approved files are tracked")
fi

if ! cmp -s "${ENFORCEMENT}/managed-settings.json" /etc/claude-code/managed-settings.json 2>/dev/null \
  || ! cmp -s "${ENFORCEMENT}/hooks/guard.py" /etc/claude-code/hooks/guard.py 2>/dev/null \
  || ! cmp -s "${ENFORCEMENT}/hooks/session-check.py" /etc/claude-code/hooks/session-check.py 2>/dev/null \
  || ! cmp -s "${ENFORCEMENT}/hooks/inspection-log.py" /etc/claude-code/hooks/inspection-log.py 2>/dev/null; then
  OWNER+=("Install or update the managed layer (machine-wide): sudo install -d -m 755 /etc/claude-code/hooks && sudo install -m 755 ${ENFORCEMENT}/hooks/guard.py ${ENFORCEMENT}/hooks/session-check.py ${ENFORCEMENT}/hooks/inspection-log.py /etc/claude-code/hooks/ && sudo install -m 644 ${ENFORCEMENT}/managed-settings.json /etc/claude-code/managed-settings.json")
fi
if [ ! -e "$HOME/.claude/agents/standards-reviewer.md" ]; then
  OWNER+=("Link the reviewer agent: run ${SCRIPTS}/install-machine.sh")
fi
if git remote get-url origin >/dev/null 2>&1 || [ -n "$(git remote 2>/dev/null)" ]; then
  OWNER+=("On the remote: protect the default branch, require the CI check, require your review for .github/ changes")
fi
OWNER+=("Push yourself after reading the diff: ! git push")

echo "Project setup report ($(pwd), mode: ${MODE})"
echo "Detected: ${ECOSYSTEMS}; server parts: ${BACKEND_DIRS[*]:-none}; UI parts: ${FRONTEND_DIRS[*]:-none}"
echo
echo "Created (${#CREATED[@]}):"
for item in "${CREATED[@]}"; do echo "  + ${item}"; done
echo
echo "Still missing (${#MISSING[@]}):"
for item in "${MISSING[@]}"; do echo "  - ${item}"; done
echo
echo "Owner actions (${#OWNER[@]}):"
for item in "${OWNER[@]}"; do echo "  ! ${item}"; done
if [ "$MODE" = "check" ]; then
  if [ ${#MISSING[@]} -eq 0 ]; then
    if [ "$LOCAL_ONLY" -eq 1 ]; then
      echo "Setup check passed locally; cross-device continuity unverified"
    else
      echo "Setup check passed"
    fi
  else
    echo "Setup check failed"
    exit 1
  fi
fi
