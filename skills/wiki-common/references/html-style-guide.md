# HTML 可視化スタイルガイド（正本）

> **適用範囲**: wiki 系（wiki-view / wiki-dashboard / wiki-visualize、ライトテーマ・JS 禁止）のみ。
> スキル可視化系（shime / manual-todo / source-explainer / tech-intro-writer / user-guide 等のダークテーマ）の正本は
> `visualize-common/references/style-guide.md` を参照すること。

`wiki-visualize`（→ REB-025 で `wiki-view` へ migration 予定）が持っていたインライン CSS・カラーパレット・HTML スニペットをここに集約する。

## 大原則（CSP 堅牢性）

- **JS を一切使わない**（Obsidian / vault 同期 / CSP / 印刷すべてに堅牢にするため）
- **外部リソース読込禁止**（フォント CDN・画像 URL・スクリプト）。すべて `system-ui` フォント＋インライン SVG
- 1 ファイル自己完結（CSS インライン・外部依存ゼロ）
- フォント: `system-ui, -apple-system, "Segoe UI", "Hiragino Kaku Gothic ProN", sans-serif`
- `@media print` で背景色除去・改ページ調整・URL を脚注表示
- `@media (max-width: 768px)` で 1 カラムにフォールバック

## カラーパレット（医療/ビジネス向け落ち着いた青グレー系）

```css
--bg: #f8fafc;          /* 背景 */
--surface: #ffffff;     /* カード背景 */
--surface-2: #f1f5f9;   /* セクション背景 */
--border: #e2e8f0;      /* 境界線 */
--text: #0f172a;        /* 主要テキスト */
--text-muted: #64748b;  /* 補助テキスト */
--primary: #2563eb;     /* プライマリ（青） */
--primary-soft: #dbeafe;
--accent: #0ea5e9;      /* アクセント */
--success: #16a34a;     /* 良い・低リスク */
--success-soft: #dcfce7;
--warning: #f59e0b;     /* 注意・中 */
--warning-soft: #fef3c7;
--danger: #dc2626;      /* 危険・高 */
--danger-soft: #fee2e2;
--purple: #7c3aed;      /* P1 等の特別強調 */
--purple-soft: #ede9fe;
```

## Markdown → HTML 視覚要素マッピング

| Markdown 要素 | HTML 視覚要素 |
|---|---|
| H1 タイトル + frontmatter | ヘッダーカード（タイトル・confidence バッジ・更新日・domain チップ） |
| 「## 1. ...」「## 2. ...」 | セクションカード（番号付きアコーディオン風） |
| 「### 結論」「### 核」「### TL;DR」 | 強調カラーボックス（左ボーダー青・大きめフォント） |
| テーブル | ダッシュボードテーブル（ヘッダ強調・ストライプ・hover） |
| 「メリット」「デメリット」リスト | 対比カード2列（緑/赤） |
| 「優先順位 P1/P2/P3」 | 優先度バッジ（赤/黄/緑） |
| 「Phase 0/1/2...」 | ロードマップ水平タイムライン（SVG or flex） |
| `[[wikilink]]` | Obsidian URI リンク（下記） |
| 「buy/build/NG」「3区分」 | 3分割カードレイアウト（カラーコード） |
| 数値（％・件数） | メトリクスカード（大文字数字＋ラベル） |
| ASCII 図 | SVG に再描画 |

判断基準: 元 Markdown の構造を尊重しつつ「読むより見る」体験になるかを毎セクション自問する。3 セクション以上テキストが続いたらカードで割る。

## 構成図（積極的に描く）

元 Markdown に図が無くても、**構成・フロー・依存関係・因果チェーンなど図解できる構造を見つけたら、インライン SVG の構成図を積極的に描く**。テキストの説明が 3 段落を超えそうな関係性は図が先。

- `viewBox` 指定でレスポンシブに。ノードは `rect`+`text`、矢印は `path`+`marker-end`
- 配色はページのカラー変数に合わせる。外部画像・Mermaid CDN・draw.io 形式は使わない（自己完結原則）

## Obsidian リンク変換規約

```html
<a href="obsidian://open?vault=LLM_Wiki&file=wiki%2Fconcepts%2F<URL-encoded-name>">ページ名</a>
```

- vault 名は `LLM_Wiki`（実体パス `~/Obsidian/LLM_Wiki`）
- ページ名は `encodeURIComponent` 相当で URL エンコード、拡張子 `.md` は付けない

## コンポーネント例

**ヘッダーカード**:
```html
<header class="dash-hero">
  <div class="hero-tags">
    <span class="chip chip-domain">clinic-management</span>
    <span class="chip chip-confidence">confidence: medium</span>
    <span class="chip chip-date">2026-06-21</span>
  </div>
  <h1 class="hero-title">ページタイトル</h1>
  <p class="hero-lead">1〜2文の要約</p>
</header>
```

**メトリクスカード**:
```html
<div class="metrics-grid">
  <div class="metric-card">
    <div class="metric-value">7</div>
    <div class="metric-label">既存自作資産</div>
  </div>
</div>
```

**カラーボックス（重要度別）**:
```html
<div class="callout callout-primary"><strong>結論</strong>: ...</div>
<div class="callout callout-success">...</div>
<div class="callout callout-warning">...</div>
<div class="callout callout-danger">...</div>
```

**3分割カード（buy/build/NG 等）**:
```html
<div class="triptych">
  <div class="card card-success"><h3>buy（買う）</h3>...</div>
  <div class="card card-primary"><h3>build（自作可）</h3>...</div>
  <div class="card card-danger"><h3>NG（自作NG）</h3>...</div>
</div>
```

**ロードマップ（水平タイムライン）**:
```html
<ol class="roadmap">
  <li class="phase">
    <span class="phase-num">Phase 0</span>
    <span class="phase-period">1-2ヶ月</span>
    <span class="phase-content">SSOT 確定...</span>
  </li>
</ol>
```

## レイアウト

- 最大幅 1200px・中央寄せ・左右パディング 24px
- セクション間 48px、カード間 24px グリッド

## 出力ディレクトリ構造

```
~/Obsidian/LLM_Wiki/meta/reports/
└── [YYYY-MM-DD]_[slug]/
    ├── index.md          # Obsidian 内表示用ラッパー
    ├── report.html       # 自己完結フル HTML
    └── assets/           # （あれば。SVG・小画像）
```

## Obsidian 内表示用 Markdown ラッパー（index.md）

- frontmatter: `type: report`, `domain`, `source: [[元ページ名]]`, `created`, `report_for`
- 中身: ヘッダー（対象ページへのバックリンク）→「フル HTML レポートを開く」リンク（`[ブラウザで開く](report.html)` ＋ `file:///絶対パス` 併記）→ サマリ抜粋 → 元ページへの `[[wikilink]]`
- Obsidian 標準ではラッパー内リンクがブラウザに飛ばないことがあるため、`file:///絶対パス` と Bash `open` コマンドも併記する
