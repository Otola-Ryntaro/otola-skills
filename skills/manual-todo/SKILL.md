---
name: manual-todo
description: 実装作業の途中・完了時に、Claude では完結できず**ユーザー本人が手作業でやる必要がある残タスク**を、進捗バー＋チェックボックス＋ステージ分けのシンプルな HTML TODO リストとして出力するスキル。出力先は集約ハブ `~/dev/todo/pages/YYYY-MM-DD_HHmm_<slug>.html`（全プロジェクト共通。`~/dev/todo/index.html` が一覧ハブ）。チェック状態は todo-hub ローカルサーバ経由で `~/dev/todo/state/<slug>.json` に保存され、Claude が次セッションで読める。サーバ停止時は localStorage フォールバック。発動条件 (1) /manual-todo コマンド (2)「手動でやる作業」「わたしがやる作業」「ユーザー側でやる必要がある」「手作業のTODO」「残作業をリストにして」「セットアップ手順をチェックリストに」等のキーワード (3) 実装完了後に「アカウント作成」「APIキー発行」「ドメイン設定」「課金登録」「OAuth承認」「DNS設定」「ブラウザでクリック」等、Claude では実行不能な人間側作業が複数残っているとき。使用しないケース：Claude が自分で実行可能な作業（コマンド実行・ファイル編集・テスト）を含むだけのリスト → 通常の TodoWrite で十分。コードレビュー・PR レビューのチェックリスト → /code-review。日報・引き継ぎ → /shime /nakajime。
---

# Manual TODO: 手作業残タスクの HTML 化スキル

実装の流れの中で必ず出てくる「これだけは音良さん本人がブラウザを開いて／カードを取り出して／フォームを埋めて、やらないと先に進まない」作業を、**進捗が見える・後から戻ってこられる・順番が分かる**形の HTML として書き出す。

簡素で良い。**「ユーザーの手元タスクを HTML 化する」以外のことはしない**。

---

## いつ使うか（判別の核）

「自分が手作業でやる作業」とは、**Claude のツール権限・実行環境では物理的に完結不能な作業**を指す。判別基準は次の3つの「ない」：

1. **コード／ファイルで完結しない** — リポジトリ外の世界（ブラウザ管理画面・物理デバイス・銀行アプリ）が絡む
2. **CLI／API では代行不能** — 人間のクリック・認証・本人確認・支払いが必須
3. **判断が委任不能** — 「このプラン名でいい？」「この金額で承認していい？」のように音良さん本人の合意が要る

該当例：

- アカウント新規作成（メール認証クリック含む）
- クレジットカード登録／支払い手続き
- OAuth 承認画面でのクリック
- ドメイン取得・DNS レコード設定（レジストラ管理画面）
- App Store / Google Play への審査提出
- SMS／メール OTP 入力
- 物理デバイス操作（ルーター再起動・USB 接続）
- ブラウザでのみ取得できる API キー・トークンのコピー
- 法務・経理判断（規約同意・請求書承認）

**該当しない例**（→ これらは通常の TodoWrite か、Claude が自分で実行する）：

- 「`npm install` を実行する」 ← Claude が Bash で実行可能
- 「テストを書く」「ファイルを修正する」 ← Claude の本業
- 「README に追記する」 ← Claude が Write で実行可能
- 「git commit する」 ← Claude が Bash で実行可能（承認が必要ならその旨を別途確認）

---

## 起動時にやること

1. **直近の作業文脈から、上記基準に当てはまる残タスクを洗い出す**
   - 会話履歴・実装内容・最近書いたファイル・docs/ や README の TODO・コミットメッセージから拾う
   - 漠然と「設定する」ではなく、**画面名・ボタン名・入力値**まで具体化する
   - 不明点があれば 1 問だけ確認質問を許可する（複数なら推測で書いて後で直す方が早い）

2. **タスクを Stage に分ける（順序が重要）**

   テンプレ的な Stage 構成（必要なものだけ使う／案件に応じて改変可）：

   | Stage | 内容 |
   |-------|------|
   | Stage 1: 事前準備 | アカウント有無の確認・必要情報の手元準備（カード・身分証） |
   | Stage 2: アカウント・サービス登録 | 新規登録・本人確認・支払い設定 |
   | Stage 3: 設定・認証 | API キー発行・OAuth 連携・環境変数の取得 |
   | Stage 4: コードとの接続 | 取得した値を `.env` 等に貼る／Claude に渡す |
   | Stage 5: 動作確認 | 実機で叩く・課金が走るか確認・メール到達確認 |
   | Stage 6: 任意・後片付け | 不要アカウント削除・テスト用カード解除 |

   - **依存があれば必ず順序に反映する**（DNS 浸透待ち → 動作確認、等）
   - **並列でよいタスクは同じ Stage 内にまとめる**
   - Stage 数の目安は 3〜6 個。1 個に偏ったり 10 個超えになるなら粒度を見直す
   - **Stage 間に分岐・並列・待ち時間依存がある場合**（例: DNS 浸透待ちの間に別 Stage を進められる）、HTML 冒頭にインライン SVG のミニフロー図（Stage をノード、依存を矢印で示す 1 枚）を入れて全体の流れを見せる。一直線に進むだけなら図は不要

3. **各タスクは「具体動詞 + 対象 + 結果状態」で書く**

   悪い例：
   - 「Stripe を設定する」
   - 「ドメインを買う」

   良い例：
   - 「Stripe ダッシュボード → Developers → API keys で `sk_live_...` をコピーして音良に渡す」
   - 「お名前.com で `example-staging.com` を取得（年額 ¥1,200 想定、本人カードで決済）」

   各タスクには **必ず** 次の 2 つを地の文で添える（テンプレの `.task-why` / `.task-after`）：
   - **なぜやるか**（これをやらないと何が進まないのか）
   - **完了するとどうなるか**（完了後にユーザーが確認できる結果状態）

   さらに次のいずれかを必要に応じて添える：
   - **URL**（直リンク。`https://dashboard.stripe.com/apikeys` のように深いリンクが望ましい）
   - **コマンド・コード片**（コピペで使える形）
   - **入力値**（フィールド名と入れるべき値）
   - **所要時間目安**（5分／30分／要・浸透待ち）
   - **参考スクショ**（対象画面の見本が `output/` 等にあれば base64 で埋め込む。
     手順とサイズ規約は `~/.claude/skills/visualize-common/references/screenshot-embed.md` に従う）

4. **HTML を生成して保存する**

   - テンプレ：`~/.claude/skills/manual-todo/assets/template.html`
     - 見た目は末尾の `kanban-theme` ブロック（正本 `assets/kanban-theme.css`）で上書きしている。テーマを直したら
       `python3 scripts/apply-theme.py assets/template.html ~/dev/todo/pages/*.html` で全ページへ再配布する（冪等）
   - 出力先：**集約ハブ** `~/dev/todo/pages/<YYYY-MM-DD>_<HHmm>_<slug>.html`
     - 例：`~/dev/todo/pages/2026-06-24_1610_stripe-honban-setup.html`
     - `<slug>` は内容を表すケバブケース 3〜6 単語（ファイル名から `.html` を除いた全体が slug）
   - 日時取得は `date +"%Y-%m-%d_%H%M"` を Bash で実行（Claude 自身は時刻を知らない）
   - ディレクトリが無ければ `mkdir -p ~/dev/todo/pages` で作る

5. **ハブに登録して index を更新する**

   HTML 生成後、todo-hub CLI（`~/.claude/skills/manual-todo/scripts/todo-hub.py`）で登録する：

   ```bash
   python3 ~/.claude/skills/manual-todo/scripts/todo-hub.py register \
     --slug "2026-06-24_1610_stripe-honban-setup" \
     --project "$(basename "$PWD")" \
     --project-path "$PWD" \
     --title "Stripe 本番環境セットアップ"
   ```

   - `register` は state JSON の骨組み生成と `reindex`（index.html 再生成、hero.png があればサムネコピー）まで自動で行う
   - ハブには shime visualize の作業ログ機能も同居する: `todo-hub report-add --path <visualize HTML絶対パス>` で `~/dev/todo/reports.html`（index ヘッダの「📊 作業ログ」リンク先）に登録、`todo-hub report-scan` で `~/claude code/*/daily_report/*_visualize.html` の一括登録＋消失分 prune
   - さらに、全タスクの初期状態（`done: false`）を state JSON に **Claude が Write で書き込む**：
     `~/dev/todo/state/<slug>.json` の `tasks` を `{"1-1": {"title": "...", "done": false, "checkedAt": ""}, ...}` の形で埋める（ページを開かなくても index に総数が出るようにするため）

6. **生成後の案内**

   ```
   作成しました: ~/dev/todo/pages/2026-06-24_1610_xxx.html
   → 開きますか？（専用ウィンドウで開きます）
   ```

   ユーザーから「開いて」と言われたら次を実行する：

   ```bash
   python3 ~/.claude/skills/manual-todo/scripts/todo-hub.py open "<slug>"
   ```

   これはサーバ（localhost:7799）を自動起動し、**Chrome アプリモード＋専用プロファイル**（`~/dev/todo/chrome-profile`）の独立ウィンドウで開く。通常の Chrome アカウントとは混ざらない。ハブ一覧を開くときは slug なしで `... open`。

---

## セッション開始時・タスク確認時の読み方（Claude 向け）

ユーザーの手作業タスクの進捗を確認したいとき（Plans.md 更新時、/shime、/nakajime、「TODO どうなってる？」等）：

1. `~/dev/todo/state/*.json` を読む（現在のプロジェクトに関係する分は `projectPath` で判別）
2. `done: false` のタスクが残っていれば、次にやるべき手作業として提示する
3. 全完了していれば Plans.md の該当項目を完了扱いにしてよい
4. `checkedAt` でいつチェックされたかが分かる（ブラウザでのチェック操作がサーバ経由で即書き込まれている）

---

## HTML テンプレートの埋め方

`assets/template.html` を Read し、以下のプレースホルダを置換した完全な HTML を `Write` で出力する：

| プレースホルダ | 置換内容 |
|---------------|---------|
| `__PROJECT__` | 実行時のカレントディレクトリ名（`pwd` の basename、例: 「my-app」「my-site」）をそのまま機械的に使う。後で見返したときにどのプロジェクトの手作業か一目で分かるようにするための表示で、要約や言い換えはしない |
| `__TITLE__` | このリストのタイトル（例: 「Stripe 本番環境セットアップ」） |
| `__SUBTITLE__` | 1 行サブタイトル（背景・目的。例: 「2026-06-24 実装分。これが終わると本番決済が動きます」） |
| `__STORAGE_KEY__` | localStorage のキー。**他リストと衝突しないユニーク文字列**（ファイル名と同じスラッグでよい） |
| `__STAGES__` | 後述の Stage HTML 群（複数の `<section class="stage">` を連結） |

### Stage HTML の形式

```html
<section class="stage">
  <h2 class="stage-title">
    <span class="stage-num">1</span>
    <span class="stage-name">事前準備</span>
    <span class="stage-progress" data-stage="1">0/3</span>
  </h2>
  <p class="stage-desc">この Stage の狙いを 1 行で。省略可。</p>
  <ul class="tasks">
    <li class="task">
      <label>
        <input type="checkbox" data-task-id="1-1">
        <span class="task-title">Stripe アカウントの本人確認を完了させる</span>
      </label>
      <div class="task-body">
        <p class="task-desc">「Activate your account」リンクを踏み、事業情報・銀行口座・身分証アップロードまで完了する。審査は 1〜2 営業日かかる場合あり。</p>
        <p class="task-why">本人確認が通らないと本番 API キーが発行されず、決済実装のテストが一切進まないため。</p>
        <p class="task-after">ダッシュボード上部の「Test mode」表示が消え、本番キーの発行画面に進めるようになる。</p>
        <a class="task-link" href="https://dashboard.stripe.com/account/onboarding" target="_blank">→ Stripe オンボーディングを開く</a>
        <span class="task-meta">所要: 30分（審査待ちは別）</span>
        <!-- 対象画面の見本スクショがあれば（任意）:
        <figure class="task-shot">
          <img src="data:image/png;base64,..." alt="対象画面">
          <figcaption>この画面が出ていれば正しい場所</figcaption>
        </figure> -->
      </div>
    </li>
    <li class="task">
      <!-- 次のタスク -->
    </li>
  </ul>
</section>
```

ルール：

- `data-task-id` は `<stage番号>-<task番号>` の形式でユニークに（localStorage キーになる）
- `task-why`（なぜやるか）と `task-after`（完了するとどうなるか）は全タスクに、一目で読める地の文で書く
- `task-body` 内の `task-desc`／`task-link`／`task-meta`／`task-shot` は省略可。不要なら出力しない
- 冒頭の「⚡ いまやること」Hero カードはテンプレの JS が未完了の先頭タスクを自動表示する（手動で埋めない）
- CSS・構成・スクショ埋め込みの正本: `~/.claude/skills/visualize-common/references/`（style-guide.md / action-first.md / screenshot-embed.md）
- リンクは新規タブで開く（`target="_blank"`）
- **ファイル参照タスク**（「docs/012 の文面を使う」「.env の値を貼る」等、リポジトリ内のファイルを見ながらやる作業）には、`task-body` 内に VS Code オープンボタンを入れる：
  `<button class="task-vscode" data-path="/Users/you/xxx/docs/012_foo.md" data-line="24">VS Code で開く</button>`
  - `data-path` は**絶対パス必須**（register した `--project-path` 配下であること。サーバがそれ以外を 403 で拒否する）
  - `data-line` は任意（該当箇所の行番号）
  - クリックするとプロジェクトフォルダがワークスペースとして VS Code で開き、該当ファイル・行にジャンプする。サーバ停止時は `vscode://` URL スキームにフォールバックする（この場合フォルダは開かずファイルのみ）
- コマンド片を載せたい場合は `<pre class="task-cmd"><code>npm install</code></pre>` を `task-body` 内に入れる（右上に「コピー」ボタンがテンプレJSで自動注入され、`<code>` のテキストがクリップボードにコピーされる。複数行コマンドもそのまま可）
- 入力値の表は `<dl class="task-fields"><dt>フィールド名</dt><dd>入れる値</dd></dl>` で

---

## 出力の品質チェック（書く前に自問）

- [ ] **タスクは全て「自分が手作業でやるしかないもの」か？** Claude が代行可能な作業を混ぜていないか
- [ ] **Stage の順序は依存関係に沿っているか？** 後の Stage が前の Stage の成果物に依存する流れになっているか
- [ ] **各タスクは画面名・ボタン名・入力値まで具体的か？** 「設定する」では失格
- [ ] **全タスクに `task-why` と `task-after` があるか？** 「なぜやるか」「完了するとどうなるか」が地の文で書かれているか
- [ ] **URL は最深部の直リンクか？** トップページではなく「API keys」「DNS settings」の画面に直接飛ぶか
- [ ] **`data-task-id` は全てユニークか？** localStorage 衝突を避けるため
- [ ] **`__STORAGE_KEY__` は他の TODO リストと衝突しないか？** ファイル名スラッグをそのまま使うのが安全

---

## デザイン原則（テンプレ側で実装済み・改変するときの指針）

- 軽量・自己完結（外部 CSS / JS / フォント・CDN は一切使わない）
- 進捗バーは最上部に sticky 表示。チェックすると即座に伸びる
- ステージごとに小さい進捗カウンタ（`0/3` のような）を見出し横に出す
- チェック状態は todo-hub サーバに保存し、サーバ停止時は localStorage に保存する。リロードしても残る
- 「進捗をリセット」ボタンを footer に置く（誤クリック防止に confirm あり）
- 全タスク完了で「🎉 全タスク完了！」のバナーがふわっと出る
- 色味は控えめ（**ホワイトベース・デイモード**。配色の正本は `assets/kanban-theme.css`。ダークテーマ正本 visualize-common の例外で、配色のみライト・構成語彙は共通）／フォントはシステムデフォルト

これら以上の凝った機能（フィルタ・並べ替え・タグ・締切日・通知）は要求があるまで追加しない。**シンプルさが正義**。

---

## アンチパターン

- ❌ Claude が自分で実行可能な作業を混ぜる（「`npm test` を実行する」など）
- ❌ Stage を 1 個だけにして全タスクを並べる（→ 通常の TodoWrite で十分）
- ❌ 「適切に設定する」のような曖昧な動詞を使う
- ❌ ファイル名に日本語スラッシュや空白を入れる（macOS で `open` が壊れる）
- ❌ テンプレを毎回作り直す（`assets/template.html` を必ず再利用する）
- ❌ サーバ必須にして file:// で開けない HTML を作る（サーバ停止時も localStorage で動くこと）
- ❌ `register` / state JSON 初期化を忘れる（index に載らず「気付けない TODO」に逆戻りする）
