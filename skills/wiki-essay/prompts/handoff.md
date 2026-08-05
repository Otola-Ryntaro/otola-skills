# wiki-essay handoff モード — 完成記事から相手拠点向け申し送り文を生成

完成したコラム/エッセイから、相手拠点の `_inbox/` に投函する `_request.md`（申し送り文）を生成する。
セッションを越境せず、ファイルだけで疎結合に連携するための要。

## 引数

- `<file>` — **必須**。完成記事の絶対パスまたは相対パス（拡張子 .md）

未指定なら `AskUserQuestion` で対象ファイルを確認。

## 🔴 鉄則

- **承認なしには相手拠点に投函しない**（提案→承認の原則）
- **拠点判定はファイルパスで優先**（pwd は補助情報）
- **frontmatter なしの旧形式コラムも扱える**（コラム/ 既存テーマ群の retrofit 用途）

---

## Phase 1: 対象ファイルと拠点判定

### 1-1. ファイル Read

1. 引数の `<file>` を Read
2. 存在しなければエラーで中断
3. ファイル本文と（あれば）frontmatter を保持

### 1-2. 拠点判定

ファイルの絶対パスから発拠点と相手拠点を決定:

| ファイルパスの場所 | 発拠点 | 相手拠点 | 投函先 |
|------------------|--------|---------|--------|
| `~/claude code/コラム/...` 配下 | A (コラム/) | B (LLM_wiki/essays/) | `~/claude code/LLM_wiki/essays/_inbox/` |
| `~/claude code/LLM_wiki/essays/...` 配下 | B (LLM_wiki/essays/) | A (コラム/) | `~/claude code/コラム/_inbox/` |
| `~/claude code/LLM_wiki/X_book/...` 配下 | X_book | B (LLM_wiki/essays/) | `~/claude code/LLM_wiki/essays/_inbox/` |
| その他 | 不明 | — | `AskUserQuestion` で「どちらの拠点に投函するか」を確認 |

pwd は補助参考のみ（`Bash pwd` で取得）。

---

## Phase 2: 抽出（seed / references / 概要）

### 2-1. frontmatter ありの場合（LLM_wiki/essays/ 発が想定）

frontmatter から以下を取得:
- `seed:` → `seeds_referenced` の主要 seed
- `references:` → そのまま使う（[[wikilink]] 配列）
- 本文の `[[wikilink]]` も追加で grep してマージ（重複除外）

### 2-2. frontmatter なしの場合（コラム/ 既存ファイル想定）

1. ファイル本文から `[[...]]` を全て grep → `references` 候補
2. 本文冒頭の見出しや内容から seed を LLM 推論
   - `~/Obsidian/LLM_Wiki/interests/questions.md` を Read して候補一覧を取得
   - 内容と最も適合する seed を 1〜3案提示 → `AskUserQuestion` で確認
   - 該当なしなら「新規 seed 候補」として扱う（reflect 側で登録される）

### 2-3. 概要生成

本文を読み、200字程度に要約。

- 主張・論拠の核を捉える
- 客観的なトーン（reflect モードのユーザーが内容を判断する材料）
- 一文目に「このコラムは〇〇を論じている」と立てる

---

## Phase 3: 申し送り文の組み立て

### 3-1. テンプレ取得

`~/.claude/skills/wiki-essay/templates/inbox_request.md` を Read してテンプレ取得。

### 3-2. アクション候補の LLM 推論

「## wiki への依頼アクション」のチェックボックス候補を以下の観点で生成:

1. **seed status 更新候補**: 参照 seed の現在 status が `open` / `collecting` の場合 → `covered` 提案
2. **関連節への wikilink 追加**: 各 references の wiki ページに対して「## 関連にこのコラムへのリンク追加」を提案
3. **opinions 追加候補**: 本文に「強い主張」と判定できる一文があれば、それを opinion 化候補として提案（LLM 推論で1〜3件）
4. **concepts 収集 seed 化候補**: 本文中の引用事実・統計・概念で、既存 wiki/concepts/ に無さそうなものを 1〜3件提案

慎重に：候補は出すが「最終承認は reflect 側ユーザー」と認識して、生成段階では多めに出して OK。

### 3-3. 申し送り文の充填

`<相手_inbox>/YYYY-MM-DD_<slug>_request.md` のファイル名を組み立て:
- `YYYY-MM-DD` は今日
- `<slug>` は元ファイル名から拡張子を除いて短く（最大30文字）

中身（frontmatter + 本文）:

```yaml
---
source: <絶対パス>
seeds_referenced:
  - <seed-slug>
created: YYYY-MM-DD
---

## このコラムの概要

<200字程度の要約>

## wiki への依頼アクション

- [ ] interests/questions.md の seed `<seed-slug>` を <new-status> に更新
- [ ] [[wiki/opinions/<page>]] の「## 関連」にリンク追加
- [ ] 新主張「<一文>」を opinions/ 追加候補
- [ ] 引用した事実「<一文>」を concepts/ 収集 seed 化候補
```

---

## Phase 4: 承認 + 投函

### 4-1. ユーザー承認

生成内容を全文ユーザーに見せて `AskUserQuestion` で承認求める:
- そのまま投函 / 部分修正後に投函 / 取り消し

### 4-2. 投函

承認後、Write で相手拠点 `_inbox/` に保存。
**既存同名ファイルがあれば**: タイムスタンプを `_HHMM` 形式で付加して衝突回避（上書きしない）。

### 4-3. 案内

ユーザーに次のアクションを TodoWrite で残す:
- 「相手拠点 (<拠点名>) で `/wiki-essay reflect` を起動してください」
- 「投函ファイル: `<相手_inbox>/YYYY-MM-DD_<slug>_request.md`」

---

## エラー処理

| 状況 | 動作 |
|------|------|
| 対象ファイル不存在 | エラーで中断 |
| 拠点判定不能 | `AskUserQuestion` で確認、それでも不明なら中断 |
| 相手 `_inbox/` フォルダ未存在 | エラー（mkdir しない、WE-001 でセットアップ済みのはず） |
| seed 推定 0件 | `AskUserQuestion` で seed を聞く、未指定なら「seed 未指定」で投函（reflect 側で扱う） |
| references 抽出 0件 | そのまま続行（参照なくても投函可、reflect 側でも問題ない） |

## 完了確認

- 相手拠点 `_inbox/` に `_request.md` が保存されている
- 承認なしには投函されていない
- TodoWrite で「次は相手拠点で `/wiki-essay reflect`」案内が残っている
