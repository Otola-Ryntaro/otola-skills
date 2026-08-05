# wiki-essay rebuild-threads モード — `_seed_threads.md` 全体再生成

3 拠点（`LLM_wiki/essays/`、`コラム/`、`LLM_wiki/X_book/`）を再走査して
`_seed_threads.md` を一から組み立て直す。差分更新（write/reflect）では取りこぼす
ファイル移動・frontmatter 改変・retrofit 後の整合性ズレを回収する。

## 引数

なし（デフォルト3拠点を走査）。
`--include <path>` で走査対象を追加可能（複数指定可）。

## 🔴 鉄則

- **必ず `.bak` を取ってから書き換える**（手動編集を失わない）
- **「書いていない（候補）」セクションは新版でも保持**（マージ保護、手動追記を尊重）
- **拠点ファイル大幅変動時は警告して中断**（既存記載の80%超が消えるなら処理しない）
- **書き換えはユーザー承認後**（旧版↔新版の差分を見せて Y/N）

---

## Phase 1: 事前準備

### 1-1. バックアップ

1. `~/claude code/LLM_wiki/essays/_seed_threads.md` の存在確認
2. 存在すれば `_seed_threads.md.bak` にコピー（既存 `.bak` は上書き）
3. 存在しなければ空ヘッダーから新規作成扱い（バックアップ不要）

### 1-2. 既存内容の Read

旧 `_seed_threads.md` を Read し、以下を抽出して保持:
- 各 seed セクション（`## seed: <slug>`）
- 各セクションの「書いた」table 全行（後で照合）
- 各セクションの「書いていない（候補）」リスト（**マージ保護対象**）
- frontmatter 的な冒頭ヘッダー

---

## Phase 2: 全拠点走査

### 2-1. 走査対象（デフォルト）

1. `~/claude code/LLM_wiki/essays/drafts/*.md` + `essays/books/**/*.md`（_インデックス系除外）
2. `~/claude code/コラム/*/*.md`（各テーマフォルダ配下のコラム）
3. `~/claude code/LLM_wiki/X_book/drafts/*.md`
4. `--include` 指定があれば追加

### 2-2. 各ファイルから抽出する情報

| 項目 | 取得元 |
|------|--------|
| `seed` | frontmatter があれば `seed:` フィールド、なければ既存 `_seed_threads.md.bak` から逆引き |
| `audience` | frontmatter `audience:`、なければ `unknown` |
| `angle` | frontmatter `angle:`、なければ `unknown` |
| `medium` | frontmatter `medium:`、なければ拠点で推定（コラム/→blog, X_book→book-chapter, essays/→media不明） |
| `status` | frontmatter `status:`、なければ拠点で推定（コラム/→`published`, X_book→`adopted`, essays/→`draft`） |
| `created` | frontmatter `created:`、なければファイル mtime の日付 |
| `location` | ファイル絶対パス |

### 2-3. seed が判定不能なファイルの扱い

frontmatter なし & `.bak` にも記載なしのファイルは「未紐づけ」セクションに集約。
このセクションは新版 `_seed_threads.md` の末尾に置いて、ユーザーが後で reflect / write の対話で seed 紐づけできるよう案内する。

---

## Phase 3: 新版 `_seed_threads.md` の組み立て

### 3-1. seed セクションのビルド

各 seed について:
1. 既存セクションのヘッダー（`status: ...` 行、`関連: [[...]]` 行）を保持
2. 「書いた（N本）」table を **全拠点走査結果で再構築**（行は date 昇順）
3. 「書いていない（候補）」リストを **旧版から完全コピー**（マージ保護）

### 3-2. 新規 seed の扱い

走査で見つかった seed が旧版に存在しなければ、新規セクションを `templates/seed_threads_entry.md` テンプレで追加。

### 3-3. 「未紐づけ」セクション

末尾に以下を追加（該当ファイルがあれば）:

```markdown
## 未紐づけ（手動で seed 紐づけ要）

> rebuild-threads 時に seed 判定できなかったファイル。
> reflect モードか write モードで対話的に seed を紐づけてください。

| date | location | 推定 audience | 推定 angle |
|------|----------|-------------|-----------|
| ... | ... | unknown | unknown |
```

---

## Phase 4: 差分確認 + 承認

### 4-1. 旧版↔新版の差分

`difflib` 相当の処理で旧版と新版を比較し、以下のサマリをユーザーに見せる:

```
## rebuild-threads 差分サマリ

- seed セクション: 旧 N → 新 M（+X / -Y）
- 「書いた」行: 旧 A 行 → 新 B 行（+C 追加 / -D 削除）
- 「書いていない候補」: 旧 P 件 → 新 Q 件（マージ保護で完全保持）
- 未紐づけファイル: R 件

### 警告
- ⚠️ 大幅変動検知: 旧「書いた」行の Z% が新版に存在しません
  → 中断推奨。手動確認してください。
```

### 4-2. 承認

`AskUserQuestion` で:
- そのまま上書き / 部分修正 / 取り消し（`.bak` から復元せず旧版維持）

### 4-3. 大幅変動時の挙動

旧版「書いた」行の **80% 以上が新版に存在しない** 場合は警告 → ユーザーが「強制続行」を選ばない限り中断。

---

## Phase 5: 書き込み + ログ

### 5-1. 承認後の書き込み

1. 承認 → `_seed_threads.md` に新版を上書き保存
2. ユーザー却下 → `.bak` を残したまま旧版は無変更で終了

### 5-2. log.md 追記

`~/Obsidian/LLM_Wiki/log.md` に1行追記:
```
## [YYYY-MM-DD] essay-rebuild-threads | <旧 N> seeds → <新 M> seeds, <未紐づけ R> files
```

### 5-3. ユーザー案内

`TodoWrite` で次アクション:
- 「未紐づけ R 件は reflect / write モードで seed 紐づけ可能」
- 「`.bak` が `_seed_threads.md.bak` に保存されている」

---

## 共通化（WE-011 retrofit との関係）

`essays/scripts/retrofit_seed_threads.py`（WE-011 で実装）が走査ヘルパーを提供するなら、
本モードからも同じヘルパーを呼んで DRY 化する。具体的には:

- ファイル列挙ロジック
- frontmatter パース
- seed 紐づけ推論

これらは `retrofit_seed_threads.py` の関数を `import` または `subprocess` で呼ぶ
（Python なら module import が綺麗）。

retrofit が「初回限定の過去執筆取り込み」、rebuild-threads が「日常的な再生成」と射程が異なるが、
内部ロジックは共有可能。

---

## エラー処理

| 状況 | 動作 |
|------|------|
| `_seed_threads.md` 不存在 | 空ヘッダーから新規生成扱い、`.bak` は作らない |
| 拠点ディレクトリ不存在 | その拠点だけスキップ、ユーザーに通知 |
| 大幅変動検知 (>80% 消失) | 警告 → ユーザー強制続行確認 |
| `.bak` 作成失敗 | エラーで中断（書き込みは行わない） |
| Phase 4 承認で却下 | `.bak` をそのまま残し、旧版維持 |

## 完了確認

- `_seed_threads.md.bak` が生成されている（旧版が存在した場合）
- 新版 `_seed_threads.md` が seed 単位で整列されている
- 「書いていない候補」が旧版から完全保持されている
- 未紐づけセクションがあれば末尾にある
- `log.md` に1行追記されている
