# wiki-essay write モード — seed から多視点コラムを書き起こす

LLM_Wiki の seed（意見の芽）を起点に、**読者ペルソナ × 論証切り口** の二軸で
過去執筆と重複しない視点を選び、骨格 → 下書き → `esseist` 仕上げまで一気通貫で執筆する。

## 引数

- `<seed-slug>` — **必須**。`interests/questions.md` の seed と対応
- `--book` — 任意。連作モード、`essays/books/<seed-slug>/` に章立てで保存

未指定なら `AskUserQuestion` で seed を1問だけ確認。

## 🔴 鉄則

- **骨格承認なしに下書きへ進まない**（提案→承認の原則）
- **章ごと段階執筆を原則とする** — Phase 3 で章ごと内容 draft を全章一括提示して承認、Phase 4 で **1章ずつ** 本文化してユーザー確認を取りながら進める。まとめて全章書かない（破綻・満足いかない問題への対策、ユーザーフィードバック 2026-06-25）
- **esseist 仕上げを必ず通す**（LLM 直生成のまま保存しない）。仕上げは **全章揃ったあと一括** が原則（章ごとに通すと文体が章間で揺れる）
- **vault は読み取りのみ**（writing 段階で vault に書き込まない、reflect モードでの取り回し対象）
- **過去に書いた同 seed × 同 audience × 同 angle 組合せは候補から除外**

---

## Phase 1: seed の取り込みと文脈収集

### 1-1. seed の確認

1. `~/Obsidian/LLM_Wiki/interests/questions.md` を Read
2. `<seed-slug>` を含む行を grep（部分一致 OK）
3. **見つからない場合**: `AskUserQuestion` で「新規 seed として `interests/questions.md` に登録するか？」を確認
   - はい → 末尾「## 対話seed由来」セクションに `- [ ] (<domain>/P?/open) <磨いた問い>` を追記（提案→承認、勝手に書かない）
   - いいえ → 中断、ユーザーに seed を正しく指定するよう案内
4. 該当行から `domain`（medical-science / society-thought / clinic-management / ai-tech / investment）を抽出

### 1-2. 既存 wiki 文脈の収集

1. **domain 一致の wiki/opinions/** から最大5件 Read（`Glob ~/Obsidian/LLM_Wiki/wiki/opinions/*.md` → frontmatter の `domain:` チェック）
2. **domain 一致の wiki/concepts/** から最大5件 Read（同様）
3. 任意: `wiki-query` スキルを `Skill` ツール経由で呼び、seed 文字列で関連ページを取得（重複は除く）

### 1-3. 過去執筆履歴の取得

1. `~/claude code/LLM_wiki/essays/_seed_threads.md` を Read
2. `## seed: <seed-slug>` セクションがあれば、「書いた」table と「書いていない（候補）」リストを抽出
3. 無ければ「初回執筆」として記憶

→ ここまでの結果（seed、wiki 文脈、過去執筆）をプロンプト文脈に積む。

---

## Phase 2: 視点候補の提示

「書いた audience × angle 組合せは除外」の原則で、3〜5案を `AskUserQuestion` で提示。

### 候補生成ロジック

1. **「書いていない候補」リスト** に明示されているものを最優先で採用（ユーザーが手動追記したもの）
2. リストにない場合、過去執筆の audience を見て補完案を LLM 推論で出す
   - 例: 過去に patient / doctor で書いている → manager / general / student で展開
   - angle は wiki/opinions の論点パターン（ポジショントーク / 反対論への反論 / 制度目線 / 当事者目線 / 比較論）を参考に
3. 既存 audience × angle 組合せは候補から除外
4. 媒体（medium）は audience に応じて推奨（例: doctor → newsletter, general → note/Twitter, manager → blog）

### 提示形式

`AskUserQuestion` の選択肢として 3〜5案、各案に audience / angle / medium / 想定字数の概要を1〜2行。
「その他（自由記述）」も含めること。

---

## Phase 3: 章ごと内容 draft の生成 + 承認

ユーザー選択後、該当視点で **章立て＋章ごと内容 draft** を組む。
これは Phase 4 の章単位段階執筆の設計図になる。

### 章ごと内容 draft の構造

```
## 想定全体像
- 主張（一文）: ...
- 想定字数: <total>字、N章構成
- トーン: ...
- references（本文中で動線を張る wiki ページ）: [[...]] / [[...]]

## 章ごと内容 draft（全章一括提示）

### 書き出し
- 読者の関心を掴む数行
- 主張の予告
- 想定字数: ...字

### 第1章: <章タイトル>
- 内容ポイント1（具体例・エビデンス）
- 内容ポイント2
- wiki 動線: [[<wiki page>]]
- 想定字数: ...字

### 第2章: <章タイトル>
- 内容ポイント1
- 内容ポイント2
- 想定字数: ...字

### 第N章: ...

### 結び: <章タイトル>
- 着地点（宣言／問い／余韻）
- 読者への問いかけ
- 想定字数: ...字
```

**🔴 全章一括提示** — 章タイトル＋箇条書き内容を **全章まとめて** ユーザーに見せる。
ユーザーはこの段階で「章構成と各章の中身」を見渡せ、承認 or 修正を判断する。

**`AskUserQuestion` で承認を求める**。NG なら何が違うかを聞いて draft を作り直す（最大3往復、それでも合意できなければ中断）。承認されたら Phase 4 へ。

---

## Phase 4: 章単位段階執筆 → 全章揃ったあと esseist 仕上げ

### 4-1. 章単位段階執筆（🔴 章ごとに区切る）

Phase 3 で承認された章ごと内容 draft をベースに、**1章ずつ** 本文を起こす。

**手順**:
1. 第1章の本文を起こす（想定字数に従う、LLM 直生成のままで構わない）
2. ユーザーに **章単独で** 提示して確認を求める（『この章でOK／修正したい／次の章へ』）
3. 承認 or 修正完了したら第2章へ進む。全章揃うまで繰り返し
4. 全章揃ったら下書きファイルに **章を順序通り結合** して保存（Phase 4-2 へ）

**🔴 鉄則: 章ごとに区切ること**。まとめて全章書かない。
理由: まとめて書くと破綻する／満足いかないことが多い（ユーザーフィードバック 2026-06-25）。
ユーザーは章単位で「ここは違う／もう少しこう書きたい」と方向修正できる。

**length 仕様（媒体別、合計字数の目安）**：
- `note` — 3000-5000字（標準）。10000字級長文は --book または明示指定時のみ
- `x` — **X 長文投稿1本** として 1500-2500字。連投スレッドではなく、X Premium の長文投稿機能で1ページに収まる長文。見出し（`##`）は X では反映されないので使わない。太字・箇条書きは反映される。
- `x-thread` — 連投スレッド形式（明示指定時のみ）、各ツイート140字以内
- `newsletter`、`blog` 等 — 適宜

各章の想定字数は合計字数を章数で按分（Phase 3 の章ごと draft で章単位に明示済み）。

この段階では LLM 直生成のままで構わない（次段で脱AI処理する）。

**🔴 戻り動線の必須化**: 本文には Phase 1-2 で集めた wiki ページへの `[[wikilink]]` を**必ず埋め込む**（references の各 wiki ページに最低1回ずつ）。esseist は事実関係保持の安全弁により新規 wikilink を追加しないので、ここで入れておかないと仕上げ後の本文に wikilink がゼロになり、Obsidian バックリンクが効かなくなる。書き換え後の本文中に `[[...]]` が残るよう、wikilink は地の文に自然に組み込むこと（例：「エビデンスは [[補聴器診療の検査体系]] に整理した」）。

**X 媒体の戻り動線**: `x` / `x-thread` の場合、本文中に wikilink を埋め込むと X 投稿時に余分になるため、**ファイル末尾に「## 関連 wiki ページ（投稿時は削除）」セクション**として wikilink を列挙する。投稿時にユーザーが手動で削除する前提の管理用メタ情報。

### 4-2. esseist 仕上げ（必須）

#### 手順

🔴 **ファイル配置規約（2026-06-25 変更）**: フラットな長い英語slugではなく、**1テーマ1フォルダ・日本語短タイトル・media別ファイル** で管理する。

**フォルダ**: `essays/drafts/<YYYY-MM-DD>_<日本語短タイトル>/`
- 日本語短タイトルは 4〜10字程度。Phase 3 終了時に骨格と一緒にユーザー承認を取る（提案 → 修正可）
- 例: `2026-06-25_便利の対価/`、`2026-06-23_ちょっと考えれば/`

**ファイル**:
- `<medium>.md` — 下書き（esseist 投入前）
- `<medium>_v1.md` — esseist 仕上げ後（連番 v1, v2, ...）

例:
```
essays/drafts/2026-06-25_便利の対価/
├── note.md          # 下書き
├── note_v1.md       # esseist仕上げ
├── x.md             # X長文版下書き
└── x_v1.md          # X長文版仕上げ
```

#### 実行手順

1. Phase 3 で承認された **日本語短タイトル** でフォルダを作成（既存なら使い回し）
2. 下書きを `essays/drafts/<日付>_<短タイトル>/<medium>.md` に Write で保存（**frontmatter は付けず本文のみ**、esseist は本文の書き換え担当）
3. `Skill` ツール経由で `esseist` を起動し、上記ファイルパスを args で渡す
4. esseist は規約により `<medium>_v1.md`（連番なし元 → `_v1`）を新規生成する
5. 元の連番なしファイル（`<medium>.md`）は esseist 規約により上書きされない ── これは**「下書き履歴」として残す**（後で振り返る材料、削除はユーザー判断）
6. esseist が出した `_v1.md` を**最終本文**として、Phase 5 で frontmatter を後付け Edit する

#### 🔴 コンテキストパッケージ送出（必須）

esseist 起動時の args に**必ず以下のコンテキストを最初から渡す**。esseist 側のプランモード内インタビュー（A・B・D・E 必須）を最小化するため。これを渡さないと、ユーザーが wiki-essay 内で既に答えた質問を esseist 側でも改めて聞かれ、二重対話になる。

```
書き換え対象ファイル: <絶対パス>

wiki-essay write モードからの呼び出し。下記コンテキスト確認済みなので、esseist プランモードでのインタビューは可能な範囲で省略（不足あれば1〜2問のみ確認）。

## 事前確認済みコンテキスト
- 書き手: <職業・専門性>（Phase 1 ユーザー情報）
- 公開先: <medium>（例：note / X スレッド / メルマガ）
- 想定読者: <audience>（例：doctor、general 等）
- 主張の輪郭: <Phase 3 で承認された主張一文>
- 高揚点: <骨格で特定した強調段>
- 沈静点: <骨格で特定した抑制段>
- 文体温度: <ユーザーが Phase 3 で示唆した温度（淡々 / 抑制された熱 / 明示の高揚 等）>
- 想定字数: <length>
- 出力先: <絶対パス>_v1.md（esseist 規約に従う）
```

文体温度がユーザー指定で曖昧なら、esseist Phase 2 で1問だけ追加確認する設計を許容（完全省略を強制しない）。

---

## Phase 5: 保存 + メタ更新

### 5-1. frontmatter 充填と保存

`~/.claude/skills/wiki-essay/templates/column_frontmatter.md` を Read してテンプレ取得。
以下を充填して `essays/drafts/<日付>_<日本語短タイトル>/<medium>_v1.md` の先頭に Edit で挿入:

- `title` — Phase 3 で決めた、または LLM 提案 + ユーザー承認
- `seed` — `<seed-slug>`（英語 kebab-case、`interests/questions.md` の seed と対応）
- `audience`, `angle`, `medium`, `length` — Phase 2 で選択した値
- `status: draft`、`adopted_at:` は空
- `created` — 今日の日付
- `references` — 本文中の `[[wikilink]]` を全部 grep して列挙
- `domain` — seed の domain（複数可）
- `confidence` — LLM 判定（high/medium/low）、不明なら medium

**medium の値**:
- `note` — note 長文（3000-5000字）
- `x` — X 長文投稿1本（1500-2500字、X Premium 長文機能、見出し不使用）
- `x-thread` — 連投スレッド（明示時のみ）
- `newsletter`、`blog` 等

### 5-2. `_seed_threads.md` 更新

1. `_seed_threads.md` を Read
2. `## seed: <seed-slug>` セクションを探す
   - **あれば**: 「書いた（N本）」table に新行を append、N をインクリメント
   - **なければ**: `templates/seed_threads_entry.md` を Read してセクション新規追加
3. 「書いていない（候補）」リストにあった対応項目があれば、対応する `- [ ]` を `- [x]` に変更

### 5-3. log.md 追記

`~/Obsidian/LLM_Wiki/log.md` に1行追記:
```
## [YYYY-MM-DD] essay-write | <saved-file-relpath> (seed: <seed-slug>, audience: <a>, angle: <ang>)
```

### 5-4. TodoWrite で次アクション案内

ユーザーに次のアクションを TodoWrite で残す:
- 「内容確認して `status:` を `adopted` に手動更新」
- 「採用後 `python3 essays/scripts/sync_to_vault.py` で dry-run 確認」
- 「OK なら `--apply` で vault に同期」
- 「コラム/ 拠点に投げたいなら `/wiki-essay handoff <saved-file>` を起動」

---

## --book モード（連作）

Phase 1〜4 は同じ。Phase 5 が変わる:

### 5-book-1. 保存先

`~/claude code/LLM_wiki/essays/books/<seed-slug>/` 配下に章立てで保存:
- `_index.md`（無ければ新規作成、章リストと進捗）
- `NN_<chapter-slug>.md`（NN は2桁ゼロ埋め、最大章数から +1）

### 5-book-2. `_index.md` 形式

```markdown
# <seed-slug> — 連作コラム

## 章立て
1. [x] [[01_<title>]] — adopted (2026-06-21)
2. [x] [[02_<title>]] — draft
3. [ ] <未着手の章タイトル候補>
```

### 5-book-3. `_seed_threads.md` 更新

`location` 列は `essays/books/<seed-slug>/NN_<chapter>.md` 形式で記載。
ただし連作の場合は「書いた一覧」が膨らみすぎないよう、`_index.md` への参照1行で集約する選択肢もあり（ユーザー判断）。

---

## エラー処理

| 状況 | 動作 |
|------|------|
| seed が見つからない | 新規 seed 登録を提案、却下なら中断 |
| wiki 文脈ゼロ件 | そのまま続行（文脈なくても書ける）、ただしユーザーに通知 |
| 骨格承認が3往復で合意できない | 中断、ユーザーに方針再考を依頼 |
| esseist 仕上げが失敗 | 下書きまでで保存（`status: review` で記録）、ユーザーに手動仕上げ案内 |
| `_seed_threads.md` 書き込み競合 | エラー表示して中断（`.bak` は作らない、手動回復前提） |

## 完了確認

- 保存ファイルの frontmatter 全フィールドが埋まっている
- `_seed_threads.md` に新規行 or セクションが反映されている
- `log.md` に1行追記されている
- TodoWrite に次アクションが残っている
