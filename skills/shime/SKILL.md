---
name: shime
description: セッション終了時の締め作業スキル。日報の作成とPlans.mdへの引き継ぎ情報の保存を対話的に行う。「/shime」「締め作業」「今日の作業をまとめて」「作業終了」「今日の振り返り」「日報書いて」で発動。daily_report/ フォルダに YYYY-MM-DD_[タイトル].md 形式で日報を作成し、docs/MILESTONES.md（ロードマップ進捗の正本）があれば現在地を更新して Plans.md の「ロードマップ進捗」セクションを上書きし、日報作成直後にHTML可視化（--visualize）の要否をAskUserQuestionで確認し（デフォルト不要）、次回セッションへの引き継ぎ事項をユーザーと確認しながら Plans.md に保存する。さらに、アカウント作成・APIキー発行・DNS設定等のユーザー本人の手作業が残っている場合は manual-todo スキルでの HTML チェックリスト化を提案する。終わった worktree（統合済み・未コミットなし）と、使われなくなった agmsg のエージェント名・実行用チームがあれば、確認のうえ片付ける（worktree 削除はユーザーが ! で実行）。
---

# 締め作業（/shime）

セッション終了時の振り返り・引き継ぎを行う。

## 実行手順

### Step 1: セッションの振り返り

会話履歴から今日の作業を要約する。以下の観点で整理：

- **完了したこと**: 実装・作成・調査が終わったもの
- **未完了のこと**: 途中で止まっているもの
- **決定事項**: 設計・方針・選択したアプローチ
- **気づき・学び**: エラー解決策、有効だったやり方など

### Step 2: 日報ファイルの作成

`daily_report/` フォルダに以下のフォーマットで保存する。

**ファイル名**: `YYYY-MM-DD_[一言サマリー].md`  
例: `2026-04-13_ハーネス記憶ガイド作成.md`

**日報テンプレート:**

```markdown
# 日報 YYYY-MM-DD

## 今日やったこと
- 

## 完了
- 

## 未完了・残タスク
- 

## 決定事項・気づき
- 

## 次回やること
- 
```

`daily_report/` フォルダが存在しない場合は作成する。

### Step 3: 可視化（--visualize）の要否確認

日報ファイルを保存したら、**必ず** AskUserQuestion で可視化の要否を確認する。起動時に毎回聞くのではなく、日報を書き終えたこのタイミングでのみ聞く。

```
AskUserQuestion:
  question: "このセッションの更新作業をHTMLで可視化しますか？（ノンプログラマ向けのダッシュボード形式）"
  header: "可視化"
  options:
    - label: "不要"
      description: "日報の.mdファイルのみで十分な場合はスキップ（デフォルト）"
    - label: "作成する"
      description: "daily_report/ にHTMLダッシュボードを追加生成する"
```

選択肢は「不要」を1番目に置く（この機能のデフォルト挙動は不要のため）。

**「作成する」が選ばれた場合:**

1. `references/visualize-template.html` を読み込み、これをベースに新規HTMLを作成する（テンプレート自体は上書きしない）。`{{PROJECT_NAME}}` にはカレントディレクトリ名（`pwd` の basename）をそのまま機械的に入れる。あとで見返したときにどのプロジェクトの日報かをヘッダーで即判別できるようにするための表示
2. **主役は「実際に実装された内容」**。セッションの進行記録（レビュー往復・承認フロー等）ではなく、**何がどう作られ・どう動くか**を中心に書く。実装セッション（自分または Codex 等の協調エージェントが実装した場合）では必ず以下を含める:
   - **仕組みの全体像**: 新機能がどう動くかをデータフロー図・構成図で示す。**複雑な図（ノード 6 個以上、または状態遷移・分岐・並列を含む）は `archify` スキル（`~/.claude/skills/archify`）で生成する**：構成図→`architecture`、処理フロー→`workflow`、状態遷移→`lifecycle`、API 呼び出し順→`sequence`、パイプライン→`dataflow` 型。作法（validate → deliver、`--quality showcase`）は archify の SKILL.md に従い、出力先は `daily_report/YYYY-MM-DD_[slug]_diagram.html`。日報 HTML には `<iframe src="./YYYY-MM-DD_[slug]_diagram.html" style="width:100%;height:640px;border:1px solid #333;border-radius:12px" loading="lazy"></iframe>` ＋「🔍 別タブで大きく開く」リンクを置く。**archify が失敗した／node が使えない／図が単純な場合はインライン SVG**（`viewBox` 指定、ノードは `rect`+`text`、矢印は `path`+`marker-end`、配色はテンプレのカラー変数に合わせる。外部画像・CDN は使わない）。一直線の単純なフローだけなら ASCII の `.flow` ブロックでも可
   - **新規・変更モジュールの詳細**: 各ファイルが「何をするか・どう動くか」を行数付きカードで（`git diff --stat <wave開始>..HEAD` で実差分を取り、会話の記憶だけに頼らない）
   - **実際に入ったデータ・数値**: 新しい定数・KPI・しきい値などの実値テーブル
   - **レビューで実装が変わった箇所**: 指摘→実装変更の対応表（あれば）
   ノンプログラマの読者が「自分のプロジェクトに何が入ったのか」を理解できることが合格基準。
3. **アクションファースト**（正本: `~/.claude/skills/visualize-common/references/action-first.md`）。
   「次回やること」は h1 直下の `.hero` カードに置き、各アクションに「なぜやるのか」を 1 文添える（末尾には置かない）。
   やることが無ければ Hero を「✅ このセッションで完結。次回やることはありません」にする。
   「未完了」は補助セクションとして本文中に置く。該当データが無いセクション（例: 未完了タスクが無い）はセクションごと省略してよい。
   各 h2 セクションの見出し直下には必ず 2〜4 文の地の文を置き、箇条書きだけのセクションを作らない
3b. **本日のスクショ**: 当日撮影されたスクリーンショットがあれば「本日のスクショ」セクション（`.shots` ギャラリー）として base64 埋め込みする。
   - 収集元: `output/playwright/YYYYMMDD_*/`, `output/browser-exam/YYYYMMDD_*/`, `output/goal-feed/YYYYMMDD_*/`, `.playwright-mcp/`（当日 mtime）
   - 代表 3〜8 枚を選定（同一画面の連番は間引く）し、`sips --resampleWidth 1200` → `base64 -i` で埋め込む
   - 手順・サイズ規約（合計 5MB 目安）は `~/.claude/skills/visualize-common/references/screenshot-embed.md` に従う
   - 1 枚も無ければセクションごと省略する
3c. **ロードマップ現在地**: `docs/MILESTONES.md` が存在する場合は、**先に Step 3.5-A の (1)(2)（タスクチェック更新・現在地移動）を済ませてから** HTML を生成し、「ロードマップ現在地」セクションを含める。
   - 形式はテンプレの `.roadmap` ブロック: マイルストーンごとのボックスを**横軸タイムライン**で並べ、現在地ボックスの上に ▼ マーカー（「今ここ」）を置く
   - 各ボックスの下に `<details>` で折りたたみのタスクリスト（☑ / ☐）を付ける（デフォルト閉、進行中のみ `open`）
   - 完了マイルストーンは達成色（good）、進行中はアクセント色、未来は減光
   - `docs/MILESTONES.md` が無いプロジェクトではセクションごと省略する
4. 保存先は `daily_report/YYYY-MM-DD_[一言サマリー]_visualize.html`。**日報の .md と同じ日付・slugを使う**（例: 日報が `2026-07-01_ハーネス記憶ガイド作成.md` なら `2026-07-01_ハーネス記憶ガイド作成_visualize.html`）
5. **todo ハブの作業ログに登録する（可視化 HTML を作ったら必須）**:
   ```bash
   ~/dev/todo/bin/todo-hub report-add --path "<生成したHTMLの絶対パス>" --title "<一言サマリー>"
   ```
   - `report-add` は登録と同時に `~/dev/todo/reports.html`（ハブの「📊 作業ログ」ページ）を再生成する。**これがハブ側 HTML の更新作業を兼ねる**ので、別途 reports.html を手編集しない
   - 実行後、コマンドの exit code を確認し、失敗していたらエラー内容をユーザーに報告する（黙って先へ進まない）
   - `~/dev/todo/bin/todo-hub` が存在しない環境（別マシン等）のみスキップし、その旨を一言添える
5b. **双方向リンクの確認**: テンプレート由来の `📊 作業ログハブへ` リンク（`.hub-link`、`file:///Users/you/dev/todo/reports.html` 向き）が生成 HTML のヘッダーに残っていることを確認する。テンプレを大きく改変した場合も、このリンクは必ず残す（ハブ → 日報 → ハブ の往復動線を切らさない）
6. 完了確認（Step 5）で、このファイルをターミナルからそのまま開けるコピペ用コマンドを提示する:
   ```
   ! open "daily_report/2026-07-01_ハーネス記憶ガイド作成_visualize.html"
   ```

**「不要」が選ばれた場合**はそのまま Step 3.5 に進む。

### Step 3.5: ロードマップ進捗の更新（毎回必ず判定）

大ゴールまでの現在地を可視化するステップ。正本は `docs/MILESTONES.md`（進捗）と
`USER_GUIDE/ROADMAP.md`（大ゴール定義）。**このタイミングでのみ読み込む**（セッション常駐させない）。

**A) `docs/MILESTONES.md` が存在する場合:**

1. `docs/MILESTONES.md` を読み込み、このセッションの作業に該当するタスクを `- [x]` に更新する
2. 進行中マイルストーンのタスクが全て完了したら、見出しに `✅ (YYYY-MM-DD)` を付け、
   冒頭の `現在地: ▶ Mn` と次マイルストーンの見出しマーカー `▶ 進行中` を移動する
3. Plans.md の「## ロードマップ進捗」セクションを**上書き**更新する（追記しない。下の 3 項目だけにする）:

   ```markdown
   ## ロードマップ進捗（shime が上書き更新・正本は docs/MILESTONES.md）

   - 現在地: M2 MVP公開（3/5 タスク完了）／全体: M2/M4
   - 残り: 認証まわり、公開
   - 最終更新: YYYY-MM-DD
   ```

   セクションが無ければ Plans.md 冒頭（タイトル直後）に新設する
4. ユーザーに 2〜3 文で提示する。例:
   「今回の作業は M2『MVP公開』のデプロイ環境構築に該当します。M2 の残りは認証まわりと公開の 2 件、全体では M2/M4 の位置です。」

**B) `docs/MILESTONES.md` が無い場合（first-action を通していない既存プロジェクト等）:**

1. まず Plans.md に `<!-- roadmap: declined -->` マーカーが**無いこと**を確認する。あれば何もせず Step 4 へ
2. マーカーが無ければ、AskUserQuestion で一度だけ提案する:
   - question: 「このプロジェクトの大ゴールまでのロードマップを作りますか？（USER_GUIDE/ROADMAP.md と docs/MILESTONES.md を作成し、以後 shime で進捗を追跡できます）」
   - options: 「今はしない（デフォルト）」／「作成する」／「今後も提案不要」
3. 「作成する」→ 対話で大ゴール（商用化レベルの最終到達点）を確認し、マイルストーン
   M1〜Mn（事業段階レベルの粒度）に分割して、first-action スキルのテンプレ
   （`~/.claude/skills/first-action/references/templates/roadmap.md` / `milestones.md`）を使って
   2 ファイルを作成。CLAUDE.md の Project-Specific Notes にポインタ 3 行を追記し、A) の手順に続く
4. 「今後も提案不要」→ Plans.md 末尾に `<!-- roadmap: declined -->` を記録し、以後このステップの提案をスキップ
5. 「今はしない」→ 何も記録せず Step 4 へ（次回の shime でまた判定される）

### Step 4: Plans.md への引き継ぎ（対話）

以下を番号付きリストでユーザーに提示し、Plans.md に追記する内容を選ばせる：

```
次回セッションへの引き継ぎ候補です。Plans.md に追記するものを番号で教えてください
（例: 1,3,5 または「全部」「なし」）：

1. [残タスクA]
2. [残タスクB]
3. [決定事項: 〇〇]
4. [次回やること: 〇〇]
```

ユーザーが選択したものを Plans.md の「## 次回セッション」セクションに追記する。
Plans.md が存在しない場合は新規作成する。

**Plans.md への追記フォーマット:**

```markdown
## 次回セッション（YYYY-MM-DD 引き継ぎ）

### 残タスク
- [ ] 

### 決定事項の引き継ぎ
- 

### 次回やること
- 
```

### Step 4.5: 手作業残タスク判定（毎回必ず実施）

Plans.md への引き継ぎが終わったら、**毎回**次の判定を行う：

1. このセッションの作業の中に、次の3つの「ない」に該当する残タスクがないか確認する
   - コード／ファイルで完結し**ない**（ブラウザ管理画面・物理デバイス等が絡む）
   - CLI／API では代行でき**ない**（人間のクリック・認証・支払いが必須）
   - 判断を委任でき**ない**（本人の合意・承認が要る）
2. さらに `~/dev/todo/state/*.json` を確認し、このプロジェクト（`projectPath` で判別）の**既存 TODO に未完了（`done: false`）が残っていないか**も見る
2b. **既存 TODO の消し込み（突合）**: 未完了タスクが残っている場合、このセッションでやったこと（会話・変更ファイル・コミット）と突合し、**実はもう終わっているタスク**がないか確認する
   - 終わっていると判断できるタスク → state JSON の該当タスクを `done: true` に、`checkedAt` を現在時刻（ISO 8601）に **Claude が Edit で更新**し、消し込んだタスク名をユーザーに報告する（確信が持てない場合は勝手に消し込まず「これは終わっていますか？」と確認する）
   - 消し込みの結果**リスト全体が完了**（全タスク `done: true`）になったら、そのリストを削除する：pages の HTML・state の JSON を削除し、`registry.json` の `pages` から該当 slug のエントリを除去する
   - state を1件でも更新・削除したら `python3 ~/.claude/skills/manual-todo/scripts/todo-hub.py reindex` を実行してハブに反映する
3. 判定結果に応じて：
   - **新しい手作業タスクが1つ以上ある** → AskUserQuestion で「manual-todo で HTML チェックリスト化しますか？」と提案。承認されたら `manual-todo` スキルを起動
   - **既存 TODO に未完了が残っている**（消し込み後も） → 「前回分の手作業 TODO が N 件未完了です（〜〜など）」と件数と代表例を報告し、ハブを開くコマンドを添える。古いリストが複数残っている・妥当性が怪しいタスクがある場合は `/todo-tanaoroshi`（過去 TODO 棚卸しスキル）を提案する
   - **どちらも無い** → 何も言わずに Step 5 へ進む（提案自体をスキップ）

### Step 4.7: worktree と agmsg の片付け（毎回判定・候補が無ければ黙ってスキップ）

orca-master・idea-relay・goal-feed で立てた worktree や agmsg の名前を放置すると、同じプロジェクトに名前が溜まり、次回 agmsg が自分の名前を判定できなくなる（`whoami.sh` が `multiple=true` を返す）。締めのたびに、終わったものを片付ける。

**1. 候補を集める（読み取りだけ）**

- worktree: `git worktree list --porcelain` のうちメイン以外。Orca があれば `orca worktree list --repo path:"$(git rev-parse --show-toplevel)" --json` も見る。各 worktree について次を調べる:
  - 未コミットの変更: `git -C <path> status --porcelain`
  - 既定ブランチへの統合済みか: `git branch --merged <既定ブランチ>` に含まれるか
  - 生きているターミナル: `orca terminal list --worktree path:<path> --json`
- agmsg: このプロジェクトが属するチームごとに `~/.agents/skills/agmsg/scripts/team.sh <team>` を実行し、このプロジェクトのパスで登録された名前を集める。
- 実行記録: `.work/orca-master/state.json`（`worktrees[].agmsg_names`・`team`・`team_created_by_run`）と `.work/idea-relay/*/state.json`（`codex_agent`・`claude_agent`）。

**2. 片付け候補を決める**

| 対象 | 候補にする条件 | 候補にしないもの |
|------|---------------|-----------------|
| worktree | 統合済み、かつ未コミットの変更なし、かつ生きているターミナルなし | 未統合・未コミットあり・作業中のもの（理由を添えて報告だけする） |
| agmsg の名前 | 対応する worktree が無い／今回片付ける worktree の名前／status が done の idea-relay の名前 | プロジェクトの常用名（例: `<project>_cc`・`<project>_codex`）、生きているターミナルが使っている名前、別プロジェクトのパスで登録された名前 |
| agmsg のチーム | `team_created_by_run: true` で、候補の名前を外すと誰も残らないもの | プロジェクト共通の既存チーム（たたまない） |

候補が 1 件も無ければ何も言わずに Step 5 へ進む。

**3. 確認する**

候補を表（worktree のパス・ブランチ・状態、外す agmsg の名前、たたむチーム）で示し、AskUserQuestion で選んでもらう:

- 「候補をすべて片付ける」
- 「agmsg の名前だけ外す（worktree は残す）」
- 「今回はしない」（デフォルトにしない。候補が見えている以上、選んでもらう）

**4. 実行する**

- **worktree の削除はユーザーが `!` で実行する**（直接実行しない）。コピー可能な形で提示する:
  - Orca 管理: `! orca worktree rm --worktree path:<path> --json`
  - それ以外: `! git worktree remove <path>`
  - 統合済みブランチの削除: `! git branch -d <branch>`（`-D` は提示しない）
- ユーザーの実行後、`git worktree list` で消えたことを確かめてから、agmsg の名前を外す（これは Claude が実行してよい）: `~/.agents/skills/agmsg/scripts/leave.sh <team> <name>`。たたむチームは最後の 1 人が抜けた時点で消える。
- 外したら `team.sh <team>` で残りを表示し、`whoami.sh "$(pwd)" claude-code` と `whoami.sh "$(pwd)" codex` が `multiple=true` を返さないことを確かめる。まだ複数返す場合は、残っている名前を報告する。
- メッセージ履歴と `.work/` 配下の記録（log.md など）は消さない。

片付けた内容は Step 5 の完了確認に 1〜3 行で含め、日報の「今日やったこと」にも追記する。

### Step 5: 完了確認

日報のファイルパス・（作成した場合）可視化HTMLのファイルパス・Plans.mdへの追記内容を確認メッセージとして表示する。可視化HTMLを作成した場合は、ターミナルからそのまま開けるコピペ用コマンドも添える：

```
日報を保存しました: daily_report/2026-07-01_ハーネス記憶ガイド作成.md
可視化レポートも作成しました: daily_report/2026-07-01_ハーネス記憶ガイド作成_visualize.html
手作業TODOも作成しました: ~/dev/todo/pages/2026-07-01_1830_ハーネス記憶ガイド作成.html

ブラウザで開くには次のコマンドをコピペしてください:
! open "daily_report/2026-07-01_ハーネス記憶ガイド作成_visualize.html"
! python3 ~/.claude/skills/manual-todo/scripts/todo-hub.py open "2026-07-01_1830_ハーネス記憶ガイド作成"
```

（手作業TODO・可視化HTMLは、それぞれ作成した場合のみ行を表示する。Step 4.7 で片付けを行った場合は「片付け: worktree N 件・agmsg の名前 M 件・チーム K 件」の行も添える）

---

## 注意事項

- Plans.md が存在しない場合のみ新規作成。存在する場合は末尾に追記。**例外**: 「## ロードマップ進捗」セクション（Step 3.5）だけは追記ではなく上書き更新する（肥大化防止）
- ロードマップ関連の正本（`USER_GUIDE/ROADMAP.md` / `docs/MILESTONES.md`）を読み込むのは Step 3.5（と Step 3c の図示）のときだけ。セッション冒頭や他ステップで読み込まない（コンテキスト汚染防止）。判定（Step 3.5）自体は毎回行う
- 日報の内容はあくまで会話から推測するため、不明な場合は「（未記録）」と記載
- ユーザーが「なし」と答えた場合は Plans.md を更新しない
- 可視化HTML（`--visualize`）は Step 3 で「作成する」を選んだときのみ生成する。デフォルトは生成しない
- 可視化HTMLのテンプレートは `references/visualize-template.html`。スタイル（ダークテーマ・card/pill/box UI）を変更する場合はテンプレート側を直接編集する。CSS・構成の正本は `~/.claude/skills/visualize-common/references/`（style-guide.md / action-first.md / screenshot-embed.md）で、正本変更時はテンプレへ手動同期する
- 手作業TODO（Step 4.5）と可視化HTML（Step 3）は別物。前者は「ユーザー本人がやる残作業のチェックリスト」、後者は「このセッションで実装された内容のダッシュボード」。手作業が残っていなければ提案自体をスキップするが、**判定（Step 4.5）自体は毎回行う**
- 手作業TODOの生成は `manual-todo` スキルに委譲する（HTML の中身は shime 側で作らない）
