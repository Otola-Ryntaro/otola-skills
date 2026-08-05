---
name: codex-second-opinion
description: OpenAI Codex CLI を使い、セカンドオピニオン・コードレビュー・設計挑戦レビューを行うスキル。CLI 直接（codex exec）をデフォルトとし、プラグインコマンド・MCP Server はフォールバック。以下のいずれかに該当する場合に使用する：(1) コードレビューで別のAIモデルの視点が欲しいとき、(2) アーキテクチャや実装方針のセカンドオピニオンが必要なとき、(3) セキュリティ・パフォーマンス・保守性の多角的レビューを行いたいとき、(4) /codex-review や /second-opinion コマンドが使われたとき。単純なタスクや検証不要な作業には使用しない。
---

# Codex Second Opinion Skill

OpenAI Codex CLI を活用したセカンドオピニオン取得スキル。

## ⚠️ 重要：デフォルトは `codex exec`（CLI 直接）

**過去にレビューが途中で止まる／タイムアウトする不具合が頻発した原因は、プラグインコマンドや MCP が常駐サーバー（`codex app-server` / `codex-mcp-server`）を起動・蓄積していたこと。**

`codex exec` は **単発プロセスで実行し終了時にサーバーを残さない**ため、ゾンビ蓄積・OAuth リフレッシュ失敗・タイムアウトに巻き込まれにくい。`review` サブコマンドで未コミット差分・ブランチ比較・コミット指定・構造化出力まで全てカバーできる。

| 呼び出し方法 | 起動するサーバー | 評価 |
| ------------ | ---------------- | ---- |
| `codex exec review`（Bash） | なし（単発） | ✅ デフォルト推奨 |
| `SlashCommand(/codex:review)` | `codex app-server` 常駐 | △ リッチUI/BG管理が要るとき |
| `mcp__codex-cli__review` | `codex-mcp-server` 常駐 | △ MCP前提のとき |
| `Skill(skill: "codex:review")` | — | ❌ 動かない（プラグインコマンドであり Skill ではない） |

## Method Selection（優先度順）

| 優先度 | 方式 | 呼び出し | 使い分け |
| ------ | ---- | -------- | -------- |
| 1 | **CLI 直接（推奨・デフォルト）** | `codex exec review` via Bash | 通常のレビュー全般。常駐サーバーを残さず最も安定 |
| 2 | **プラグインコマンド** | `SlashCommand` で `/codex:review` / `/codex:adversarial-review` | バックグラウンドジョブ管理（`/codex:status` 等）やリッチな対話UIが欲しいとき |
| 3 | **MCP ツール** | `mcp__codex-cli__review`, `mcp__codex-cli__codex` | 既に MCP ワークフローに組み込んでいるとき |

## Pattern 1: CLI 直接（推奨・デフォルト）

`codex exec review` を Bash で実行する。常駐サーバーを起動しないため最も安定。

### 1-A. 標準コードレビュー

```bash
# 未コミット変更（staged + unstaged + untracked）をレビュー
codex exec review --ephemeral --uncommitted

# ブランチ差分をレビュー
codex exec review --ephemeral --base main

# 特定コミットの変更をレビュー
codex exec review --ephemeral --commit <SHA>
```

主要オプション:

- `--uncommitted`: 未コミット変更をレビュー
- `--base <BRANCH>`: 比較元ブランチを指定
- `--commit <SHA>`: 特定コミットをレビュー
- `-m, --model <MODEL>`: モデル指定（省略時はデフォルト）
- `--title <TITLE>`: レビューサマリに表示するタイトル
- `--ephemeral`: セッションファイルをディスクに残さない（0.145 で追加）。**単発のセカンドオピニオンでは常時付与を推奨** — `~/.codex/sessions/` の肥大（GB 単位に蓄積した実績あり）を防ぐ

出力はそのまま（要約・改変せず）ユーザーに提示する。

### 1-B. 設計挑戦レビュー（Adversarial）

カスタム指示をプロンプト引数で渡し、設計判断・トレードオフ・前提条件に厳しく異議を唱えさせる。

```bash
codex exec review --ephemeral --uncommitted "設計判断・トレードオフ・前提条件に厳しく異議を唱える adversarial レビューを行う。\
このアプローチが本当に正しいかを検証し、見落とされている前提・代替案・リスクを指摘する。\
特にセキュリティとテナント分離に注目する。"
```

- アーキテクチャ変更・大型リファクタリング時に推奨
- 末尾の自由記述で重点領域（セキュリティ等）を指定

### 1-C. 計画・設計のセカンドオピニオン（差分なし）

git 差分ではなく、計画文やアプローチそのものをレビューさせる場合は汎用実行を使う。

```bash
codex exec --ephemeral --skip-git-repo-check "次のアプローチをレビューせよ: [計画]。\
長所・短所・代替案・見落としているリスクを列挙する。"
```

補足（0.145 時点の汎用 `exec` オプション）:

- `-C, --cd <DIR>`: 作業ルートを指定（対象プロジェクト外から実行するとき）
- `--add-dir <DIR>`: 追加で読み書き許可するディレクトリ
- `-s, --sandbox read-only`: 読み取り専用サンドボックス（レビュー用途では推奨）
- `codex exec resume --last`: 直前の exec セッションを再開（追い質問に使える。`--ephemeral` 実行分は再開不可）

### 1-D. 構造化出力・ファイル保存

```bash
codex exec review --ephemeral --uncommitted \
  --output-schema /tmp/claude/schema.json \
  -o /tmp/claude/result.json
cat /tmp/claude/result.json
```

- `--output-schema <FILE>`: JSON Schema で出力形状を指定
- `-o, --output-last-message <FILE>`: 最終メッセージをファイル保存
- `--json`: イベントを JSONL で出力
- `-i, --image <FILE>`: 画像添付（**`codex exec` のみ。`review` サブコマンドでは使えない**）

## Pattern 2: プラグインコマンド（フォールバック）

バックグラウンドジョブ管理やリッチな対話UIが必要な場合のみ使用。内部で `codex app-server` に委譲するため、多用するとプロセスが蓄積する点に注意。

```
SlashCommand: /codex:review --wait --scope working-tree
SlashCommand: /codex:adversarial-review --wait --scope working-tree セキュリティに注目
SlashCommand: /codex:status     # バックグラウンドジョブの進捗
SlashCommand: /codex:result     # 最新結果の取得
SlashCommand: /codex:cancel     # 実行中レビューのキャンセル
```

- `--wait`: フォアグラウンド実行 / `--background`: バックグラウンド実行
- `--scope working-tree|branch`, `--base <ref>`
- **Skill ツールでは呼べない**（`codex:*` のスキルは `codex:setup`/`codex:rescue` のみ）

## Pattern 3: MCP ツール（フォールバック）

既存の MCP ワークフローに組み込んでいる場合に使用。`codex-mcp-server` が常駐する。

```
Tool: mcp__codex-cli__review
Parameters:
  commit: "abc1234"        # 特定コミット
  base: "main"             # ブランチ比較
  uncommitted: true        # 未コミット変更（prompt と同時使用不可）
```

```
Tool: mcp__codex-cli__codex
Parameters:
  prompt: "Review this approach: [plan]. List pros, cons, alternatives."
  sandbox: "read-only"
  fullAuto: true
```

## /cr スキルとの連携

`/cr` コマンドのフラグでこのスキルが使用される:

```
/cr --codex          → codex exec review（CLI 直接・デフォルト）
/cr --adversarial    → codex exec review + adversarial プロンプト
/cr --codex-plugin   → /codex:review（プラグインコマンド）
/cr --codex-mcp      → mcp__codex-cli__review（MCP 直接）
```

## Best Practices

1. **CLI 直接を優先** — 通常レビューは `codex exec review` を Bash で実行する
2. **常駐サーバーを避ける** — プラグイン/MCP は app-server / mcp-server を残すため、必要なときだけ
3. **設計変更には adversarial プロンプト** — `codex exec review --uncommitted "..."` で重点指定
4. **Skill ツールで呼ばない** — `codex:review` はプラグインコマンドであり Skill ではない
5. **結果はそのまま表示** — Codex の出力を要約・改変しない
6. **Compare perspectives** — Codex の分析と自身の分析を比較提示する

## Troubleshooting（よくある不具合）

### 症状: レビューが途中で止まる／タイムアウトする

**まず `codex exec` 方式（Pattern 1）を使っているか確認する。** exec は単発プロセスでサーバーを残さないため、この症状はほぼ起きない。プラグイン/MCP 使用時に発生する。

```bash
# 残存サーバー確認（種類を区別すること）
ps aux | grep -E "codex-mcp-server|codex app-server" | grep -v grep
```

**重要：プロセスの正体を区別する。**

- `codex-mcp-server` … Claude Code の MCP 経由（`mcp__codex-cli__*`）で起動。これが Claude Code 由来のゾンビ。安全に kill できる:
  ```bash
  pkill -f "codex-mcp-server"
  ```
- `codex app-server` … **大半は VS Code 拡張（openai.chatgpt）や Codex デスクトップアプリの常駐プロセス**。`pkill -f "codex app-server"` はそれらを巻き込んで落とす（VS Code 拡張は自動再起動するが、Desktop アプリは手動再起動が要る場合がある）。**安易に一掃しない。** プラグインコマンドを使った直後に増えた分のみが対象。

→ そもそも Pattern 1（exec）に切り替えれば、この対処自体が不要になる。

### 症状: `The 'gpt-5.3-codex' model is not supported when using Codex with a ChatGPT account.` が出る

古いモデル名がどこかの `config.toml` にピン留めされたまま。codex 0.145 時点で `gpt-5.3-codex` は ChatGPT アカウントでは使用不可（codex 本体が `gpt-5.3-codex → gpt-5.5` の移行マップを持つ）。

```bash
# ピン留め箇所を特定（プロジェクト側の .codex/config.toml が優先されることに注意）
grep -n "model" ./.codex/config.toml ~/.codex/config.toml 2>/dev/null
```

- 恒久対処: 該当行を `model = "gpt-5.5"` などサポート中のモデルに書き換える
- 一時対処: `codex exec review -m gpt-5.5 ...` とモデルを明示する
- 2026-07-28: `Evironment/.codex/config.toml` の同件を `gpt-5.5` へ修正済み

### 症状: `Auth(TokenRefreshFailed("invalid_grant: ..."))` が出る

ChatGPT 認証のリフレッシュトークン期限切れ。

```bash
codex login status   # ステータス確認（"Logged in using ChatGPT" ならOK）
codex login          # 再ログイン（ブラウザ起動）
```

### 症状: `Request forbidden by administrative rules` が出る

GitHub プラグイン MCP の User-Agent エラー。Codex 本体には影響しない。気になる場合は `~/.codex/config.toml` の `[plugins."github@openai-curated"]` を `enabled = false` に。

### プラグイン未インストール時

Pattern 1（exec）はプラグイン不要。プラグインコマンドを使いたい場合の確認:

```bash
ls ~/.claude/plugins/cache/openai-codex/codex/*/commands/ 2>/dev/null
```

## Limitations

- Codex は OpenAI モデル（gpt-5.6-sol / gpt-5.5 等、`config.toml` の `model` 設定に従う）を使用し、Claude ではない
- インターネット接続と ChatGPT Plus/Pro/Business/Enterprise サブスクリプションが必要
- Homebrew 版は古い。必ず npm 版（`@openai/codex`）を使用すること
- 確認済みバージョン: `codex-cli 0.145.0`（npm 最新と一致、2026-07 時点）。更新は `npm install -g @openai/codex@latest`
