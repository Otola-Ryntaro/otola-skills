---
name: first-action
description: Use when the user is starting a brand-new service/project from scratch and wants a complete 0→1 kickoff workflow. Triggers include "新しいサービスを作りたい", "こんなプロジェクトを始めたい", "/first-action", or presenting a fresh service idea in an empty directory. Orchestrates requirements brainstorming → GitHub recon → skill/MCP/agent scoring → docs/YYYY-MM-DD_First_definition.md → git init + my_first_commit → /ticket-gen → codex-second-opinion review loop (max 3 rounds, file-based) → /ko phased execution with /next per phase. Do NOT use for existing projects, partial features, debugging, or reviews of already-planned work.
---

# first-action

新規サービス・プロジェクトの「0→1 立ち上げ」を完全自動化するオーケストレーションスキル。
ユーザーがサービスアイデアを投げた瞬間から、要件定義 → 外部レビュー → 実装フェーズ開始までを一気通貫で走らせる。

## 前提依存（発動直後に確認する）

このスキルは以下のスキル・コマンドに依存する。**Phase 0 を始める前に**、利用可能な
スキル一覧にこれらが揃っているか確認し、欠けているものがあればユーザーに報告して
指示を仰ぐ（自己判断で代替しない）:

- `superpowers:brainstorming`（Phase 1）
- `find-skills`（Phase 3）
- `ticket-gen`（Phase 5）
- `codex-second-opinion`（Phase 6）
- `ko` / `next`（Phase 7）

確認と同時に、TodoWrite で Phase 0〜7 をタスク化してから開始する（7 フェーズの長丁場で
フェーズ飛ばし・実行忘れを防ぐ）。日付が必要な箇所（定義書ファイル名等）は推測せず
`date +%Y-%m-%d` を実行して取得する。

## 使用条件

### 発動する
- ユーザーが新サービス・新プロジェクトを始めたいと言う
- 空ディレクトリ or `.git` 未初期化のディレクトリで発話された
- `/first-action` が明示的に呼ばれた

### 発動しない
- 既存プロジェクトの機能追加・バグ修正・リファクタリング
- 単発の質問、デバッグ、コードレビュー
- 既に要件定義済みのプロジェクトの実装着手

## 全体フロー（7 Phase）

```
Phase 0: Preflight Gate
   ↓
Phase 1: Requirements (Plan Mode + superpowers:brainstorming)
   ↓
Phase 2: GitHub Recon (WebSearch)
   ↓
Phase 3: Skill/MCP/Agent Recommendation (find-skills + scoring)
   ↓ (ExitPlanMode)
Phase 4: docs/YYYY-MM-DD_First_definition.md + my_first_commit
   ↓
Phase 5: /ticket-gen
   ↓
Phase 6: codex-second-opinion レビューループ (最大 3 周)
   ↓
Phase 7: /ko + /next で段階実装
```

---

## Phase 0: Preflight Gate

**目的**: 誤って既存プロジェクトの上書きや意図しない初期化を防ぐ。

### 手順
1. `preflight.sh` を実行する。**相対パスではなく、スキル起動時に提示される
   スキルのベースディレクトリからの絶対パスで呼び出すこと**（CWD はユーザーの
   プロジェクトディレクトリであり、`scripts/preflight.sh` は CWD には存在しない）:
   ```bash
   bash "<スキルのベースディレクトリ>/scripts/preflight.sh"
   ```
2. 結果が `BLOCK:` で始まる場合、**ユーザーに明示確認してから続行**
3. プロジェクト名（ディレクトリ名から推定）とサービスアイデアの一行サマリをユーザーに確認

### Block 条件（preflight.sh）
- `.git` が既に存在
- `CLAUDE.md` / `package.json` / `pyproject.toml` / `Cargo.toml` など既存プロジェクトの痕跡
- カレントディレクトリに既にファイルが 5 個以上ある

ユーザーが「それでも続行」を選んだ場合のみ Phase 1 へ。

---

## Phase 1: 要件定義（Plan Mode + Brainstorming）

**目的**: Socratic 対話でサービス要件を言語化する。

### 手順
1. `EnterPlanMode` で Plan モードに入る。
   **EnterPlanMode ツールが利用できない環境では**、代替として「Phase 1〜3 の間は
   ファイルの作成・編集・コマンドによる状態変更を一切行わない」ことを自分に課して続行する
   （Plan モードの目的は Phase 3 終了までの読み取り専用保証なので、それを手動で守れば同等）。
2. `Skill` ツールで `superpowers:brainstorming` を起動
3. 以下の順に対話で掘り下げる:
   - **課題**: 誰のどんな痛みを解くか
   - **ユーザー**: 想定ユーザー像と現状の代替手段
   - **MVP**: 最小動作に必要な機能 / やらないこと（Out of scope）
   - **技術**: 希望スタック（未定なら Phase 3 で提案）
   - **非機能**: スケール / セキュリティ / 予算 / 期限
4. 回答を要件ドラフトとしてメモリ（書き出さない）に保持

Plan モードは **Phase 3 終了まで維持**。

---

## Phase 2: 既存リポジトリ調査

**目的**: 再発明を避け、良質な参考実装を要件に取り込む。

### 手順
1. 要件ドラフトから検索クエリを 3〜5 件生成（英語推奨）
2. `WebSearch` で GitHub / OSS を探索
3. 各候補を以下の観点でメモ:
   - License（MIT / Apache-2.0 / GPL 等）
   - 直近コミット（6 ヶ月以内が望ましい）
   - Stars / Forks
   - 要件一致度（どの部分が使えるか）
4. 上位 3 件を「参考リポジトリ」として保持

---

## Phase 3: Skill / MCP / Agent 推薦

**目的**: 利用可能な自動化資産を漏れなく検討し、スコアリングで絞り込む。

詳細は [references/scoring-criteria.md](references/scoring-criteria.md) を参照。
コンテキスト最適化（不要 MCP の disable）は [references/context-hygiene.md](references/context-hygiene.md) を参照。

### 手順
1. `Skill` ツールで `find-skills` を起動し、要件に合うスキルを探索
2. MCP 候補を列挙（Context7 / Magic / Sequential / Playwright / Serena / Morphllm / codex-cli / chrome-devtools 等）
3. サブエージェント候補を列挙（frontend-architect / backend-architect / database-optimizer / security-auditor / test-automator 等）
4. **各候補を 3 軸でスコアリング**:
   - マッチ度 (0–5)
   - 使用頻度期待値 (0–5)
   - 導入コスト（逆スコア 0–5）
5. 合計 10 点以上 → 「導入推奨」、7–9 点 → 「検討」、6 点以下 → 記録のみ
6. **導入スコープを明示**: 推奨リストの各項目に「project / global」のスコープを付ける。
   - **デフォルトは project**（`.claude/settings.local.json` での導入）
   - global にするのはユーザーが明示的に「グローバルで使いたい」と言った場合のみ
7. **Disable 候補リスト作成**: グローバルで有効だが今回のプロジェクトで使わない MCP を列挙し、Phase 4 で `disabledMcpjsonServers` に追記する素材として保持

---

## Phase 4: 定義書書き出し + my_first_commit

**ここで `ExitPlanMode` を呼び、実行フェーズに入る。**

### 手順
1. 定義書を書き出す
   - パス: `docs/YYYY-MM-DD_First_definition.md`（実行日の ISO 日付）
   - テンプレ: [references/templates/first-definition.md](references/templates/first-definition.md) をコピー＋埋め込み
2. `CLAUDE.md` を**分岐処理**で整備（詳細は下記「CLAUDE.md 取扱いルール」）
3. その他の基盤ファイルを生成
   - `.gitignore` ← [references/templates/gitignore](references/templates/gitignore)
   - `tasks/lessons.md`（空ファイル、1 行コメントのみ）
   - `docs/codex_review_log/.gitkeep`（空ファイル）
4. **`.claude/settings.local.json` を整備**（コンテキスト最適化）
   - Phase 3 の「Disable 候補リスト」を `disabledMcpjsonServers` に書き込む
   - Phase 3 で project スコープ導入と判定した MCP の有効化設定もここに集約
   - 詳細は [references/context-hygiene.md](references/context-hygiene.md) を参照
   - **書き込み前にユーザーに対象 MCP リストを提示し、最終確認を取る**
   - 既存の `permissions` などは保持し、設定をマージする（既存項目を消さない）
5. ユーザー領域ファイルの扱い
   - `memo.md` — **読み取り専用**。存在しても編集・削除しない
   - `Agent.md` — **読み取り専用**（Codex レビュー用指示書）。first-action は触らない
6. **トップ画像の作成（スキップ可）**
   - project-hero スキルを呼び出し、プロジェクトの英語名でヒーロー画像
     （`assets/hero.png`）を生成して README 冒頭に設置する
   - ユーザーが急いでいる場合・後回しにしたい場合はスキップし、
     「後で `/project-hero` で追加できる」と一言添える
7. 初回コミット
   ```bash
   git init
   git add .
   git commit -m "chore: my first commit"
   ```

### CLAUDE.md 取扱いルール

`CLAUDE.md` はグローバルベース部（ワークフロー・コア原則など）と `— ` 区切り以降の **`# Project-Specific Notes`** 部の二層構造。first-action は **Project-Specific Notes 以降のみを更新し、上段のグローバルベースには決して触らない**。

以下の 3 分岐で処理する：

**a) `CLAUDE.md` が存在しない**
→ [references/templates/claude-md.md](references/templates/claude-md.md) を丸ごとコピーし、`{{PROJECT_SUMMARY}}` 等のプレースホルダを Phase 1-3 の結果で置換して新規作成。

**b) `CLAUDE.md` が存在し、`# Project-Specific Notes` セクションが含まれる**
→ 当該セクション配下のみを Phase 1-3 の要件・参考リポジトリ・推奨 Skill/MCP/Agent で埋める。
→ 既に中身が埋まっている場合は **ユーザーに上書き確認**してから更新。

**c) `CLAUDE.md` が存在するが `# Project-Specific Notes` セクションがない**
→ ファイル末尾にセクションを**追記**（ユーザーに追記することを事前通知）。
→ 既存の上段は一切改変しない。

---

## Phase 5: チケット分割

### 手順
1. `Skill` ツールで `ticket-gen` を起動
2. 入力として定義書パス（`docs/YYYY-MM-DD_First_definition.md`）を渡す
3. ticket-gen の既存仕様に従い `docs/tickets/` 配下に Phase 分割されたチケットが生成される
4. **チケット出力をコミット**（git 履歴の整理）。
   出力先は決め打ちせず、**ticket-gen が完了報告で示した実際の出力先ディレクトリ**を add する:
   ```bash
   git add <ticket-gen が報告した出力先>
   git commit -m "chore: add tickets from /ticket-gen"
   ```
   - Phase 6 はファイル直接指定方式の `codex-second-opinion` を使うので、コミットは履歴整理目的のみ。

---

## Phase 6: Codex Adversarial Review ループ

**目的**: 要件とチケット構成を外部モデルに批判的レビューさせ、抜け漏れを潰す。

**使用ツール**: `codex-second-opinion` スキル（ファイル直接指定方式）。

### 採用理由（過去の試行と決定）
- `/codex:adversarial-review` プラグインは **diff ベース**で動作し、companion script 内で `git merge-base` を呼び出す。
- empty tree SHA (`4b825dc642cb6eb9a060e54bf8d69288fbee4904`) は **tree オブジェクトであって commit ではない**ため、`git merge-base` がエラーで失敗する。
- 単一コミット直後の「リポジトリ全体を対象にした批判レビュー」というユースケースは plugin の前提と噛み合わない。
- `codex-second-opinion` スキルは **ファイルパスを直接渡す設計**で、diff 不要。Phase 6 のような初期定義書レビューに適合する。
- `/codex:adversarial-review` は実装フェーズ（Phase 7 以降）の **コード差分レビュー**として後続利用可能。

### 手順（各 round）
1. `Skill` ツールで `codex-second-opinion` を起動
2. 入力: 定義書 (`docs/YYYY-MM-DD_First_definition.md`) + `docs/tickets/` 配下のファイル一式（パス指定で渡す）
3. レビュー観点を明示:
   - 要件の実現性・抜け漏れ
   - チケット粒度・依存関係・順序
   - MVP スコープの妥当性
   - 採用技術スタック・参考リポジトリの整合性
4. 出力を `docs/codex_review_log/round-N.md` に保存（N は 1, 2, 3）
5. 指摘を分類:
   - **major**: 要件定義 or チケットに反映（編集）
   - **minor**: `tasks/lessons.md` に追記
6. round 完了コミット: `chore: apply codex review round N`

### 終了条件
- `major 0 件` を達成 → Phase 7 へ
- **3 round 到達** → ユーザーに最終判断を委ねる（続行 or Phase 7 強行 or 中止）

---

## Phase 7: 段階実装（`/ko` + `/next`）

### 手順
1. `Skill` ツールで `ko`（Task Kickoff, Phase 対応）を起動
2. Phase 単位で作業を進める
3. 各 Phase 完了時に `Skill` ツールで `next` を起動し、進捗管理とコミット促進
4. ユーザーが `/shime` / `/nakajime` / セッション終了を宣言するまで継続

---

## 参照ファイル

- [references/scoring-criteria.md](references/scoring-criteria.md) — Phase 3 の 3 軸スコアリング詳細
- [references/context-hygiene.md](references/context-hygiene.md) — Project-First 原則と不要 MCP の disable 手順
- [references/templates/first-definition.md](references/templates/first-definition.md) — Phase 4 の定義書テンプレ
- [references/templates/claude-md.md](references/templates/claude-md.md) — プロジェクト用 CLAUDE.md 雛形
- [references/templates/gitignore](references/templates/gitignore) — デフォルト .gitignore
- [scripts/preflight.sh](scripts/preflight.sh) — Phase 0 ゲートチェック

## 原則

- **Plan モードは Phase 1–3 のみ**。Phase 4 以降は実行モード。
- **Project-First 導入原則**: MCP・スキル・プラグインの導入はプロジェクト単位（`.claude/settings.local.json`）が基本。グローバル（`~/.claude/`）への新規導入はユーザーが明示的に承認した場合のみ。詳細は [references/context-hygiene.md](references/context-hygiene.md)。
- **コンテキスト最適化**: グローバル有効でも今回のプロジェクトで使わない MCP は `disabledMcpjsonServers` で disable する。スキルは軽量（system-reminder のメタデータのみ）なので、明示要望がない限り disable しない。
- **CLAUDE.md のグローバルベース部（`— ` 区切りより上）には絶対に触れない**。編集対象は `# Project-Specific Notes` 以降のみ。
- **`memo.md` / `Agent.md` はユーザー領域 / Codex 領域**として読み取り専用。first-action は編集・削除しない。
- **Codex レビューの major は必ず反映**。minor は `tasks/lessons.md` に蓄積し次サイクルで消化。
- **各 Phase 完了時に進捗をユーザーに報告**（1–2 文）。
- 未知のコマンド・未登録スキルに遭遇したら **止まってユーザーに確認**。自己判断で代替しない。
