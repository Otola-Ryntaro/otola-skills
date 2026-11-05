![otola-skills](assets/hero.png)

# otola-skills

音良林太郎が自作した Claude Code のスキル・コマンド集です。プロジェクト管理、監査、執筆支援、エージェント協調、ブラウザ検証など、実運用で使っているものをサニタイズして公開しています。自作ではないものは[別枠](#自作ではないスキル1-件)に分けて記載しています。

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

多くのスキルは、他のスキルや外部ツールを前提にしています。導入前に、各一覧の「前提」列と[外部ツール・プラグインの入手先](#外部ツールプラグインの入手先)を確認してください。「必須」が欠けると動きません。「任意」は無くても動き、その機能だけ使えません。

## Claude Code と Codex の協調スキルの前提

`orca-master`、`idea-relay`、`goal-feed`、`goal-feed-impl` は、次のツールを導入した環境で動きます。agmsg と Orca は外部のプロジェクトで、このリポジトリには同梱していません。

| ツール | 役割 | 導入 |
|--------|------|------|
| [agmsg](https://github.com/fujibee/agmsg)（MIT） | Claude Code と Codex のあいだでメッセージをやり取りする | `npx agmsg` のあと、各エージェントを再起動して `/agmsg`（Codex は `$agmsg`）でチームに参加する |
| [Orca](https://github.com/stablyai/orca) | worktree とターミナルを管理する。`orca` CLI と orca-cli スキルを使う | 配布元の手順に従う |
| Codex CLI | 実装とレビューを担当する | OpenAI の手順に従う |

`goal-feed` と `goal-feed-impl` は Claude Code 側と Codex 側の 2 つで 1 組です。`skills/` と `codex-skills/` の同名スキルを両方入れてください。`orca-master` は `goal-feed` の `references/orca-protocol.md` を参照するので、`goal-feed` も必要です。

## 外部ツール・プラグインの入手先

一覧の「前提」列に出てくる、このリポジトリに同梱していないものです。

| 名前 | 種類 | 入手先 |
|------|------|--------|
| superpowers | Claude Code プラグイン | [claude-plugins-official](https://github.com/anthropics/claude-plugins-official) の `superpowers` |
| feature-dev | Claude Code プラグイン | [claude-plugins-official](https://github.com/anthropics/claude-plugins-official) の `feature-dev` |
| claude-code-harness | Claude Code プラグイン | [Chachamaru127/claude-code-harness](https://github.com/Chachamaru127/claude-code-harness) |
| knowledge-work-plugins | Claude Code プラグイン集 | [anthropics/knowledge-work-plugins](https://github.com/anthropics/knowledge-work-plugins) |
| find-skills | スキル | [vercel-labs/skills](https://github.com/vercel-labs/skills) |
| cognitive-rhythm-writing | スキル | [k16shikano 氏の Gist](https://gist.github.com/k16shikano/eb2929f13ed19c97188393d297be8432) |
| archify | スキル | 配布元の手順に従う |
| user-guide | スキル | 作者の非公開スキル。`USER_GUIDE/` があるプロジェクトでだけ呼ばれる |
| playwright-cli | CLI | [microsoft/playwright-cli](https://github.com/microsoft/playwright-cli) |
| Browser Use CLI | CLI | [browser-use/browser-use](https://github.com/browser-use/browser-use)。`~/.browser-use-env/bin/browser-use` に導入する前提 |
| ComfyUI | ローカル画像生成 | [Comfy-Org/ComfyUI](https://github.com/Comfy-Org/ComfyUI) |
| oracle MCP | MCP サーバー | [steipete/oracle](https://github.com/steipete/oracle) |

`/recon` と `/fakecheck` は、実行時に `npx skills add` で第三者のスキルをプロジェクトへ導入します。対象は各コマンドの行に記載しました。

## スキル一覧（29 件）

この一覧のスキル・コマンドは音良林太郎の自作です。ただし esseist の脱 AI パターンは第三者の著作物に基づきます（[第三者由来の表示](THIRD_PARTY_NOTICES.md)）。

| スキル | 概要 | 前提 |
|--------|------|------|
| [claude-setup-check](skills/claude-setup-check/) | プロジェクトの`.claude`フォルダ構成がベストプラクティスに準拠しているか診断（コード変更なし） | なし |
| [context-audit](skills/context-audit/) | Claude Codeのコンテキスト常時消費（固定オーバーヘッド）を棚卸し・ランク付けし削減策をレポート | 必須: Python 3 |
| [cover-image](skills/cover-image/) | プロジェクトのヒーロー画像（OGP風トップ画像）を AI背景＋文字合成で生成し README/HTML成果物に設置 | 必須: Playwright（`npx playwright`）。任意: 背景生成は Codex CLI、ComfyUI、Gemini API キー、oracle MCP のいずれか（どれも無ければ HTML/SVG のみで構成。Codex と ComfyUI の経路は jq も使う）、agmsg |
| [esseist](skills/esseist/) | 日本語テキストを脱AIした上で、感情の起伏を持つ三幕構成のエッセイに書き換える（polish/co-writeの2モード） | 任意: cognitive-rhythm-writing |
| [first-action](skills/first-action/) | ゼロから新規サービスを立ち上げる0→1キックオフを一気通貫でオーケストレーション（要件定義→GitHub調査→スキル選定→docs作成→git init→ticket-gen→codexレビュー→/ko実行） | 必須: superpowers、find-skills、ticket-gen、codex-second-opinion と Codex CLI、/ko、/next。任意: cover-image |
| [goal-feed](skills/goal-feed/) | Codexの/goal機能とClaude Codeの並行レビューを組み合わせ、有料品質の実装ループをプランから最終監査まで協調運用 | 必須: agmsg、Orca、Codex CLI、Codex 側 goal-feed、ticket-gen、/ko、/cr、/next、/ticket-verify、shime。任意: feature-dev |
| [goal-feed-impl](skills/goal-feed-impl/) | チケット生成済みの状態でCC側がレビュー役として実装ループに並走する短縮版goal-feed | 必須: agmsg、Orca、Codex CLI、goal-feed（references を共有）、Codex 側 goal-feed-impl、ticket-gen、/ko、/cr、/next、/ticket-verify、shime |
| [idea-relay](skills/idea-relay/) | Orca上でClaude CodeとCodexをagmsgでつなぎ、ユーザーが毎回読んで方向を直しながらアイデアを合議で磨く | 必須: agmsg、Orca、Codex CLI |
| [manual-todo](skills/manual-todo/) | 実装完了後にユーザー本人が手作業で行う必要がある残タスクをHTML TODOリストとして出力 | 必須: Python 3。任意: visualize-common |
| [nakajime](skills/nakajime/) | セッション中断時に作業状況をPlans.mdへ軽量記録する中締めスキル | なし（再開には saikai を使う） |
| [naming-brainstorm](skills/naming-brainstorm/) | 新規サービス・アプリの名称を対話形式（ヒアリング→生成→絞り込み→衝突確認→レポート）で考案する命名パートナー | なし |
| [orca-master](skills/orca-master/) | Orcaのメインペインを司令部にして、worktreeごとのエージェント配置とgoal-feed駆動の並行開発を統括する（実装はしない） | 必須: agmsg、Orca、Codex CLI、goal-feed。任意: idea-relay、codex-second-opinion、Cursor、Hermes Agent |
| [plugin-consult](skills/plugin-consult/) | タスクに合う knowledge-work プラグイン（engineering/PM/data/design/marketing/small-business/canva 等9種）を提案し、即席Read適用またはプロジェクト単位有効化まで案内 | 必須: knowledge-work-plugins |
| [project-audit](skills/project-audit/) | 指定プロジェクトのClaude Codeベストプラクティス適合度を外部評価し、`.claude-audit/`にスコア付きレポート出力 | なし |
| [project-setup](skills/project-setup/) | project-auditの監査レポートに基づき、低スコア項目のClaude Code設定を自動生成・改善 | 必須: project-audit のレポート |
| [saikai](skills/saikai/) | nakajime・shimeが残した記録を読み込み、現在地と次の候補を提示して作業を再開する | 必須: nakajime または shime が残した Plans.md |
| [shime](skills/shime/) | セッション終了時に日報作成とPlans.mdへの引き継ぎ保存を対話的に行う | 任意: manual-todo、todo-tanaoroshi、visualize-common、first-action のテンプレート、archify、agmsg、Orca |
| [skill-publish](skills/skill-publish/) | 自作スキル・コマンドを公開リポ otola-skills へ手動同期（自作判定→サニタイズ→コピー→台帳更新→push前確認） | 作者の公開運用専用。任意: gh |
| [storage-audit](skills/storage-audit/) | 放置worktree・~/.codexセッションログ・プロジェクト内蓄積ファイルをread-onlyで棚卸しし、回収可能容量と削除コマンドを提示（削除は実行しない） | なし |
| [ticket-gen](skills/ticket-gen/) | 成果レポート（codex/配下）を作業チケットに分解し、Phase整理・管理ファイル生成を自動化 | 必須: /ko、/next（生成物の実行先）。任意: /ticket-verify、user-guide |
| [todo-hub-connect](skills/todo-hub-connect/) | 旧形式のTODO・日報HTMLを集約ハブへ登録する（ファイルはコピーしない非破壊操作） | 必須: manual-todo |
| [todo-tanaoroshi](skills/todo-tanaoroshi/) | manual-todoで溜まったTODOを過去の記録と照合して棚卸しし、完了確認と整理を行う | 必須: manual-todo |
| [ui-audit](skills/ui-audit/) | テスト通過済みプロダクトの実地ブラウザUI監査。全ページをPhase分割で巡回しCritical/Major/Minor分類のチケット化可能なレポート生成 | 必須: web-exam、Browser Use CLI。任意: ticket-gen |
| [update-scan](skills/update-scan/) | インストール済み MCP・プラグイン・スキルを棚卸しし、更新可能なものを read-only で検出しレポート | 必須: Python 3、gh |
| [visualize-common](skills/visualize-common/) | スキル可視化HTML（ダークテーマ）の共通正本。CSS・アクションファースト構成・base64スクショギャラリーを提供する参照専用アセット集 | なし |
| [vpush](skills/vpush/) | 直前の作業内容からリリース内容を自動収集し、semverバンプ→リリースノート更新→タグ付きpushを一気通貫実行 | 任意: gh（CI の確認と GitHub Releases） |
| [web-exam](skills/web-exam/) | Browser Use CLIベースのブラウザ総合検証。スクショ・コンソールエラー・性能・a11y・SEO・セキュリティを自動チェック | 必須: Browser Use CLI |
| [web-test](skills/web-test/) | Playwright CLIベースのブラウザ目視検証。操作ステップごとにスクショ・コンソールログ・ネットワークを記録 | 必須: playwright-cli |
| [zero-design](skills/zero-design/) | プロジェクトを「ゼロから再設計するなら」の視点で総合分析し、根拠付き改善レポートを生成（コード変更なし） | 任意: ticket-gen、codex-second-opinion |

## 自作ではないスキル（1 件）

外部のものをコピーして取り込み、手元で更新しているスキルです。出典を特定できていないため、このリポジトリの MIT ライセンスの対象外です（[SOURCE.md](skills/codex-second-opinion/SOURCE.md)）。

| スキル | 概要 | 前提 |
|--------|------|------|
| [codex-second-opinion](skills/codex-second-opinion/) | OpenAI Codex CLIを使い、コードレビュー・設計挑戦レビューのセカンドオピニオンを行う | 必須: Codex CLI |

## Codex 側スキル一覧（2 件）

| スキル | 概要 | 前提 |
|--------|------|------|
| [goal-feed](codex-skills/goal-feed/) | Claude Code 側 goal-feed の対。受け手、独立プランナー、実装役として動く | 必須: agmsg、Orca、Claude Code 側 goal-feed、ticket-gen、/ko、/cr、/next、/ticket-verify、shime |
| [goal-feed-impl](codex-skills/goal-feed-impl/) | Claude Code 側 goal-feed-impl の対。チケット生成済みの実装ループを回す | 必須: agmsg、Orca、Claude Code 側 goal-feed-impl、ticket-gen、/ko、/cr、/next、/ticket-verify、shime |

## コマンド一覧（7 件）

| コマンド | 概要 | 前提 |
|---------|------|------|
| [cr](commands/cr.md) | コードレビューを実行するコマンド | 必須: claude-code-harness または feature-dev（既定のレビュー手段）。任意: Codex CLI（`--codex`、`--adversarial`）、superpowers |
| [fakecheck](commands/fakecheck.md) | 実装のごまかし・虚偽報告チェック | 実行時に導入: `dagster-io/erk@fake-driven-testing`、`bobmatnyc/claude-mpm-skills@testing-anti-patterns` |
| [ko](commands/ko.md) | チケットの Phase 単位キックオフ（並列実行対応） | 必須: ticket-gen のチケット、/cr、/next。任意: superpowers（`--fresh`） |
| [next](commands/next.md) | Phase 単位の進捗管理と次の作業提示 | 必須: ticket-gen のチケット |
| [recon](commands/recon.md) | プロジェクト総ざらい→ゼロから再設計 | 実行時に導入: `outfitter-dev/agents@codebase-recon`、`openhands/skills@codereview-roasted`、`aj-geddes/claude-code-bmad-skills@system-architect` |
| [ticket-review](commands/ticket-review.md) | Codex セカンドオピニオンによる計画品質ゲート | 必須: ticket-gen、codex-second-opinion、Codex CLI（無いとレビューをスキップ） |
| [ticket-verify](commands/ticket-verify.md) | 実装検証（並列サブエージェント） | 必須: ticket-gen のチケット |

## 更新履歴

### 2026-11-05

- `humanizer-ja` を公開から外した（[blader/humanizer](https://github.com/blader/humanizer) の翻案で、自作ではないため）
- `esseist` に原著の表記を追加し、[第三者由来の表示](THIRD_PARTY_NOTICES.md)を置いた
- `codex-second-opinion` を自作の一覧から分け、由来を注記した
- 全スキル・コマンドの一覧に「前提」列を追加し、外部ツール・プラグインの入手先をまとめた

### 2026-11-04

- Claude Opus 5.5 向けに全スキルを点検し、呼び出せない経路、実在しない参照、ファイル同士の矛盾を修正した
- `orca-master`、`idea-relay`、`saikai`、`todo-tanaoroshi`、`todo-hub-connect` を追加した
- Codex 側の `goal-feed`、`goal-feed-impl` を `codex-skills/` に追加した
- `goal-feed` 系を Orca 前提に更新し、待機方法を `orca-protocol.md` に統一した
- `/cr --codex` と `--adversarial` の実行方法を `codex exec review` に変更した
- `manual-todo` のハブで、VS Code を開く API を POST 限定にして、他サイトから起動できないようにした
- `manual-todo` のハブの配信範囲を画面に必要なファイルだけに絞り、取り込んだレポートをサンドボックスで表示するようにした
- `web-exam`、`web-test` は localhost が応答しないとき、本番へ切り替えずユーザーに確認するようにした
- `mine-check` を公開から外し、`project-audit`、`project-setup` の同名コマンドを削除した（スキルは引き続き利用可能）
- 特定プロジェクトの固有情報を除き、`web-exam`、`web-test` の `references/flows.md` を雛形にした

## License

MIT — 詳細は [LICENSE](LICENSE) を参照。第三者に由来する部分の扱いは [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) を参照。

## Author

音良林太郎 ([@Otola_ryntaro](https://x.com/Otola_ryntaro))
