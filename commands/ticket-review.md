# Ticket Review: Codex セカンドオピニオンによる計画品質ゲート

ticket-gen で生成したチケット計画を、OpenAI Codex の第三者視点で厳しく評価し、
Major 以上の指摘が出なくなるか最大ラウンドに到達するまで修正ループを回す。

> ticket-gen の Phase 5 を独立コマンド化したもの。
> 単独実行可、ticket-gen 完了後の任意ステップとしても呼び出せる。

## 引数

```
/ticket-review <tickets-dir>             → 対象 tickets ディレクトリを指定
/ticket-review <tickets-dir> --rounds 5  → 最大ラウンド数指定（デフォルト 3）
/ticket-review <tickets-dir> --no-review → 即終了（スキップ報告のみ）
```

`<tickets-dir>` の例: `docs/tickets20260321/` または `docs/tickets20260321_refactor/`

---

## Step 0: 事前準備

1. 引数から tickets ディレクトリパスを取得（必須）
2. 対象を列挙:
   - `<tickets-dir>/ticket_index.md`（必須、なければエラー終了）
   - `<tickets-dir>/{PREFIX}-*.md`（全チケット）
   - 元レポート: ticket_index.md の冒頭または「元レポート」セクションから取得
   - 要件定義書: `docs/*_First_definition.md` が存在する場合
3. `docs/codex_review_log/` ディレクトリを作成（既存なら再利用）
4. 既存の `round-*.md` があれば最大番号を確認し、続きの番号から開始

`--no-review` 指定時はここで終了し、「Codex レビュー: スキップ（--no-review 指定）」を報告する。

---

## Step 1: レビュー実行ループ

`round = 開始番号` から開始し、以下を繰り返す。

### ステップ A: Codex に投げる

`Skill(skill: "codex-second-opinion")` を呼び出し、以下の args を渡す:

```
/codex:adversarial-review --wait --scope working-tree
以下の観点で、チケット計画がユーザーの実装目標を達成できるかを厳しく評価してください。
対象: <tickets-dir> 配下の ticket_index.md と全チケット + 元レポート。

評価観点:
1. カバレッジ: 元レポート/要件定義書の要求がすべてチケットに落ちているか。抜け漏れはないか。
2. 実装可能性: 各チケットの「作業内容」「対象ファイル」「受け入れ条件」が、
   実装者が迷わず着手できる粒度まで具体化されているか。
3. 粒度: 1 チケット = 1 セッションで完了可能か（過大/過小はないか）。
   Phase サイズも確認（1 Phase 4〜5 チケット以内か。超過は /ko の並列容量を圧迫する）。
4. 依存・順序: Phase 順序がチケット間の依存関係と整合しているか。
5. リスク: セキュリティ・データ安全・後方互換・OAuth/スコープ等の見落としはないか。
6. 矛盾: チケット間・要件定義書との矛盾や重複はないか。

出力は必ず以下の見出し構造で:
## Verdict
approve / approve with revisions / reject のいずれか
## Critical findings
（なければ「なし」）
## Major findings
（なければ「なし」）
## Minor findings
（なければ「なし」）
## Recommended changes per ticket
チケット ID ごとに、何をどう修正すべきか具体的に記述
```

### ステップ B: 結果保存

Codex の応答全文を `docs/codex_review_log/round-{N}.md` に保存。フロントマター:

```markdown
# Codex Adversarial Review — Round {N}

**実行日**: YYYY-MM-DD HH:MM
**対象**: <tickets-dir>/ticket_index.md + 配下全チケット + 元レポート
**手段**: codex-second-opinion スキル経由
**Verdict**: {Codex が返した verdict}

---

{Codex の本文全文をそのまま貼り付け}

---

## 対応内容（ラウンド終了後に記載）

（チケット修正の差分サマリ。ループ終了時に残すこと）
```

### ステップ C: Major 以上の指摘カウント

保存したレポートから、**Critical + Major の合計件数**を数える（以降「Major 以上件数」と呼ぶ）。

- パース方針: `## Critical findings` / `## Major findings` セクション配下の見出し（例: `### C-1)` / `### M-1)`）または箇条書き項目を数える。「なし」と明記されていれば 0 件。
- 曖昧な場合は **多めにカウント**（false positive 側に倒す）。

### ステップ D: 判定

| 条件 | 動作 |
|------|------|
| Major 以上件数 = 0 | ループ終了、Step 2 へ進む |
| Major 以上件数 > 0 かつ round < 最大ラウンド | ステップ E（修正）→ round += 1 → ステップ A へ戻る |
| Major 以上件数 > 0 かつ round == 最大ラウンド | ループ強制終了、残指摘を Step 3 完了報告で「未解消 Major」として報告 |

### ステップ E: チケット修正

Codex の `Recommended changes per ticket` を参照し、`Edit` で該当ファイルを修正:

- **カバレッジ不足** → 新規チケット追加（既存最大番号 + 1）、index の Phase 表・凡例を更新
- **粒度過大** → 1 チケットを 2 つ以上に分割、index の Phase 表を再構成
- **粒度過小** → 複数チケットを統合
- **受け入れ条件不明瞭** → 該当チケットの受入条件セクションを書き直し
- **Phase 順序誤り** → index の Phase 表でチケットを移動、依存関係コメントを更新
- **セキュリティ/データ安全指摘** → 該当チケットに MIGRATION-CHECK 相当の注意書き or 新規ガードチケット追加

修正が完了したら、当該 `round-{N}.md` 末尾の「対応内容」セクションに:
- 修正したチケット ID とファイル
- どの指摘に対応したか（C-1, M-2 等の指摘番号で参照）
- 未対応の指摘があればその理由

を記録する。

---

## Step 2: ループ終了後

- 全ラウンドの概要を `docs/codex_review_log/summary.md` に追記:

  ```markdown
  # Codex Review Summary — <tickets-dir>

  | Round | 実行日 | Verdict | Critical | Major | Minor | 対応状況 |
  |-------|--------|---------|----------|-------|-------|---------|
  | 1 | YYYY-MM-DD | approve with revisions | 4 | 6 | 3 | 修正済み |
  | 2 | YYYY-MM-DD | approve | 0 | 0 | 2 | 完了 |

  **最終ステータス**: ✅ Major 以上 0 件で終了 / ⚠️ 最大ラウンド到達、残 Major N 件
  ```

- **ticket_index.md に実行記録を追記**: 「## 実行記録」セクション（無ければ作成）に以下を 1 行追記する。
  `/ko` の 🔒 Wave 警告と `/next` がこの記録を一次ソースとして参照する:

  ```markdown
  - 計画レビュー: ✅ round N 完了 / YYYY-MM-DD / 残 Major X 件
  ```

- 残 Major がある場合は Step 3 完了報告で明示し、ユーザーに追加ラウンド実行 or 残指摘を許容して先に進むか判断を仰ぐ

---

## Step 3: 完了報告

```
## /ticket-review 完了

**対象**: <tickets-dir>
**総ラウンド数**: N 回（最大 {最大ラウンド}）
**最終ステータス**: ✅ Major 以上 0 件で終了 / ⚠️ 最大ラウンド到達、残 Major N 件

### レビューログ
- `docs/codex_review_log/round-1.md` 〜 `round-N.md`
- `docs/codex_review_log/summary.md`

### 主な指摘と対応
（Critical/Major の要約を 3〜5 項目、対応済みかどうか併記）

### 未解消の Major（あれば）
- 指摘内容と理由を列挙
- ユーザーに追加対応の可否を確認

### 次のアクション
- 計画 OK なら: `/ko <tickets-dir>/ticket_index.md Phase 1`
- 残 Major を処理するなら: `/ticket-review <tickets-dir> --rounds {追加}`
```

---

## エラー処理

- **codex-second-opinion が未インストール / 利用不可**: 警告を表示してレビューをスキップ。完了報告に「Codex レビュー: スキップ（理由）」と記載
- **Codex 応答が空/不明瞭**: そのラウンドを「Verdict: inconclusive」として保存し、Major 以上 0 件と同等に扱ってループ終了（人手レビュー誘導）
- **ユーザー割り込み**: 現ラウンドまでの結果を保存して中断を許可
- **tickets ディレクトリが見つからない**: 引数誤りとしてエラー終了

---

## 関連コマンド

- `/ticket-gen <レポート>` — チケット生成（前段）
- `/ko <ticket_index.md> Phase N` — 計画 OK 後の実装
- `/ticket-verify <tickets-dir>` — 全完了後の実装検証

---

> 使い方: `/ticket-review docs/tickets20260321/`
