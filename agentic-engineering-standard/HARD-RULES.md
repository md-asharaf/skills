# Agent Hard Rules (always loaded)

The full standard is `~/coding/skills/agentic-engineering-standard/SKILL.md`; server code also follows `~/coding/skills/backend-engineering-standard/SKILL.md` and UI code `~/coding/skills/frontend-engineering-standard/SKILL.md`. When a task touches a section cited below, locate it with `grep -n '^##'` and read that slice. How these rules are enforced: `enforcement/README.md`.

## Before writing
1. First action of a session: read `TASK.md`. A new request made mid-task goes into its Queued Tasks at once (§9).
2. Read the spec section and an existing pattern before coding, and read the code before recommending. Write the Primary Source Inspection Log (sections read, pattern files followed) in chat before the first code edit, not only in the final report (§2, §12.2).
3. Project rules (CLAUDE.md, AGENTS.md, layout sections) outrank existing code. Code that breaks them is a defect to fix, never a pattern to copy (§11).
4. Stop and ask on: spec ambiguity, rule conflict, public contract change, destructive schema or data action, new dependency, gates that cannot both pass. State the dilemma, the options and one recommendation (§5.1).

## Verification
5. Never claim a check passed unless you ran it in this session and saw exit 0. Otherwise write "Not run (reason)" (§3).
6. Gates fastest first: lint, typecheck, unit, integration, end-to-end. Targeted specs while iterating; the full suite only for wide changes (§4).
7. Static checks are not proof. Exercise the change at runtime, or state why you could not (§7).
8. The same failure twice: stop repeating it and change the hypothesis. A third time: ask (§4.4).
9. Bugs get a failing regression test first; new behaviour gets a failing test first; tests live under `tests/` (§10).

## Code
10. Zero comments; zero type bypasses (`any` or its language's equivalent, ignore directives, double casts; `as never` only in tests, to stub a third-party SDK); zero suppression directives in any language (`eslint-disable`, `biome-ignore`, `noqa`, `type: ignore`, `nolint`, `@SuppressWarnings`, `#[allow]`); plain names without jargon or migration tags (§13).
11. Touch only the lines the task needs: no drive-by refactors, no repository-wide formatting, no speculative code (§5.2, §5.4).
12. Behaviour and its documentation change in the same commit (§8).

## Backend and data (any server code)
13. Before server code, read the matching backend standard sections: file roles §2.3, transactions §6.3, jobs and outbox §6.5, concurrency §6.6, queries §6.12, outbound calls §5.8.
14. External side effects (email, SMS, webhooks, provider calls) go only through the project's job or outbox mechanism, enqueued with the change. Never fire-and-forget, never inside a database transaction.
15. Database work is set-based: read each table once per request, batch work in a constant number of statements, checks under one lock in one statement, row locks in id order, constraints instead of read-then-write checks.

## Frontend (any UI code)
16. Before UI code, read the matching frontend standard sections; reuse the shared components and design tokens; cover loading, empty, error, pending and success; check changed screens at phone and desktop width in light and dark.

## Enforcement
17. Never edit, weaken or bypass gates, hooks, lint rules, CI workflows, allowlists or permission settings unless the user asked for that exact change; show the diff first.
18. Never push and never apply migrations: the user pushes after reviewing the diff.
19. When you miss a rule, say so plainly and propose the lint rule, check or test that would have caught it, in the same report.
20. Before each commit of server or UI code, run the reviewer agent on the staged diff (the project's own in `.claude/agents/` when it defines one, else `standards-reviewer`) (or review it against `enforcement/REVIEW.md`) and fix every blocker first.

## Git
21. Single-line Conventional Commit messages: no body, no trailers, no AI attribution. Commit with explicit paths after checking `git diff --stat` (§6).
22. Never bypass hooks (`--no-verify`). Never force-push, delete branches, push to `main` where branches are used, or run migrations or SQL against any real database without explicit instruction (§4.3, §5.3).
23. Remove every temporary resource you created (containers, worktrees, scratch files) before finishing (§5.5).

## Tokens
24. Locate with grep, then read 50–150 line slices. Pipe long command output. Never paste files back into chat (§1).
25. Use subagents only for large jobs, and brief them with these rules (§1.5).

## Reporting and decisions
26. Argue before agreeing: say what is right, what is costly, and recommend one option (§12).
27. End finished work with what changed, a gate table (PASSED, FAILED, or NOT RUN with the reason), the runtime check and open risks. Open items follow the Universal Memory Architecture (§9): technical debt and code smells go into `docs/AUDIT_BACKLOG.md`, feature ideas into `docs/BACKLOG.md`, decisions into `docs/DECISIONS.md`, and completed tasks into `docs/archive/COMPLETED_YYYY_MM.md`. `TASK.md` remains strictly <= 40 lines (aim for 30) (Goal, Active Task, Queued, Blockers). After a milestone commit, end with exactly one line: "Run `/clear` now", "Run `/compact` now" or "No clear yet: <reason>" (§3.2, §9.3).
