---
name: context-audit
description: Claude Code のコンテキスト常時消費（会話開始前の固定オーバーヘッド）を棚卸し・ランク付けし、安全で可逆な削減策をレポートする分析スキル。グローバル指示の @import 連鎖と「# @」import トラップ検出、~/.claude/rules/ 自動ロード、有効プラグインごとの skills/agents/commands 量、~/.claude/agents/・~/.claude/skills/ の個数とサイズ、claude-mem の SessionStart 注入を計測する。コード/設定は変更せず分析とレポートのみ（削減の適用は必ずユーザー確認後）。発動: 「コンテキスト棚卸し」「context-audit」「コンテキスト削減」「何が重い/トークンを食ってるか調べて」「セッションを軽くしたい」「.claude を診断して」。
---

# context-audit

毎セッション固定で注入されるコンテキストの内訳を可視化し、安全な削減対象を特定する。**分析とレポートのみ。設定やファイルは変更しない。**

## 実行

```bash
python3 ~/.claude/skills/context-audit/scripts/audit.py
```

読み取り専用。CLAUDE.md・settings.json・plugins・~/.claude/agents/・skills/・rules/ を走査し、サイズ降順のランキング表＋発見＋次の一手を出力する。

## 結果の読み方

- **推定tok は粗い近似**（bytes/4）。地上の真値は Claude Code の `/context` で確認するよう必ず案内する。スクリプトの数値は「何をなぜ削るか」の根拠用。
- 大きい順に並ぶので、上位＝削減レバーの大きい候補。

## 主要な発見パターン

1. **「# @」import トラップ**: CLAUDE.md で `# @FLAGS.md` のように `#` を付けても import は止まらない（コメント化されない）。停止するには行頭の `@` を外す（`# FLAGS.md`）。スクリプトが該当行を列挙する。
2. **rules/ 自動ロード**: `~/.claude/rules/*.md` は CLAUDE.md から参照されていなくても自動ロードされる。不要なら別ディレクトリへ移動。
3. **agents/skills はグローバル常駐**: `~/.claude/agents/`・`~/.claude/skills/` は全プロジェクトで一覧注入される。プロジェクト専用のものは各プロジェクトの `.claude/` 配下へ移すと、そのプロジェクトでのみロードされる。
4. **プラグイン**: 無関係なプラグイン（例: 法務系）は skills/agents/MCP を大量に注入する。

## 削減プレイブック（適用は必ずユーザー確認後・すべて可逆）

- **プラグイン無効化**: `settings.json` の `enabledPlugins` で該当を `false`（または `/plugin`）。
- **プロジェクト専用へ移動（推奨）**: `mv ~/.claude/skills/<name> <project>/.claude/skills/`（agents も同様）。その専用プロジェクトでは使えるまま、他では非ロード。
- **アーカイブ退避**: `mkdir -p ~/.claude/skills_archive && mv ~/.claude/skills/<name> ~/.claude/skills_archive/`。どこでも非ロード・即復元可。
- 復元は逆向きの `mv` 一発。

## 鉄則

- 計測 → ランキング提示 → **ユーザーに削減方針を確認** → 適用、の順。勝手に移動・無効化しない。
- 「使っていない＝不要」と「別プロジェクトで使う」を混同しない。後者は削除でなく移動。
- zsh では `for d in $VAR` は単語分割されない。一括処理する移動コマンドは名前を直接並べるか配列を使う。
