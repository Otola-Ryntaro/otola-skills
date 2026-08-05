![otola-skills](assets/hero.png)

# otola-skills

音良林太郎が自作した Claude Code のスキル・コマンド集です。プロジェクト管理、監査、執筆支援、wiki 運用、ブラウザ検証など、実運用で使っているものをサニタイズして公開しています。

## 導入方法

スキルは `~/.claude/skills/` にフォルダごとコピーすると使えます:

```bash
git clone https://github.com/Otola-Ryntaro/otola-skills.git
cp -R otola-skills/skills/<スキル名> ~/.claude/skills/
```

コマンドは `~/.claude/commands/` に `.md` をコピーします。

一部のスキルは特定の環境（Codex CLI、oracle MCP、Playwright、Obsidian vault 等）を前提にしています。各 SKILL.md の前提セクションを確認してください。

## スキル一覧（40 件）

| スキル | 概要 |
|--------|------|
| [claude-setup-check](skills/claude-setup-check/) | プロジェクトの`.claude`フォルダ構成がベストプラクティスに準拠しているか診断（コード変更なし） |
| [codex-second-opinion](skills/codex-second-opinion/) | OpenAI Codex CLIを使い、コードレビュー・設計挑戦レビューのセカンドオピニオンを行う |
| [context-audit](skills/context-audit/) | Claude Codeのコンテキスト常時消費（固定オーバーヘッド）を棚卸し・ランク付けし削減策をレポート |
| [esseist](skills/esseist/) | 日本語テキストを脱AIした上で、感情の起伏を持つ三幕構成のエッセイに書き換える（polish/co-writeの2モード） |
| [first-action](skills/first-action/) | ゼロから新規サービスを立ち上げる0→1キックオフを一気通貫でオーケストレーション（要件定義→GitHub調査→スキル選定→docs作成→git init→ticket-gen→codexレビュー→/ko実行） |
| [goal-feed](skills/goal-feed/) | Codexの/goal機能とClaude Codeの並行レビューを組み合わせ、有料品質の実装ループをプランから最終監査まで協調運用 |
| [goal-feed-impl](skills/goal-feed-impl/) | チケット生成済みの状態でCC側がレビュー役として実装ループに並走する短縮版goal-feed |
| [humanizer-ja](skills/humanizer-ja/) | 日本語テキストからAI生成の痕跡を34パターンで検出・除去し自然な文章に書き直す |
| [manual-todo](skills/manual-todo/) | 実装完了後にユーザー本人が手作業で行う必要がある残タスクをHTML TODOリストとして出力 |
| [mine-check](skills/mine-check/) | 大規模コード変更の計画レポートを、過去事故・障害レポートと機械的に照合し「触ると壊れる地雷」をチェック |
| [nakajime](skills/nakajime/) | セッション中断時に作業状況をPlans.mdへ軽量記録する中締めスキル |
| [naming-brainstorm](skills/naming-brainstorm/) | 新規サービス・アプリの名称を対話形式（ヒアリング→生成→絞り込み→衝突確認→レポート）で考案する命名パートナー |
| [plugin-consult](skills/plugin-consult/) | タスクに合う knowledge-work プラグイン（engineering/PM/data/design/marketing/small-business/canva 等9種）を提案し、即席Read適用またはプロジェクト単位有効化まで案内 |
| [project-audit](skills/project-audit/) | 指定プロジェクトのClaude Codeベストプラクティス適合度を外部評価し、`.claude-audit/`にスコア付きレポート出力 |
| [project-hero](skills/project-hero/) | プロジェクトのヒーロー画像（OGP風トップ画像）を AI背景＋文字合成で生成し README/HTML成果物に設置 |
| [project-setup](skills/project-setup/) | project-auditの監査レポートに基づき、低スコア項目のClaude Code設定を自動生成・改善 |
| [shime](skills/shime/) | セッション終了時に日報作成とPlans.mdへの引き継ぎ保存を対話的に行う |
| [skill-publish](skills/skill-publish/) | 自作スキル・コマンドを公開リポ otola-skills へ手動同期（自作判定→サニタイズ→コピー→台帳更新→push前確認） |
| [storage-audit](skills/storage-audit/) | 放置worktree・~/.codexセッションログ・プロジェクト内蓄積ファイルをread-onlyで棚卸しし、回収可能容量と削除コマンドを提示（削除は実行しない） |
| [ticket-gen](skills/ticket-gen/) | 成果レポート（codex/配下）を作業チケットに分解し、Phase整理・管理ファイル生成を自動化 |
| [ui-audit](skills/ui-audit/) | テスト通過済みプロダクトの実地ブラウザUI監査。全ページをPhase分割で巡回しCritical/Major/Minor分類のチケット化可能なレポート生成 |
| [update-scan](skills/update-scan/) | インストール済み MCP・プラグイン・スキルを棚卸しし、更新可能なものを read-only で検出しレポート |
| [visualize-common](skills/visualize-common/) | スキル可視化HTML（ダークテーマ）の共通正本。CSS・アクションファースト構成・base64スクショギャラリーを提供する参照専用アセット集 |
| [vpush](skills/vpush/) | 直前の作業内容からリリース内容を自動収集し、semverバンプ→リリースノート更新→タグ付きpushを一気通貫実行 |
| [web-exam](skills/web-exam/) | Browser Use CLIベースのブラウザ総合検証。スクショ・コンソールエラー・性能・a11y・SEO・セキュリティを自動チェック |
| [web-test](skills/web-test/) | Playwright CLIベースのブラウザ目視検証。操作ステップごとにスクショ・コンソールログ・ネットワークを記録 |
| [wiki-absorb](skills/wiki-absorb/) | wiki-extractの抽出ノートを深さを保ったままwiki本体（concepts/opinions/entities）へ構造化統合する段階2 |
| [wiki-clip](skills/wiki-clip/) | Obsidian Web Clipperで取り込んだWebページから使える知識だけを蒸留してwikiに統合 |
| [wiki-common](skills/wiki-common/) | 単独では発動しない共有リファレンス置き場。confidence判定基準・frontmatter規約等を他のwiki-*スキルがRead参照 |
| [wiki-dashboard](skills/wiki-dashboard/) | wiki全体を走査しドメイン別件数・confidence:low一覧・未解決の問い数を集計しmeta/dashboard.mdを更新 |
| [wiki-essay](skills/wiki-essay/) | seed（意見の芽）から読者ペルソナ×論証切り口の多角度で長文コラムを執筆（write/reflect/handoff/rebuild-threadsの4モード） |
| [wiki-extract](skills/wiki-extract/) | プロジェクトやvaultを網羅的に読み込み、深い抽出ノートをraw/staging配下に出力する2段階吸い出しの段階1 |
| [wiki-help](skills/wiki-help/) | 状況に応じてどのwiki系スキルを使うべきか案内する道案内役（実際の処理は行わない） |
| [wiki-interview](skills/wiki-interview/) | ユーザー自身の思考・違和感を対話インタビューで引き出し「育てる問い(seed)」として登録 |
| [wiki-lint](skills/wiki-lint/) | wikiの矛盾・陳腐化・孤立ページ・リンク切れ・裏取り不足を検出し修復案を提案 |
| [wiki-prospect](skills/wiki-prospect/) | 既存wiki知識を起点に手薄なドメイン・未解決の問いを検出し新しい知識を能動的に収集・拡張 |
| [wiki-query](skills/wiki-query/) | wikiに質問し関連ページを引用付きで回答、再利用価値があればページとして還元 |
| [wiki-visualize](skills/wiki-visualize/) | concept/opinionページやwiki-prospect成果物をダッシュボード風HTMLレポートに可視化 |
| [wiki-weave](skills/wiki-weave/) | 孤立ノード（リンクの無いページ）を検出し意味的に関連する既存ページへ双方向リンクを追記 |
| [zero-design](skills/zero-design/) | プロジェクトを「ゼロから再設計するなら」の視点で総合分析し、根拠付き改善レポートを生成（コード変更なし） |

## コマンド一覧（9 件）

| コマンド | 概要 |
|---------|------|
| [cr](commands/cr.md) | コードレビューを実行するコマンド |
| [fakecheck](commands/fakecheck.md) | 実装のごまかし・虚偽報告チェック |
| [ko](commands/ko.md) | チケットの Phase 単位キックオフ（並列実行対応） |
| [next](commands/next.md) | Phase 単位の進捗管理と次の作業提示 |
| [project-audit](commands/project-audit.md) | プロジェクトの Claude Code 設定品質を監査 |
| [project-setup](commands/project-setup.md) | 監査レポートに基づく設定改善 |
| [recon](commands/recon.md) | プロジェクト総ざらい→ゼロから再設計 |
| [ticket-review](commands/ticket-review.md) | Codex セカンドオピニオンによる計画品質ゲート |
| [ticket-verify](commands/ticket-verify.md) | 実装検証（並列サブエージェント） |

## License

MIT — 詳細は [LICENSE](LICENSE) を参照。

## Author

音良林太郎 ([@Otola_ryntaro](https://x.com/Otola_ryntaro))
