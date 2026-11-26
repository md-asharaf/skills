# Review checklist: the rules no machine checks yet

Used by the `standards-reviewer` agent before every commit, by any other agent asked to review, and by the owner before every push. Gates (lint, typecheck, custom checks, tests) already hold the mechanical rules; a review never repeats them, it reads the diff for these. Every finding names `file:line`, the rule, and the gate that would catch it next time (`GATES.md`). A rule found broken twice moves from this list to a gate.

## How to review

1. `git diff --cached --stat` (or the range you were given), then read each changed hunk with enough surrounding code to judge it.
2. Read the project's `AGENTS.md` laws marked `Enforced by: review` and the directory `CLAUDE.md` of each changed part; they add to this list.
3. For every new query, side effect, component or file, find the existing pattern the project names (the "Patterns to copy" table) and compare.
4. Report findings most severe first. No finding without a line; no style opinions outside these rules.

## Every change

- [ ] **Inspection log:** the conversation or PR shows the sections read and the pattern file followed, before the first edit.
- [ ] **Existing pattern:** new code copies the pattern the project names; code that breaks a rule was not copied as a pattern.
- [ ] **Scope:** only the lines the task needs; no drive-by refactors, formatting sweeps or speculative options.
- [ ] **Tests first:** a bug fix has a regression test; new behaviour has a test of that behaviour; tests live under `tests/`.
- [ ] **Docs in the same commit:** the spec section, `AGENTS.md`, README or API docs change with the behaviour they describe.
- [ ] **Plain names:** a new teammate understands every name and text without the project's history.
- [ ] **Honest report:** every gate claimed as passed was run in this session.

## Server code (backend standard)

- [ ] **Side effects only in jobs:** email, SMS, chat, webhooks, payment and provider calls run inside a job handler, enqueued in the same transaction as the change; never fire-and-forget, never inside a transaction, never from a controller or plain service (§6.5).
- [ ] **Each table read once per request:** no second read of a row already loaded; no query inside a loop; batch work in a constant number of statements (§6.12).
- [ ] **One statement under a lock:** checks under a lock are one statement; rows locked in id order; constraints reject conflicts instead of read-then-write (§6.6).
- [ ] **Transactions:** opened through the repository unit of work; no network call inside (§6.3).
- [ ] **Outbound calls:** timeouts, retries only when idempotent, errors mapped to typed errors (§5.8).
- [ ] **Error contract:** typed errors with catalogue codes; one code, one status; no internal message reaches the client (§4).
- [ ] **Tenant isolation:** every new tenant query path has a test proving another tenant can neither read nor change it (§9.1).
- [ ] **Migrations:** journaled, forward-only, no silent data loss, destructive steps approved and planned (§6.1, §6.10).
- [ ] **Logs:** no tokens, passwords, session ids or personal data (§1.1).

## UI code (frontend standard)

- [ ] **Shared components and tokens:** no hand-rolled table, alert, dialog, button or card that the project already has; no literal colours or sizes (§1–2, §4).
- [ ] **Five view states:** loading, empty, error, pending and success are each handled and visible (§3).
- [ ] **Prop contracts:** icons through `icon`, loading through `isLoading`, labels on icon-only actions, link primitives for navigation.
- [ ] **UX golden rules:** settings live with their item, one primary action, errors say what to do next, no internal names in text people read (§5, §6).
- [ ] **Screens checked:** screenshots at phone and desktop width, light and dark, for each changed screen (§8).

## Output

```
<severity> <file>:<line> <rule> — <what is wrong> — fix: <one line> — gate: <GATES.md row or "none yet">
```

Severity is `blocker` (breaks a rule above), `risk` (likely breaks one, needs a look) or `nit`. End with `Blockers: N`. With none, end with `Clean against REVIEW.md and AGENTS.md review laws` and list the rules you could not judge from the diff.
