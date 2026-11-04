![otola-skills](assets/hero.png)

# otola-skills

音良林太郎が自作した Claude Code のスキル・コマンド集です。プロジェクト管理、監査、執筆支援、エージェント協調、ブラウザ検証など、実運用で使っているものをサニタイズして公開しています。

## 導入方法

スキルは `~/.claude/skills/` にフォルダごとコピーすると使えます:

```bash
git clone https://github.com/Otola-Ryntaro/otola-skills.git
cp -R otola-skills/skills/<スキル名> ~/.claude/skills/
```

コマンドは `~/.claude/commands/` に `.md` をコピーします。

Codex 側のスキルは `~/.codex/skills/` にコピーします:

```bash
cp -R otola-skills/codex-skills/<スキル名> ~/.codex/skills/
```

一部のスキルは特定の環境（Codex CLI、oracle MCP、Playwright 等）を前提にしています。各 SKILL.md の前提セクションを確認してください。

## Claude Code と Codex の協調スキルの前提

`orca-master`、`idea-relay`、`goal-feed`、`goal-feed-impl` は、次のツールを導入した環境で動きます。agmsg と Orca は外部のプロジェクトで、このリポジトリには同梱していません。

| ツール | 役割 | 導入 |
|--------|------|------|
| [agmsg](https://github.com/fujibee/agmsg)（MIT） | Claude Code と Codex のあいだでメッセージをやり取りする | `npx agmsg` のあと、各エージェントを再起動して `/agmsg`（Codex は `$agmsg`）でチームに参加する |
| [Orca](https://github.com/stablyai/orca) | worktree とターミナルを管理する。`orca` CLI と orca-cli スキルを使う | 配布元の手順に従う |
| Codex CLI | 実装とレビューを担当する | OpenAI の手順に従う |

`goal-feed` と `goal-feed-impl` は Claude Code 側と Codex 側の 2 つで 1 組です。`skills/` と `codex-skills/` の同名スキルを両方入れてください。`orca-master` は `goal-feed` の `references/orca-protocol.md` を参照するので、`goal-feed` も必要です。

## スキル一覧（31 件）

| スキル | 概要 |
|--------|------|
| [claude-setup-check](skills/claude-setup-check/) | プロジェクトの`.claude`フォルダ構成がベストプラクティスに準拠しているか診断（コード変更なし） |
| [codex-second-opinion](skills/codex-second-opinion/) | OpenAI Codex CLIを使い、コードレビュー・設計挑戦レビューのセカンドオピニオンを行う |
| [context-audit](skills/context-audit/) | Claude Codeのコンテキスト常時消費（固定オーバーヘッド）を棚卸し・ランク付けし削減策をレポート |
| [cover-image](skills/cover-image/) | プロジェクトのヒーロー画像（OGP風トップ画像）を AI背景＋文字合成で生成し README/HTML成果物に設置 |
| [esseist](skills/esseist/) | 日本語テキストを脱AIした上で、感情の起伏を持つ三幕構成のエッセイに書き換える（polish/co-writeの2モード） |
| [first-action](skills/first-action/) | ゼロから新規サービスを立ち上げる0→1キックオフを一気通貫でオーケストレーション（要件定義→GitHub調査→スキル選定→docs作成→git init→ticket-gen→codexレビュー→/ko実行） |
| [goal-feed](skills/goal-feed/) | Codexの/goal機能とClaude Codeの並行レビューを組み合わせ、有料品質の実装ループをプランから最終監査まで協調運用 |
| [goal-feed-impl](skills/goal-feed-impl/) | チケット生成済みの状態でCC側がレビュー役として実装ループに並走する短縮版goal-feed |
| [humanizer-ja](skills/humanizer-ja/) | 日本語テキストからAI生成の痕跡を34パターンで検出・除去し自然な文章に書き直す |
| [idea-relay](skills/idea-relay/) | Orca上でClaude CodeとCodexをagmsgでつなぎ、ユーザーが毎回読んで方向を直しながらアイデアを合議で磨く |
| [manual-todo](skills/manual-todo/) | 実装完了後にユーザー本人が手作業で行う必要がある残タスクをHTML TODOリストとして出力 |
| [nakajime](skills/nakajime/) | セッション中断時に作業状況をPlans.mdへ軽量記録する中締めスキル |
| [naming-brainstorm](skills/naming-brainstorm/) | 新規サービス・アプリの名称を対話形式（ヒアリング→生成→絞り込み→衝突確認→レポート）で考案する命名パートナー |
| [orca-master](skills/orca-master/) | Orcaのメインペインを司令部にして、worktreeごとのエージェント配置とgoal-feed駆動の並行開発を統括する（実装はしない） |
| [plugin-consult](skills/plugin-consult/) | タスクに合う knowledge-work プラグイン（engineering/PM/data/design/marketing/small-business/canva 等9種）を提案し、即席Read適用またはプロジェクト単位有効化まで案内 |
| [project-audit](skills/project-audit/) | 指定プロジェクトのClaude Codeベストプラクティス適合度を外部評価し、`.claude-audit/`にスコア付きレポート出力 |
| [project-setup](skills/project-setup/) | project-auditの監査レポートに基づき、低スコア項目のClaude Code設定を自動生成・改善 |
| [saikai](skills/saikai/) | nakajime・shimeが残した記録を読み込み、現在地と次の候補を提示して作業を再開する |
| [shime](skills/shime/) | セッション終了時に日報作成とPlans.mdへの引き継ぎ保存を対話的に行う |
| [skill-publish](skills/skill-publish/) | 自作スキル・コマンドを公開リポ otola-skills へ手動同期（自作判定→サニタイズ→コピー→台帳更新→push前確認） |
| [storage-audit](skills/storage-audit/) | 放置worktree・~/.codexセッションログ・プロジェクト内蓄積ファイルをread-onlyで棚卸しし、回収可能容量と削除コマンドを提示（削除は実行しない） |
| [ticket-gen](skills/ticket-gen/) | 成果レポート（codex/配下）を作業チケットに分解し、Phase整理・管理ファイル生成を自動化 |
| [todo-hub-connect](skills/todo-hub-connect/) | 旧形式のTODO・日報HTMLを集約ハブへ登録する（ファイルはコピーしない非破壊操作） |
| [todo-tanaoroshi](skills/todo-tanaoroshi/) | manual-todoで溜まったTODOを過去の記録と照合して棚卸しし、完了確認と整理を行う |
| [ui-audit](skills/ui-audit/) | テスト通過済みプロダクトの実地ブラウザUI監査。全ページをPhase分割で巡回しCritical/Major/Minor分類のチケット化可能なレポート生成 |
| [update-scan](skills/update-scan/) | インストール済み MCP・プラグイン・スキルを棚卸しし、更新可能なものを read-only で検出しレポート |
| [visualize-common](skills/visualize-common/) | スキル可視化HTML（ダークテーマ）の共通正本。CSS・アクションファースト構成・base64スクショギャラリーを提供する参照専用アセット集 |
| [vpush](skills/vpush/) | 直前の作業内容からリリース内容を自動収集し、semverバンプ→リリースノート更新→タグ付きpushを一気通貫実行 |
| [web-exam](skills/web-exam/) | Browser Use CLIベースのブラウザ総合検証。スクショ・コンソールエラー・性能・a11y・SEO・セキュリティを自動チェック |
| [web-test](skills/web-test/) | Playwright CLIベースのブラウザ目視検証。操作ステップごとにスクショ・コンソールログ・ネットワークを記録 |
| [zero-design](skills/zero-design/) | プロジェクトを「ゼロから再設計するなら」の視点で総合分析し、根拠付き改善レポートを生成（コード変更なし） |

## Codex 側スキル一覧（2 件）

| スキル | 概要 |
|--------|------|
| [goal-feed](codex-skills/goal-feed/) | Claude Code 側 goal-feed の対。受け手、独立プランナー、実装役として動く |
| [goal-feed-impl](codex-skills/goal-feed-impl/) | Claude Code 側 goal-feed-impl の対。チケット生成済みの実装ループを回す |

## コマンド一覧（7 件）

| コマンド | 概要 |
|---------|------|
| [cr](commands/cr.md) | コードレビューを実行するコマンド |
| [fakecheck](commands/fakecheck.md) | 実装のごまかし・虚偽報告チェック |
| [ko](commands/ko.md) | チケットの Phase 単位キックオフ（並列実行対応） |
| [next](commands/next.md) | Phase 単位の進捗管理と次の作業提示 |
| [recon](commands/recon.md) | プロジェクト総ざらい→ゼロから再設計 |
| [ticket-review](commands/ticket-review.md) | Codex セカンドオピニオンによる計画品質ゲート |
| [ticket-verify](commands/ticket-verify.md) | 実装検証（並列サブエージェント） |

## 更新履歴

### 2026-11-04

- Claude Opus 5.5 向けに全スキルを点検し、呼び出せない経路、実在しない参照、ファイル同士の矛盾を修正した
- `orca-master`、`idea-relay`、`saikai`、`todo-tanaoroshi`、`todo-hub-connect` を追加した
- Codex 側の `goal-feed`、`goal-feed-impl` を `codex-skills/` に追加した
- `goal-feed` 系を Orca 前提に更新し、待機方法を `orca-protocol.md` に統一した
- `/cr --codex` と `--adversarial` の実行方法を `codex exec review` に変更した
- `manual-todo` のハブで、VS Code を開く API を POST 限定にして、他サイトから起動できないようにした
- `web-exam`、`web-test` は localhost が応答しないとき、本番へ切り替えずユーザーに確認するようにした
- `mine-check` を公開から外し、`project-audit`、`project-setup` の同名コマンドを削除した（スキルは引き続き利用可能）
- 特定プロジェクトの固有情報を除き、`web-exam`、`web-test` の `references/flows.md` を雛形にした

## License

MIT — 詳細は [LICENSE](LICENSE) を参照。

## Author

音良林太郎 ([@Otola_ryntaro](https://x.com/Otola_ryntaro))
