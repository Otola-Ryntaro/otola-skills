# Context Hygiene — プロジェクト単位のコンテキスト最適化

新規プロジェクトでは「使わないグローバル資産はプロジェクトレベルで黙らせる」のが基本。
コンテキストを節約し、不要な MCP サーバー起動・トークン消費を抑える。

## 原則（first-action 全体に適用）

1. **Project-First**: MCP・プラグイン・スキルの追加導入はプロジェクト単位（`.claude/settings.local.json` または `.claude/settings.json`）が基本。
2. **Global は明示承認のみ**: グローバル（`~/.claude/`）への新規導入はユーザーが明示的に「グローバルで」と言った場合のみ。
3. **Disable by Default**: グローバルで有効だが**今回のプロジェクトで使わない MCP** は、プロジェクト設定で disable してコンテキスト消費を削減する。
4. **スキルは原則そのまま**: スキルは system-reminder のメタデータのみで軽量なので、明示要望がない限り disable しない。

## コンテキスト消費の重み付け（disable 優先度）

| 種別 | コンテキスト消費 | disable 優先度 |
|---|---|---|
| **MCP server (instructions あり)** | 大（説明文＋ツールスキーマ） | 🔴 高 |
| **MCP server (instructions なし)** | 中（ツールスキーマのみ） | 🟡 中 |
| **プラグイン（コマンド/agents 提供）** | 中 | 🟡 中 |
| **スキル** | 小（name + description のみ） | 🟢 低（基本そのまま） |

## settings.local.json の書き方

### MCP を無効化（プロジェクト単位）

```json
{
  "disabledMcpjsonServers": [
    "chrome-devtools",
    "playwright",
    "morphllm-fast-apply"
  ]
}
```

- 配列の文字列は MCP サーバー名（`mcp__<name>__<tool>` の `<name>` 部分）。
- グローバル設定で有効でも、このプロジェクトでは起動しない。
- ホワイトリスト方式が必要なら `enableAllProjectMcpServers: false` + `enabledMcpjsonServers` を使う。

### プラグイン無効化

プラグインを丸ごと黙らせる場合は `~/.claude/plugins/config.json` のプロジェクト相当機構を使うか、
プラグイン提供スキル/コマンドを CLAUDE.md で「使用禁止リスト」として明記する運用方式を併用する。

### permissions（参考、既存運用）

```json
{
  "permissions": {
    "allow": [
      "Skill(ticket-gen)",
      "Bash(git:*)"
    ]
  }
}
```

## first-action での運用フロー

Phase 3 で推薦リストが確定したら、Phase 4 の基盤ファイル生成時に以下を実施する：

1. **使用予定 MCP リスト** ＝ Phase 3 の「導入推奨」「検討」に挙がった MCP
2. **グローバル有効 MCP リスト** ＝ `~/.claude/settings.json` および `~/.claude/plugins/` から取得
3. **差集合（不要 MCP）** ＝ グローバル有効 − 使用予定
4. 差集合を `.claude/settings.local.json` の `disabledMcpjsonServers` に追記
5. ユーザーに **disable 対象一覧を提示し、最終確認**を取ってから書き込む

## 一般的な disable 候補（参考）

プロジェクト性質ごとの典型例：

| プロジェクト性質 | disable 候補 |
|---|---|
| CLI / バックエンドのみ | `chrome-devtools`, `playwright` |
| ブラウザ自動化なし | `chrome-devtools`, `playwright` |
| Google Drive 連携なし | `claude_ai_Google_Drive` |
| パターン編集の重要性低 | `morphllm-fast-apply` |
| ドキュメント参照頻度低 | `context7`（ただし新規実装では基本残す） |

**判断は必ずユーザーと一緒に**。自動判定だけで disable しない。

## 解除（再有効化）

プロジェクトの方向性が変わって disable した MCP が必要になったら、
`.claude/settings.local.json` の `disabledMcpjsonServers` から該当エントリを削除し、Claude Code を再起動する。
