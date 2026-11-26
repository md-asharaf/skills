# Gate catalogue: how every rule is enforced, in any language

Each rule of the four standards is held by at least one layer (see `README.md`). Prefer the highest layer that can hold it: a **gate** (lint, typecheck, custom check or test, run by the pre-commit hook and CI) beats **review**. **Context** means the rule must be in the agent's context (directory `CLAUDE.md` import or `HARD-RULES.md`). Every rule in a project's `AGENTS.md` carries an `Enforced by:` line naming its gate, or `review` when none exists yet.

`/project-setup` picks the tools for the ecosystems it detects. `scripts/check-rules.py` (copied into each project as `scripts/checks/check-rules.py`, so CI needs no `.skills` link) already holds the language-independent custom checks: comments and suppressions in every language listed below (aware of strings, regex literals and heredocs), TypeScript type bypasses, the `TASK.md` limit and sections, and the `docs/` schemas; exceptions go in `scripts/checks/rules-allow.txt` as `<glob> [rule]` lines, a gate file. Projects with their own gate for code rules run it with `--skip-code`. When a cell says "custom check" and `check-rules.py` does not cover it, write a small script in the project's check folder (an AST or tokenizer walk, never a plain grep where code structure matters) and run it in the hook and CI.

## One gate entry point per project

Every project exposes `scripts/gates.sh` (template: `templates/gates.sh`, with `templates/pre-commit` and `templates/commit-msg` for the hooks, `templates/cspell.json` for jargon) with two modes: `staged` (fast gates on staged files, run by the pre-commit hook) and `ci` (every gate, run by CI). Both the hook and CI call it, so they can never drift apart. Setup checks verify that both commands are wired, that the runner defines both modes without template placeholders, and that CI and the staged gate run the secret scan. They also verify that the cspell configuration defines `flagWords` and that each agent entrypoint contains the required instruction links. It is a gate file: the guard asks the owner before any change. In a project that already has a gate runner (`verify-all.mjs`, `make check`, `nox`, `mage`), `gates.sh` only calls it.

CI toolchains for the `Toolchain` step of `ci/verify.yml`: `actions/setup-node` with `pnpm/action-setup` (TS/JS), `actions/setup-python` with `astral-sh/setup-uv` (Python), `actions/setup-go` (Go), `actions/setup-java` (JVM), `dtolnay/rust-toolchain` (Rust), `shivammathur/setup-php` (PHP), `actions/setup-dotnet` (C#), `subosito/flutter-action` (Dart/Flutter), `ruby/setup-ruby` (Ruby). Pin GitHub Actions to full commit SHAs and verify downloaded tools against a fixed checksum before extracting them. Services the tests need (PostgreSQL, Redis) go under `services:`. Templates for the other systems: `ci/gitlab-ci.yml`, `ci/bitbucket-pipelines.yml`, `ci/Jenkinsfile`. Every template fails until its `REPLACE_WITH_TOOLCHAIN` marker is replaced, and `setup-project.sh` reports any marker left.

## Profile coverage contract

The language and framework rows below are maintained profiles, not an exhaustive list of every technology. Each supported profile must state how it is detected, which standards apply, how agent instructions are loaded, which local and CI gates run, and how its tests and runtime behavior are verified. Agent instruction entrypoints must be tested for each supported agent.

The agentic standard applies to every project. Backend, frontend, and monorepo standards apply only when the project contains that kind of work. Technology-specific rules apply only when the project uses that technology. A project with an unknown language, framework, or agent is unverified until a profile is added and tested; setup checks must not report it as ready. Add a profile with its detection and failure-case tests before claiming support.

## Adding any new rule (any project, any feature)

1. Write the rule once, in the standard or the project's `AGENTS.md`, with an `Enforced by:` line.
2. If a machine can detect a break, add the gate in the same change: a lint rule, a custom check, or a test. Measure how many existing violations it reports and fix them or record them in `docs/AUDIT_BACKLOG.md` before turning it on.
2b. When the check finds existing violations that cannot all be fixed now, use a named allowlist (each entry with its reason or open item, and stale entries failing) or a per-file count baseline that may only go down; never a blanket file or folder exclusion.
3. If no machine can detect it, mark it `review` and add it to `REVIEW.md`, the checklist the `standards-reviewer` agent and the owner use.
4. A rule missed twice moves from `review` to a gate.

## Code invariants (agentic standard §13)

| Rule | TS / JS | Python | Go | Java / Kotlin | Rust | PHP | C# | Dart / Flutter |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| Zero comments §13.1 | `check-rules.py` | same | same | same | same | same | same | same |
| No `any` / type bypasses §13.2 | `strict` tsconfig, `@typescript-eslint/no-explicit-any`, `no-unsafe-*`, ban double casts (custom) | `mypy --strict` or `pyright` strict, ruff `ANN401` | `forbidigo` on `interface{}`/`any` in domain code | Kotlin `allWarningsAsErrors`; Error Prone | `#![forbid(unsafe_code)]`, clippy `pedantic` | PHPStan or Psalm max level | `<Nullable>enable</Nullable>`, `TreatWarningsAsErrors` | `strict-casts`, `strict-inference`, `strict-raw-types`, `avoid_dynamic_calls` |
| No suppressions §13.3 | custom check: `eslint-disable`, `@ts-ignore`, `@ts-expect-error`, `biome-ignore` | custom check: `noqa`, `type: ignore`, `pragma: no cover` | custom check: `//nolint` | custom check: `@SuppressWarnings` | custom check: `#[allow(` | custom check: `@phpstan-ignore`, `@psalm-suppress` | custom check: `#pragma warning disable`, `[SuppressMessage]` | custom check: `// ignore:`, `ignore_for_file` |
| Plain names, no jargon §13.4 | `cspell` with a `flagWords` list (any language) | same | same | same | same | same | same | same |
| No debug output | `no-console` | ruff `T20` | `forbidigo` on `fmt.Print*` | Error Prone, Checkstyle `System.out` | clippy `print_stdout` | PHPStan `disallowed-calls` | analyzer rule on `Console.Write` | `avoid_print` |
| Tests only under `tests/` | custom check (path rule) | same | Go keeps `_test.go` beside code: adapt the rule per language | Maven/Gradle `src/test` | `tests/` plus unit `mod tests` | `tests/` | test project | `test/` |

## Backend standard

| Rule | Gate (any language unless named) |
| :--- | :--- |
| Layer direction, no cycles, file roles §2.1–2.3, §3 | TS `dependency-cruiser` or `eslint-plugin-boundaries`, `dpdm`; Python `import-linter`; Go `depguard`, `go-arch-lint`; Java `ArchUnit`; PHP `deptrac`; C# `NetArchTest`; Rust crate boundaries in the workspace |
| External side effects only in jobs or adapters §6.5 | the same architecture tool as a forbidden-import or forbidden-call rule: sender, gateway and HTTP-client types allowed only in job handlers and adapter folders, with a reviewed allowlist |
| No fire-and-forget | TS `@typescript-eslint/no-floating-promises` (`ignoreVoid: false`), `no-misused-promises`; Python ruff `RUF006`, `flake8-async`; Go `errcheck`; Rust `#![deny(unused_must_use)]`; Java Error Prone `FutureReturnValueIgnored`; C# `CS4014` as error; Dart `unawaited_futures`, `discarded_futures` |
| No network call inside a transaction §6.3 | custom check (AST: no sender or gateway call inside a transaction callback); otherwise review |
| Set-based queries, no N+1 §6.12 | query-count tests per route or use case (strongest, language-agnostic); an await-in-loop check scoped to services and repositories with a per-file baseline that only goes down (TS `no-await-in-loop` or an AST check; Python `flake8-async`); Django `assertNumQueries`, `nplusone`; Rails `bullet`; Laravel `preventLazyLoading` |
| Lock order, constraints over read-then-write §6.6, §6.12 | concurrency integration tests; review |
| Outbound timeouts §5.8 | custom check (every HTTP client built with a timeout); Go `noctx`, `bodyclose` |
| Migrations journaled, forward-only, non-destructive §6.1, §6.10 | the migration tool's drift check (`drizzle-kit check`, `prisma migrate diff`, `alembic check`, `manage.py makemigrations --check`, `sqlx migrate info`); `squawk` for destructive Postgres DDL; `strong_migrations` (Rails); `django-migration-linter` |
| Typed errors, one code per status §4 | custom check (no generic throws); a test comparing documented and thrown codes |
| Customer data isolation §9.1 | integration tests proving one customer cannot read or change another's data, for every such query path |
| Secrets §2.8 | `gitleaks` in the hook and CI; `.env.example` lockstep check (custom) |
| Dependencies | `osv-scanner` (any language), or `npm audit`, `pip-audit`, `govulncheck`, `cargo audit` |
| Runtime boot §10.4 | boot smoke test in CI |
| Logging without personal data §1.1 | redaction tests; review |

## Frontend standard

| Rule | Gate |
| :--- | :--- |
| Shared UI primitives and semantic HTML §1–2 | review for design-system reuse; framework accessibility lint (§7) |
| Five view states §3, §9.1 | component tests for each state (Storybook stories with interaction tests, Testing Library, Flutter widget tests) |
| Design tokens only §4 | `stylelint` `declaration-strict-value`, `color-no-hex`; Tailwind `no-arbitrary-value`; Flutter custom check on literal colours and sizes |
| Accessibility §7 | `eslint-plugin-jsx-a11y` or `vuejs-accessibility`; `axe-core` in browser tests; Flutter `meetsGuideline` tests |
| 320 px, no sideways scroll §5.11 | browser test at 320 px asserting no horizontal overflow |
| Screenshot proof §8 | visual tests (Playwright, Flutter golden tests) for changed screens, light and dark, phone and desktop |
| UX golden rules §5, plain language §6 | review; `cspell` `flagWords` for jargon in UI text |

## Monorepo standard

| Rule | Gate |
| :--- | :--- |
| Apps depend on packages, package DAG §2 | `@nx/enforce-module-boundaries`, `dependency-cruiser`, `turbo` boundaries; Cargo or Go workspace layout |
| Single lockfile, workspace protocol, no phantom deps §3 | lockfile check in CI (`--frozen-lockfile`), `knip` or `depcheck`, `syncpack` for one version per dependency |
| Pipelines and caches §4, §6 | CI runs the orchestrator graph; cache keys reviewed |

## Agentic process rules

| Rule | Gate |
| :--- | :--- |
| Hooks never bypassed, no push, no migrations | managed settings and the guard hook |
| Gate files changed only with the owner | the guard asks; CI changes need owner review on the remote |
| Single-line commit messages | `commit-msg` hook (`commitlint` or a custom check) |
| `TASK.md` at most 40 lines, `AGENTS.md` <= 12 KB (<= 32 KiB chain, `GEMINI.md` <= 24 KB, `CLAUDE.md` <= 40 KB, no `@` inline expansion of full `SKILL.md` manuals), docs schemas §9.2 | `check-rules.py` in the hook and CI |
| Inspection log before the first edit | `hooks/inspection-log.py` refuses the first code edit of a session (and after each compaction) until the log is in chat; review |
| Judgement rules (patterns, reads per table, side effects, view states) | the `standards-reviewer` agent with `REVIEW.md` before each commit; owner review before push |
| Other agents (Codex, Cursor, Copilot, Gemini) get the rules | `AGENTS.md`, `GEMINI.md`, `.github/copilot-instructions.md`, `.cursor/rules/standards.mdc` created by `setup-project.sh`; the gates and CI hold them like any agent |
| Machine and project drift | `hooks/session-check.py` reports a stale managed layer, unpushed skills commits, an old `check-rules.py` copy and an overlong `TASK.md` at session start |
| Honest reporting | review; CI is the record of what passed |
