---
name: wiki-visualize
description: LLM_Wiki（~/Obsidian/LLM_Wiki/）の concept/opinion ページや wiki-prospect の成果物を「ダッシュボード風 HTML レポート」に可視化するスキル。ハイブリッド出力（Obsidian 内表示用 .md ラッパー＋自己完結フル HTML）で、Obsidian からは Markdown ラッパー経由でブラウザに HTML を投げる構成。JS なし・インライン CSS のみ・vault 同期/CSP に堅牢。発動条件 (1) /wiki-visualize <ページパス or "最新"> コマンド (2)「HTML レポートで可視化」「ダッシュボード化」「wiki-visualize」「Obsidianで見やすく」等のキーワード (3) wiki-prospect / wiki-absorb / wiki-essay 完了直後に「成果物を視覚化したい」と言われたとき。LLM_Wiki 文脈でのみ使用。コード/シミュレーション/データ分析のグラフ可視化には使わない（その場合は別途 Python/Plotly 等を直接使う）。
---

# wiki-visualize — wiki ページをダッシュボード風 HTML に可視化

LLM_Wiki の concept ページや prospect 成果物を、視覚的に把握しやすい **ダッシュボード風 HTML レポート** に変換する。Obsidian でそのまま見られる Markdown ラッパーと、ブラウザで開く自己完結 HTML の **ハイブリッド出力**。

## このスキルの位置づけ
- 入力: 既存の wiki ページ（1 つまたは複数）
- 出力: vault 内 `meta/reports/[YYYY-MM-DD]_[slug]/` に `index.md` + `report.html`（+必要なら `assets/`）
- DRY: wiki ページの内容は転記しない。**Markdown 本文を構造化抽出して視覚要素に再配置**する
- 非破壊: 元 wiki ページは触らない（リンクの追記のみ提案）

## 必ず最初に読む
1. `~/Obsidian/LLM_Wiki/CLAUDE.md` — schema/規約
2. `~/Obsidian/LLM_Wiki/config.md` — 入口の一覧
3. このスキルの `templates/` （後述、テンプレ HTML/CSS）

## モード
- **single モード**: 1 ページの HTML レポート化（最頻）
- **multi モード**: 複数ページを 1 レポートに統合（例: clinic-erp 関連 3 ページを 1 つに）
- **digest モード**: ドメインハブから派生する全 concept をオーバービュー化

## Phase（共通）

### Phase 1: 対象決定と読み込み
- 引数で指定された wiki ページ（複数可）を Read
- 「最新」キーワードなら log.md の最新 prospect/ingest を起点に該当 concept を抽出
- frontmatter から `title` `type` `domain` `tags` `confidence` を取得
- 本文の章構造（H2/H3）を解析し、視覚要素にマッピング

### Phase 2: 視覚要素マッピング（**重要**）
| Markdown 要素 | HTML 視覚要素 |
|---|---|
| H1 タイトル + frontmatter | **ヘッダーカード**（タイトル・confidence バッジ・更新日・domain チップ） |
| 「## 1. ...」「## 2. ...」 | **セクションカード**（番号付きアコーディオン風） |
| 「### 結論」「### 核」「### TL;DR」 | **強調カラーボックス**（左ボーダー青・大きめフォント） |
| テーブル | **ダッシュボードテーブル**（ヘッダ強調・ストライプ・hover） |
| 「メリット」「デメリット」リスト | **対比カード2列**（緑/赤） |
| 「優先順位 P1/P2/P3」 | **優先度バッジ**（赤/黄/緑） |
| 「Phase 0/1/2...」 | **ロードマップ水平タイムライン**（SVG or flex） |
| `[[wikilink]]` | Obsidian URI リンク（後述） |
| 「buy/build/NG」「3区分」 | **3分割カードレイアウト**（カラーコード） |
| 数値（％・件数） | **メトリクスカード**（大文字数字＋ラベル） |
| ASCII 図（```...```）| SVG に再描画 |

> **判断基準**: 元 Markdown の構造を尊重しつつ、「読むより見る」体験になるかを毎セクション自問する。3 セクション以上テキストが続いたらカードで割る。

### Phase 3: HTML 生成（テンプレート）
- スタイルは下記「ダッシュボード風スタイルガイド」に準拠
- 1 ファイル自己完結（CSS インライン・外部依存ゼロ・JS なし）
- Obsidian の CSP 制約を回避（`onload` 等の inline JS、外部 fetch、外部 font CDN は **禁止**）
- フォントは `system-ui, -apple-system, "Segoe UI", "Hiragino Kaku Gothic ProN", sans-serif`
- レポートは A4 で印刷しても破綻しない（@media print）

### Phase 4: Obsidian 内表示用 Markdown ラッパー
- `index.md` を `meta/reports/[YYYY-MM-DD]_[slug]/` に作成
- frontmatter: `type: report`, `domain`, `source: [[元ページ名]]`, `created`, `report_for`
- 中身:
  - ヘッダー（タイトル・対象ページへのバックリンク）
  - **「フル HTML レポートを開く」リンク**: `[ブラウザで開く](report.html)` ＋ macOS 用 `[open コマンドでブラウザ起動](file://...絶対パス)`
  - サマリ抜粋（HTML の主要メトリクス・結論カードのテキスト版）
  - 元ページへの `[[wikilink]]`

### Phase 5: 反映
- 元 wiki ページの末尾に「## 可視化レポート」節を追加する **提案**（自動編集はせずユーザー承認）
- `meta/reports/log.md`（無ければ新規）に1行追記
- 大幅な可視化なら `log.md` 本体にも 1 行
- index 反映は提案のみ（ノイズ防止）

## Obsidian リンク変換規約

HTML 内で `[[ページ名]]` を表現するときは **Obsidian URI スキーマ** を使う:
```html
<a href="obsidian://open?vault=LLM_Wiki&file=wiki%2Fconcepts%2F<URL-encoded-name>">ページ名</a>
```

- vault 名は `LLM_Wiki`（実体パス `~/Obsidian/LLM_Wiki`）
- ページ名は `encodeURIComponent` 相当で URL エンコード
- 拡張子 `.md` は付けない（Obsidian が解決）
- 同時に「ブラウザで HTML を見ながら Obsidian の元ページを開ける」になる

## ダッシュボード風スタイルガイド（必須）

### カラーパレット（医療/ビジネス向け落ち着いた青グレー系）
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

### コンポーネント例（SKILL に書き出す典型 HTML）

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

**メトリクスカード（KPI 風）**:
```html
<div class="metrics-grid">
  <div class="metric-card">
    <div class="metric-value">7</div>
    <div class="metric-label">既存自作資産</div>
  </div>
  <!-- ... -->
</div>
```

**カラーボックス（重要度別）**:
```html
<div class="callout callout-primary">
  <strong>結論</strong>: ...
</div>
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
  <!-- ... -->
</ol>
```

**SVG 構造図（n8n ハブの中央配置等）**:
- 横幅 100% で縦横比固定
- 矢印・ボックスは flat デザイン、影なし
- ラベルは画像ではなく `<text>` で（コピー可能・検索可能・アクセシブル）

### レイアウト
- 最大幅 1200px・中央寄せ・左右パディング 24px
- セクション間 48px
- カード間 24px グリッド
- `@media (max-width: 768px)` で 1 カラム

### 印刷スタイル
- `@media print` で背景色除去・改ページ調整・URL を脚注表示

## 出力ディレクトリ構造

```
~/Obsidian/LLM_Wiki/meta/reports/
└── 2026-06-21_clinic-vibe-erp/
    ├── index.md          # Obsidian 内表示用ラッパー
    ├── report.html       # 自己完結フル HTML
    └── assets/           # （あれば。SVG・小画像）
```

`meta/reports/log.md` には:
```
## [2026-06-21] visualize | 2026-06-21_clinic-vibe-erp/
- 対象: [[クリニック向け vibe coding ERP — 自作領域マップと統合設計]]
- モード: single
```

## 注意
- 元 wiki ページの内容を **書き換えない**（リンク追記のみ提案）。
- HTML は **JS を一切使わない**（Obsidian / vault 同期 / CSP / 印刷 すべてに堅牢にするため）。
- 外部リソース読込（フォント CDN・画像 URL・スクリプト）禁止。すべて `system-ui` フォント＋インライン SVG。
- 出典・confidence は HTML にも必ず明記（元 frontmatter から転写）。
- 大きすぎる concept ページは **複数セクションに分割した HTML を1 ページ内タブ風ナビ**（CSS のみで `<details>` 利用）にして縦長を防ぐ。
- 「ダッシュボード」と言って実データの可視化を期待されたら断る（このスキルは概念ページの構造可視化が用途。実データの数値可視化なら Python/Plotly を別途使う）。

## 互換性メモ
- Obsidian のコアレンダラは Markdown 内 HTML を制限的にサポート（CSS 一部のみ）。ラッパー `index.md` は **テキスト中心**にし、複雑な HTML は `report.html` 側に寄せる。
- ラッパー内の `[ブラウザで開く](report.html)` は Obsidian 標準ではブラウザに飛ばないことがある。**併記**: `[ファイルパス](file:///絶対パス)` と、Bash で `open` する 1 行コマンドも案内する。
