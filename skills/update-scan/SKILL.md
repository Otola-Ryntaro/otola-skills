---
name: update-scan
description: >
  インストール済みの MCP サーバ・プラグイン・スキルを網羅的に棚卸しし、
  バージョンアップ可能なものを検出してレポートするスキル。read-only で、
  更新の実行は一切しない（レポートにコピペ可能な更新コマンドを記載する）。
  発動条件:
  (1) /update-scan コマンド
  (2) 「アップデートチェック」「バージョンアップ確認」「更新できるものある?」等のキーワード
  (3) MCP / plugin / skill の更新状況を点検したいとき
allowed-tools: Read, Glob, Grep, Bash, Write
---

# update-scan: MCP・Plugin・Skill 更新スキャン

インストール済みコンポーネントを網羅的に列挙し、「現在バージョン / 最新バージョン / 更新コマンド / リスク」をレポートする。**スキャンのみ。更新の実行はしない。** ユーザーがレポートを見てコマンドを選んで実行する。

## 設計原則

1. **網羅性は「検出漏れゼロ」で担保する**: すべての MCP・プラグイン・スキルを必ずレポートに載せる。ただし「全対象の更新可否を判定できる」ことは目標にしない — 判定不能なものは判定不能と正直に書く。
2. **最初に更新モデルで分類する**: バージョン比較の前に、各対象が「固定型（更新作業が必要）」か「自動追従型（更新不要）」かを分類する。これを飛ばすと「不明」だらけのレポートになる。
3. **read-only**: `git fetch` 等のローカルメタデータ取得は可、install / update / upgrade 系コマンドの実行は不可。
4. **正直な報告**: 最新バージョンの取得に失敗したら「取得失敗（理由）」と書く。推測でバージョンを埋めない。

## Phase 1: MCP サーバ

### 1-1. 列挙

3 スコープすべてを確認する（漏れ防止）:

```bash
# user スコープ + プロジェクト別
python3 -c "
import json
d = json.load(open('$HOME/.claude.json'))
print('=== user scope ===')
for k, v in d.get('mcpServers', {}).items():
    print(k, '|', v.get('command',''), ' '.join(v.get('args',[])))
for proj, pv in d.get('projects', {}).items():
    if pv.get('mcpServers'):
        print(f'=== project: {proj} ===')
        for k, v in pv['mcpServers'].items():
            print(k, '|', v.get('command',''), ' '.join(v.get('args',[])))
"
# カレントプロジェクトの .mcp.json（あれば）
cat .mcp.json 2>/dev/null
```

### 1-2. 更新モデルで分類

各サーバの起動コマンドを見て 4 タイプに分類する:

| タイプ | 判定基準 | 更新確認 |
|---|---|---|
| A: 自動追従 | `npx -y pkg@latest` / バージョン指定なしの `npx` | **不要**（起動ごとに最新を取得）。レポートには「自動追従」と記載。npx キャッシュが古い可能性のみ注記 |
| E: リモートホスト型 | `"type": "http"` / `"type": "sse"` で URL 接続 | **不要**（サーバ側で更新される）。設定の妥当性のみ確認（URL 欄にコマンドが入っている等の設定ミスを検出したら報告） |
| B: バージョン固定 npm | `npx pkg@1.2.3` / グローバル install 済みバイナリで npm 配布 | `npm view <pkg> version` と比較 |
| C: git ソース | `uvx --from git+https://github.com/O/R ...` | `gh api repos/O/R/commits/HEAD --jq .sha` 等で上流の動きを確認。uvx はキャッシュ利用のため `uv cache clean` 案内 |
| D: ローカルバイナリ | 絶対パスのコマンド（例: `~/.local/bin/xxx`） | 配布元不明なら「手動管理・確認不能」と記載。`<cmd> --version` は試す |

タイプ B の最新取得はまとめて実行してよい:

```bash
npm view <pkg> version 2>/dev/null
```

### 1-3. 現在バージョンの取得（可能な範囲で）

- グローバル install 済み: `npm ls -g <pkg> --depth=0`
- npx キャッシュ: 取得困難なら深追いしない。「npx 経由・キャッシュバージョン不明」でよい

## Phase 2: プラグイン

### 2-1. 列挙

```bash
python3 -c "
import json
d = json.load(open('$HOME/.claude/plugins/installed_plugins.json'))
for name, entries in d.get('plugins', {}).items():
    for e in entries:
        print(name, '|', e.get('version'), '|', e.get('lastUpdated'), '|', e.get('installPath',''))
"
```

`version` フィールドが semver（例: `9.1.1`）のものと git SHA（例: `99e11d9...`）のものがある点に注意。

### 2-2. 最新確認

プラグインの正式な更新ルートは **marketplace 更新 → 再インストール**:

1. marketplace の上流差分を確認（read-only）。各 marketplace は `~/.claude/plugins/marketplaces/<name>/` に git clone されている:

```bash
export GIT_TERMINAL_PROMPT=0   # 認証プロンプト待ちハング防止（必須）
for d in ~/.claude/plugins/marketplaces/*/; do
  [ -d "$d/.git" ] || continue
  name=$(basename "$d")
  if ! git -C "$d" -c http.lowSpeedLimit=1000 -c http.lowSpeedTime=15 fetch --quiet 2>/dev/null; then
    echo "$name: fetch failed ($(git -C "$d" remote get-url origin))"; continue
  fi
  default=$(git -C "$d" symbolic-ref --short refs/remotes/origin/HEAD 2>/dev/null | sed 's|origin/||')
  [ -z "$default" ] && default=$(git -C "$d" rev-parse --abbrev-ref HEAD)
  behind=$(git -C "$d" rev-list --count HEAD..origin/$default 2>/dev/null)
  echo "$name: ${behind:-?} commits behind origin/$default"
done
```

**注意（実測で判明した落とし穴）**:
- デフォルトブランチは `main` 決め打ちにしない（上記のとおり `origin/HEAD` から取る）
- macOS には `timeout` コマンドがない。`GIT_TERMINAL_PROMPT=0` + git の `http.lowSpeedLimit/lowSpeedTime` でハング対策する
- 大きい上流リポ（数千コミット遅れ）の fetch は数分かかることがある。一括ループがタイムアウトしたら、失敗分だけ個別に Bash timeout を長めにして再実行する

2. behind > 0 の marketplace に属するプラグインは「更新候補」。新バージョン番号の確認方法:
   - `git show origin/<default>:.claude-plugin/marketplace.json` の各 plugin の `version`（無いことも多い）
   - `source` がローカルパスなら `git show origin/<default>:<path>/.claude-plugin/plugin.json`
   - `source` が外部 URL（SHA ピン留め）なら `gh api repos/O/R/contents/.claude-plugin/plugin.json --jq .content | base64 -d` で上流バージョンを取得
   - どれでも取れなければ「behind N コミット（バージョン番号不明）」と記載

3. レポートに載せる更新コマンド:

```bash
claude plugin marketplace update <marketplace名>   # または引数なしで全部
claude plugin install <plugin>@<marketplace>        # 再インストールで最新化
```

## Phase 3: スキル

### 3-1. 列挙

- `~/.claude/skills/` 直下
- プロジェクトの `Skill-library/global-skills/` などスキル置き場（プロジェクト CLAUDE.md を確認）

### 3-2. 分類（更新可否判定はしない）

| 分類 | 判定 | レポート記載 |
|---|---|---|
| 自作スキル | git 上流を持たないローカル作 | 「手動管理・上流なし」 |
| 外部由来コピー | SuperClaude 等からのコピー（fork ではない） | 「コピー由来・git 差分不可。由来元を注記」 |
| git 管理下 | ディレクトリに `.git` がある | marketplace と同じ手順で behind を確認 |

自作か外部由来かの判定にはメモリ `skill-library-originality` の基準を参照する（存在すれば）。**スキルは「全件列挙して分類する」ことが目的で、バージョン比較は git 管理下のものだけに限定する。** それ以外を無理に判定しようとしない。

### 3-3. Claude Code 本体（おまけ・1 行のみ)

```bash
claude --version
npm view @anthropic-ai/claude-code version
```

差があれば「`claude update` で更新可」と 1 行記載。専用の分析はしない。

## Phase 4: レポート出力

出力先: `<プロジェクトルート>/work/update-scan/update-scan_YYYY-MM-DD.md`（日付は `date +%F` で実測する）

構成:

```markdown
# 更新スキャンレポート YYYY-MM-DD

## サマリー
- 更新可能: N 件 / 自動追従（更新不要）: N 件 / 判定不能: N 件

## 1. MCP サーバ
| 名前 | タイプ | 現在 | 最新 | 状態 | 更新コマンド |
（全サーバを必ず記載。自動追従型も「A: 自動追従」として載せる）

## 2. プラグイン
| 名前 | marketplace | 現在 | 上流の動き | 更新コマンド |

## 3. スキル
| 名前 | 場所 | 分類 | 状態 |

## 4. Claude Code 本体
（1 行）

## 5. 更新時の注意（該当がある場合のみ）
- 破壊的変更の可能性がある対象は、リリースノート URL と注意点を記載
```

レポート末尾に「このレポートは read-only スキャンの結果です。更新は上記コマンドを確認のうえ手動で実行してください」と明記する。

## 実行時の注意

- Phase 1〜3 の外部照会（npm view / gh api / git fetch）は独立なので並列実行してよい
- ネットワークエラー時はリトライ 1 回まで。失敗は「取得失敗」としてレポートに残す
- `gh` 未認証・npm レジストリ不達など環境起因の失敗は、レポート冒頭の「スキャン制約」節にまとめる
