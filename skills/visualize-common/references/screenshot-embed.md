# screenshot-embed.md — base64 スクショギャラリー部品

<!--
  where: visualize-common/references/screenshot-embed.md
  what : スクショを自己完結 HTML に埋め込むための HTML 断片・コマンド手順・サイズ規約
  why  : 外部画像禁止（自己完結原則）を守りつつ、セッションの変化を画像で伝えるため
-->

## HTML 断片（正本）

```html
<h2><span class="n">NN</span>本日のスクショ</h2>
<p>{{ギャラリーの前置き 2〜3 文 — どの画面で何が変わったか}}</p>
<div class="shots">
  <figure>
    <img src="data:image/png;base64,{{BASE64_1}}" alt="{{ALT_1}}">
    <figcaption>{{何の画面で・何が確認できるか 1 文}}</figcaption>
  </figure>
</div>
```

CSS（テンプレの `<style>` に追加する）:

```css
.shots{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin:14px 0}
@media(max-width:720px){.shots{grid-template-columns:1fr}}
.shots figure{margin:0;background:var(--card);border:1px solid var(--line);
  border-radius:12px;padding:10px;overflow:hidden}
.shots img{width:100%;height:auto;border-radius:8px;display:block;cursor:zoom-in}
.shots figcaption{color:var(--sub);font-size:12.5px;margin-top:8px;line-height:1.5}
/* クリック拡大は CSS のみ: figure 内 img を <a href="#shot-N"> で包み、
   対応する .lightbox(:target で表示) を末尾に置く方式でもよい。過剰なら省略可 */
```

## 埋め込み手順（macOS 標準ツールのみ）

```bash
# 1) 幅 1200px に縮小（元ファイルは触らない）
sips --resampleWidth 1200 input.png --out /tmp/resized.png

# 2) base64 化（改行なし）
base64 -i /tmp/resized.png | tr -d '\n' > /tmp/shot.b64

# 3) HTML の {{BASE64_N}} に流し込む（Edit ツールでは巨大文字列を扱いにくいので
#    python3 か sed でプレースホルダ置換するのが確実）
python3 - <<'EOF'
from pathlib import Path
html = Path("report.html").read_text()
html = html.replace("{{BASE64_1}}", Path("/tmp/shot.b64").read_text())
Path("report.html").write_text(html)
EOF
```

## サイズ規約

- 幅 1200px 上限（詳細不要なら 800px）。1 枚あたり base64 後 ~500KB 目安。
- 1 HTML の合計 5MB 目安。超えそうなら枚数を絞る（代表 3〜8 枚）か幅 800px に落とす。
- 埋め込み後に `ls -lh <html>` でサイズを確認し、5MB 超なら削減する。

## 収集元パス（当日分を拾う）

セッションのスクショは以下の規約ディレクトリから収集する。日付ディレクトリ名（`YYYYMMDD_*`）または
mtime で当日分にフィルタする。

```bash
D=$(date +%Y%m%d)
# web-test / web-exam / goal-feed（規約: NNN_<step>.png）
ls output/playwright/${D}_*/*.png output/browser-exam/${D}_*/*.png output/goal-feed/${D}_*/*.png 2>/dev/null
# Playwright MCP の自動保存（当日 mtime）
find .playwright-mcp -name '*.png' -mtime -1 2>/dev/null
```

- 候補が多い場合は「変化が分かる代表カット」を優先して 3〜8 枚選ぶ（同一画面の連番は間引く）。
- 1 枚も無ければギャラリーセクションごと省略する。
