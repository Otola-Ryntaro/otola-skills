---
name: wiki-help
description: LLM_Wiki（~/Obsidian/LLM_Wiki/）の運用で「今この状況でどの wiki 系スキル/コマンドを使うべきか」の判断を手伝う案内役スキル。wiki-extract / wiki-absorb / wiki-prospect / wiki-clip / wiki-interview / wiki-essay や、点検・問い合わせ・可視化のグローバル版 wiki-lint / wiki-query / wiki-dashboard、vault内コマンド(/wiki-ingest 等)が多くて迷うときに、状況を1〜2問ヒアリングして最適な入口を推奨し、必要なら起動まで案内する。「wiki-help」「どのwikiスキルを使えばいい」「wikiの使い方がわからない」「wikiに入れたいけどどれ？」「wikiスキル迷う」「コラム書きたい」「seedからエッセイ」等で発動。LLM_Wiki文脈の道案内のみで、実際の取込・収集・執筆は推奨先スキルに委ねる。
allowed-tools: Read, AskUserQuestion, Skill
---

# wiki-help — どの wiki スキルを使うべきか案内する

LLM_Wiki の入口（スキル/コマンド）が多くて迷うときの **道案内**。状況を見極めて最適な1つを推奨し、必要なら起動する。
**このスキル自身は取込・収集をしない**（判断と誘導に徹する）。全体像は `~/claude code/LLM_wiki/README.md` 参照。

## よくある操作 → 推奨入口（早見表）（ZD-008 追加）

| よくある操作 | 推奨入口 | 補足 |
| --- | --- | --- |
| プロジェクト/vault の知識を取り込む | wiki-extract → wiki-absorb | 1ファイルだけなら /wiki-ingest 可 |
| Web 記事を取り込む | Web Clipper → wiki-clip | |
| 知りたいことを調べて追加 | wiki-prospect | 問いの登録は interests/questions.md |
| 自分の考えを整理して登録 | wiki-interview → wiki-prospect | |
| seed から多視点でコラム/エッセイを書く（公開原稿） | wiki-essay write | `/wiki-essay write <seed-slug>`、esseist で仕上げ |
| コラム/側で書いた完成記事を wiki に還元 | wiki-essay handoff → reflect | コラム/ で handoff → LLM_wiki で reflect |
| 質問する | wiki-query（vault 外）/ /wiki-query（vault 内） | |
| 点検 → 修復 | wiki-lint → wiki-weave | lint は検出、weave は修復 |
| 状態を見る | wiki-dashboard（vault 外）/ /wiki-dashboard（vault 内） | |
| **wiki ページを HTML レポートで可視化したい** | **wiki-visualize** | `meta/reports/[date]_[slug]/` に Obsidian 内表示用 .md とフル HTML を生成（ハイブリッド・ダッシュボード風） |

## 進め方
1. ユーザーの発言から **やりたいこと** が既に明確なら、下の判断マトリクスで即推奨する（質問しない）。
2. 曖昧なら、`AskUserQuestion` で **最小限（1問）** だけ確認する。聞くのは原則これだけ:
   - 「いま手元にあるもの/やりたいことは？」
     - 既存プロジェクトの知識を入れたい / Webや論文から新しく集めたい / ブラウザで見た記事を入れたい / wikiに質問したい / 全体を点検・整理したい
3. 推奨を **「推奨スキル＋理由＋起動の言い方」** の形で提示。ユーザーがOKなら `Skill` ツールで起動（vault内コマンドはコマンド名を案内）。

## 判断マトリクス（状況 → 推奨 → 起動の言い方）
| いまの状況 | 推奨 | 起動の言い方 |
|---|---|---|
| `~/claude code/` のプロジェクトの知識を wiki に入れたい | **wiki-extract → wiki-absorb**（2段階） | プロジェクトで「このプロジェクトを網羅的に吸い出して」→ 確認後「stagingを取り込んで」 |
| 既存 Obsidian vault のコラム等を深く入れたい | **wiki-extract → wiki-absorb** | 同上（対象パスを指定） |
| 「知りたいこと」を新しく集めたい / 手薄な領域を埋めたい | **wiki-prospect** | 「新しい知識を集めて」(フロンティア) / 「○○を深掘りしてwikiに」(トピック) |
| 既存概念を最新化・深掘りしたい | **wiki-prospect** | 「○○を最新化して」 |
| 自分の中の考え・コメント・違和感を芽にしたい（まだ言語化前） | **wiki-interview**（→確認後 wiki-prospect） | 「この考えを深掘りして」「コメントから芽を育てて」 |
| seed から長文コラム/エッセイ（note・X・メルマガ等の公開原稿）を書きたい | **wiki-essay write** | `/wiki-essay write <seed-slug>` 視点候補→骨格→下書き→esseist 仕上げまで一気通貫 |
| 同じ seed を別の視点（読者×切り口）で書き直したい | **wiki-essay write**（再起動） | 過去執筆は `_seed_threads.md` で除外される、未着手視点が候補に出る |
| コラム/拠点で完成した記事を wiki に還元したい | **wiki-essay handoff** → **wiki-essay reflect** | コラム/ 側で handoff、LLM_wiki 側で reflect（提案→承認） |
| `_seed_threads.md` を全拠点走査でまとめ直したい | **wiki-essay rebuild-threads** | `_seed_threads.md.bak` を取って提案→承認で再生成 |
| ブラウザで見た記事を入れたい | **Web Clipper → wiki-clip** | クリップ後に「クリップを取り込んで」 |
| 1ファイル/URL/貼り付けをサッと入れたい（vault内作業中） | **/wiki-ingest** | `/wiki-ingest <対象>` |
| wiki に質問したい | **wiki-query**（スキル・どこでも可） | 「wikiに質問」「wikiでは何と言ってる」※vault内なら `/wiki-query <質問>` も可 |
| 矛盾・孤立・リンク切れ・欠落を点検したい | **wiki-lint**（スキル・どこでも可） | 「wikiをlint」「wikiを点検」※vault内なら `/wiki-lint` も可 |
| 孤立ページを実際に繋ぎ直したい（リンクを張る） | **wiki-weave**（スキル・どこでも可） | 「孤立ノードを繋いで」「浮いてるページを繋いで」※lint で見つけた孤立の適用系 |
| 何がどれだけ溜まったか見たい | **wiki-dashboard**（スキル・どこでも可） | 「wikiのダッシュボード」「wiki集計」※vault内なら `/wiki-dashboard` も可 |
| 取り込んだ後に整理・棚卸ししたい | **wiki-lint** ＋ 棚卸し依頼 | 「wikiをlint」→ 「investigationsを整理して」 |
| 出来上がった concept ページを HTML レポートで可視化したい | **wiki-visualize** | 「HTMLレポートで可視化」「ダッシュボード化」「Obsidianで見やすく」。`meta/reports/[date]_[slug]/` に Markdown ラッパー＋フル HTML を出力 |

## 簡易フローチャート
```
何をしたい？
├─ 既にある資料を入れる
│   ├─ ~/claude code/ のプロジェクト or 既存vault → wiki-extract →(確認)→ wiki-absorb
│   ├─ ブラウザのページ                         → Web Clipper → wiki-clip
│   └─ 単一ファイル/URLをvault内で即取込          → /wiki-ingest
├─ まだ無い知識を取りに行く / 知りたいことがある   → wiki-prospect
├─ 自分の中の考えを芽にして育てたい（対話で引き出す）→ wiki-interview →(確認)→ wiki-prospect
├─ seed から長文コラム/エッセイを書く（公開原稿）  → wiki-essay write （→採用後 sync_to_vault.py --apply）
├─ コラム/側で書いた記事を wiki に還元する         → wiki-essay handoff →(相手で)→ wiki-essay reflect
├─ wikiに聞く                                    → wiki-query（スキル・どこでも可）
├─ 手入れ（点検・可視化・整理）                   → wiki-lint · wiki-dashboard（スキル・どこでも可）
└─ ページを HTML レポートで可視化したい           → wiki-visualize（meta/reports/ にハイブリッド出力）
```

> 注: lint/query/dashboard は**グローバルスキル版**があり、外部プロジェクト（例: `~/claude code/...`）から
> extract→absorb した直後でもそのまま使える。`/wiki-*` スラッシュは vault を開いたときの別経路（同等動作）。

## 迷いやすいポイントの補足
- **extract と ingest の違い**: `wiki-extract`(+absorb) は「プロジェクト/vault を**深く網羅的に**2段階で」。`/wiki-ingest` は「単一ソースを**サッと1回で**」。大きい/深さ重視なら extract、軽い1件なら ingest。
- **prospect と collect の違い**: `wiki-prospect` は「**フロンティア検出＋既存深掘り**もできる強化版」。`/wiki-collect`(vault内) は「登録済みの問いを収集する基本版」。迷ったら prospect。
- **interview と prospect の違い**: `wiki-interview` は「**自分の頭の中**の考えを対話で引き出して問い化」（Web調査しない）。`wiki-prospect` は「**外（Web）から**集める」。interview で芽を作り、prospect で裏取り・育成する流れ。
- **opinion と essay の違い**: `wiki-prospect`/`wiki-absorb` が作る `wiki/opinions/` は「**短文要約型**の主張」（数百字、主張＋論拠の骨だけ）。`wiki-essay` は「**公開原稿水準の長文**」（5000字級、note/X/メルマガ等の素材）。同じ seed を opinion でも essay でも持ててよく、essay は opinion を引用する。**意見の蓄積は opinion、世に出す原稿は essay**。
- **wiki-essay の3拠点**: 拠点A = `~/claude code/コラム/`（歴史的本拠地、既存16テーマ、今後も継続）、拠点B = `~/claude code/LLM_wiki/essays/`（wiki seed 駆動の新拠点）、vault `~/Obsidian/LLM_Wiki/essays/`（採用時のみワンウェイ同期、Obsidian バックリンク用）。両拠点は `_inbox/*_request.md` で疎結合連携（handoff → reflect の流れ）。
- **lint と weave の違い**: `wiki-lint` は「検出して提案するだけ（読み取り専用）」。`wiki-weave` は「孤立ノードに実際に双方向リンクを張る（適用系）」。点検は lint、繋ぎ直しは weave。
- **wiki-feed は廃止**: 出てきたら `wiki-extract`＋`wiki-absorb` を案内する。
- 入れた後は **wiki-lint**（スキル・どこでも可）で点検する習慣を勧める。外部プロジェクトからでも実行できる。

## 注意
- このスキルは**判断と誘導まで**。実処理は推奨先に任せる（DRY）。
- 確信が持てない時は曖昧なまま進めず、1問だけ確認する。
