---
name: orca-master
description: |
  Orca のメインペインで起動した Claude Code を「司令部（マスター）」にして、実装は一切せずオーケストレーションだけを行うスキル。
  マスターが Orca worktree を立ち上げ、各 worktree に Claude Code・Codex（必要に応じて 2 体目の Codex・Cursor・Hermes Agent）を配置し、agmsg でつないで goal-feed 駆動で回す。
  Phase ごとの相互レビュー・都度コミット・worktree 内で新しいブランチを作らない、といった基本ルールを全エージェントに徹底させる。
  発動条件: (1) /orca-master コマンド (2)「Orca でマスターとして」「司令部として回して」「worktree を立ててエージェントを配置」「Orca で goal-feed を回す」等のキーワード (3) Orca のメインペインで複数 worktree・複数エージェントの並行開発を始めるとき。
  使用しないケース: worktree 1 本・エージェント 1 体で済む小さな作業 / worktree 1 本の goal-feed を単独で回すとき（→ goal-feed をそのまま使う）/ 単発のハンドオフ（→ orca-cli の handoff）/ 方針を探っている段階の作業（何を作るか・どう設計するかが未定、成功条件をまだ書けない）→ worktree を作らず references/relay-mode.md に従い、idea-relay（人間が全メッセージを読んで送る Claude × Codex 合議）へ誘導する。
allowed-tools: Read, Write, Bash, Skill, AskUserQuestion, TaskCreate, TaskUpdate
---

# orca-master — Orca 司令部スキル

Orca のメインペインの Claude Code（以下マスター）が司令部になり、worktree ごとのエージェントチームを立ち上げ、つなぎ、見張る。
実装・レビューの実務は各 worktree のチームが goal-feed で回す。マスターは「誰に何をやらせるか」と「ルールが守られているか」だけを持つ。

```text
[Orca メインペイン] マスター CC（司令部・実装しない）
   │  orca worktree create / orca terminal send / agmsg
   ├─ worktree A: CC（プラン・レビュー） + Codex（/goal 実装） [+ Codex2 / Cursor / Hermes]
   ├─ worktree B: CC + Codex
   └─ ...
```

## 参照ファイル（該当ステップの直前に Read する）

- `references/agent-roster.md` — エージェントの配分基準と起動コマンド
- `~/.claude/skills/goal-feed/references/orca-protocol.md` — worktree・agmsg の名前・ペイン入力・待機の正本（goal-feed と共通）
- `references/kickoff-template.md` — worktree の CC への初期指示テンプレート
- `references/worktree-rules.md` — worktree 内の全エージェントが守るルール（初期指示でこのファイルを読ませる）
- `references/relay-mode.md` — 方針が未定の作業を idea-relay（または Kanary Relay）での探索的検討へ誘導する判定基準と手順

## 絶対のルール（マスター自身）

1. **マスターは実装しない。** プロダクトコード・テスト・設定ファイルを Edit / Write しない。書いてよいのは `.work/orca-master/` 配下の状態ファイルと、ユーザーに頼まれたプラン・指示書だけ。実装が必要になったら worktree に振る。
2. **ブランチを作るのは `orca worktree create` だけ。** 1 タスク = 1 worktree = 1 ブランチ。マスターも worktree 側も `git checkout -b` / `git switch -c` / `git branch <name>` をしない。
3. **push・main への統合・worktree 削除はユーザー承認後。** コマンドをコピー可能な形で提示し、`!` プレフィックスでの実行を依頼する（`git push`・`orca worktree rm` は直接実行しない）。
4. **送ったら届いたか確かめる。** `orca terminal send` は `--wait-submit` を付けて `turn_started` を確認する。確認できなければ `orca terminal read --screen` で画面を見て判断する。無反応を理由に同じ文を重ねて送らない（通信エラーで受付が不明なときだけ `--retry-request <id>` で同じ要求を再送する）。届いたと仮定しない。
5. **ルールは worktree に毎回渡す。** 初期指示に必ず `references/worktree-rules.md` を読むよう書く。口頭（プロンプト本文）だけで済ませない。
6. **agmsg の名前は毎回明示し、自動配信に頼らない。** 下の「agmsg の注意」を守る。

## agmsg の注意（Orca の worktree で起きること）

- agmsg は Orca の worktree（`~/orca/workspaces/<repo>/<slug>`）を本体のリポジトリと同じプロジェクトとして登録する。worktree が増えるほど同じプロジェクトに名前が溜まり、`whoami.sh` は `multiple=true` を返して自分の名前を決められなくなる。
- 自動配信（monitor / turn）は worktree では動かない前提で扱う。設定ファイル（`.claude/settings.local.json`・`.codex/hooks.json`）は git で追跡されず worktree に来ないうえ、turn モードは同じプロジェクトの最初の 1 体にしか届かない。ユーザーは自動配信を全プロジェクトで止めている。
- したがって、送受信は必ず名前を書いたコマンドで行う: `~/.agents/skills/agmsg/scripts/send.sh <team> <自分の名前> <相手の名前> "<本文>"`、`~/.agents/skills/agmsg/scripts/inbox.sh <team> <自分の名前>`。`whoami.sh` に名前を決めさせない。
- 送ったら、相手のペインを `orca terminal send` で起こす。起こす文には相手が実行する `inbox.sh` のコマンドを名前入りで書く。
- マスター自身のハンドルは `$ORCA_TERMINAL_HANDLE` で取れる。キックオフで worktree の CC に渡し、報告のたびにマスターを起こしてもらう。

## 状態ファイル

`.work/orca-master/state.json` に現在地を保存し、worktree の追加・Phase 遷移・メッセージ送受信のたびに上書きする。会話の要約や中断で記憶が飛んでも、再開時はまずこのファイルから復元する。

```json
{
  "team": "<agmsg チーム名>",
  "master_agent": "<マスターの agmsg 名>",
  "team_created_by_run": false,
  "worktrees": [
    {
      "slug": "auth-flow",
      "worktree_id": "<repoId>::<path>",
      "branch": "Otola-Ryntaro/auth-flow",
      "agents": { "cc": "<handle>", "codex": "<handle>" },
      "agmsg_names": { "cc": "auth-cc", "codex": "auth-codex" },
      "phase": "F",
      "last_report_at": "2026-10-20T10:00:00+09:00",
      "status": "in-progress"
    }
  ]
}
```

`.work/` が `.gitignore` に入っていなければ追加を提案する。

## 実行フロー

### Step 0 — 探索段階かの判定と前提チェック（欠けていたら止まってユーザーに確認）

1. **最初に、依頼が方針を探っている段階かを判定する。** `references/relay-mode.md` を Read し、判定基準に 2 つ以上当てはまれば理由を示して Relay モードへの切り替えを確認する。切り替えたら以降の Step には進まず、relay-mode.md の手順に従う。探索から戻ってきたら、保存した探索結果を入力にしてここから再開する。
2. `orca worktree current --json` でマスターが Orca の管理下にいること、メイン worktree（`isMainWorktree: true`）であることを確認する。
3. `git status` と `git branch --show-current` を見る。未コミットの変更があれば、worktree を切る前にどう扱うか確認する（worktree はコミット済みの base から作られるため）。
4. agmsg: `~/.agents/skills/agmsg/scripts/whoami.sh "$(pwd)" claude-code` でマスターの identity を確認。未参加なら `/agmsg` の join を案内する。
5. 使う予定のエージェント CLI があるか確認する（`command -v claude codex cursor-agent hermes`）。

### Step 1 — 作業の分割と配分（ユーザーと合意）

1. ユーザーの依頼を、互いに独立して進められる単位に分ける。同じファイル群を触る作業は同じ worktree にまとめる（worktree 間のコンフリクトを避けるため）。
2. `references/agent-roster.md` を Read し、worktree ごとのエージェント構成を決める。基本は **CC + Codex** で完結させ、ちょっとした追加作業があれば Cursor を足す。Codex の 2 体目・Hermes は配分基準に当てはまるときだけ足す。Antigravity（agy）は日本語の出力を自然な日本語に整えるときだけ、worktree の CC が `agy-japanese` 経由で使う。
3. 分割案と配分を表で示し、`AskUserQuestion` で承認を取る。

### Step 2 — worktree の起動

`~/.claude/skills/goal-feed/references/orca-protocol.md` を Read し、worktree ごとに次を行う。

1. `orca worktree create --name <slug> --base-branch "$(git branch --show-current)" --agent claude --surface terminal --json` で worktree と CC を作る（未 push のローカルコミットも含めるため `--base-branch` を渡す）。返ってきた `worktree.id` と `launch.outcome.handle` を state.json に記録する。
2. Codex を `orca agent launch --agent codex --surface terminal --worktree id:<worktreeId> --json` で同じ worktree に追加する。Cursor / Hermes は `references/agent-roster.md` の起動コマンドで追加する。
3. 各ターミナルを `orca terminal wait --for tui-idle --timeout-ms 60000` で待ち、`satisfied: true` を確認してから次へ進む。
4. 各エージェントの名前を、マスターが agmsg の同じチームに登録する（`join.sh <team> <slug>-cc claude-code <worktreePath>`。名前は `<slug>-cc`・`<slug>-codex` のように worktree を接頭辞にする）。`send.sh` は未登録の宛先を拒否するので、最初の送信より先に行う。同じ名前が既に登録されていれば join は不要。
5. `orca worktree set --worktree id:<worktreeId> --comment "<役割の一行要約>" --workspace-status in-progress` でカードに状態を出す。

### Step 3 — goal-feed のキックオフ

`references/kickoff-template.md` を埋めて、worktree の CC に送る。CC は goal-feed（チケットがあれば goal-feed-impl）を起動し、同じ worktree の Codex と組んで Phase A 以降を回す。Codex 側の起動指示は worktree の CC が出す（マスターは Codex に直接作業指示を出さない。指揮系統を一本にするため）。

### Step 4 — 監視（ブロッキング待機・前面ポーリング禁止）

- 各 worktree の CC には、Phase 完了・ブロック・ユーザー判断が必要な事項を `orca-master report` / `orca-master blocked` / `orca-master needs-human` の件名でマスターに送らせ、送った直後にマスターのペインを起こさせる（worktree-rules.md に記載済み）。起こされたら、次の「受信の確認」を行う。
- 待つときは `orca-protocol.md` 7 節と同じく、見張りたい worktree の CC について `orca terminal wait --terminal <ccHandle> --for tui-idle --timeout-ms 1800000 --json` を `run_in_background` で 1 本だけ起動し、前面でポーリングしない（タイムアウトは下の期限に合わせる）。起こされたら待機の終了を待たずに受信を確認し、待機が戻ったときも受信を確認する。
- 受信の確認: `~/.agents/skills/agmsg/scripts/inbox.sh <team> <master_agent> > .work/orca-master/inbox-<日時>.txt` を 1 回実行し、そのファイルを読む（`inbox.sh` は読んだ時点で既読にするため、出力を必ずファイルに残す）。
- 期限（既定 30 分）を過ぎても報告がない worktree は、`orca terminal read --terminal <handle> --screen --json` で今の画面だけ読み、止まっていれば再開を促す 1 行を送る。3 回続けて止まっていたらユーザーにエスカレーションする。
- Phase 完了報告を受けたら、`git -C <worktreePath> log --oneline -5` でコミットが積まれていること、`git -C <worktreePath> branch --list` でブランチが増えていないことを確認する。ルール違反があれば当該 CC に是正を指示する。
- worktree のカードのコメントを Phase ごとに更新する。

### Step 5 — 完了と統合

1. worktree の CC から goal-feed の最終監査（Phase G）完了報告を受けたら、`--workspace-status in-review` にする。
2. worktree ごとに「main へ統合 / PR を作る / 保留 / 破棄」を `AskUserQuestion` で選んでもらう。
3. 統合・push・`orca worktree rm` のコマンドを提示し、ユーザーに `!` で実行してもらう。
4. worktree を片付けたら、その worktree のエージェントを agmsg からも外す（ユーザーが `orca worktree rm` を実行したのを確認してから行う）。
   - state.json の `agmsg_names` にある名前すべてについて `~/.agents/skills/agmsg/scripts/leave.sh <team> <name>` を実行する（`<slug>-cc`・`<slug>-codex`・補助エージェント）。残すと同じプロジェクトに名前が溜まり、次の worktree で名前の判定が狂う。
   - チームがこの実行のために作ったもの（state.json の `team_created_by_run: true`）なら、全 worktree を片付けたあとにマスター自身も `leave.sh <team> <master_agent>` で外す。最後の 1 人が抜けるとチームも消える。プロジェクト共通の既存チーム（例: `playground`）はたたまない。
   - 外したら `~/.agents/skills/agmsg/scripts/team.sh <team>` で残りを表示して確かめる。メッセージ履歴は消えない。
5. 全 worktree が片付いたら `/shime` を呼ぶ。

## メッセージ件名（agmsg）

| 件名 | 送り手 → 受け手 | 用途 |
|------|----------------|------|
| `orca-master kickoff` | マスター → worktree CC | 担当範囲・成功条件・ルールファイルの場所 |
| `orca-master report` | worktree CC → マスター | Phase 完了（コミット hash・レビュー結果・次の Phase） |
| `orca-master blocked` | worktree CC → マスター | 進めない理由と必要なもの |
| `orca-master needs-human` | worktree CC → マスター | ユーザー判断が必要な事項（選択肢つき） |
| `orca-master directive` | マスター → worktree CC | 是正・方針変更・追加指示 |

goal-feed 内部の件名（`goal-feed ...`）は worktree の CC と Codex の間で使い、マスターは関与しない。

## エラー・分岐

| 状況 | 動作 |
|------|------|
| Orca が起動していない | `orca open --json` で起動して再試行 |
| `runtime_access_denied` | サンドボックスの制限。権限を上げて再実行する（Orca を再起動しない） |
| `terminal_handle_stale` | `orca terminal list --worktree <id> --json` で取り直し、新しいハンドルだけを使う |
| 2 つの worktree が同じファイルを触り始めた | 片方を止め、どちらに寄せるかユーザーに確認 |
| worktree 内でブランチが増えていた | 当該 CC に、増えたブランチのコミットを worktree のブランチへ戻させ、余分なブランチの削除コマンドをユーザーに提示 |
| ユーザー判断待ちが溜まった | `.work/orca-master/needs-human.md` に選択肢つきで追記し、他の worktree は止めずに進める |

## 変更しないもの

- goal-feed / goal-feed-impl（Claude 側・Codex 側とも）の SKILL.md。Orca の手順を変えるときは `orca-protocol.md` を直す
- agmsg の DB・config・チームファイル
