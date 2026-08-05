---
name: project-hero
description: プロジェクトのトップ画像（OGP 風ヒーロー画像、1280×640）を「AI 背景アート＋HTML/SVG 文字合成」のハイブリッドで生成し、README 冒頭への埋込・HTML 成果物ヘッダー表示・GitHub Social Preview 手動設定の案内まで行うスキル。プロジェクト名は英語表記で画像内に正確な書体で合成する。背景生成は mcp__oracle__chatgpt_image を一次手段、Gemini API（scripts/gemini-image.sh）をフォールバックとする二重構造。発動条件 (1) /project-hero コマンド (2)「トップ画像」「ヒーロー画像」「OGP画像」「リポジトリの顔画像」「hero.png 作って/更新」等のキーワード (3) first-action の立ち上げフローからの呼び出し。使用しないケース：Web サイト自体の OGP メタタグ設計／スライド・記事用の挿絵（別スキル）／ロゴデザインの本格検討。
---

# project-hero — プロジェクトヒーロー画像生成

<!--
  where: Skill-library/global-skills/project-hero/（実働ミラー: ~/.claude/skills/project-hero/）
  what : ヒーロー画像の生成（3案提示→選択→微調整）と設置（README/HTML成果物/Social Preview案内）
  why  : どのプロジェクトか一目で分かるビジュアルアイデンティティを、正確な英語表記・毎回異なる書体で担保する
-->

## 出力物

- `assets/hero.png` — 1280×640（2:1、GitHub Social Preview 規格）
- README.md 冒頭に `![<Project Name>](assets/hero.png)`（README がなければ最小限を新規生成）
- 中間生成物は `assets/hero-work/`（確定後に削除するか確認）

## フロー

### Step 0: 前提確認
- 対象プロジェクトのルートを確認。`assets/hero.png` が既にあれば上書きしてよいか確認する。
- `npx playwright --version` が通ることを確認（不可なら playwright-cli スキルの手順でセットアップ）。

### Step 1: ヒアリング
AskUserQuestion で以下を確認（既に会話で判明している項目は聞かない）:
- プロジェクトの**英語表記名**（未定なら README/CLAUDE.md から 2〜3 候補を提示。本格的な命名は naming-brainstorm へ）
- タグライン（英語 1 行、なしでも可）
- 雰囲気キーワード（例: 信頼感／実験的／ポップ／ミニマル）と避けたい色・書体

### Step 2: 3 案生成
1. `references/font-catalog.md` を Read し、`references/used-fonts.md` の記録済み書体を除外した上で、
   **異なる系統から 3 書体**を選ぶ。
2. 案ごとに背景アートのプロンプトを作る。必ず英語で、**「no text, no letters, no typography」を明記**し、
   雰囲気キーワード・配色を反映した抽象アート／イラストを指示する。
3. 背景生成（二重構造）:
   - **一次**: `mcp__oracle__chatgpt_image` で生成。
   - **フォールバック**: oracle がエラー・タイムアウト・トークン枯渇、または品質不良で再試行 1 回でも
     ダメだった場合、`scripts/gemini-image.sh "<prompt>" <out.png>` に切替。
     **切替したことを必ずユーザーに報告する。**
   - gemini-image.sh が exit 2（API キー未設定）の場合は manual-todo スキルで
     「Google AI Studio で API キー発行 → ~/.gemini/api_key に保存」のチェックリストを提示して中断。
4. 合成: `assets/hero-template.html` のプレースホルダ
   （`{{FONT_FAMILY}}` `{{FONT_URL}}` `{{PROJECT_NAME}}` `{{TAGLINE}}` `{{BG_IMAGE}}` `{{OVERLAY_CSS}}`）
   を sed または Write で置換し、案ごとに
   `npx playwright screenshot --viewport-size=1280,640 <html> <png>` で PNG 化。
   背景の明度に応じて `{{OVERLAY_CSS}}` で文字色・オーバーレイを調整してよい。
5. 3 案を横並びにした比較 HTML を `assets/hero-work/compare.html` に生成して `open` で見せ、
   AskUserQuestion で選択してもらう（「どれも違う」→ ヒアリングに戻る）。

### Step 3: 微調整 → 確定
- 文字サイズ・位置・色・タグライン・背景の部分再生成（選択案のみ）を要望に応じて反映。
- 確定したら `assets/hero.png` として保存し、`references/used-fonts.md` に
  「日付・プロジェクト・書体・系統」を追記（正本とミラーの両方）。

### Step 4: 設置
1. README.md 冒頭（タイトル行の直後）に画像を挿入。README がなければ
   「hero 画像＋プロジェクト名＋1 行説明」の最小 README を新規生成。
2. GitHub リポジトリがある場合、Social Preview は API 設定不可のため、
   manual-todo スキルで「Settings → General → Social preview に assets/hero.png をアップロード」
   のチェックリストを提示する。
3. `assets/hero-work/` を削除してよいか確認して掃除。

## HTML 成果物との連携

visualize-common 正本に「プロジェクト直下に `assets/hero.png` があれば
📂プロジェクト名表記の上にヒーロー画像を表示する」規約がある。
本スキルは画像を置くだけでよく、各 HTML 生成スキルが次回生成時に規約へ従う。

## 運用メモ

- 正本: `Skill-library/global-skills/project-hero/` ／ ミラー: `~/.claude/skills/project-hero/`（cp -R 同期）
- oracle 生成は 1 枚数十秒〜。3 案で 1〜2 分待ちうる旨を生成前にユーザーへ伝える。
- oracle の癖: `outputPath` は `~/.oracle/generated/` 配下のみ指定可。Cloudflare「Just a moment…」で
  失敗したらユーザーに手動通過を依頼して再試行（`browserModelStrategy: "ignore"` 推奨）。
- oracle が完了検知に失敗しても（タイムアウト・Chrome 切断）、ChatGPT 側では画像生成が成功している
  ことが多い。その場合は**ユーザーに「開いている ChatGPT 画面から画像を手動ダウンロードしてほしい」と
  依頼**し、`~/Downloads/ChatGPT Image *.png` を回収するのが速い（自動では落ちてこない）。
- 品質・コスト事情で「HTML/SVG のみ（背景もグラデ・パターンで組む）」も選択肢として提示してよい。
