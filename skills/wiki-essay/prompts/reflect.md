# wiki-essay reflect モード — _inbox 申し送りを処理して wiki に還元する

`~/claude code/LLM_wiki/essays/_inbox/` に投げ込まれた `*_request.md`（申し送り文）を読み、
記述されたアクションを **提案→承認** 方式で vault に反映する。

## 引数

なし。`_inbox/` 配下を全件処理する。

## 🔴 鉄則

- **vault 書き込みは必ず提案→承認経由**（自動書き込み禁止、wiki-weave と同形式）
- **vault は git管理外で復元不可** — 失敗時のロールバックは試みない
- **承認されたアクションのみ適用**、却下分は変更しない
- **`questions.md` のフォーマット変動を検知したらユーザー確認**（regex 書き換えの脆弱性対策）
- **`_inbox/archive/` は永久保存**（古いものを自動削除しない）

---

## Phase 1: _inbox 走査

1. `~/claude code/LLM_wiki/essays/_inbox/` 配下の `*_request.md` を `Glob` で列挙（`archive/` 配下は除外）
2. **0件なら** 「処理待ちなし、クリーン終了」とユーザーに報告して終了
3. 各 request ファイルを Read

---

## Phase 2: アクション集約

各 request の構造（`templates/inbox_request.md` 参照）：
- frontmatter: `source`, `seeds_referenced`, `created`
- 本文: 「## このコラムの概要」「## wiki への依頼アクション」（チェックボックスリスト）

### 集約ロジック

すべての request からチェックボックスを抽出し、種類別にグルーピング:

| 種類 | パターン例 |
|------|----------|
| **seed status 更新** | `seed <slug> を <new-status> に` |
| **opinions/ 関連節への追記** | `[[opinions/<page>]] の「## 関連」にリンク追加` |
| **opinions/ 追加候補** | `新主張「<一文>」を opinions/ 追加候補として登録` |
| **concepts/ 収集 seed 化** | `引用した事実「<一文>」を concepts/ 収集 seed 化候補` |
| **その他** | 上記に当てはまらない自由記述 |

各アクションは `(request-file, action-type, payload, source-line)` のタプルで保持。

---

## Phase 3: 提案リスト提示 + 承認

`AskUserQuestion` でユーザーに以下の形式で提示:

```
## 提案アクション（_inbox 由来）

### seed status 更新（N件）
- [ ] <seed-slug>: <old> → <new>（出典: <request-file>）
- [ ] ...

### opinions/ 関連節への追記（N件）
- [ ] [[opinions/<page>]] ← essays/<コラム名>（出典: <request-file>）
- [ ] ...

### opinions/ 追加候補（N件、承認後に questions.md に登録）
- [ ] 「<新主張>」（出典: <request-file>）
- [ ] ...

### concepts/ 収集 seed 化（N件、承認後に questions.md に新規 seed）
- [ ] 「<引用事実>」（出典: <request-file>）
- [ ] ...
```

選択肢:
- すべて承認 / 一部承認（個別選択モードへ）/ すべて却下 / 提案リスト見直し

---

## Phase 4: 承認分の適用

### 4-1. seed status 更新

1. `~/Obsidian/LLM_Wiki/interests/questions.md` を Read
2. **フォーマット検証**: 該当 seed 行が `- [ ] (<domain>/P?/<status>) <問い>` 形式と一致するか正規表現で確認
   - **一致しない**（フォーマット変動）: ユーザーに「該当行が想定外フォーマット。手動更新してください」と通知してこのアクションだけスキップ
3. `status` 部分（`open` / `collecting` / `collected` / `covered`）を新値に置換
4. `collected` への変更なら `(収集日: YYYY-MM-DD)` も付記
5. `Edit` でファイル更新

### 4-2. opinions/ 関連節への追記

1. 対象 `~/Obsidian/LLM_Wiki/wiki/opinions/<page>.md` を Read
2. 「## 関連」セクションを探す
   - **あれば** その下に `- エッセイ: [[essays/<コラム名>]]` を追記
   - **なければ** ファイル末尾に `\n## 関連\n- エッセイ: [[essays/<コラム名>]]\n` を追加
3. 既に同じリンクがあれば重複追加しない（idempotent）
4. `Edit` でファイル更新

### 4-3. opinions/ 追加候補

`~/Obsidian/LLM_Wiki/interests/questions.md` の末尾付近に「## opinion 追加候補（reflect 由来）」セクションを作り（無ければ）、以下の形式で追記:

```
- [ ] 新主張: 「<一文>」 / 出典: <source-file>
```

実際の `opinions/<page>.md` ページ作成はユーザー判断（提案だけ残す）。

### 4-4. concepts/ 収集 seed 化

`~/Obsidian/LLM_Wiki/interests/questions.md` の「## 対話seed由来」セクションに追記:

```
- [ ] (<domain>/P3/open) <引用事実を問いに変換> — 出典: <source-file>
```

domain は source 記事の content から推定（不明なら `general` で登録）。

---

## Phase 5: archive 移送 + status 更新 + log

### 5-1. 処理済み request を archive へ

承認・処理が完了した request ファイルを `_inbox/archive/` に `mv`（Bash `mv` を使う）。
**却下された request はそのまま `_inbox/` に残す**（次回 reflect で再提案できるよう）。

### 5-2. `_seed_threads.md` の status 列更新

各 request の `seeds_referenced` を参照し、該当 seed セクションの該当行の `status` 列を最新化:
- seed が `covered` になった → 行末の status を `published` 相当に更新（実際の published は publish_queue で管理）
- 関連節への追記が完了 → 視覚的なマーカーは不要

### 5-3. log.md 追記

`~/Obsidian/LLM_Wiki/log.md` に1行追記:
```
## [YYYY-MM-DD] essay-reflect | <処理 request 数> requests, <承認アクション数> actions applied
```

---

## エラー処理

| 状況 | 動作 |
|------|------|
| `_inbox/` 0件 | クリーン終了 |
| request の frontmatter 不正 | そのファイルだけスキップ、ユーザーに報告 |
| `questions.md` フォーマット変動 | 該当アクションだけスキップ、ユーザーに通知 |
| 対象 opinions/concepts ページが見つからない | アクションを「未適用」として残し、ユーザーに報告 |
| 書き込み失敗 | 中断、その時点で承認済みのアクションは適用済みとして残す（ロールバックなし） |

## 完了確認

- 処理した request 数とアクション数をユーザーに報告
- 承認分が vault に反映、却下分は無変更
- 処理済み request が `_inbox/archive/` に移動
- 却下 request は `_inbox/` に残る
- `_seed_threads.md` の status 列更新済み
- `log.md` に1行追記済み
