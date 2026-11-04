---
name: cover-image
description: プロジェクトのトップ画像（OGP 風ヒーロー画像、1280×640）を「AI 背景アート＋HTML/SVG 文字合成」のハイブリッドで生成し、README 冒頭への埋込・HTML 成果物ヘッダー表示・GitHub Social Preview 手動設定の案内まで行うスキル。プロジェクト名は英語表記で画像内に正確な書体で合成する。背景生成は Codex を一次手段とし（稼働中の Codex へ agmsg で依頼、または scripts/codex-image.sh で Codex CLI を実行）、ローカル ComfyUI（scripts/comfy-image.sh）を二次、Gemini API（scripts/gemini-image.sh）を三次、mcp__oracle__chatgpt_image を最後の四次とする四段フォールバック構造。発動条件 (1) /cover-image コマンド (2)「トップ画像」「カバー画像」「タイトル画像」「ヒーロー画像」「OGP画像」「リポジトリの顔画像」「hero.png 作って/更新」等のキーワード (3) first-action の立ち上げフローからの呼び出し。使用しないケース：Web サイト自体の OGP メタタグ設計／スライド・記事用の挿絵（別スキル）／ロゴデザインの本格検討。
---

# cover-image — プロジェクトヒーロー画像生成

<!--
  where: ~/.claude/skills/cover-image/（ミラー: Skill-library/global-skills/cover-image/）
  what : ヒーロー画像の生成（3案提示→選択→微調整）と設置（README/HTML成果物/Social Preview案内）
  why  : どのプロジェクトか一目で分かるビジュアルアイデンティティを、正確な英語表記・毎回異なる書体で担保する
-->

## 出力物

- `assets/hero.png` — 1280×640（2:1、GitHub Social Preview 規格）
- README.md 冒頭に `![<Project Name>](assets/hero.png)`（README がなければ最小限を新規生成）
- 中間生成物は `assets/hero-work/`（確定後に削除するか確認）

## フロー

### Step 0: 前提確認（プリフライト — ヒアリングより前に必ず実施）

他の作業を始める前に、以下を一括チェックして結果を 1 メッセージで報告する。欠けている前提があれば**ここで停止**してユーザーに確認する（途中で発覚させない）:

1. 対象プロジェクトのルートを確認。`assets/hero.png` が既にあれば上書きしてよいか確認する。
2. `npx playwright --version` が通ることを確認（不可なら playwright-cli スキルの手順でセットアップ）。
3. **一次手段の疎通**: `codex login status` で Codex CLI のログインを確認し、このセッションで Codex が稼働中か（orca-master / goal-feed の実行中、またはユーザーの明言）も確認する。
4. **二次手段の疎通**: `curl -s -m 3 http://127.0.0.1:8188/system_stats` で ComfyUI の起動を確認（未起動なら告知のみ）。
5. **三次手段の前提**: `~/.gemini/api_key` の存在を確認（`[ -s ~/.gemini/api_key ]`）。
6. **四次手段の疎通**: `mcp__oracle__chatgpt_image` が ToolSearch で見つかるか確認（oracle MCP サーバー未接続なら告知のみ）。四段とも使えない場合は、生成手段がない旨を伝えて「HTML/SVG のみ構成」への切替か中断をユーザーに選ばせる。

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
3. 背景生成（四段フォールバック）:
   - **一次 A（agmsg で Codex に依頼）**: このセッションで Codex が稼働中と分かっているときだけ使う。
     `team.sh` の名簿は稼働状況を示さないので、名簿に載っているだけでは使わない。
     `send.sh` で 3 案のプロンプトと保存先の絶対パス（`assets/hero-work/bg-1.png` など）を渡し、
     「imagegen スキルの組み込み image_gen で文字なし背景だけを生成し、指定パスへコピーして返信。
     Codex 側の cover-image スキルは使わない」と明記する。5 分待っても 3 枚そろわなければ一次 B へ。
   - **一次 B（Codex CLI）**: 稼働中の Codex がいなければ最初からこちらを使う。
     案ごとに `scripts/codex-image.sh "<prompt>" <out.png>` を実行する。約 30 秒/枚。失敗したら二次へ。
   - **二次**: `scripts/comfy-image.sh "<prompt>" <out.png>` でローカル ComfyUI（SDXL）生成。
     無料・約 1 分/枚。exit 2（ComfyUI 未起動）なら三次へ。
   - **三次**: `scripts/gemini-image.sh "<prompt>" <out.png>` に切替。exit 2（API キー未設定）なら四次へ。
   - **四次**: 上記がすべて使えないとき、またはユーザーが oracle を指定したときだけ
     `mcp__oracle__chatgpt_image` で生成。
   - **どの段でも、切替したことを必ずユーザーに報告する。** 品質が雰囲気に合わない場合も、
     ユーザー了承の上で次の段に切り替えてよい。
   - 四次まで失敗し、gemini-image.sh が exit 2 だった場合は manual-todo スキルで
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

- 正本: `~/.claude/skills/cover-image/` ／ ミラー: `Skill-library/global-skills/cover-image/`（cp -R 同期）
- Codex 生成（一次）: ChatGPT ログインで動き API キー不要。出力は約 1672×941 の 16:9 だが、
  テンプレートの `background: center / cover` で 2:1 に切り抜かれる。保存先は
  `~/.codex/generated_images/<thread_id>/`。打ち切りは既定 300 秒（`CODEX_IMAGE_TIMEOUT` で変更可）。
- ComfyUI 生成（二次）: `http://127.0.0.1:8188` の REST API を curl で叩く。モデルは
  sd_xl_base_1.0、1280×640 直接生成、約 1 分/枚・無料。ホストは環境変数 `COMFY_HOST` で変更可。
  ネガティブプロンプトに text/letters/typography 除外を組込済みだが、プロンプト側でも明記する。
- oracle 生成（四次）は 1 枚数十秒〜。3 案で 1〜2 分待ちうる旨を生成前にユーザーへ伝える。
- oracle の癖: `outputPath` は `~/.oracle/generated/` 配下のみ指定可。Cloudflare「Just a moment…」で
  失敗したらユーザーに手動通過を依頼して再試行（`browserModelStrategy: "ignore"` 推奨）。
- oracle が完了検知に失敗しても（タイムアウト・Chrome 切断）、ChatGPT 側では画像生成が成功している
  ことが多い。その場合は**ユーザーに「開いている ChatGPT 画面から画像を手動ダウンロードしてほしい」と
  依頼**し、`~/Downloads/ChatGPT Image *.png` を回収するのが速い（自動では落ちてこない）。
- 品質・コスト事情で「HTML/SVG のみ（背景もグラデ・パターンで組む）」も選択肢として提示してよい。
