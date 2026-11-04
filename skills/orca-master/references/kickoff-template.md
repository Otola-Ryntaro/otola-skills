# 初期指示テンプレート（マスター → worktree の CC）

マスターは agmsg で `orca-master kickoff` を送り、続けて `orca terminal send` で下の文を CC に送る。`<...>` を埋める。
worktree 内の手順は `~/.claude/skills/goal-feed/references/orca-protocol.md` が正本で、Codex の起動済み・名前の登録済みは同ファイル 2 節の「orca-master 配下」に当たる。

```text
あなたは worktree「<slug>」の Claude Code です。マスター（agmsg 名: <master_agent>、チーム: <team>、ターミナル <masterHandle>）の指揮下で作業します。
最初に ~/.claude/skills/orca-master/references/worktree-rules.md と ~/.claude/skills/goal-feed/references/orca-protocol.md を読み、そのルールに従ってください。

担当範囲: <この worktree でやること>
成功条件: <検証可能な完了条件>
触ってよい範囲: <ディレクトリ・ファイル>（範囲外を変更する必要が出たら orca-master blocked で相談）
同じ worktree のエージェント: Codex（ターミナル <codexHandle>、agmsg 名 <slug>-codex）<, 2 体目の Codex / Cursor / Hermes があれば追記>

あなたの agmsg 名は <slug>-cc です（登録済み）。whoami.sh で名前を決めないこと。
準備ができたら <goal-feed | goal-feed-impl> を起動してください。worktree の作成と Codex の起動は不要です。Codex へのブリーフは orca-protocol.md の 5 節の文を terminal send で送ります。
Phase が終わるたびに orca-master report をマスターに送り、続けてマスターを起こしてください。
```

`<masterHandle>` はマスター自身の `$ORCA_TERMINAL_HANDLE` を入れる。

Codex・補助エージェント（Cursor・Hermes など）への指示は worktree の CC が出す（指揮系統を一本にするため）。

## マスターの起こし方

```bash
orca terminal send --terminal <masterHandle> --enter --json \
  --text '~/.agents/skills/agmsg/scripts/inbox.sh <team> <master_agent> で orca-master のメッセージを確認して'
```
