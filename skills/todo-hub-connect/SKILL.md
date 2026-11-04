---
name: todo-hub-connect
description: |
  ハブ未連結プロジェクトに残っている既存成果物——旧形式の manual_todo/*.html と daily_report/*_visualize.html——を、集約ハブ ~/dev/todo（index.html / reports.html）へ後付けで登録・吸い上げるスキル。対象プロジェクトのセッション内（CWD がそのプロジェクト）で起動する前提。ファイルの変換や移動は行わず、todo-hub CLI の register --legacy / report-add で「その場のパスのまま」ハブに連結する。
  発動条件: (1) /todo-hub-connect コマンド (2)「ハブに連結」「ハブへ吸い上げ」「既存TODOをハブに載せて」「日報をハブに登録」「todo-hub-connect」等のキーワード (3) 旧プロジェクトを再開した際に manual_todo/ や daily_report/ がハブ未登録と判明したとき。
  使用しないケース: 新規 TODO の作成（→ manual-todo が最初からハブへ出力する）/ 日報の新規作成・visualize 生成（→ shime）/ ハブ自体の修理・サーバ運用（→ manual-todo スキルの運用章）。
---

# todo-hub-connect

対象プロジェクト内の既存成果物をスキャンし、`~/dev/todo` ハブへ登録する。**ファイルはコピー・変換・移動しない**。ハブの registry / reports.json にパスを登録するだけの非破壊操作。

## 前提

- ハブ実体: `~/dev/todo/`（`index.html` = TODO ハブ、`reports.html` = 作業ログ）
- CLI: `~/dev/todo/bin/todo-hub`（実体は `~/.claude/skills/manual-todo/scripts/todo-hub.py`）
- `register` / `report-add` は実行と同時に index.html / reports.html を再生成する。手編集は不要・禁止
- `assets/hero.png` がプロジェクトにあれば reindex 時に自動でハブへコピーされる（追加作業不要）

## Phase 1: スキャン（read-only）

CWD（対象プロジェクト）で以下を列挙する:

```bash
ls manual_todo/*.html 2>/dev/null          # 旧形式 TODO（残置分）
ls daily_report/*_visualize.html 2>/dev/null  # 可視化済み日報
ls daily_report/*.md 2>/dev/null | head       # md のみの日報（対象外の把握用）
```

登録済みかどうかの重複チェック:

```bash
grep -l "$(pwd)" ~/dev/todo/state/registry.json ~/dev/todo/state/reports.json 2>/dev/null
```

registry.json / reports.json 内に既に同じパスのエントリがあるものはスキップ対象としてマークする。

## Phase 2: インベントリ提示と確認

登録候補を一覧で提示し、ユーザー確認を取ってから Phase 3 へ進む:

- 旧 TODO: ファイル名・抽出タイトル・作成日（N 件）
- 日報 visualize: ファイル名・タイトル・日付（N 件）
- **対象外**: md のみの日報（ハブは HTML しか配信しないため登録不可。件数だけ報告し、必要なら「/shime の --visualize で HTML 化してから再実行」を案内する）

タイトルは各 HTML の `<title>` または最初の `<h1>` から抽出する。

## Phase 3: 登録実行

### 旧 TODO（manual_todo/*.html → index.html）

1 ファイルごとに:

```bash
~/dev/todo/bin/todo-hub register \
  --slug "<YYYY-MM-DD_slug>" \
  --project "<プロジェクトディレクトリ名>" \
  --project-path "$(pwd)" \
  --title "<抽出タイトル>" \
  --created "<ファイルの日付 ISO8601>" \
  --legacy "<HTML の絶対パス>"
```

制約と注意:

- **slug は英数・ハイフン・ドットのみ**。日本語ファイル名はローマ字や英訳に変換して `YYYY-MM-DD_<slug>` 形式にする（日付はファイル名 or mtime から）
- 同一 slug は上書きされるので、既存ハブページと衝突しない slug を選ぶ
- `--legacy` 登録では state JSON は空の骨組みが作られるだけ。**チェック状態は旧ページの localStorage のまま**で、ハブからは閲覧リンクとしての連結になる（この制約を最終報告に明記する）

### 日報（daily_report/*_visualize.html → reports.html）

1 ファイルごとに:

```bash
~/dev/todo/bin/todo-hub report-add --path "<絶対パス>" --title "<抽出タイトル>"
```

`--title` 省略時はファイル名から推定されるが、日本語タイトルが正しく出るよう原則明示する。project 名と日付はパスとファイル名から自動推定される。

## Phase 4: 検証と報告

1. `~/dev/todo/state/registry.json` / `reports.json` に全件入ったことを grep で確認
2. `open ~/dev/todo/index.html`（または `todo-hub open`）でハブを開き、目視確認をユーザーに委ねる
3. 最終報告に含める内容:
   - 登録件数（TODO n 件 / 日報 n 件、スキップ n 件と理由）
   - md のみで登録できなかった日報の件数と HTML 化の案内
   - 旧 TODO のチェック状態は localStorage 依存のままである旨
