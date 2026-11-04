# エージェント配分基準

基本は **Claude Code + Codex** の 2 体で完結させる。ちょっとした追加作業を頼みたいときは Cursor を足す。それ以外の補助（Codex の 2 体目・Hermes）は、下の「足す条件」に当てはまるときだけ追加する。
1 つの worktree に入れるのは最大 4 体まで。体数が増えるほどレビューの往復と待ち時間が増えるため、迷ったら足さない。

## 役割

| エージェント | worktree での役割 | 向いている作業 | 向いていない作業 |
|-------------|------------------|---------------|-----------------|
| Claude Code | goal-feed の CC 側。プラン作成・チケットレビュー・Phase ごとの diff レビュー・最終監査。マスターへの報告窓口 | 設計判断、レビュー、仕様の穴探し | 長時間の反復実装（Codex に任せる） |
| Codex | goal-feed の Codex 側。`/goal` ループでチケットを実装 | 実装、リファクタ、テストを通すまでの反復 | 方針の最終決定 |
| Codex（2 体目） | 補助。1 体目と重ならないファイル群のチケットを並列で実装 | UI・文言の作業を含め、1 体目と独立に進められる実装 | 1 体目と同じファイルを触る作業 |
| Cursor（`cursor-agent`） | 補助。UI・フロントエンドの見た目調整、画面文言の書き換え | 画面・文言・ドキュメント | 認証・課金・データ移行など壊れると困る箇所の実装 |
| Hermes Agent（`hermes`、DeepSeek） | 補助。安価・高速な中難度タスクの並列処理 | 定型の量産（テストケース追加、型付け、移行作業の繰り返し部分）、Web 調査 | 設計判断、セキュリティに関わる実装 |

Antigravity（`agy`）は、日本語の出力（ユーザー向け文書・画面文言・README など）を自然な日本語に整えるときだけ使う。worktree にペインは立てず、worktree の CC が `agy-japanese` スキルを呼んで書き換えさせ、数値・固有名詞・断定の強さが変わっていないかを CC が検品する。それ以外の作業には使わない。

## 足す条件

- **Codex の 2 体目を足す**: ファイル単位で直交に分けられるチケットが複数あり、1 体目だけでは時間がかかるとき。UI・文言の補助も、Cursor が使えなければこちらに振る。
- **Cursor を足す**: CC と Codex の本筋から外れる、ちょっとした追加作業を頼みたいとき（UI の見た目調整、画面文言、ユーザー向け文書、小さな修正など）。`command -v cursor-agent` で CLI が見つからなければ足さず、Codex の 2 体目にする（CLI の導入はユーザーに確認する）。
- **Hermes を足す**: 同じ形の作業が 10 件以上あり、並列で流すと早いとき。または外部ドキュメントの調査が多いとき。
- 補助エージェントの成果は、必ず CC か Codex のどちらかがレビューする（補助同士でレビューを完結させない）。

## 相互レビューの組み合わせ

| 実装した側 | レビューする側 |
|-----------|---------------|
| Codex（1 体目・2 体目） | CC（goal-feed の Phase F。既定） |
| CC（例外的に CC が実装した部分） | Codex（`codex-second-opinion` 経由でも可） |
| Cursor / Hermes | CC。セキュリティ・データに触れる変更なら Codex も |

## 起動コマンド（Orca 上）

worktree 作成と同時に CC を立てる:

```text
orca worktree create --name <slug> --base-branch "$(git branch --show-current)" --agent claude --surface terminal --json
```

同じ worktree に追加する:

```text
orca agent launch --agent codex --surface terminal --worktree id:<repoId>::<path> --json
orca terminal create --worktree id:<repoId>::<path> --title <slug>-cursor  --command "cursor-agent" --json
orca terminal create --worktree id:<repoId>::<path> --title <slug>-hermes  --command "hermes"       --json
```

2 体目の Codex も同じコマンドで足す。`--surface terminal` は省かない（チャットで開くと `orca terminal send` で起こせない）。
どれも起動後に `orca terminal wait --terminal <handle> --for tui-idle --timeout-ms 60000 --json` で `satisfied: true` を確認してから指示を送る。起動中の TUI に送った文字は失われる。

## agmsg の種別名

`join.sh <team> <name> <type> <path>` の `<type>` は `claude-code` / `codex` / `hermes` など、agmsg が対応している種別を使う。Cursor の種別名は初回に `join.sh` の対応一覧で確認する。
名前は `<slug>-cc`・`<slug>-codex`・`<slug>-codex2`・`<slug>-cursor`・`<slug>-hermes` に揃える。
