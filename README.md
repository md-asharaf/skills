# Universal Engineering Standards & Agent Skills

This directory contains the universal, framework-agnostic engineering standards and autonomous agent skills governing codebase architecture, quality, and craftsmanship.

---

## Directory Index

| Skill / Standard | Primary Domain & Coverage | Specification Link |
| :--- | :--- | :--- |
| **`backend-engineering-standard`** | Hexagonal (Ports & Adapters) architecture, layered separation, typed domain exceptions (13 subclasses), error contracts, Units of Work, PostgreSQL concurrency & advisory locks, caching pipelines, and SSRF egress security. | [`backend-engineering-standard/SKILL.md`](./backend-engineering-standard/SKILL.md) |
| **`frontend-engineering-standard`** | UI/UX craftsmanship, zero inline HTML primitives, custom primitive taxonomy, 5 mandatory view lifecycle states, design token exclusivity, responsive design down to 320px, and WCAG 2.2 AA accessibility. | [`frontend-engineering-standard/SKILL.md`](./frontend-engineering-standard/SKILL.md) |
| **`universal-enterprise-monorepo`** | Multi-package workspace topology (`apps/*` vs `packages/*`), dependency DAG invariants, workspace protocol (`workspace:*`), Turborepo/Nx pipeline orchestration, shared configurations, and Docker pruning. | [`universal-enterprise-monorepo/SKILL.md`](./universal-enterprise-monorepo/SKILL.md) |
| **`agentic-engineering-standard`** | How an AI agent works in any project: token and context hygiene, honest verification, targeted gates, stop-and-ask, git and commits, `TASK.md` state machine, test-driven process, decision standard, plus the code invariants shared by every language (zero comments, type safety, zero suppressions, plain naming). Suitable to import into a `CLAUDE.md`. | [`agentic-engineering-standard/SKILL.md`](./agentic-engineering-standard/SKILL.md) |
| **`project-setup`** | One command (`/project-setup`) that brings any new or existing repository to these standards: memory files in the mandatory schemas, directory imports of the backend and frontend standards, gate and CI gaps, and the owner actions. | [`project-setup/SKILL.md`](./project-setup/SKILL.md) |

---

## Enforcement

Rules only hold when something outside the agent checks them. [`agentic-engineering-standard/enforcement/README.md`](./agentic-engineering-standard/enforcement/README.md) sets up the five layers for every machine and project: root-owned managed settings with a guard hook, directory `CLAUDE.md` imports of the standards, project gates, CI, and owner review before push.

## Usage Guidelines

- **For AI Agents:** These files follow the standard `SKILL.md` format (YAML frontmatter + markdown body) and can be loaded directly as agent skills or inspected as architectural specifications.
- **For Human Contributors:** These standards serve as the universal engineering constitution for fullstack architecture, design system implementation, and code review criteria.
