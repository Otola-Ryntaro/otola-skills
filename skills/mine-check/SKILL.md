---
name: mine-check
description: |
  大規模コード変更（リファクタ・全体エラー修正・セキュリティ修正・zero-design 改善等）の計画レポートを受け取り、過去事故・障害レポート・error-patterns との照合により「触ると壊れる地雷」を機械的にチェックするスキル。直接コード修正はせず、リスク評価レポートを生成して /ticket-gen に渡すための前段ゲートとして機能する。Codex Second Opinion による外部検証フェーズと、新規発見パターンを .claude/error-patterns/ に蓄積するフェーズを内包。
  発動条件:
  (1) /mine-check <レポートファイルパス> コマンド
  (2) 「地雷チェック」「過去エラー照合」「mine-check」「触ると壊れる場所」等のキーワード
  (3) zero-design / total-review / cto-audit / recon の直後に「ticket-gen 前のチェック」として
  使用しないケース: 単純なバグ修正・小規模変更・新規プロジェクト初期化（過去事故知識ベースが空）
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, Skill
---

# mine-check: 過去エラーパターン（地雷）重点チェック

大規模コード変更計画に対して、対象プロジェクトで過去に問題となったパターン（`.claude/error-patterns/`・`docs/problem_solved/`・`memory/feedback_*.md`。件数は実行時に実測する）と機械的に照合し、危険箇所と修正提案をレポート化する。`/codex:adversarial-review` の commit 差分制約を回避する 3 ルート fallback を内蔵。

## 起動時の必須手順

**スキル発動直後、引数の有無を確認:**

- 引数あり（レポートパス）: そのまま Phase A から開始
- 引数なし: `git diff --name-only HEAD~1..HEAD` でスコープ自動抽出 → fallback モードで Phase A から開始

**直接ファイル編集はしない。** 出力は `codex/YYYYMMDD_mine_check_report.md` のみ。コード修正は /ticket-gen → 実装フェーズで行う。

## 設計原則（4 原則を厳守）

1. **知識ソース単一化**: `<project>/.claude/error-patterns/INDEX.md` を SSOT とし、Phase A で必ず全件読み込む
2. **多重照合**: 1 地雷あたり最低 2 つの検出手法（grep + git log、grep + doc 参照 等）を必ず併用
3. **誤検知許容**: false positive を恐れず疑わしきは Warning として報告。判断はユーザー / Codex に委ねる
4. **新規パターン蓄積義務**: Phase F で発見した新規地雷は `.claude/error-patterns/` に登録（ci-fix Phase 7b と同じ流儀）

---

## Phase A: 知識ベース読込み（決定論的・全件必読）

以下を **すべて Read** する。読み忘れは設計違反。

### A-1. プロジェクトの error-patterns

```
<project>/.claude/error-patterns/INDEX.md
<project>/.claude/error-patterns/*.md  (Glob で全件取得)
```

**Fallback**: `.claude/error-patterns/` が存在しないプロジェクトでは、A-2 の known_landmines.md のみで照合を続行し、レポート冒頭に「プロジェクト知識ベースなし（error-patterns 未整備）」と明記する。エラーで停止しない。

### A-2. 本スキル付属の地雷カタログ

```
references/known_landmines.md  (12 カテゴリの照合表)
references/grep_patterns.md    (検出 grep カタログ)
```

### A-3. プロジェクト固有の禁忌

```
<project>/CLAUDE.md
  → 「Never」「禁忌」「絶対にやらないこと」等の禁止事項セクションを検出して読む
    （セクション名はプロジェクトごとに異なる。契約・不可侵領域系のセクションも含める。
     例: kuchikomi_maker の「患者アクセス URL 契約」）
```

### A-4. memory（過去事故の教訓）

```
~/.claude/projects/<現プロジェクトの slug>/memory/MEMORY.md
  → slug はカレントプロジェクトの絶対パスの "/" を "-" に置換したもの
    （例: /Users/you/projects/myapp → -Users-you-projects-myapp）
  → feedback_*.md エントリのリンク先（必要に応じて Read）
  → MEMORY.md が存在しない場合はスキップし、レポートに「memory なし」と明記
```

### A-5. 入力レポート本体

引数で渡されたレポートファイルを Read。

---

## Phase B: スコープ抽出

入力レポートから以下を抽出（LLM 解析）:

- **対象ファイル一覧**: 明示記載のパス + glob パターン（例: `app/middleware*`, `prisma/schema/**`）
- **変更領域カテゴリ**: middleware / DB / migration / auth / payment / API / CI / バックグラウンドジョブ / 他（プロジェクト固有領域も追加してよい。例: kuchikomi_maker なら patient flow / inngest）
- **依存ライブラリ変更**: package.json 言及の有無
- **作業規模**: 改善項目数、Phase 数、推定影響範囲

抽出結果はメモリ内に保持（`scopes.json` 相当の構造）。

---

## Phase C: 既知パターン照合（多重照合）

`scripts/scan_mines.sh` を起動し、Phase B のスコープに対して全カテゴリの grep を一括実行 → JSON 出力を受け取る。

```bash
bash scripts/scan_mines.sh --project-root <PROJECT_ROOT_ABS_PATH>
```

その後、各カテゴリで **2 つ目の検出手法** を LLM が手動実行（コンテキスト読み・git log・doc 照合）。

照合カテゴリ詳細は `references/known_landmines.md` を必読。

### 判定基準

| 判定        | 条件                                                                 |
| ----------- | -------------------------------------------------------------------- |
| 🚨 Critical | 過去に本番事故を引き起こしたパターンに完全一致、または複数手法で検出 |
| ⚠️ Warning  | 1 手法で検出、過去パターンに類似、要人間確認                         |
| ℹ️ Info     | 周辺領域への変更、参考情報レベル                                     |

**疑わしきは Warning に倒す**（false negative より false positive を許容）

---

## Phase D: リスク評価レポート生成

出力先: `codex/YYYYMMDD_mine_check_report.md`（YYYYMMDD は `date +%Y%m%d`）

レポート構造:

```markdown
# Mine Check Report — YYYYMMDD

**入力**: <元レポートパス>
**スコープ**: N ファイル / M カテゴリ
**照合済みパターン**: error-patterns/ <実測 N> 件 + known_landmines.md <実測 M> 件 = <合計> 件（実行時に Glob で実測した件数を記載）
**ヒット**: Critical X 件 / Warning Y 件 / Info Z 件

---

## 🚨 Critical（着手前に必ず対応）

### [LM-001] <地雷名>

- **検出箇所**: `<file:line>`
- **過去事故**: `docs/problem_solved/YYYYMMDD_*.md` または `error-patterns/<slug>.md`
- **検出根拠**:
  - 手法 1: <grep ヒット内容>
  - 手法 2: <doc 照合結果 / git log 結果>
- **推奨修正**: <具体的なコード変更指針>
- **チケット候補**: `<PREFIX>-NN_<slug>`

## ⚠️ Warning（要確認）

### [LM-005] <地雷名>

（Critical と同形式、ただし「要人間確認」を強調）

## ℹ️ Info（参考情報）

### [LM-009] <地雷名>

（参考レベル）

---

## 📊 照合済みパターン一覧

| ID     | カテゴリ            | 検出   | 備考              |
| ------ | ------------------- | ------ | ----------------- |
| EP-001 | Prisma 破壊コマンド | ✅ Hit | LM-001 として報告 |
| EP-002 | middleware Prisma   | —      | スコープ外        |
| ...    |

---

## 🆕 新規発見パターン候補（Phase F でユーザー確認）

- (なし) または以下の候補:
  - **<slug>**: <one-liner>
    - 検出根拠: ...
    - 蓄積価値: high / medium / low

---

## 🤖 Codex Second Opinion 結果

（Phase E で記入。未実行時は「Phase E 未完了」と明記）

---

## ✅ 次のステップ

1. 本レポートをユーザーが確認
2. `/ticket-gen codex/YYYYMMDD_mine_check_report.md` でチケット化
3. チケット実装フェーズへ
```

---

## Phase E: Codex Second Opinion（3 ルート fallback）

**目的**: LLM 単体の見落とし・過剰検知を別モデルで検証。`/codex:adversarial-review` の commit 差分制約を回避する。

### ルート判定ロジック（必ず順番に評価）

```
1. git status --porcelain で working-tree の状態を取得
2. デフォルト = ルート 1（MCP 直接呼び出し）を採用
   ※ commit 差分制約に依存しないため、最も汎用的
3. 例外条件: working-tree clean かつ Critical >= 1 件
   → ルート 2（/codex:adversarial-review）で深堀りレビュー
4. ルート 1 / 2 が失敗（API エラー、タイムアウト、空レスポンス）
   → ルート 3（/codex:second-opinion）にフォールバック
5. 全ルート失敗 → ユーザーに通知し Phase F へ進む（手動確認推奨）
```

### ルート 1: MCP 直接呼び出し（デフォルト・推奨）

`mcp__codex-cli__codex` ツールを使う。プロンプトに **レポート全文 + 知識ベース要約** を埋め込む。

詳細プロンプト雛形・呼び出し方は `references/codex_review_strategy.md` を必読。

### ルート 2: /codex:adversarial-review

```
Skill(skill: "codex:adversarial-review")
Args: --wait --scope working-tree
フォーカス: 本レポートの Critical 判定の妥当性、見落とし、過剰検知
```

### ルート 3: /codex:second-opinion（軽量フォールバック）

```
Skill(skill: "codex:second-opinion")
Args: <レポートパス> + 評価観点
```

### 結果反映

レビュー結果をレポートの「🤖 Codex Second Opinion 結果」セクションに追記:

- 同意した Critical: [LM-XXX]
- 反対する Critical: [LM-XXX] + 理由
- 追加すべき Critical/Warning: [LM-NEW] + 検出根拠
- 蓄積反対の新規パターン: ...

**Critical の追加・削除があった場合は Phase F でユーザーに必ず通知**。

---

## Phase F: ユーザー確認 + 新規パターン蓄積

### F-1. レポート提示

完成したレポートのパスをユーザーに提示し、要約（Critical 件数、Warning 件数、新規パターン候補数）を 1 行で示す。

### F-2. 新規パターン蓄積（必須・スキップ不可）

新規発見パターン候補がある場合:

1. ユーザーに候補リストを提示し、蓄積するもの／しないものを確認
2. 蓄積するものについて、`references/new_pattern_template.md` の形式で `<project>/.claude/error-patterns/<slug>.md` にドラフトを Write
3. ユーザー承認後、`<project>/.claude/error-patterns/INDEX.md` のテーブル末尾に 1 行追加（Edit）
4. 確定したら現セッション内で完結

候補なしの場合: 「新規パターンなし」と明示。

### F-3. 次ステップ案内

```
✅ Mine Check レポート生成完了
  Critical: X 件 / Warning: Y 件 / Info: Z 件
  新規パターン蓄積: N 件 (.claude/error-patterns/ に登録済み)

次のステップ:
  /ticket-gen codex/YYYYMMDD_mine_check_report.md
```

---

## 参考実装ファイル（実装/メンテ時の参照）

- 既存スキルの流儀: `~/.claude/skills/ci-fix/SKILL.md` (Phase 1c, 7b)
- migration-check の Check 構造: `~/.claude/skills/migration-check/SKILL.md`
- ticket-gen の入力形式: `~/.claude/skills/ticket-gen/SKILL.md`
- codex-second-opinion の呼び方: `~/.claude/skills/codex-second-opinion/SKILL.md`
- 過去事故レポート全件: `<project>/docs/problem_solved/`
