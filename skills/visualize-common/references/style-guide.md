# style-guide.md — ダークテーマ CSS 正本

<!--
  where: visualize-common/references/style-guide.md
  what : スキル可視化 HTML の共通 CSS（変数・コンポーネント語彙・JS ポリシー）
  why  : 各テンプレの CSS が独自進化して見た目・操作感がバラけるのを防ぐ
-->

## 大原則

- **単一ファイル自己完結**。外部 CSS / フォント / CDN / 外部画像の読み込み禁止。
- 画像は base64 data URI 埋め込みのみ許可（→ `screenshot-embed.md`）。図解はインライン SVG。
- **JS ポリシー**: 自己完結 JS のみ許可（localStorage・DOM 操作等）。外部通信（fetch / XHR / WebSocket / 外部 script）は禁止。
  ※ wiki 系（wiki-common）は JS 完全禁止のライトテーマで、本正本の対象外。
- レスポンシブ: `@media(max-width:720px)` でグリッドを 1 カラム化。

## `:root` 変数（正本ブロック — 各テンプレはこれをコピーする）

```css
:root{
  --bg:#0f1216; --card:#181c23; --card2:#1f242d; --line:#2a313c;
  --txt:#e6e9ee; --sub:#9aa4b2; --accent:#c084fc; --accent2:#7dd3fc;
  --warn:#fbbf24; --good:#34d399; --bad:#f87171; --pill:#273043;
  --gold:#fbbf24;
}
```

- `--accent` のみスキル固有色に変更してよい（shime `#c084fc` / user-guide `#5eead4` /
  source-explainer はドメイン別 / manual-todo `#4ade80`）。他の変数は変更しない。

## 基本タイポグラフィ

```css
body{margin:0;background:var(--bg);color:var(--txt);
  font-family:-apple-system,"Hiragino Kaku Gothic ProN","Yu Gothic",Meiryo,sans-serif;
  line-height:1.75;font-size:15px}
.wrap{max-width:980px;margin:0 auto;padding:32px 20px 80px}
h1{font-size:30px;margin:0 0 6px;letter-spacing:.02em}
h2{font-size:21px;margin:48px 0 14px;padding-bottom:8px;border-bottom:2px solid var(--line)}
h2 .n{color:var(--accent);font-size:15px;margin-right:8px}   /* 章番号 <span class="n">01</span> */
h3{font-size:16px;margin:22px 0 8px;color:var(--accent2)}
code{background:#0b0e12;border:1px solid var(--line);border-radius:5px;
  padding:1px 6px;font-size:13px;font-family:"SF Mono",Menlo,Consolas,monospace}
```

## 共通コンポーネント語彙

各テンプレは以下のクラス名・構造を使う。新しい見た目が必要なときも、まずこの語彙で組めないか検討する。

| クラス | 用途 |
|--------|------|
| `.kicker` | h1 上の小ラベル（レポート種別） |
| `.lead` | h1 直下の 1 行サマリ |
| `.meta` + `.pill` | プロジェクト名・日付などのメタ情報チップ列。**先頭 pill は必ず `📂 <b>{{PROJECT_NAME}}</b>`** |
| `.hero` | 冒頭の「今すぐやること」大型カード（→ `action-first.md`） |
| `.grid .g2 .g3` | カードグリッド（720px 以下で 1 カラム） |
| `.card` + `.tag` | 情報カード＋種別タグ |
| `.box warn/good/info/purple/bad` + `.ttl` | 色付きコールアウト |
| `.step` + `.num` + `.body` | 連番手順（丸数字＋本文） |
| `.flow` | ASCII / テキストフロー図（等幅・pre 相当） |
| `.quote` | 引用・決定事項 |
| `.shots` + `figure` | スクショギャラリー（→ `screenshot-embed.md`） |
| `.foot` | 末尾フッタ（生成スキル名・日付・対応ファイル） |

hero の正本 CSS:

```css
.hero{background:linear-gradient(135deg,rgba(192,132,252,.14),rgba(125,211,252,.08));
  border:1px solid var(--accent);border-radius:14px;padding:22px 24px;margin:22px 0}
.hero .ttl{font-size:13px;color:var(--accent);letter-spacing:.14em;text-transform:uppercase;
  font-weight:700;margin-bottom:10px}
.hero .action{font-size:18px;font-weight:700;margin:6px 0}
.hero .why{color:var(--sub);font-size:14px;margin:4px 0 0}
.hero code{font-size:14px}
```

## 横断規範（従来どおり維持）

- `{{PROJECT_NAME}}` にはカレントディレクトリ名（`pwd` の basename）を機械的に入れる。
- 末尾 `.foot` に生成スキル名と対応ファイルを記載。
- 生成後は `open <path>` のコピペ用コマンドをユーザーに提示する。
- テンプレ自体は上書きせず、コピーに実データを流し込む（差し替え方式）。
