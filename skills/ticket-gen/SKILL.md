---
name: ticket-gen
description: |
  成果レポート（codex/ 配下）を読み取り、作業チケットに分解・Phase整理・管理ファイル生成を自動化するスキル。
  発動条件:
  (1) /ticket-gen <レポートファイルパス> コマンド
  (2) 「チケットに分解」「チケット化」「ticket化」等のキーワード + レポートファイルパス
  /ko スキルでPhase単位の並列実行に接続する前提。
allowed-tools: Read, Write, Edit, Glob, Grep, Bash(date:*), Bash(ls:*), Bash(mkdir:*), Skill, EnterPlanMode, ExitPlanMode
---

# ticket-gen: レポート → チケット自動生成スキル

codex/ 配下の成果レポートを読み取り、作業チケットと ticket_index.md を自動生成する。

## 起動時の必須手順

**スキル発動直後、必ずプランモードに入ること。**

1. `EnterPlanMode` を呼び出す
2. Phase 0〜1（入力検証・レポート分析）を実行し、チケット分解計画を提示する
3. ユーザーが計画を承認（CONFIRM）したら `ExitPlanMode` で抜けて実行に移る
4. ユーザーが修正を求めたら計画を調整し、再度承認を待つ

プランモード中は **ファイル生成（Write）を行わない**。分析・計画の提示のみ。

## 実行プロトコル

### Phase 0: 入力検証

1. 引数からレポートファイルパスを取得
2. ファイルの存在確認・内容読み込み
3. 日付取得: `date +%Y%m%d`

### Phase 1: レポート分析

1. レポート全体を読み込み、以下を抽出:
   - **問題点・作業項目**: 独立したチケットに分解可能な単位
   - **依存関係**: 作業間の前後関係
   - **全体方針**: Wave名・設計思想
   - **対象ファイル**: 各作業の影響範囲
2. レポート内容からPREFIXを自動決定:
   - リファクタリング系 → `RF-`
   - セキュリティ系 → `SEC-`
   - パフォーマンス系 → `PERF-`
   - バグ修正系 → `BUG-`
   - 構造整理系 → `S-`
   - チェック・監査系 → `CHK-`
   - 最適化系 → `OPT-`
   - その他 → レポート内容から適切な短縮名

### Phase 2: チケット分解

各作業項目について:

1. **独立性判断**: 他の作業と切り離して実行可能か
2. **粒度調整**: 1チケット = 1人が1セッションで完了できる規模
   - S: 1-3ファイル、30分以内
   - M: 4-10ファイル、1-2時間
   - L: 10+ファイル、半日以上
3. **優先度判定**:
   - HIGH: 他のチケットの前提条件、セキュリティ、本番影響
   - MEDIUM: 品質改善、コード整理
   - LOW: ドキュメント、nice-to-have
4. **受け入れ条件の生成（必須）**: 各チケットに「受け入れ条件」セクションを必ず生成する。
   - 元レポートの該当記述から導出し、**検証可能形式**で書く（「〜を実装する」ではなく「〜すると〜になる」）
   - 各条件に確認方法（コマンド or 目視手順）を併記する
   - `/ko` strict モードと `/cr --spec` がこのセクションを spec 照合の判定対象にするため、欠落は品質ゲートの無効化を意味する
5. **元レポート該当箇所の記載（必須）**: 各チケットに「元レポート該当箇所」セクションを生成し、レポートパス + セクション見出し（必要なら1–2行引用）を記す。実装者がチケット単体からでも調査時の意図・実害シナリオに遡れるようにする

### Phase 3: Phase自動判断

1. **依存グラフ構築**: チケット間の依存関係を分析
2. **並列グループ化**: 依存関係のないチケットを同一Phaseにまとめる
   - **Phase サイズ上限**: 1 Phase は最大 4〜5 チケットを目安とし、超える場合は依存が無くても Phase を分割する（/ko の並列レビュー容量とメインコンテキストの逼迫を防ぐ）
3. **Phase順序決定**:
   - Phase 1: 前提条件なし、並列実行可能な基盤作業
   - Phase 2: Phase 1 に依存する作業
   - Phase 3+: 前のPhaseに依存する作業
   - 最終Phase: ドキュメント更新、統合テスト等
4. **Phase構成テーブルにステータス列を含める**: 各Phaseの初期ステータスを ⬜ で生成する。`/ko` と `/next` がPhase単位の進捗判定に使用する。

### Phase 4: ファイル生成

1. **出力ディレクトリ**: `docs/tickets{YYYYMMDD}/` を作成
   - 同日に複数Wave → `docs/tickets{YYYYMMDD}_{suffix}/` (suffix例: `_checks`, `_refactor`)
2. **個別チケット生成**: [references/ticket_template.md](references/ticket_template.md) に準拠
3. **🔒 DB/Migration 依存チェック（MIGRATION-CHECK 義務付け）**:

   2026-04-05 の本番 DB 全消失事故（commit 481362b9 baseline 再構成中に本番 URL で `prisma migrate reset` 相当が走った）を踏まえた再発防止。**プロジェクトに `.claude/skills/migration-check/SKILL.md` が存在する場合のみ有効**。無ければこのステップは noop。

   **3-1. キーワード検出**: 各チケットの `背景` / `作業内容` / `対象ファイル` / `受け入れ条件` を全文 scan し、以下のキーワードのいずれかにヒットするか判定（大文字小文字無視、部分一致）。
   - Prisma 系: `prisma`, `schema.prisma`, `prisma/migrations`, `prisma/schema`, `migrate`, `migration`, `baseline`, `db push`, `db pull`
   - Supabase 系: `supabase db`, `supabase migration`, `SUPABASE_DB_`, `--linked`, `pg_dump`, `pg_restore`, `pgrst`
   - DB 接続: `DATABASE_URL`, `DIRECT_URL`（DB 直接操作の文脈時のみ）
   - DDL: `ALTER TABLE`, `CREATE TABLE`, `DROP TABLE`, `TRUNCATE`, `DROP SCHEMA`, `CREATE INDEX`, `_prisma_migrations`
   - スキーマ同期: `schema cache`, `NOTIFY pgrst`, `reload schema`

   **3-2. ヒットしたチケットの本文冒頭に強制挿入**（frontmatter の直後、`## 概要` / `## 背景` の直前）:

   ```markdown
   ## 🔒 着手前に必須: MIGRATION-CHECK

   このチケットは **DB / Supabase / Prisma** を触ります。
   **着手前に必ず `Skill(skill: "migration-check")` を呼び出し、Check-1〜6 を全て通過** させてから作業を開始してください。

   - 事故背景: 2026-04-05 に本番 DB 全消失事故（commit 481362b9 baseline 再構成中、本番 URL で `prisma migrate reset` 相当が走った）
   - スキル本体: `.claude/skills/migration-check/SKILL.md`
   - 関連: `docs/operations/prisma-safety-guardrails.md`

   **このブロックを削除・スキップして着手することは禁止**。自信があっても必ず呼ぶ。
   ```

   **3-3. ticket_index.md のチケット行に `🔒` マーカー**: ヒットしたチケットのタイトル前に `🔒` を付与。

   ```markdown
   | DB-012 | 🔒 Prisma schema に facility 列追加 | M | HIGH | Phase 2 | ⬜ |
   ```

   **3-4. 凡例追記**: index 表の下に以下の凡例を追加（まだ無ければ）。

   ```markdown
   > 🔒 = 着手前に `Skill(skill: "migration-check")` を必ず呼び出すこと（DB/Migration 依存チケット）
   ```

   **3-5. 除外**: 以下はキーワードにヒットしても付与しない。
   - `docs/problem_solved/**`, `docs/archives/**` を**読むだけ**のチケット
   - コメント / テスト名 / 文言修正のみで、実コード・スキーマに影響しないチケット

   判断に迷ったら **付ける側に倒す**（false positive の方が false negative より害が少ない）。

4. **ticket_index.md 生成**: [references/index_template.md](references/index_template.md) に準拠
5. **検証コマンド埋め込み**: ticket_index.md 末尾の「実装検証」セクションに、元レポートの実パスを埋め込んだ `/ticket-verify <tickets-dir> --report <実パス>` を記載する（ユーザーがパスを覚える必要をなくす）

### Phase 5: 計画品質ゲート（`/ticket-review` に分離）

ticket-gen の責務は計画ファイルの生成までとし、計画品質の検証は **`/ticket-review` コマンド** に
委譲する。Phase 4 完了後、Phase 8 の完了報告で `/ticket-review` の実行を推奨する。

> 推奨実行: `/ticket-review docs/tickets{YYYYMMDD}/`
>
> Codex セカンドオピニオンによる adversarial review（最大 3 ラウンド）を実行し、
> カバレッジ・粒度・依存・リスクを多角的に検証する。Major 以上の指摘が出なくなるか
> 最大ラウンドに到達するまで修正ループを回す。詳細は `~/.claude/commands/ticket-review.md` を参照。

ticket-gen 自体は **/ticket-review を自動実行しない**。ユーザーが明示的に呼ぶ運用とする
（軽微な変更やドキュメントのみの修正でスキップしたいケースを尊重するため）。

### Phase 6: USER_GUIDE 更新判定

チケット群の内容が USER_GUIDE に影響するかを判定し、必要に応じて更新する。**USER_GUIDE/ の体系を判定し、汎用版と MEOcli 専用版で処理を分岐する**。

#### 6-1. USER_GUIDE 体系の判定（最初に必ず実行）

```bash
# USER_GUIDE/ 自体が存在するか
test -d USER_GUIDE && echo "exists" || echo "none"

# 汎用版マーカー（user-guide スキル生成）
test -f USER_GUIDE/00_index.md && echo "generic"

# MEOcli 専用版マーカー（kuchikomi_maker 等の既存運用）
ls USER_GUIDE/Authentication.md USER_GUIDE/Admin_Setup.md USER_GUIDE/Question_Table.md 2>/dev/null | head -1
```

分岐：

| 判定 | 動作 |
|------|------|
| `USER_GUIDE/` なし | スキップ（影響評価のみ報告） |
| `USER_GUIDE/00_index.md` あり | **汎用版 → 6-2-A（user-guide スキルに委譲）** |
| `Authentication.md` 等あり | **MEOcli 専用版 → 6-2-B（従来通り直接 Edit）** |
| 両方ある（移行途中） | 汎用版を優先（6-2-A） |

#### 6-2-A: 汎用版（user-guide スキル委譲）

`USER_GUIDE/00_index.md` を検出した場合、**user-guide スキルの軽量モードに自動委譲** する。ticket-gen 自身は Edit しない。

```
Skill(skill: "user-guide", args: "--from-tickets docs/tickets{YYYYMMDD}/")
```

user-guide 側で以下が自動実行される（詳細は `~/.claude/skills/user-guide/references/light_update.md`）：

- 全チケットを読み込み、影響カテゴリを判定
- `04_history.md` に ticket-gen 完了エントリを追記（必ず）
- アーキ / スタック / 用語 / 未解決の影響時のみ該当章を Edit
- USER_EDIT マーカー区画は保護
- 完了報告を返す

ticket-gen の責務は「軽量モードを起動するところまで」。判定結果は完了報告に転記する。

#### 6-2-B: MEOcli 専用版（従来通り直接 Edit）

`Authentication.md` `Admin_Setup.md` `Question_Table.md` 等の体系を検出した場合は、ticket-gen が直接 Edit する従来ロジックを使う（kuchikomi_maker 想定）。

##### 影響カテゴリの判定（MEOcli 専用）

生成した全チケットの `背景` `作業内容` `対象ファイル` を分析し、以下のカテゴリに該当するか判定:

| カテゴリ       | 該当する変更例                          | 更新対象                                      |
| -------------- | --------------------------------------- | --------------------------------------------- |
| 患者導線       | URL変更、session仕様、QR仕様            | `Overview.md`, `Architecture.md`              |
| 認証・ロール   | ロール追加/変更、MFA、OAuth             | `Authentication.md`, `Admin_Auth_Identity.md` |
| 管理画面       | 管理人向け画面追加/変更                 | `Platform_Admin_Guide.md`                     |
| 院長設定       | 院長向け初期設定変更                    | `Admin_Setup.md`                              |
| 質問構造       | 質問セットの構造変更                    | `Question_Table.md`                           |
| アーキテクチャ | レイヤー追加、API構造変更、新サービス層 | `Architecture.md`                             |
| 新機能ドメイン | 既存ガイドに該当しない新しい概念・機能  | 新規ファイル作成を検討                        |

##### 更新の実行

**影響ありの場合:**

1. 該当する USER_GUIDE ファイルを `Read` で読み込む
2. チケット内容に基づき、**完了後に反映すべき変更** を特定する
3. 以下のいずれかを実行:
   - **既存ファイル更新**: `Edit` で該当セクションを更新。変更箇所にはチケットIDを `<!-- Updated by {PREFIX}-{NNN} -->` コメントで記録
   - **新規ファイル作成**: 新ドメインの場合、`USER_GUIDE/` に新規 `.md` を作成し、`README.md` の「まず読むもの」テーブルにも追加
4. 更新内容は **チケットの作業内容が完了した想定** で書く（未完了状態を記述しない）
5. 大規模な変更が予想される場合は、USER_GUIDE 更新自体を最終Phaseの独立チケットとして生成し、実装完了後に別途実行する方針を取る

**影響なしの場合:**

- 「USER_GUIDE への影響なし」と報告してスキップ

#### 6-3. 判定のガイドライン（両方式共通）

- **更新する**: 外部仕様（URL、ロール、画面フロー）が変わる場合
- **更新する**: 新しい概念・用語が導入される場合
- **スキップする**: 内部リファクタリングのみで外部仕様が不変の場合
- **スキップする**: テスト追加・コード品質改善のみの場合
- **チケット化する**: 変更が大きすぎて現時点で正確な更新ができない場合 → 最終Phaseに `{PREFIX}-DOC` チケットを追加

### Phase 7: 実装検証（`/ticket-verify` に分離）

ticket-gen の責務は計画ファイルの生成までとし、全チケット完了後の実装検証は
**`/ticket-verify` コマンド** に委譲する。ticket_index.md 末尾の「実装検証」セクションには
`/ticket-verify <tickets-dir> --report <レポートパス>` を記載しておく（Phase 4 で実施済み）。

> 推奨実行（全チケット完了後）: `/ticket-verify docs/tickets{YYYYMMDD}/`
>
> 3 つの並列サブエージェントでコード整合性・テスト/ビルド・Gap 分析を実行し、
> `codex/{YYYYMMDD}_{tickets-dir名}_verification_report.md` を生成する。
> 詳細は `~/.claude/commands/ticket-verify.md` を参照。

`/next` は全 Phase 完了時に `/ticket-verify` の実行を推奨する。
ticket-gen 自体は **/ticket-verify を自動実行しない**（チケット完了タイミングはユーザーが管理）。

### Phase 8: 完了報告

以下のフォーマットで報告:

```
## ticket-gen 完了

**元レポート**: `<ファイルパス>`
**出力先**: `docs/tickets{YYYYMMDD}/`
**生成チケット数**: N件
**Phase構成**:
| Phase | チケット | 概要 |
|-------|---------|------|
| Phase 1 | {PREFIX}-001〜{PREFIX}-00N | ... |
| Phase 2 | ... | ... |

### USER_GUIDE 更新

**汎用版（USER_GUIDE/00_index.md あり）の場合:**
- 体系: 汎用版（user-guide スキル生成）
- 委譲先: `/user-guide --from-tickets docs/tickets{YYYYMMDD}/`
- 結果: user-guide 軽量モードの完了報告を転記
  - 04_history.md: 追記済（必ず）
  - 02_architecture.md: 影響あり/なし
  - 03_tech_stack.md: 影響あり/なし
  - 06_glossary.md: 影響あり/なし
  - 99_open_questions.md: 影響あり/なし

**MEOcli 専用版（Authentication.md 等あり）の場合:**
- 更新: `USER_GUIDE/Authentication.md` — ロール定義にXXXを追加
- 新規: `USER_GUIDE/Onboarding.md` — オンボーディングフローの説明
- スキップ: 内部リファクタリングのみ、外部仕様への影響なし

**USER_GUIDE/ なしの場合:**
- スキップ。「`/user-guide` で初回生成を検討」と案内

（上記のうち体系判定結果に応じたものを記載）

### 生成ファイル一覧
- `ticket_index.md`
- `{PREFIX}-001_{slug}.md`
- ...

---

### 次のアクション（推奨フロー）

1. **計画品質ゲート（任意）**: `/ticket-review docs/tickets{YYYYMMDD}/`
   - Codex セカンドオピニオンによる adversarial review（最大 3 ラウンド）
   - 軽微な変更でスキップしたい場合は省略可
2. **実装開始**: `/ko docs/tickets{YYYYMMDD}/ticket_index.md Phase 1`
   - 🔒/HIGH/セキュリティ系チケットでは strict モードが自動発動
3. **Phase 完了ごと**: `/cr` でレビュー → `/next` で次 Phase へ
4. **全 Phase 完了後**: `/ticket-verify docs/tickets{YYYYMMDD}/`
   - 並列サブエージェントによる実装検証
   - `/next` から自動推奨される
```

## チケット分解のガイドライン

### 良い分解

- 1チケット = 1つの明確な成果物
- ファイルの移動/リネーム → 1チケット
- API変更 + UI変更 → 別チケット（依存関係で順序付け）
- テスト更新 → 対象チケットに含める（別チケットにしない）

### 避けるべき分解

- 1ファイルの1行変更を独立チケットにしない
- 密結合な変更を無理に分割しない
- ドキュメント更新だけのチケットが多すぎない（1つにまとめる）

## /ko スキルとの連携

- `ticket_index.md` のPhase構成を `/ko` が参照
- 同一Phase内のチケットをサブエージェントで並列実行
- 各チケットの `作業内容` セクションが `/ko` のタスク分解入力になる
- 使い方: `/ko docs/tickets{YYYYMMDD}/ticket_index.md Phase 1`

## 既存ディレクトリとの共存

生成前に `docs/tickets{YYYYMMDD}/` の存在を確認:

- **存在しない**: そのまま作成
- **存在する**: suffix を付与 (`_v2`, `_checks`, `_refactor` 等、レポート内容に応じて)
- **ユーザーに確認**: 上書きの場合は必ず確認を取る

## テンプレート参照

- [references/ticket_template.md](references/ticket_template.md) — 個別チケットテンプレート
- [references/index_template.md](references/index_template.md) — ticket_index.md テンプレート
