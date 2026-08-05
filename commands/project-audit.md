---
description: プロジェクトの Claude Code ベストプラクティス適合度を評価し、対象プロジェクト内にレポートを出力する
---

指定プロジェクトの Claude Code ベストプラクティス適合度を評価してください。

対象プロジェクト: $ARGUMENTS

## 手順

1. 評価基準を読み込む: `~/claude code/Evironment/Claude_Codeベストプラクティス指示書.md`
2. 対象プロジェクトに `.claude-audit/` フォルダを作成
3. 評価基準ドキュメントを `.claude-audit/best-practices.md` にコピー
4. `.gitignore` に `.claude-audit/` を追加（未登録の場合のみ）
5. 対象プロジェクトの情報を並列で収集:
   - CLAUDE.md（内容・行数）
   - .claude/settings.json（permissions・hooks）
   - .claudeignore
   - .gitignore
   - .mcp.json
   - .claude/commands/ 配下のコマンド一覧
   - .claude/agents/ または .agents/ 配下のエージェント一覧
   - .claude/skills/ 配下のスキル一覧
   - package.json（スクリプト・依存関係）
   - テストファイル数（*.test.*, *.spec.*）
   - .env 系ファイル一覧（中身は読まない）
   - ディレクトリ構成
   - 直近5コミット
6. 9カテゴリで 0-10 点採点:
   1. CLAUDE.md
   2. Permission 設定
   3. Hooks 自動化
   4. カスタムコマンド
   5. Git ワークフロー
   6. テスト体制
   7. セキュリティ
   8. MCP 統合
   9. サブエージェント / スキル
7. レポートを `.claude-audit/audit-report.md` に出力
8. ターミナルにスコアサマリーを表示

## 制約
- 対象プロジェクトの既存ファイルは一切変更しない（.gitignore への追記と .claude-audit/ 作成のみ）
- .env の中身は読まない（ファイル名のみ）
- スコアは事実ベース（推測で加点・減点しない）
