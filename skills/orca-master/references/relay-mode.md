# Relay モード（探索的検討への誘導）

方針がまだ固まっていない作業を worktree とエージェントの並列実行に流すと、誤った前提のまま実装が進む。
この段階では、人間が Claude と Codex の間に入り、やり取りを毎回読んで方向を直すほうが結果が良い（@kenn「Harness of Harnesses」2026-10-16）。
その受け渡しを楽にする道具が Kanary の Relay で、Claude と Codex のデスクトップアプリ間で、ラベル付きでメッセージを送れる。

orca-master は、探索段階の作業を受け取ったら worktree を作らず、このモードに切り替える。

## 判定基準（Step 0 で確認する）

次のうち **2 つ以上** に当てはまれば探索段階とみなす。

- 何を作るか、またはどう設計するかについて、候補が複数あって決まっていない
- 検証できる成功条件（テストで確かめられる完了条件）をまだ書けない
- ユーザーの依頼文が「どうしたらいい」「相談したい」「方向性を考えたい」「比較して決めたい」の形をしている
- 既存の設計・前提を崩すかどうかの判断を含む（大きなリファクタ、技術選定、データ構造の作り直し）
- 作業を独立した単位に分けようとしても、分け方自体が設計判断に依存する

1 つだけ当てはまる場合は、その点だけ `AskUserQuestion` で確かめてから orca-master を続ける。

## 切り替えの確認

判定結果と理由を 2〜3 行で示し、`AskUserQuestion` で確認する。

- **idea-relay で探索する（推奨）**: マスターがそのまま `idea-relay` スキルを起動する。Orca 上で Claude と Codex を agmsg でつなぎ、ユーザーが全メッセージを読んで送るかどうかを決めながら合議する
- **Kanary Relay で探索する**: デスクトップアプリで作業したい場合。下の「Kanary Relay を使う場合」に従う
- **このまま orca-master で進める**: ユーザーが方針は固まっていると判断した場合。Step 1 へ

## idea-relay を使う場合（既定）

マスターは worktree を作らず、`idea-relay` を起動して判定で当てはまった論点を議題として渡す。idea-relay の Step 2 で探索メモ（`codex/plans/YYYYMMDD_<slug>_explore.md`）が確定し、ユーザーが「orca-master で実装に入る」を選んだら、下の「探索の終わり」に進む。

## Kanary Relay を使う場合

Relay の対象は Claude・Codex・Cursor の **デスクトップアプリ** だけで、CLI（Orca などのターミナル上の Claude Code / Codex）には対応していない（Kanary 3.2.0 で確認: 公式ページの対応アプリ一覧、本体が対象として持つアプリ識別子 `com.anthropic.claudefordesktop`・`com.openai.codex`・Cursor のみ、同梱 `kanary` CLI に relay コマンドなし）。送信にはアクセシビリティ権限が要り、無料・Personal プランは週 75 回まで。

1. Kanary が `/Applications/Kanary.app` にあることを確認する。
2. Claude アプリに貼れる出発メモをコードブロック 1 つで示す（解きたい問題、分かっている制約、未決の論点、「まず候補を 3 つ以上出し、利点と弱点を挙げる。Codex の指摘が届いたら案を絞る」という進め方）。
3. マスターは worktree を作らず、agmsg も使わずに待つ。

## 探索の終わりと orca-master への復帰

次がそろったら探索は終わり。

- 採用する方針が 1 つに決まり、捨てた案とその理由が言える
- 検証できる成功条件が書ける
- 作業を独立した単位に分けられる

ユーザーが結論（Claude か Codex の最終的なまとめ）を持って戻ってきたら、マスターはそれを `codex/plans/YYYYMMDD_<slug>_explore.md` に保存し、orca-master の Step 1 に進む。worktree の CC への初期指示では、このファイルを goal-feed の入力レポートとして渡す。
