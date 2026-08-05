# Codex Second Opinion 3 ルート Fallback 戦略

mine-check Phase E で使うレビュー戦略の詳細。`/codex:adversarial-review` が commit 差分ベースで動作するため、本スキルが「レポートファイル単体」の妥当性を評価する用途では誤動作することがある。本ドキュメントはその回避策を規定する。

---

## 課題の整理

| 制約                                                                                          | 影響                                             |
| --------------------------------------------------------------------------------------------- | ------------------------------------------------ |
| `/codex:adversarial-review --scope working-tree` は git diff ベース                           | working-tree が dirty だと無関係な変更がノイズに |
| レポートが未コミット状態                                                                      | Codex が「変更内容」として認識しない可能性       |
| `--scope branch` も commit が必要                                                             | レポート生成直後に commit を強要するのは過剰     |
| プラグインコマンドはフォーカステキストでヒントを渡せるが、ファイル本文を直接渡す API ではない | レポートの構造化評価が難しい                     |

→ **結論**: ルート 1（MCP 直接呼び出し）をデフォルトとして採用し、レポート全文をプロンプトに埋め込む方式が最も汎用的かつ確実。

---

## ルート判定ロジック（Phase E 冒頭で実行）

```
Step 1: git status --porcelain で working-tree 状態を取得
Step 2: 以下の優先順位で選択
  (a) ルート 1（デフォルト・最汎用）
  (b) working-tree が clean かつ Critical >= 1 件 のときのみルート 2 へ昇格
  (c) ルート 1 / 2 が API エラー or 空レスポンスならルート 3 へ降格
  (d) 全失敗 → ユーザー通知 + Phase F 進行（手動確認）
```

具体的な判定コード（疑似コード）:

```python
def select_codex_route(report_path, critical_count):
    git_status = run("git status --porcelain")
    is_clean = (git_status.strip() == "")
    if is_clean and critical_count >= 1:
        return "route2"  # adversarial で深堀り
    return "route1"      # MCP 直接（デフォルト）

def execute_review(route, report_path, critical_count):
    try:
        if route == "route1":
            return call_mcp_codex(report_path)
        if route == "route2":
            return call_skill("codex:adversarial-review", "--wait --scope working-tree")
    except (APIError, EmptyResponse):
        return call_skill("codex:second-opinion", report_path)
    return None  # ルート 3 も失敗
```

---

## ルート 1: MCP 直接呼び出し（推奨デフォルト）

**ツール**: `mcp__codex-cli__codex`（プラグインの MCP サーバ経由）

**呼び出し例**:

```
Tool: mcp__codex-cli__codex
Parameters:
  prompt: |
    あなたは kuchikomi_maker プロジェクトの過去事故 14 件と error-patterns 9 件を
    熟知したシニアエンジニア。以下の Mine Check Report を評価してほしい。

    ## 評価観点
    1. Critical 判定の妥当性（false positive はないか）
    2. 見落としている地雷はないか（特に過去事故 14 件と照合）
    3. 推奨修正は十分か（より安全な代替）
    4. 新規パターン候補の蓄積価値

    ## レポート本体
    [ここにレポート全文を Read してから埋め込む]

    ## 参照知識ベース要約
    [.claude/error-patterns/INDEX.md の本文]
    [docs/problem_solved/ から最新 5 ファイルのタイトルとサマリ]

    ## 出力フォーマット（厳守）
    - 同意した Critical: [LM-XXX]
    - 反対する Critical: [LM-XXX] + 理由
    - 追加すべき Critical: [LM-NEW] + 検出根拠
    - 追加すべき Warning: ...
    - 蓄積反対の新規パターン候補: ...
```

**メリット**:

- working-tree が dirty でも動作
- レポート全文を直接渡せる（差分ではない）
- プロンプトを完全制御できる

**デメリット**:

- MCP 設定が必要（`@openai/codex` v0.98.0 + `~/.codex/config.toml`）
- レスポンスサイズ制限あり（プロンプト長要管理）

---

## ルート 2: /codex:adversarial-review

**呼び出し**:

```
Skill(skill: "codex:adversarial-review")
Args: --wait --scope working-tree
フォーカステキスト: |
  Mine Check Report (codex/YYYYMMDD_mine_check_report.md) の Critical 判定の妥当性を
  深く検証してほしい。kuchikomi_maker プロジェクトの過去事故と error-patterns を踏まえ、
  - false positive はないか
  - 見落としている地雷はないか
  - 推奨修正は十分か
  に注目。設計判断レベルで挑戦的にレビューしてほしい。
```

**起動条件**: working-tree が clean かつ Critical >= 1 件

**メリット**:

- 既存の codex-second-opinion スキルの公式ルート
- App Server 経由で高機能
- 設計判断を挑戦的に検証する深いレビュー

**デメリット**:

- working-tree dirty 時はノイズ混入で誤動作
- レポートを commit しないと拾われない可能性

---

## ルート 3: /codex:second-opinion（軽量フォールバック）

**呼び出し**:

```
Skill(skill: "codex:second-opinion")
Args: <レポートパス> + 評価観点プロンプト
```

**起動条件**: ルート 1 / 2 が失敗（API エラー、タイムアウト、空レスポンス）

**メリット**:

- 標準的なコードレビュー、軽量・高速
- フォールバック先として安定

**デメリット**:

- 設計挑戦は弱め
- カスタマイズ性低い

---

## 失敗時の挙動

すべてのルートが失敗した場合:

1. レポートの「🤖 Codex Second Opinion 結果」セクションに以下を明記:

   ```markdown
   ## 🤖 Codex Second Opinion 結果

   ⚠️ Codex レビュー失敗（全ルート: route1=API error, route2=working-tree dirty, route3=timeout）
   手動レビュー推奨: ユーザーが個別に過去事故レポートと照合してください。
   ```

2. ユーザーに通知してそのまま Phase F へ進む
3. レビュー失敗を理由に Phase F をスキップしてはいけない（蓄積義務は独立）

---

## レビュー結果のレポート反映ルール

ルート 1〜3 のいずれが成功しても、結果は以下フォーマットに正規化してレポートに追記:

```markdown
## 🤖 Codex Second Opinion 結果

**実行ルート**: route1 / route2 / route3
**実行時刻**: YYYY-MM-DDTHH:MM:SSZ
**モデル**: gpt-5.3-codex（または codex 側が報告したモデル名）

### 同意

- [LM-001], [LM-005] — Critical 判定に同意

### 反論

- [LM-003] — Critical ではなく Warning が妥当（理由: 過去事故とは異なる発火条件）

### 追加提案

- [LM-NEW-A] middleware/admin-auth.ts:120 で auth metadata の読み取りタイミングが古い実装に戻っている
  - 検出根拠: docs/problem*solved/20260418_e2e_auth*\*.md と類似
  - 推奨修正: subscription_status を app_metadata から優先的に読む

### 蓄積反対

- 新規候補 inngest-retry-loop は本リポジトリ固有の事象であり、汎用パターンとして登録するには根拠が薄い
```

**Critical の追加・削除があった場合**: Phase F でユーザーに必ず通知し、最終的なレポート版に反映するか確認する。

---

## トラブルシューティング

| 症状                                      | 原因候補                                                 | 対処                                                                                 |
| ----------------------------------------- | -------------------------------------------------------- | ------------------------------------------------------------------------------------ |
| MCP ツール呼び出しで "Tool not found"     | `~/.codex/config.toml` 未設定 / Codex CLI 未インストール | `npm i -g @openai/codex` + config.toml 設定                                          |
| ルート 2 で「変更がありません」レスポンス | working-tree clean なのにレポートが見えていない          | レポートを `git add -N codex/...` で intent-to-add するか、ルート 1 にフォールバック |
| プロンプト長すぎでエラー                  | レポート + 知識ベース全文が長大                          | error-patterns/INDEX.md だけにし、個別 .md は要約のみ埋め込む                        |
| 全ルート失敗                              | ネットワーク・認証問題                                   | ユーザー通知して手動レビュー指示                                                     |
