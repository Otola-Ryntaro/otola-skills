---
name: goal-feed-impl
description: |
  Use when tickets already exist and the user wants a short command-style workflow to feed Codex a goal for repeated implementation: take an existing ticket_index.md or tickets directory, set /goal, run /ko by phase, report progress to Claude Code through agmsg, run /cr self-review, request cc review, advance with /next, finish with ticket-verify and the Claude Code final review. Trigger on "goal-feed-impl", "ticket作成済み", "ticket作成後の実装", "Phase実装を回して", or requests to execute tickets through /goal.
---

# goal-feed-impl

## Purpose

Execute an already-created ticket plan through a goal-driven implementation loop.
This is the short version of `goal-feed`: it starts after `ticket-gen` and ticket review.

Do not create the plan or run `ticket-gen` here. If the user has no tickets yet, switch to `goal-feed`.

## Orca Runtime

This skill runs inside an Orca worktree that Claude Code created. Read `~/.claude/skills/goal-feed/references/orca-protocol.md` first; it is the source of truth for worktrees, agmsg names, waking the peer, and cleanup.

- The launch brief gives the team, your agmsg name, the Claude Code name, and `cc_handle`. Use them as given. Both names are already registered, so do not run `join.sh` or `whoami.sh`.
- Never create a worktree or branch (`git worktree add`, `orca worktree create`, `git checkout -b`). The current directory is the task worktree. If the brief is missing or this is the primary worktree, stop and tell the user that Claude Code must start the run.
- After every `send.sh`, wake Claude Code with `orca terminal send --terminal <cc_handle> --text '<inbox command>' --enter --json` (section 6 of the protocol).
- Claude Code owns the worktree cleanup decision and `/shime`. Do not remove worktrees.

## Required Inputs

- A `ticket_index.md` path, or a tickets directory containing `ticket_index.md`.
- Current repository state.

## Preflight

1. Locate `ticket_index.md`.
   - If the user passed a file, use it.
   - If the user passed a directory, use `<dir>/ticket_index.md`.
   - If omitted, search the latest `docs/tickets*/ticket_index.md`, then `codex/tickets*/ticket_index.md`.
2. Read `ticket_index.md` and identify all phases, current status, and first incomplete phase.
3. Check the inbox with the names from the brief, using only scripts under `~/.agents/skills/agmsg/scripts/`.
4. Confirm there are no unresolved Critical plan-review findings if review logs exist. If there are unresolved Critical findings, stop and ask for user direction.
5. Confirm the current directory is the task worktree on the Orca-created branch, not a protected branch. Treat unrelated changes as user-owned and stop if the worktree is not appropriate for the tickets.

## Set The Goal

Create or update `/goal` with this objective:

```text
Complete all phases in <ticket_index.md>. For each phase, run /ko, run Codex self-review with /cr or /cr --spec, request review from Claude Code through agmsg, handle Critical/Major findings, advance with /next, then after all phases run /ticket-verify, request the final review, and stop when Claude Code sends session closed.
```

The goal is complete only after:

- Every phase is complete.
- Claude Code final review has been requested.
- Codex self-review has no unresolved Critical/Major findings.
- `/ticket-verify <tickets-dir>` has completed.
- Claude Code has sent `goal-feed-impl session closed`.

## Phase Loop

Repeat until all phases are done:

1. Run implementation for the active phase:
   - `/ko <ticket_index.md> Phase <N>`
2. Run Codex self-review:
   - Use `/cr` for normal phase diffs.
   - Use `/cr --spec <ticket-path>` for strict, HIGH, auth, payment, migration, DB, security, or acceptance-sensitive tickets.
3. Fix all Critical/Major findings from Codex self-review.
4. Run relevant verification for the phase.
5. Send a Phase progress review request to Claude Code through `agmsg`, wake Claude Code, and stop. Do not `sleep` or poll, and do not edit the reviewed diff meanwhile. Do not advance with `/next` until the review response is confirmed with `inbox.sh`.
6. When Claude Code review arrives:
   - Fix Critical findings.
   - Fix Major findings unless the user explicitly accepts the risk.
   - Track Minor findings as optional follow-up unless cheap and low-risk.
   - Re-run verification for anything you changed.
7. Run `/next <ticket_index.md>` to mark progress and select the next phase.
8. Send a short progress report to Claude Code when `/next` moves to a new phase.

Codex has no monitor delivery, so the wake from Claude Code is what resumes the loop.

## Finalization

After `/next` reports all phases complete:

1. Run:
   - `/ticket-verify <tickets-dir>`
2. If `/ticket-verify` fails:
   - Create follow-up tickets or return to the relevant phase.
   - Do not mark the goal complete.
3. If verification passes, send Final review request to Claude Code and wake it.
4. Handle the findings, then wait for `goal-feed-impl session closed` from Claude Code. Confirm nothing is left uncommitted, then mark `/goal` complete and stop.

## agmsg Message Templates

### Plan Review Request

Usually not used by `goal-feed-impl`. If a missing plan-quality decision blocks implementation, send:

```text
件名: goal-feed-impl plan clarification request

ticket_index: <ticket-index>
詰まっている計画判断:
<issue>

確認してほしい観点:
- 既存チケットのまま進めてよいか
- チケット修正または追加Phaseが必要か
- 有料サービス品質・本質修正の観点で弱い点がないか
```

### Ticket Review Request

```text
件名: goal-feed-impl ticket review request

ticket_index: <ticket-index>
tickets-dir: <tickets-dir>

実装前の確認:
- 未解消のCritical/Majorがないか
- Phase順序に問題がないか
- /goalで全Phase実装に入ってよいか
```

### Phase Progress Review Request

```text
件名: goal-feed-impl phase progress review request

ticket_index: <ticket-index>
phase: Phase <N>
状態: <completed/in-progress/blocked>

Codex実施内容:
<summary>

スクショ:
<UI を伴う Phase は必須。実画面を撮影し
output/goal-feed/YYYYMMDD_phase<N>/NNN_<desc>.png に保存してパスを列挙する。
UI 変更が無い Phase は「UI 変更なし」と 1 行書く>

自己レビュー:
<cr summary>

検証:
<commands and results>

見てほしい点:
- 受け入れ条件の漏れ
- Critical/Major相当の実装リスク
- 次Phaseに進む前に必要な修正
```

### Final Review Request

```text
件名: goal-feed-impl final review request

ticket_index: <ticket-index>
ticket-verify: <report path or result summary>

全Phase完了サマリ:
<summary>

残リスク:
<known risks or none>

最終レビューをお願いします。Critical/Majorがあれば優先して返してください。
```

## Completion Report

Report to the user:

- Completed phases.
- Claude Code review status.
- `/cr` rounds and unresolved findings, if any.
- `/ticket-verify` result and report path.
- Whether `/goal` was marked complete.
