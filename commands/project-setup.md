---
description: 監査レポートに基づいてプロジェクトの Claude Code 設定を改善する
---

監査レポートに基づいてプロジェクトの Claude Code 設定を改善してください。

対象プロジェクト: $ARGUMENTS

## 手順

1. `<target>/.claude-audit/audit-report.md` を読み込む（なければ `/project-audit` を先に実行するよう案内）
2. `<target>/.claude-audit/best-practices.md` を読み込む
3. スコアが 6 以下のカテゴリを特定
4. 各カテゴリの改善ファイルを生成（プレビュー表示）
5. ユーザーに確認を取ってから実行
6. 変更ログを `.claude-audit/setup-log.md` に記録

## 制約
- 必ずユーザー確認後に変更を実行する
- 既存ファイルは上書きせず、マージ・追記する
- .env の中身は読まない
- 変更内容をすべて `.claude-audit/setup-log.md` に記録する
