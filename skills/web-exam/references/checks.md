# 自動チェック項目リファレンス

## チェックスクリプト一覧

全スクリプトは `scripts/` 配下。`browser-use eval "$(cat scripts/xxx.js)"` で実行し、JSON を取得する。

### 1. inject-monitors.js — コンソール監視の注入

**実行タイミング**: ページ遷移直後（フローの最初）
**戻り値**: `"monitors injected"` or `"already injected"`

捕捉対象:
- `console.error()` / `console.warn()` の呼び出し
- `window.onerror`（未捕捉JS例外）
- `unhandledrejection`（未捕捉Promise拒否）

### 2. collect-monitors.js — 監視データ回収

**実行タイミング**: フロー終了時
**戻り値**: JSON

```json
{
  "errors": [{"ts": 1234, "msg": "...", "src": "file:line"}],
  "warnings": [{"ts": 1234, "msg": "..."}],
  "performance": {
    "timing": {"dns": 0, "tcp": 0, "ttfb": 50, "domReady": 200, "load": 500},
    "resources": {"total": 30, "totalSize": 512000, "slowest": [...]},
    "first-paint": 100,
    "first-contentful-paint": 200,
    "cls": 0.05
  }
}
```

### 3. a11y-check.js — アクセシビリティチェック

**チェック項目** (10項目):

| チェック | 内容 |
|---------|------|
| heading-hierarchy | 見出しレベルの飛び検出 |
| h1-exists | h1 要素の存在 |
| h1-single | h1 が1つだけか |
| img-alt | img の alt 属性 |
| form-labels | フォーム要素のラベル |
| button-text | ボタンのテキスト |
| link-text | リンクのテキスト |
| lang-attr | html の lang 属性 |
| viewport-meta | viewport メタタグ |
| tabindex | tabindex > 0 の検出 |
| aria-hidden-focusable | aria-hidden 内のフォーカス可能要素 |

### 4. seo-check.js — SEO チェック

**チェック項目** (11項目):

| チェック | 内容 |
|---------|------|
| title-exists | title タグの存在 |
| title-length | title の長さ (10-60文字) |
| meta-description | meta description の存在 |
| meta-desc-length | meta description の長さ (50-160文字) |
| canonical | canonical URL |
| ogp-title/desc/image/url | OGP タグ |
| twitter-card | Twitter Card |
| single-h1 | h1 が1つ |
| img-alt-seo | img の alt |
| structured-data | JSON-LD 構造化データ |

### 5. security-check.js — セキュリティチェック

**チェック項目** (8項目):

| チェック | 内容 |
|---------|------|
| https | HTTPS 使用 |
| mixed-content | HTTP リンクの検出 |
| form-action-https | フォーム送信先の HTTPS |
| password-autocomplete | パスワード入力の autocomplete |
| sri | 外部スクリプトの SRI (integrity) |
| iframe-sandbox | 外部 iframe の sandbox |
| no-inline-handlers | インラインイベントハンドラ |
| noopener | target=_blank の rel=noopener |

### 6. page-audit.js — ページ総合監査

**取得データ**:

| カテゴリ | 内容 |
|---------|------|
| images | 総数、alt なし、lazy loading なし、大サイズ画像 |
| links | 総数、壊れたリンク、外部リンク数 |
| forms | 総数、各フォームの action/method/inputs |
| viewport | 幅・高さ・devicePixelRatio |
| dom | 総要素数、最大ネスト深度 |

## パフォーマンス指標の目安

| 指標 | 良好 | 要改善 | 不良 |
|------|------|--------|------|
| TTFB | < 200ms | 200-600ms | > 600ms |
| FCP (first-contentful-paint) | < 1800ms | 1800-3000ms | > 3000ms |
| DOM Ready | < 2500ms | 2500-4000ms | > 4000ms |
| Load | < 3000ms | 3000-5000ms | > 5000ms |
| CLS | < 0.1 | 0.1-0.25 | > 0.25 |
| リソース総サイズ | < 1MB | 1-3MB | > 3MB |
