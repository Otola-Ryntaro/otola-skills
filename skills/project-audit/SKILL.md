---
name: project-audit
description: >
  指定プロジェクトが Claude Code ベストプラクティスに沿っているかを外部から評価し、
  対象プロジェクト内の .claude-audit/ にスコア付きレポートと評価基準ドキュメントを出力する。
  発動条件:
  (1) /project-audit <パス> コマンド
  (2) 「プロジェクト評価」「ベストプラクティス監査」「audit」等のキーワード
  (3) 他プロジェクトの Claude Code 設定品質を確認したいとき
---

# Project Audit — Claude Code ベストプラクティス適合評価

## 概要

指定されたプロジェクトディレクトリを調査し、
Claude Code ベストプラクティスへの適合度をスコア付きレポートとして出力する。

**対象プロジェクトの既存ファイルは変更しない。** `.claude-audit/` フォルダ作成と `.gitignore` 追記のみ行う。

## 起動方法

```
/project-audit <プロジェクトパス>
/project-audit ~/claude\ code/kuchikomi_maker
```

引数なしの場合はユーザーにパスを尋ねる。

## 評価基準ドキュメント

本スキルの評価基準は以下のファイルに準拠する:

```
~/claude code/Evironment/Claude_Codeベストプラクティス指示書.md
```

**まずこのファイルを Read で読み込み、評価基準を把握してから調査を開始すること。**

---

## 実行手順

### Step 0: 準備

1. `$ARGUMENTS` からプロジェクトパスを取得（なければユーザーに質問）
2. プロジェクトルートが存在することを確認
3. 評価基準ドキュメント `~/claude code/Evironment/Claude_Codeベストプラクティス指示書.md` を Read で読み込む

### Step 1: .claude-audit/ インフラ構築

1. `mkdir -p <target>/.claude-audit/`
2. 評価基準ドキュメントの内容を `<target>/.claude-audit/best-practices.md` に Write でコピー
3. `<target>/.gitignore` を確認し、`.claude-audit/` が含まれていなければ末尾に追記:
   ```
   # Claude Code Audit (auto-generated)
   .claude-audit/
   ```
   - `.gitignore` が存在しない場合は新規作成する

### Step 2: ファイル構成の収集（並列実行）

以下を **すべて並列** で実行し、プロジェクトの現状を把握する:

| 調査対象 | コマンド/ツール | 取得する情報 |
|---------|---------------|-------------|
| CLAUDE.md | Read `<target>/CLAUDE.md` | 内容・行数・構成 |
| settings.json | Read `<target>/.claude/settings.json` | permissions・hooks |
| settings.local.json | Read `<target>/.claude/settings.local.json` | ローカル設定 |
| .claudeignore | Read `<target>/.claudeignore` | 除外パターン |
| .gitignore | Read `<target>/.gitignore` | シークレット除外確認 |
| .mcp.json | Read `<target>/.mcp.json` | MCP サーバー設定 |
| カスタムコマンド | Glob `<target>/.claude/commands/**/*.md` | コマンド一覧 |
| サブエージェント | Glob `<target>/.claude/agents/**/*.md` + `<target>/.agents/**/*.md` | エージェント一覧 |
| スキル | Glob `<target>/.claude/skills/**/*.md` | スキル一覧 |
| Hooks | settings.json 内の hooks セクション | Hook 設定 |
| package.json | Read `<target>/package.json` | スクリプト・依存関係 |
| テスト設定 | Glob `<target>/**/*.test.*` + `<target>/**/*.spec.*` (head 20) | テストファイル数 |
| .env 系 | Glob `<target>/.env*` | 環境変数ファイル一覧（中身は読まない） |
| ディレクトリ構成 | Bash `ls -la <target>/` | 全体像 |
| Git 状態 | Bash `cd <target> && git log --oneline -5` | 直近コミット |

### Step 3: 9カテゴリで評価

収集した情報をもとに、以下の **9 カテゴリ** でそれぞれ 0〜10 点で採点する。

#### カテゴリ一覧

| # | カテゴリ | 配点 | 評価ポイント |
|---|---------|------|-------------|
| 1 | **CLAUDE.md** | /10 | 存在する・200行以内・具体的・プロジェクト固有・実行可能な指示 |
| 2 | **Permission 設定** | /10 | settings.json 存在・allow/deny が適切・危険コマンドをブロック |
| 3 | **Hooks 自動化** | /10 | 自動フォーマット・危険操作ブロック・品質チェック |
| 4 | **カスタムコマンド** | /10 | 3個以上・実用的（review/test/check 等） |
| 5 | **Git ワークフロー** | /10 | .gitignore 適切・Conventional Commits・ブランチ戦略 |
| 6 | **テスト体制** | /10 | テストファイル存在・TDD 方針・カバレッジ設定 |
| 7 | **セキュリティ** | /10 | .env が .gitignore に含まれる・シークレット管理・OWASP 意識 |
| 8 | **MCP 統合** | /10 | .mcp.json 存在・適切なサーバー選択 |
| 9 | **サブエージェント / スキル** | /10 | 定義ファイル存在・役割分担・専門特化 |

#### 採点ガイドライン

| 点数 | 意味 | ランク |
|------|------|-------|
| 0-2 | 未設定 / 存在しない | D |
| 3-4 | 存在するが不十分 / 形だけ | C |
| 5-6 | 基本はできている / 改善余地あり | B |
| 7-8 | 良好 / ベストプラクティスにおおむね準拠 | A |
| 9-10 | 模範的 / 他プロジェクトの手本になるレベル | S |

### Step 4: レポート出力

以下のフォーマットで `<target>/.claude-audit/audit-report.md` にレポートを出力する。

```markdown
# Project Audit Report: <プロジェクト名>

> 評価日: YYYY-MM-DD
> 対象パス: <プロジェクトパス>
> 評価者: Claude Code (project-audit skill)
> 評価基準: .claude-audit/best-practices.md

---

## 総合スコア: XX / 90

### スコアサマリー

| # | カテゴリ | スコア | 判定 |
|---|---------|--------|------|
| 1 | CLAUDE.md | X/10 | S/A/B/C/D |
| 2 | Permission 設定 | X/10 | |
| ... | ... | ... | ... |

判定: 9-10 = S, 7-8 = A, 5-6 = B, 3-4 = C, 0-2 = D

### カテゴリ別詳細

#### 1. CLAUDE.md (X/10)

**現状**: (発見した事実を簡潔に記述)
**良い点**: (具体的に)
**改善提案**: (具体的なアクション。コード例があれば添える)

(以下、全9カテゴリについて同形式で記述)

### 優先改善 TOP 3

最もインパクトが大きい改善を 3 つ、具体的アクション付きで提示する。

1. **[カテゴリ名]**: やるべきこと（1行）
   - 具体的な手順
   - 期待効果

2. ...
3. ...

---

> `/project-setup <プロジェクトパス>` でスコア 6 以下の項目を自動改善できます。
```

### Step 5: ターミナル出力

レポート書き込み後、ターミナルにスコアサマリーを表示し、以下を案内する:

```
レポート出力先: <target>/.claude-audit/audit-report.md
評価基準コピー: <target>/.claude-audit/best-practices.md

低スコア項目の自動改善: /project-setup <プロジェクトパス>
```

---

## 制約

- **既存ファイル保護**: 対象プロジェクトの既存ファイルを変更しない（.gitignore への `.claude-audit/` 追記のみ例外）
- **客観性**: 数値・事実に基づいて評価。推測で加点・減点しない
- **建設的**: 批判ではなく改善提案を中心にする
- **シークレット注意**: .env の中身は読まない（ファイル名のみ確認）
- **プロジェクト文脈考慮**: 個人開発 vs チーム、MVP vs 本番、ドキュメント専用リポなど規模・性質を考慮してコメントする
- **MCP / サブエージェント**: 「使っていない = 悪い」ではない。プロジェクト規模に応じて判断する
