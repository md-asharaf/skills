#!/usr/bin/env bash
set -euo pipefail

TARGET_DIR="${1:-.}"
cd "$TARGET_DIR"

CURRENT_MONTH=$(date +"%Y_%m")
CURRENT_DATE=$(date +"%Y-%m-%d")

echo "Initializing Universal Documentation and Memory System in: $(pwd)"

# 1. Create directory structure
mkdir -p docs/designs docs/reports docs/archive
touch docs/designs/.gitkeep docs/reports/.gitkeep

# 2. Seed TASK.md (Hot State <= 30 lines)
if [ ! -f "TASK.md" ]; then
cat <<EOF > TASK.md
# Active Task State
**Last Updated:** ${CURRENT_DATE}

## 1. Goal
Initialize project foundation and core architecture.

## 2. Active Task
- [ ] Setup initial project repository and dependencies
- [ ] Configure linting, formatting, and quality verification gates

## 3. Queued Tasks
- Core domain model implementation
- Full Backlog: docs/BACKLOG.md | Tech Debt: docs/AUDIT_BACKLOG.md

## 4. Waiting on User / Blockers
- None currently. Decisions archived in docs/DECISIONS.md.
EOF
echo "Created TASK.md"
fi

# 3. Seed SPEC.md
if [ ! -f "SPEC.md" ] && [ ! -f "SPECS.md" ]; then
cat <<EOF > SPEC.md
# System Specification & Architecture Contract

**Status:** Target Specification  
**Version:** 1.0.0 (${CURRENT_DATE})

## 1. Product Overview & Core Objectives
- Primary problem being solved
- Target users and core workflows

## 2. Architecture & Tech Stack Invariants
- Runtime environment & programming language
- Data persistence & transactional integrity rules
- Public API contract & error envelope conventions
EOF
echo "Created SPEC.md"
fi

# 4. Seed docs/BACKLOG.md
if [ ! -f "docs/BACKLOG.md" ]; then
cat <<EOF > docs/BACKLOG.md
# Product Feature Backlog & Roadmap

## 1. Future Roadmap & Milestones
- [ ] Milestone 1: Core System Foundation
- [ ] Milestone 2: Feature Implementation
- [ ] Milestone 3: Production Readiness & Quality Gates

## 2. Unscheduled Ideas (Inbox)
- Candidate features and user suggestions recorded mid-flight
EOF
echo "Created docs/BACKLOG.md"
fi

# 5. Seed docs/AUDIT_BACKLOG.md
if [ ! -f "docs/AUDIT_BACKLOG.md" ]; then
cat <<EOF > docs/AUDIT_BACKLOG.md
# Audit & Technical Debt Backlog

Open audit findings, code smells, and performance debt tracked for phased remediation.

| ID | Date | Component | Severity | Description |
| :--- | :--- | :--- | :--- | :--- |
| AUD-01 | ${CURRENT_DATE} | System | Low | Initial system baseline audit pending |
EOF
echo "Created docs/AUDIT_BACKLOG.md"
fi

# 6. Seed docs/DECISIONS.md
if [ ! -f "docs/DECISIONS.md" ]; then
cat <<EOF > docs/DECISIONS.md
# Architectural Decision Records (ADR) Log

Living record of architectural choices, trade-offs, and rationale.

## ${CURRENT_DATE} — Initial Architecture Bootstrap
- **Context:** Project initialization.
- **Decision:** Adopted Universal Documentation & Memory Operating System.
- **Reason:** Enforces hot-cold memory separation, prevents context bloat, and provides deterministic HITL coordination.
- **Rejected Alternatives:** Unstructured single-file documentation, chat-only memory.
EOF
echo "Created docs/DECISIONS.md"
fi

# 7. Seed docs/archive/COMPLETED_YYYY_MM.md
ARCHIVE_FILE="docs/archive/COMPLETED_${CURRENT_MONTH}.md"
if [ ! -f "$ARCHIVE_FILE" ]; then
cat <<EOF > "$ARCHIVE_FILE"
# Completed Tasks Archive — ${CURRENT_MONTH}

Monthly historical archive of completed milestones, closed remediation items, and git commit hashes.

| Commit | Date | Milestone / Task | Verification Status |
| :--- | :--- | :--- | :--- |
| initial | ${CURRENT_DATE} | Repository bootstrap and memory system setup | Verified |
EOF
echo "Created $ARCHIVE_FILE"
fi

echo "Universal Documentation and Memory System successfully initialized!"
