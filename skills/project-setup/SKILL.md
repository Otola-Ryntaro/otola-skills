---
name: project-setup
description: >
  project-audit の監査レポートに基づき、低スコアカテゴリの Claude Code 設定ファイルを
  自動生成・改善する。対象プロジェクト内の .claude-audit/audit-report.md を読み取り、
  スコア 6 以下の項目に対して改善ファイルを生成する。変更前に必ずユーザー確認を取る。
  発動条件:
  (1) /project-setup <パス> コマンド
  (2) 「セットアップ改善」「設定修正」「低スコア改善」等のキーワード
  (3) /project-audit 実行後の後続アクションとして
---

# Project Setup — 監査レポートに基づく Claude Code 設定改善

## 概要

`/project-audit` で生成された監査レポート（`.claude-audit/audit-report.md`）を読み取り、
スコアが **6 以下**（C/D ランク）のカテゴリに対して設定ファイルの生成・改善を行う。

**必ずユーザー確認後に変更を実行する。既存ファイルは上書きしない（マージ/追記のみ）。**

## 起動方法

```
/project-setup <プロジェクトパス>
/project-setup ~/claude\ code/kuchikomi_maker
```

引数なしの場合はユーザーにパスを尋ねる。

## 前提条件

- 対象プロジェクトに `.claude-audit/audit-report.md` が存在すること
- 存在しない場合は `/project-audit <パス>` を先に実行するよう案内して**中止**する

---

## 実行手順

### Step 0: 準備

1. `$ARGUMENTS` からプロジェクトパスを取得（なければユーザーに質問）
2. `<target>/.claude-audit/audit-report.md` の存在を確認
   - 存在しない → 「`/project-audit <パス>` を先に実行してください」と案内して中止
3. `audit-report.md` と `best-practices.md` を Read で読み込む

### Step 1: 低スコアカテゴリの特定

audit-report.md のスコアサマリーテーブルを解析し、**スコア 6 以下** のカテゴリを抽出する。

各カテゴリの「改善提案」セクションも読み取り、具体的な改善内容を把握する。

### Step 2: 改善ファイル生成計画

低スコアカテゴリごとに、以下のマッピングに従ってアクションを決定する。
**必ず対象プロジェクトの既存ファイルを先に Read し、現状を把握してから計画を立てること。**

#### カテゴリ → アクション対応表

---

**カテゴリ 1: CLAUDE.md（スコア <=6 の場合）**

対象: `<target>/CLAUDE.md`

アクション:
- CLAUDE.md が存在しない → package.json 等から技術スタックを読み取り、テンプレートから新規作成
- 存在するが不十分 → 不足セクションを末尾に追記（既存内容は一切変更しない）

追記候補セクション:
```markdown
## 開発コマンド
- ビルド: `npm run build`
- テスト: `npm test`
- リント: `npm run lint`
- 型チェック: `npx tsc --noEmit`

## 技術スタック
（package.json から自動検出して記載）

## 注意事項
- 変更前に関連ファイルを読み切る
- セキュリティに関わる変更は必ず確認する
```

---

**カテゴリ 2: Permission 設定（スコア <=6 の場合）**

対象: `<target>/.claude/settings.json`

アクション:
- settings.json が存在しない → テンプレートから新規作成
- 存在するが deny が空 → 既存 JSON を Read し、deny リストを追加（マージ）

追加する deny ルール:
```json
{
  "permissions": {
    "deny": [
      "Bash(rm -rf:*)",
      "Bash(git push --force:*)",
      "Bash(git reset --hard:*)",
      "Bash(git checkout -- .)"
    ]
  }
}
```

**重要**: 既存の permissions.allow, permissions.deny を保持した上で追加する。

---

**カテゴリ 3: Hooks 自動化（スコア <=6 の場合）**

対象: `<target>/.claude/hooks/`

アクション:
- hooks ディレクトリが存在しない → 作成
- 以下のスクリプトを作成:

`guard-dangerous.sh`:
```bash
#!/bin/bash
# PreToolUse(Bash) — 危険なコマンドをブロック
INPUT=$(cat)
COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command // empty')
if echo "$COMMAND" | grep -qE 'rm -rf|git push --force|git reset --hard|DROP TABLE|TRUNCATE'; then
  echo '{"decision":"block","reason":"Dangerous command blocked by hook"}'
else
  echo '{"decision":"approve"}'
fi
```

`auto-format.sh`:
```bash
#!/bin/bash
# PostToolUse(Edit|Write) — 自動フォーマット
INPUT=$(cat)
FILE=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')
if [ -n "$FILE" ] && echo "$FILE" | grep -qE '\.(ts|tsx|js|jsx|json|md)$'; then
  npx prettier --write "$FILE" 2>/dev/null || true
fi
```

settings.json の hooks セクションも追加（既存とマージ）。

---

**カテゴリ 4: カスタムコマンド（スコア <=6 の場合）**

対象: `<target>/.claude/commands/`

アクション:
- commands ディレクトリが存在しない → 作成
- 以下のコマンドファイルを作成:

`review.md`:
```markdown
以下のファイルをレビューしてください: $ARGUMENTS

チェック項目:
- セキュリティ脆弱性
- パフォーマンスのボトルネック
- テストカバレッジの不足
- エラーハンドリングの漏れ
```

`check.md`:
```markdown
以下を順番に実行して問題があれば修正してください:
1. 型チェック
2. リント
3. テスト実行
修正した場合は何を変えたか簡潔に報告してください。
```

`test.md`:
```markdown
$ARGUMENTS のテストを作成してください。
既存テストのスタイルに合わせ、正常系・異常系・境界値を含めてください。
テスト実行して PASS を確認してください。
```

---

**カテゴリ 5: Git ワークフロー（スコア <=6 の場合）**

対象: `<target>/.claudeignore`, `<target>/.gitignore`

アクション:
- .claudeignore が存在しない → 新規作成
  ```
  node_modules/
  .next/
  .git/
  dist/
  build/
  coverage/
  *.log
  test-results/
  playwright-report/
  ```
- .gitignore に .env 系の除外がない → 追記

---

**カテゴリ 6: テスト体制（スコア <=6 の場合）**

対象: `<target>/CLAUDE.md`

アクション:
- CLAUDE.md にテスト方針セクションを追記:
  ```markdown
  ## テスト方針
  - テスト駆動開発（TDD）を原則とする
  - カバレッジ目標: 80%
  - テストフレームワーク: （package.json から自動検出）
  ```

---

**カテゴリ 7: セキュリティ（スコア <=6 の場合）**

対象: `<target>/.gitignore`, `<target>/.claude/settings.json`

アクション:
- .gitignore に以下が含まれていなければ追記:
  ```
  .env
  .env.*
  !.env.example
  *.pem
  *.key
  ```
- settings.json の deny に機密ファイル操作のブロックを追加

---

**カテゴリ 8: MCP 統合（スコア <=6 の場合）**

対象: `<target>/.mcp.json`

アクション:
- .mcp.json が存在しない → 新規作成
- 存在する → 既存の mcpServers を保持した上で context7 を追加
  ```json
  {
    "mcpServers": {
      "context7": {
        "command": "npx",
        "args": ["-y", "@upstash/context7-mcp@latest"]
      }
    }
  }
  ```

---

**カテゴリ 9: サブエージェント / スキル（スコア <=6 の場合）**

対象: `<target>/.claude/agents/`

アクション:
- agents ディレクトリが存在しない → 作成
- テンプレートエージェントを 1 つ作成（プロジェクトに合わせた内容）

---

### Step 3: 一括確認（MANDATORY — 省略禁止）

**全改善案を以下の形式で一覧表示する:**

```
## 改善計画

対象プロジェクト: <target>
低スコアカテゴリ: X 件

### 1. カスタムコマンド (現在 3/10)
  - 作成: .claude/commands/review.md
  - 作成: .claude/commands/check.md
  - 作成: .claude/commands/test.md

### 2. MCP 統合 (現在 6/10)
  - 更新: .mcp.json に context7 を追加

---
以上の変更を実行しますか？ (y/n)
```

ユーザーが `n` → 中止して終了
ユーザーが `y` → Step 4 へ進む

### Step 4: 実行

承認された変更を実行する。

**安全ルール（絶対遵守）**:
- 既存ファイルは **上書きしない**。マージまたは追記のみ
- `settings.json`: JSON を Read → パースし、既存の allow/deny を保持した上で新規項目を追加 → Write
- `CLAUDE.md`: 末尾に区切りコメントを入れて新セクションを追記
- `.gitignore`: 末尾に追記
- `.mcp.json`: 既存の mcpServers を保持した上で新規サーバーを追加
- 新規ファイルはそのまま Write
- Hook スクリプトには `chmod +x` で実行権限を付与

### Step 5: 変更ログ記録

`<target>/.claude-audit/setup-log.md` に変更内容を記録:

```markdown
# Setup Log

## YYYY-MM-DD HH:MM

### 実行した改善
- [カテゴリ名] ファイルパス: 作成/追記/マージ
- ...

### 対象カテゴリ
| カテゴリ | 改善前スコア | 実行内容 |
|---------|------------|---------|
| カスタムコマンド | 3/10 | commands/ に 3 ファイル作成 |
| ... | ... | ... |
```

### Step 6: 再監査案内

```
改善完了。変更ログ: <target>/.claude-audit/setup-log.md

改善結果の確認: /project-audit <プロジェクトパス>
```

---

## 制約

- **ユーザー確認必須**: Step 3 の確認を省略してはならない
- **既存ファイル保護**: 上書き禁止。マージ/追記のみ
- **シークレット注意**: .env の中身は一切読まない
- **変更ログ必須**: すべての変更を setup-log.md に記録する
- **冪等性**: 同じ改善を2回実行しても問題が起きないようにする（既に存在するファイルはスキップ）
