<!--
拠点間の申し送り文テンプレート（wiki-essay handoff モードで使用、wiki-essay reflect モードが読む）
元レポート §3「申し送り文フォーマット」に準拠。

ファイル名: YYYY-MM-DD_<slug>_request.md
保存先:
  - コラム/ 発 → ~/claude code/LLM_wiki/essays/_inbox/
  - LLM_wiki/essays/ 発 → ~/claude code/コラム/_inbox/
-->
---
source: ~/claude code/コラム/<テーマ>/<file>.md   # 完成記事の絶対パス
seeds_referenced:                                  # 起点 seed（_seed_threads.md の seed-slug と一致）
  - <seed-slug>
created: 2026-06-21                                # 申し送り文の作成日
---

## このコラムの概要

（200字程度の要約。reflect モードがユーザーに何を承認させるか判断する材料）

## wiki への依頼アクション

<!-- 各アクションはチェックボックス。reflect モードが集約して提案リストとして提示する。
     不要な行は削除し、必要な行のみ残すこと。 -->

- [ ] interests/questions.md の seed `<seed-slug>` を `<新status>` に更新（例: open → covered）
- [ ] [[wiki/opinions/<page>]] の「## 関連」セクションに、このコラムへのリンク追加
- [ ] [[wiki/concepts/<page>]] の「## 関連」セクションに、このコラムへのリンク追加
- [ ] 新主張「<一文>」を wiki/opinions/ 追加候補として登録（出典: source）
- [ ] 引用した事実「<一文>」が wiki/concepts/ に未登録 → 収集 seed 化候補
