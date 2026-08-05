# knowledge-work-plugins カタログ

<!-- where: plugin-consult スキルの参照データ / what: インストール済み knowledge-work プラグイン9種の要約 / why: タスク照合の判断材料 -->

マーケットプレイス: `anthropics/knowledge-work-plugins`（user スコープでインストール済み・2026-07-19 時点）

各プラグインのスキルは有効化されていればセッション内で直接呼び出せる。無効化されている場合は
`~/.claude/plugins/cache/knowledge-work-plugins/<plugin>/<version>/skills/<skill>/SKILL.md` を Read すれば即席適用できる。

## engineering — 技術ワークフロー全般

コードレビュー・設計判断・障害対応・技術文書。コネクタ不要でそのまま使えるものが多い。

- architecture: ADR（アーキテクチャ決定記録）の作成・評価
- code-review: セキュリティ・性能・正確性のコードレビュー
- debug: 再現→切り分け→診断→修正の構造化デバッグ
- deploy-checklist: リリース前チェックリスト
- documentation: README・runbook・オンボーディング文書
- incident-response: 障害対応（トリアージ→周知→ポストモーテム）
- standup: 直近の活動からスタンドアップ報告を生成
- system-design: システム設計・アーキテクチャ検討
- tech-debt: 技術的負債の棚卸しと優先順位付け
- testing-strategy: テスト戦略・テスト計画

## product-management — 仕様・ロードマップ・リサーチ統合

- competitive-brief: 競合分析ブリーフ
- metrics-review: プロダクト指標のレビューとトレンド分析
- product-brainstorming: 壁打ち相手としての発想支援
- roadmap-update: ロードマップの作成・優先順位変更
- sprint-planning: スプリント計画（スコープ・キャパ見積もり）
- stakeholder-update: 対象別ステークホルダー報告
- synthesize-research: インタビュー・アンケートの構造化統合
- write-spec: 機能仕様書 / PRD の執筆

## enterprise-search — 横断検索（コネクタ必須）

Slack・Notion・Jira 等の MCP コネクタ接続が前提。未接続だと実質使えない。

- search: 全接続ソースの横断検索
- search-strategy: 質問をソース別クエリに分解
- knowledge-synthesis: 複数ソース結果の統合・重複排除・出典付与
- digest: 日次/週次のアクティビティダイジェスト
- source-management: 接続ソースの管理

## data — データ分析・可視化・ダッシュボード

DWH コネクタがあると強いが、ローカル CSV / SQLite でも使える。

- analyze: データ質問への回答（単発参照〜本格分析）
- explore-data: データセットのプロファイリング
- sql-queries / write-query: SQL 作成
- create-viz / data-visualization: Python での可視化
- build-dashboard: インタラクティブ HTML ダッシュボード
- statistical-analysis: 統計分析
- validate-data: データ検証
- data-context-extractor: データ文脈の抽出

## design — デザインレビュー・UXライティング

- accessibility-review: アクセシビリティレビュー
- design-critique: デザイン批評
- design-handoff: デザイン→実装の引き継ぎ
- design-system: デザインシステム
- research-synthesis / user-research: ユーザーリサーチ設計・統合
- ux-copy: マイクロコピー・エラーメッセージ・CTA の執筆/レビュー

## pdf-viewer — PDF の閲覧・注釈・フォーム記入

- view-pdf: インタラクティブ PDF ビューア（注釈・ハイライト・フォーム記入・署名配置）
- コマンド: /annotate /fill-form /open /sign

## marketing — コンテンツ制作・キャンペーン

- brand-review: ブランドボイス準拠チェック
- campaign-plan: キャンペーンブリーフ一式
- competitive-brief: 競合ポジショニング比較
- content-creation / draft-content: ブログ・SNS・メール・LP 等の執筆
- email-sequence: マルチメールシーケンス設計
- performance-report: マーケ成果レポート
- seo-audit: SEO 総合監査

## small-business — 事業運営ワークフロー（コネクタ依存が強い）

QuickBooks・PayPal・HubSpot・Canva 等の接続前提のものが多い。約30スキル。
代表: monday-brief / friday-brief（週次ブリーフ）、cash-flow-snapshot、close-month（月次締め）、
plan-payroll、invoice-chase、price-check / margin-analyzer、review-contract（契約レビュー）、
run-campaign、lead-triage / crm-cleanup、tax-prep、handle-complaint。
入口: /smb-onboard（コネクタ接続）、smb-router（振り分け）。

## canva — Canva 連携（MCP: https://mcp.canva.com/mcp、初回 OAuth 必要）

- brand-check: ブランド準拠チェック
- bulk-create: デザイン一括生成
- edit-design: 既存デザイン編集
- get-design-feedback / implement-feedback: デザインフィードバックと反映
- resize-for-social-media: SNS 向けリサイズ
- inactive-skills（無効・必要時は手動有効化）: branded-presentation, classroom-helper, design-translation, presentation-time-fitting

## タスク→プラグイン早見表

| タスクの匂い | 提案するプラグイン |
|---|---|
| PR レビュー・障害・ADR・テスト計画 | engineering |
| PRD・ロードマップ・スプリント・競合分析 | product-management |
| 「あのドキュメントどこ？」横断検索 | enterprise-search（コネクタ要確認） |
| CSV 分析・SQL・グラフ・ダッシュボード | data |
| UI 批評・a11y・UX コピー | design |
| PDF に書き込み・署名・フォーム | pdf-viewer |
| 記事・LP・メルマガ・SEO・キャンペーン | marketing |
| 資金繰り・請求・月次締め・契約・CRM | small-business（コネクタ要確認） |
| Canva でデザイン制作・編集 | canva（OAuth 要確認） |
