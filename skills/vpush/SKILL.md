---
name: vpush
description: >
  バージョン付き git push スキル。直前の作業内容（コミット履歴、タスク管理ファイル）から
  リリース内容を自動収集し、semver バンプ → リリースノート更新 → タグ付き push を
  一気通貫で実行する。
  発動条件:
  (1) /vpush コマンド
  (2) 「バージョンアップしてpush」「リリースpush」「タグ付きpush」等のキーワード
  (3) 作業完了後に「pushして」と言われたとき
  git push を含むため、必ずユーザー確認を取ってから実行する。
noplan: true
---

<!-- IMPORTANT: このスキルはplan modeに入らずに直接実行すること -->

# vpush: バージョン付き git push

作業完了 → バージョンバンプ → リリースノート → タグ付き push を一括実行する。

## 実行プロトコル

### Phase 0: プロジェクト検出（初回のみ）

プロジェクトのバージョン管理方式を自動検出する:

```bash
# バージョン情報源の検出
ls package.json pyproject.toml Cargo.toml version.txt VERSION 2>/dev/null

# リリーススクリプトの検出
ls scripts/release* .github/workflows/release* 2>/dev/null

# タスク管理ファイルの検出
ls Plans.md TODO.md CHANGELOG.md 2>/dev/null

# 既存タグの形式確認
git tag --sort=-v:refname | head -5
```

検出結果からバージョン管理方式を判定:

- **npm**: `package.json` の `version` フィールド
- **Python**: `pyproject.toml` の `[project] version`
- **Rust**: `Cargo.toml` の `version`
- **手動**: `VERSION` / `version.txt`
- **タグのみ**: ファイルなし、git tag で管理

### Phase 1: 状態確認（並列実行）

```bash
# 1. 未コミットの変更
git status

# 2. 前回タグからのコミット一覧
git log $(git describe --tags --abbrev=0 2>/dev/null || echo HEAD~10)..HEAD --oneline

# 3. 現在のバージョン（Phase 0 で検出した方式で取得）

# 4. タスク管理ファイルの最近の完了項目（存在する場合）
```

### Phase 2: プラン提示

収集した情報からバンプ種別を判定し、ユーザーに提示:

```
## vpush プラン

**現在バージョン**: vX.Y.Z
**バンプ判定**: minor（feat コミットあり）
**次バージョン**: vX.(Y+1).0

### 含まれる変更（前回タグから）
- feat: ○○
- fix: △△

### 実行ステップ
1. [ ] 未コミット変更があればコミット
2. [ ] バージョンバンプ（検出方式に応じた方法）
3. [ ] リリースノート更新（CHANGELOG 等があれば）
4. [ ] git tag vX.Y.Z
5. [ ] git push origin <branch> --tags

このプランで実行しますか？
```

バンプ種別の判定基準（Conventional Commits）:

- **major**: `BREAKING CHANGE` または `!:` を含むコミット
- **minor**: `feat:` コミットあり
- **patch**: `fix:` / `refactor:` / `docs:` / `chore:` のみ

### Phase 3: 未コミット変更の処理

未コミットの変更がある場合:

1. `git diff --stat` で変更内容を確認
2. Conventional Commits 形式でコミットメッセージを生成
3. ユーザー確認後にコミット

### Phase 4: バージョンバンプ

検出した方式に応じてバンプを実行:

| 方式                      | コマンド                                                    |
| ------------------------- | ----------------------------------------------------------- |
| npm (release script あり) | `! npm run release:minor` 等（対話式は `!` でユーザー実行） |
| npm (script なし)         | `npm version minor --no-git-tag-version`                    |
| Python                    | `pyproject.toml` の version を直接編集                      |
| Rust                      | `cargo set-version` または `Cargo.toml` 直接編集            |
| 手動                      | `VERSION` ファイルを直接編集                                |
| タグのみ                  | スキップ（Phase 5 でタグ作成）                              |

> 対話式スクリプトがある場合は `!` プレフィックスでユーザーに実行を案内する。

### Phase 5: タグ作成 & リリースノート

```bash
# CHANGELOG.md が存在する場合、エントリを追加
# git tag が未作成の場合
git tag -a vX.Y.Z -m "Release vX.Y.Z: 主な変更の要約"
```

CHANGELOG.md / リリースノートファイルが存在する場合は更新してコミット。

### Phase 6: Push

```bash
git push origin <current-branch> --tags
```

**必ずユーザー確認を取ってから実行する。**

### Phase 6.5: クロスプロジェクト連携（MEOcli プロジェクトのみ）

MEOcli プロジェクト（kuchikomi_maker または Meocli_LP）の場合、もう一方のプロジェクトにも変更を同期する。

**バージョン同期ルール（正本: `~/claude code/_shared/meocli/url-contracts.md`）**:

- アプリ本体と LP は **同一バージョン番号を維持** する
- 次のバージョンは **両者の最大バージョン + 1** にする
  - 例: アプリ v1.8.0、LP v1.9.0 → 次は v1.10.0
- Phase 1 のバージョン決定時に相手側の最新タグも確認すること

**プロジェクト判定:**

| カレントディレクトリ | 自プロジェクト | 相手プロジェクト                             |
| -------------------- | -------------- | -------------------------------------------- |
| `*/kuchikomi_maker*` | アプリ本体     | LP (`~/claude code/Meocli_LP`)               |
| `*/Meocli_LP*`       | LP             | アプリ本体 (`~/claude code/kuchikomi_maker`) |

#### 6.5-A: 相手プロジェクトのバージョン同期

```bash
# 相手側の最新タグを確認
cd <相手プロジェクト>
git tag --sort=-v:refname | head -1

git status
git log $(git describe --tags --abbrev=0 2>/dev/null)..HEAD --oneline
# 未 push のコミットがあればタグ付き push
git tag -a vX.Y.Z -m "Release vX.Y.Z: 主な変更の要約"
git push origin main --tags
```

- 相手側に未コミット変更がある場合はユーザーに確認
- 相手側にコミットがない場合はタグのみ作成してバージョン番号を同期

#### 6.5-B: アプリ側 releases.ts の自動更新（LP → アプリ方向のみ）

**LP プロジェクトで /vpush を実行した場合**、アプリ本体の `lib/data/releases.ts` にリリースエントリを自動追加する。
これにより `app.meocli.com/help/updates` のヘルプセンターにLP側の変更が反映される。

**手順:**

1. LP側のコミット履歴からリリース内容（highlights）を収集する

   ```bash
   cd ~/claude\ code/Meocli_LP
   git log $(git describe --tags --abbrev=0 HEAD^ 2>/dev/null)..HEAD --format='%s'
   ```

2. アプリ側の `lib/data/releases.ts` を Read する

   ```
   ~/claude code/kuchikomi_maker/lib/data/releases.ts
   ```

3. 既に同一バージョンのエントリが存在するか確認する
   - **存在する場合**: highlights にLP側の変更を **追記** する（重複しない項目のみ）
   - **存在しない場合**: 先頭に新エントリを追加する

4. エントリのフォーマット:

   ```typescript
   {
     version: 'X.Y.Z',
     date: 'YYYY-MM-DD',
     title: 'コミット履歴から要約したタイトル',
     highlights: [
       'LP側の変更内容1（コミットメッセージから生成）',
       'LP側の変更内容2',
     ],
     type: 'minor',  // バンプ種別に応じて設定
   },
   ```

5. highlights の生成ルール:
   - コミットメッセージの `feat:` / `fix:` / `chore:` プレフィックスを除去
   - ユーザー向けに読みやすい日本語に整形
   - `docs:` のみのコミットは除外（ユーザーに見せる必要がない）
   - LP固有の技術的変更（ESLint設定等）は除外し、ユーザー向けの変更のみ含める

   **⚠️ 公開コンテンツ表現ルール（必須）:**
   releases.ts はヘルプセンター（app.meocli.com/help/updates）で誰でも閲覧可能。
   以下を厳守すること:
   - **AIモデル名を書かない**: Gemini, GPT, Claude 等 → 「AI」とだけ書く
   - **内部ツール名を書かない**: Sentry, Prisma, Redis, ESLint, Turbopack, Inngest, vitest, DataForSEO 等
   - **セキュリティ不安を煽らない**: 「脆弱性修正」「リスクが高い」→「安全性向上」「セキュリティ強化」
   - **内部チケット番号を書かない**: ZD-xxx, SEC-xxx, BUG-xxx 等
   - **ユーザー目線で書く**: 技術的な実装詳細ではなく、ユーザーにとってのメリットや改善点で表現する

6. `featured` フラグの自動判定:
   以下のいずれかを満たす場合、エントリに `featured: true` を付ける:
   - `feat:` コミットが **2件以上** 含まれる
   - 新しいページ/画面が追加された（`app/` 配下に新規 `page.tsx`）
   - バンプ種別が **major**
   - highlights が **4件以上** かつ `feat:` 由来の項目を含む

7. Edit ツールで `releases.ts` の先頭エントリの前に新エントリを挿入する

8. アプリ側で git commit + push する（Vercel 自動デプロイ）
   ```bash
   cd ~/claude\ code/kuchikomi_maker
   git add lib/data/releases.ts
   git commit -m "docs: v{VERSION} リリースノート追加（LP側変更を含む）"
   git push origin main
   ```

**注意:**

- アプリ本体で /vpush した場合は、この手順は不要（アプリ側で直接 releases.ts を管理しているため）
- LP側のデプロイは `cd ~/claude\ code/Meocli_LP/app && npx vercel deploy --prod` で別途実行

### Phase 7: 完了レポート

```
## vpush 完了

**バージョン**: vX.Y.Z → vX.Y+1.0 (minor)
**タグ**: vX.Y+1.0
**コミット数**: N件
**主な変更**:
- feat: ○○
- fix: △△
```

### Phase 8: CI テスト結果の監視

Push 完了後、GitHub Actions の CI 結果を自動取得する。

#### 8-1: ワークフロー実行の検出

```bash
# push 直後は CI がまだ起動していない場合がある → 数秒待ってから確認
# 最新の workflow run を取得
gh run list --branch <current-branch> --limit 3
```

#### 8-2: CI 完了待ち & 結果取得

```bash
# 最新 run の ID を取得して watch（完了まで待機、最大10分）
gh run watch <run-id> --exit-status

# 失敗した場合はログを取得
gh run view <run-id> --log-failed
```

- `gh run watch` はストリーミングで進捗を表示し、完了時に終了する
- `--exit-status` により、失敗時は非ゼロで終了する
- タイムアウト（10分）を設定して無限待機を防ぐ

#### 8-3: 結果に応じた対応

**CI 成功の場合:**

```
## CI 結果: ✅ 全テスト通過

**Workflow**: <workflow-name>
**Run**: <run-url>
**所要時間**: Xm Ys

**次のステップ**:
- GitHub Releases を作成する場合: gh release create vX.Y.Z
```

**CI 失敗の場合:**

```bash
# 失敗ジョブの詳細ログを取得
gh run view <run-id> --log-failed

# 失敗したステップの特定
gh run view <run-id> --json jobs --jq '.jobs[] | select(.conclusion=="failure") | {name, conclusion, steps: [.steps[] | select(.conclusion=="failure")]}'
```

失敗ログを分析し、修正計画案を提示する:

```
## CI 結果: ❌ テスト失敗

**Workflow**: <workflow-name>
**Run**: <run-url>
**失敗ジョブ**: <job-name>

### エラー概要
- <失敗ステップ名>: <エラーの要約>

### 修正計画案

#### 原因分析
<ログから読み取れるエラー原因の分析>

#### 修正ステップ
1. <具体的な修正アクション>
2. <具体的な修正アクション>
3. ...

#### 影響範囲
- <修正が影響するファイル・機能>

修正を実行しますか？
```

**CI 失敗時は `/ci-fix` スキルに自動引き継ぎする（義務）。**
修正計画の提示で止まらず、`/ci-fix` を呼び出して並列エージェントによる調査・修正を開始すること。

## 引数

| 引数      | 説明                     |
| --------- | ------------------------ |
| `--patch` | patch バンプを強制       |
| `--minor` | minor バンプを強制       |
| `--major` | major バンプを強制       |
| （なし）  | コミット履歴から自動判定 |

## 注意事項

- `git push` は**必ずユーザー確認後**に実行
- 対話式スクリプトは `!` プレフィックスでユーザー実行を案内
- ブランチ名は自動検出（`git branch --show-current`）
