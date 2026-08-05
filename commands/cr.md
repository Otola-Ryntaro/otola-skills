# Code Review

現在の変更に対してコードレビューを実施します。

## レビュー対象

$ARGUMENTS が指定されている場合はその範囲のみ。指定がない場合は直近の変更（未コミットの差分）全体を対象とする。

## レビュー手順

### Phase 1: Claude 自己レビュー（必須）

1. `git diff` で差分を取得する（コミット済みの場合は `git diff HEAD~1`）
2. 以下の観点でレビューする:
   - **Critical**: セキュリティ脆弱性、データ損失リスク、本番障害の可能性
   - **Major**: ロジックバグ、パフォーマンス問題、型安全性の欠如
   - **Minor**: コードスタイル、命名、可読性
3. 指摘事項を重大度別にテーブルで整理する

### Phase 1.5: Spec Compliance Check（`--spec <ticket-path>` 指定時のみ）

**役割:** チケットの受け入れ条件と実装 diff を照合し、missing / extra / misunderstanding を検出する。
superpowers の spec-reviewer subagent を軽量化したインライン版。

**手順:**

1. 指定チケットファイルを Read し、以下を抽出:
   - 「受け入れ条件」セクションのチェックボックス項目
   - 「作業内容」セクションの作業項目
   - 「対象ファイル」セクションの想定ファイル
2. `git diff`（または `git diff HEAD~N`）で実装範囲の差分を取得
3. 受け入れ条件 1 件ずつを diff と照合し、以下のテーブルに整理:

   ```markdown
   ## Spec Compliance Check

   ### 受け入れ条件 vs 実装

   | # | 受け入れ条件 | 実装場所 | ステータス |
   |---|------------|---------|----------|
   | 1 | レート制限を 100req/min に設定 | lib/rate-limit.ts:42 | ✅ 充足 |
   | 2 | テストを追加 | （未実装） | ❌ Critical 欠落 |
   ```
4. **Spec 外の追加実装**を検出（対象ファイルにない変更）:

   ```markdown
   ### Spec 外の追加実装
   - `lib/zzz.ts`: 受け入れ条件にない機能（要確認: 不要か、別チケット化）
   ```
5. **Misunderstanding（受け入れ条件と実装の解釈差）**を検出:
   - 例: 受け入れ条件「JWT を使用」、実装: セッション Cookie → ❌ Misunderstanding

**重大度判定:**

- 受け入れ条件の missing → **Critical**（必ず修正）
- spec 外の追加実装 → **Major**（要確認）
- 解釈の差異 → **Critical** または **Major**（影響範囲による）

**Critical ゼロ保証ルール**: 既存ルールが Spec compliance check の結果にも適用される（Critical=0 まで修正→再確認のループ）。

### Phase 1.7: Root-Cause 分析（Critical / Major のバグ系指摘に必須）

**役割:** 症状パッチを防ぎ、根本原因側に修正を出させる品質層。goal-feed の「本質修正を最優先」思想を日常導線に降ろしたもの。

Phase 1 / 1.5 で検出した Critical・Major のうち**バグ系**（ロジックバグ、データ不整合、セキュリティ、本番障害系）の指摘それぞれに、以下3点を1行ずつ明記する:

| 項目 | 内容 |
|------|------|
| 症状 | 何が起きる/起きうるか |
| 根本原因 | なぜ起きるか（症状の発生箇所ではなく原因の発生箇所） |
| 防壁分析 | なぜ既存の防壁（テスト・型・レビュー・lint）で捕まらなかったか |

- **修正案は根本原因側に出す**。症状箇所だけを塞ぐ diff（例: null チェック追加だけで null の混入源を放置）は**それ自体を Critical 相当として扱い**、根本原因への修正を提案する
- 再現可能なバグは `superpowers:systematic-debugging` スキルの呼び出しを推奨する（再現→仮説→最小修正→回帰確認の型）
- スタイル・命名等の非バグ指摘には適用しない（過剰分析を避ける）

### Phase 2: セカンドオピニオン（選択制）

以下の手段から状況に応じて選択する。フラグ指定がない場合はデフォルト（A）を使用する。

| 手段                                            | ツール                               | 適用場面                                 | トークンコスト        |
| ----------------------------------------------- | ------------------------------------ | ---------------------------------------- | --------------------- |
| **A. harness-review** (デフォルト)              | `/harness-review code` スキル        | 4観点構造化レビュー + verdict判定        | 低（Claude内部）      |
| **B. Claude サブエージェント** (`--subagent`)   | `superpowers:code-reviewer` Agent    | harness外の軽量レビュー                  | 低（Claude内部）      |
| **C. Codex プラグインレビュー** (`--codex`)     | `/codex:review` コマンド             | OpenAI モデルによるセカンドオピニオン    | 高（OpenAI トークン） |
| **D. Codex 設計挑戦レビュー** (`--adversarial`) | `/codex:adversarial-review` コマンド | 設計判断・トレードオフを問う深いレビュー | 高（OpenAI トークン） |
| **E. Codex MCP直接** (`--codex-mcp`)            | `mcp__codex-cli__review` MCP ツール  | コミット/ブランチ指定の軽量レビュー      | 高（OpenAI トークン） |
| **F. スキップ** (`--skip-so`)                   | なし                                 | ドキュメントのみ・軽微な変更             | なし                  |

#### A. harness-review（デフォルト）

**可用性チェック（先に実行）**: `.claude/settings.json` の `enabledPlugins` で claude-code-harness が有効化されているか確認する。無効なプロジェクトでは手段 B（`--subagent` 相当）に自動フォールバックし、その旨を1行報告する。

`/harness-review code` を実行し、構造化レビューを行う。

- Security / Performance / Quality / Accessibility の4観点
- severity判定（critical/major/minor/recommendation）と **APPROVE / REQUEST_CHANGES** の verdict 出力
- REQUEST_CHANGES の場合、`harness-work` と連携して自動修正→再レビュー（最大3回）

#### B. Claude サブエージェント（`--subagent`）

`superpowers:code-reviewer` サブエージェントを起動し、差分をレビューさせる。

- Claude のコンテキスト内で完結するため、外部トークン消費なし

#### C. Codex プラグインレビュー（`--codex`）

**重要: `mcp__codex-cli__review` MCP ツールを直接呼ばないこと。必ず Skill ツールで `/codex:review` を呼ぶ。**

```
Skill ツールを使用:
  skill: "codex:review"
  args: "--wait"
```

- Skill ツール経由で `/codex:review` プラグインコマンドを実行する
- `--wait` でフォアグラウンド実行（結果を待つ）
- 出力はそのまま表示する（要約・改変しない）
- Codex プラグインが利用不可の場合のみ `mcp__codex-cli__review`（手段E）にフォールバック

#### D. Codex 設計挑戦レビュー（`--adversarial`）

**重要: 必ず Skill ツールで `/codex:adversarial-review` を呼ぶ。**

```
Skill ツールを使用:
  skill: "codex:adversarial-review"
  args: "--wait"
```

- 通常レビューより深く、設計判断・トレードオフ・前提条件を問う
- 実装の正しさだけでなく「このアプローチが正しいか」を検証する
- アーキテクチャ変更・大型リファクタリング時に推奨

#### E. Codex MCP直接（`--codex-mcp` 指定時のみ）

`--codex-mcp` フラグが**明示的に指定された場合のみ** `mcp__codex-cli__review` MCP ツールを直接呼び出す。
`--codex` フラグでは絶対に MCP ツールを呼ばないこと。

- `commit` パラメータでコミットSHA指定が可能
- `base` パラメータでブランチ比較が可能
- `uncommitted: true` でワーキングツリーレビュー
- プラグインなしでも MCP サーバーがあれば利用可能

#### F. スキップ（`--skip-so`）

ドキュメントのみの変更や軽微な修正の場合、Phase 2 をスキップする。

### Phase 3: 結果統合と報告

以下の形式で統合レポートを出力する:

```
## Code Review Report

### Critical (即時修正必須)
| # | ファイル | 行 | 指摘元 | 内容 |
|---|---------|-----|--------|------|

### Major (修正推奨)
| # | ファイル | 行 | 指摘元 | 内容 |
|---|---------|-----|--------|------|

### Minor (任意)
| # | ファイル | 行 | 指摘元 | 内容 |
|---|---------|-----|--------|------|

指摘元: 🧠 Claude / 🤖 Codex / 🧠🤖 両方 / 🔍 SubAgent
```

### Phase 3.5: レビュー記録の追記（`--spec <ticket>` 指定時のみ必須）

レビュー完了後（Critical=0 到達後）、該当チケットファイルの**末尾**に以下を追記する。
/next の完了判定・reconciler がこの記録を一次ソースとして参照する（会話コンテキストに頼らない、セッション跨ぎ対応）。

```markdown
## レビュー記録

- YYYY-MM-DD HH:MM `/cr --spec` 実行: verdict APPROVE / Critical 0 / Major N / spec 充足 M/M
- 実行した検証: `npm test` ✅ / `npm run typecheck` ✅（実行したものを列挙）
```

- 既に「レビュー記録」セクションがあれば行を追記する（上書きしない）
- 素の /cr（`--spec` なし）は追記先チケットがないため対象外

## Critical ゼロ保証ルール（必須）

**Critical 指摘が1件以上ある場合、以下を必ず実行する:**

1. Critical 指摘の修正案を提示する
2. ユーザーに修正の実施を提案する
3. 修正後、再度レビューを実施し、Critical がゼロになったことを確認する
4. Critical がゼロになるまでこのサイクルを繰り返す

**レビュー完了の条件**: Critical = 0 であること。Critical が残っている状態で「レビュー完了」と報告してはならない。

## 再発防止の還流（Critical 修正完了後）

Critical 指摘の修正が完了したら、再発可能性のあるパターン（同種のコードが他所にもある／将来また書きそうなミス）かを判定し、該当する場合は `.claude/error-patterns/` への蓄積を**ユーザーに提案**する（mine-check Phase F-2 と同形式・同テンプレート）。

- 対象: Phase 1.7 で根本原因まで特定できたバグ系 Critical
- 提案内容: パターン名（slug）、1行説明、検出方法（grep パターン等）、根本原因の要約
- ユーザー承認後に `<project>/.claude/error-patterns/<slug>.md` を作成し、`INDEX.md` に1行追加
- `.claude/error-patterns/` が存在しないプロジェクトでは、作成するかどうかから確認する
- 一度きりのミス・プロジェクト固有すぎるものは蓄積しない（ノイズ防止）

## 使用例

```
/cr                      → Claude自己レビュー + harness-review（4観点構造化）
/cr --subagent           → Claude自己レビュー + superpowers:code-reviewer
/cr --codex              → Claude自己レビュー + Codex プラグインレビュー
/cr --adversarial        → Claude自己レビュー + Codex 設計挑戦レビュー
/cr --codex-mcp          → Claude自己レビュー + Codex MCP直接レビュー
/cr --skip-so            → Claude自己レビューのみ
/cr --codex --base main  → main ブランチとの差分を Codex でレビュー

# Spec compliance check（チケット駆動の品質ゲート）
/cr --spec docs/tickets20260321/SEC-001.md           → self + spec + harness（デフォルト）
/cr --spec docs/tickets20260321/SEC-001.md --codex   → self + spec + Codex
/cr --spec docs/tickets20260321/SEC-001.md --skip-so → self + spec のみ（外部レビューなし）
```

> **/ko --strict 自動連携**: strict モードで実行されたチケットの完了時、`/ko` は自動で `/cr --spec <ticket-path>` を呼び出します。
