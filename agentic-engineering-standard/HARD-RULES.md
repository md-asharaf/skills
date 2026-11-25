# Agent Hard Rules (always loaded)

The full standard is `~/coding/skills/agentic-engineering-standard/SKILL.md`. When a task touches a section cited below, locate it with `grep -n '^##'` and read that slice.

## Before writing
1. First action of a session: read `TASK.md`. A new request made mid-task goes into its Queued Tasks at once (§9).
2. Read the spec section and an existing pattern before coding, and read the code before recommending (§2, §12.2).
3. Project rules (CLAUDE.md, AGENTS.md, layout sections) outrank existing code. Code that breaks them is a defect to fix, never a pattern to copy (§11).
4. Stop and ask on: spec ambiguity, rule conflict, public contract change, destructive schema or data action, new dependency, gates that cannot both pass. State the dilemma, the options and one recommendation (§5.1).

## Verification
5. Never claim a check passed unless you ran it in this session and saw exit 0. Otherwise write "Not run (reason)" (§3).
6. Gates fastest first: lint, typecheck, unit, integration, end-to-end. Targeted specs while iterating; the full suite only for wide changes (§4).
7. Static checks are not proof. Exercise the change at runtime, or state why you could not (§7).
8. The same failure twice: stop repeating it and change the hypothesis. A third time: ask (§4.4).
9. Bugs get a failing regression test first; new behaviour gets a failing test first; tests live under `tests/` (§10).

## Code
10. Zero comments; zero `any`, `@ts-ignore`, `@ts-expect-error`, double casts and `as never`; zero `eslint-disable` and `biome-ignore`; plain names without jargon or migration tags (§13).
11. Touch only the lines the task needs: no drive-by refactors, no repository-wide formatting, no speculative code (§5.2, §5.4).
12. Behaviour and its documentation change in the same commit (§8).

## Git
13. Single-line Conventional Commit messages: no body, no trailers, no AI attribution. Commit with explicit paths after checking `git diff --stat` (§6).
14. Never bypass hooks (`--no-verify`). Never force-push, delete branches, push to `main` where branches are used, or run migrations or SQL against any real database without explicit instruction (§4.3, §5.3).
15. Remove every temporary resource you created (containers, worktrees, scratch files) before finishing (§5.5).

## Tokens
16. Locate with grep, then read 50–150 line slices. Pipe long command output. Never paste files back into chat (§1).
17. Use subagents only for large jobs, and brief them with these rules (§1.5).

## Reporting and decisions
18. Argue before agreeing: say what is right, what is costly, and recommend one option (§12).
19. End finished work with what changed, a gate table (PASSED, FAILED, or NOT RUN with the reason), the runtime check and open risks. Open items follow the Universal Memory Architecture (§9): technical debt and code smells go into `docs/AUDIT_BACKLOG.md`, feature ideas into `docs/BACKLOG.md`, decisions into `docs/DECISIONS.md`, and completed tasks into `docs/archive/COMPLETED_YYYY_MM.md`. `TASK.md` remains strictly <= 30 lines (Goal, Active Task, Queued, Blockers). After a milestone commit, end with exactly one line: "Run `/clear` now", "Run `/compact` now" or "No clear yet: <reason>" (§3.2, §9.3).
