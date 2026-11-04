---
name: goal-feed
description: |
  Use when the user wants to feed Codex a goal that should become a high-quality paid-service-grade implementation workflow: coordinate with Claude Code via agmsg, refine a final plan, write a plan file, run ticket-gen and ticket-review, then execute all ticket phases through /goal, /ko, /cr, /next, ticket-verify, and the Claude Code final review. Trigger on "goal-feed", "goal feed", "agmsgでccと合議", "ticket作成からgoal実装", "有料サービス品質で実装", or requests to turn a report into reviewed tickets and repeated goal-driven implementation.
---

# goal-feed — Codex `/goal` × Claude Code 協調スキル

## Purpose

Turn a report, idea, audit, or improvement request into a paid-service-grade implementation flow. Codex owns the final plan, ticket generation request, `/goal` loop, and implementation. Claude Code provides independent planning/review through `agmsg`.

Prioritize quality a user would pay for. Prefer root-cause fixes and durable design over temporary patches.

## Required Inputs

- Source request, report path, audit output, product goal, or improvement brief.
- Target repository/current working directory.
- Working `agmsg` team if Claude Code collaboration is required. Use only scripts under `~/.agents/skills/agmsg/scripts/`; do not read or edit agmsg DB/config files directly.

## Orca Runtime

This skill runs inside an Orca worktree that Claude Code created. Read `~/.claude/skills/goal-feed/references/orca-protocol.md` first; it is the source of truth for worktrees, agmsg names, waking the peer, and cleanup.

- The launch brief gives the team, your agmsg name, the Claude Code name, and `cc_handle`. Use them as given. Both names are already registered, so do not run `join.sh` or `whoami.sh`.
- Never create a worktree or branch (`git worktree add`, `orca worktree create`, `git checkout -b`). The current directory is the task worktree. If the brief is missing or this is the primary worktree, stop and tell the user that Claude Code must start the run.
- After every `send.sh`, wake Claude Code with `orca terminal send --terminal <cc_handle> --text '<inbox command>' --enter --json` (section 6 of the protocol).
- Claude Code owns the worktree cleanup decision and `/shime`. Do not remove worktrees.

## Session State

Track these values during the run:

- `activated: true`
- `TEAM`, `AGENT`, `CLAUDE_PEER`
- `SLUG`, `DATE_YYYYMMDD`
- `task_worktree`, `task_branch`, `cc_handle`
- `plan_path`
- `tickets_dir`, `ticket_index_path`
- `phase_reviews: [{phase, review_path, verdict, timestamp}]`

## Quality Bar

Every plan and review must check:

- User value: the result is useful enough for a paid service.
- Root cause: bug fixes eliminate the cause, not just the symptom.
- Scope: MVP is explicit; out-of-scope is explicit.
- Safety: security, data loss, privacy, auth, payments, migrations, and production risks are called out.
- Acceptance: criteria are observable and testable.
- Verification: tests, typecheck, lint, build, smoke, or manual checks are specified.
- Operability: rollout, rollback, monitoring, and support impact are considered when relevant.

## Implementation Preflight

Before any implementation command such as `/ko`, file edit, migration discussion, dependency change, or ticket execution:

1. Confirm `git rev-parse --show-toplevel` is the task worktree from the brief and `git status --short` has no unexplained changes. Treat unrelated existing changes as user-owned; never move, stash, or revert them.
2. Confirm `git branch --show-current` is the Orca-created task branch, not a shared protected branch such as `main`, `master`, `develop`, `release/*`, or `production`.

## Phase A: Establish

1. Enter planning mode if available; otherwise avoid file writes until the user approves the plan direction.
2. Run the Implementation Preflight and record the task worktree, branch name, and whether unrelated user-owned changes exist.
3. Check the inbox with the names from the brief and take the source input and quality bar from Claude Code's request.

## Phase B: Independent Reports

Create Codex’s own planning report and request an independent Claude Code report.

Both reports must cover:

- User value and paid-service readiness.
- Root-cause or durable design direction.
- Scope and non-scope.
- Risks and guardrails.
- Acceptance criteria and verification strategy.
- Suggested ticket breakdown and Phase order.

Send this subject through agmsg:

```text
goal-feed plan review request
```

Include the source input, Codex’s preliminary direction, quality bar, and a request for Claude Code to produce an independent plan report.

Do not trust either report blindly. Reconcile them against repository facts and user constraints.

## Phase C: Reconcile

1. Compare Codex and Claude reports side by side.
2. Keep decisions that are supported by repo evidence or user value.
3. Reject suggestions that are speculative, too broad, or not tied to the current goal.
4. Ask the user only about choices that materially change scope, risk, or cost.

## Phase D: Final Plan File

Write `codex/plans/YYYYMMDD_<slug>_plan.md` after the direction is approved.

Required sections:

- `# <Title>`
- `## Goal`
- `## Paid-Service Quality Bar`
- `## Current State`
- `## Final Scope`
- `## Implementation Strategy`
- `## Acceptance Criteria`
- `## Risks And Guardrails`
- `## Test And Verification Plan`
- `## Claude Code Report Summary`
- `## Codex Report Summary`
- `## Reconciled Decisions`
- `## Ticketing Notes`

The plan must be decision-complete enough for `ticket-gen`: clear outcomes, affected areas, dependencies, acceptance criteria, and verification.

Notify Claude Code with subject:

```text
goal-feed plan finalized
```

## Phase E: Generate And Review Tickets

1. Run `ticket-gen` with the final plan file.
2. Identify `tickets_dir` and `ticket_index.md`.
3. Ask Claude Code for ticket review with subject:

```text
goal-feed ticket review request
```

4. Run Codex-side ticket review in the current session or via available `/ticket-review` workflow. Do not call another Codex as an external reviewer unless the user explicitly asks.
5. Merge Claude findings and Codex findings.
6. Fix ticket files until no Critical findings remain and Major findings are fixed or explicitly accepted by the user.

Implementation may start only when the Implementation Preflight has passed, the plan exists, `ticket_index.md` exists, and ticket review has no unresolved Critical findings.

## Phase F: Feed The Goal

Set the `/goal` objective to complete every Phase in `ticket_index.md` with these rules:

- Execute each Phase through `/ko <ticket_index.md> Phase N`.
- Strict tickets use `/cr --spec <ticket-path>` semantics.
- Run `/cr` after each Phase.
- Send a `goal-feed phase progress review request` to Claude Code after each Phase with summary, diff scope, verification, and known risks.
- After each Phase review request, wake Claude Code and stop. Do not `sleep` or poll, and do not edit the reviewed diff meanwhile. Claude Code replies and wakes you; confirm the response with `inbox.sh` before advancing.
- For any Phase that touches UI (rendering, styles, frontend components), capture real-screen screenshots and save them to `output/goal-feed/YYYYMMDD_phase<N>/NNN_<desc>.png`; list the paths in the review request. If the Phase has no UI change, state "no UI change" in the request. These screenshots are auto-collected by `/shime --visualize`.
- Fix Critical/Major review findings before advancing unless the user explicitly accepts the risk.
- After the matching review response is handled and verification passes, use `/next` to reconcile and choose the next Phase.

## Phase G: Final Audit

After all Phases:

1. Run or recommend `/ticket-verify <tickets-dir>`.
2. Send `goal-feed final review request` to Claude Code with verification report, Phase summary, and residual risks.
3. Perform Codex final self-review against the quality bar.
4. Create follow-up tickets for unresolved non-blocking gaps.
5. Wait for `goal-feed session closed` from Claude Code. Confirm nothing is left uncommitted, then mark the `/goal` complete and stop. Mark it complete only when required work is actually complete.

## Auto Message Handling

Only auto-handle `agmsg` messages when this skill is activated in the current session and the subject starts with `goal-feed `.

Subjects:

- `goal-feed plan report from claude` -> Phase C
- `goal-feed ticket review response` -> Phase E merge
- `goal-feed phase progress review response` -> Phase F gate
- `goal-feed final review response` -> Phase G gate
- `goal-feed session closed` -> Phase G step 5

Other messages require normal user-visible handling.

## Error Handling

- Claude report does not arrive: wake Claude Code once, then ask the user whether to continue with Codex-only planning or wait.
- Existing plan path: ask before overwriting; otherwise write `_v2`.
- Huge diff over roughly 2000 lines: summarize by area and use focused subreviews if available.
- Critical persists after 3 fix loops: stop and ask for direction.

## Completion Criteria

- Final plan file exists.
- Tickets generated and reviewed.
- Critical ticket-plan findings are zero.
- Every ticket Phase has run through `/ko`, `/cr`, and `/next` gates.
- Verification passed or follow-up tickets were created for accepted gaps.
- Final Claude review was handled or explicitly skipped.
- `goal-feed session closed` received and `/goal` marked complete.
