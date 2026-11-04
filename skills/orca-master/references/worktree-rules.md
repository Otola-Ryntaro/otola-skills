# worktree 内のルール（全エージェント共通）

Orca のマスター（司令部）の指揮下で、1 つの worktree の中で働くエージェント（Claude Code・Codex・Cursor・Hermes など）は次を守る。
マスターは Phase 完了報告のたびに、コミットとブランチの状態を確認する。

## ブランチ

1. **新しいブランチを作らない。** この worktree のブランチ（Orca が作成時に作ったもの）だけで作業する。`git checkout -b`・`git switch -c`・`git branch <name>`・`git worktree add` は禁止。
2. 別のブランチに切り替えない（`git checkout <other>`・`git switch <other>` をしない）。
3. 別の作業が必要だと思ったら、自分でブランチや worktree を作らず、CC がマスターに `orca-master blocked` で相談する。

## コミット

1. **チケットが 1 つ終わるたび、遅くとも Phase が終わるたびにコミットする。** 未コミットのまま次の Phase に進まない。
2. コミット前に `git diff` を見て、自分の担当範囲外の変更が混ざっていないか確かめる。
3. コミットメッセージは Conventional Commits 形式（`feat:` `fix:` `refactor:` `test:` `docs:`）で、何をなぜ変えたかを日本語で書く。
4. テストや lint が落ちている状態でコミットしない。どうしても途中経過を残すときは `wip:` を付け、次のコミットで直す。
5. `git push`・`git rebase`・`git reset --hard`・`--force` 系はしない。push と main への統合はマスター経由でユーザーが行う。

## レビュー

1. **Phase ごとに相互レビューを通してから次へ進む。** 既定は Codex が実装し CC がレビュー（goal-feed の Phase F）。CC が実装した部分は Codex がレビューする。
2. 補助エージェント（2 体目の Codex・Cursor・Hermes など）の成果は、CC か Codex が必ずレビューする。補助エージェント同士でレビューを完結させない。
3. Critical の指摘が残っている間は次の Phase に進まない。3 往復しても解消しなければ CC がマスターに `orca-master needs-human` を送る。
4. APPROVE には根拠（実行したテストコマンドと結果、ビルド出力、動作確認手順のどれか）を添える。

## 範囲

1. マスターが指定した「触ってよい範囲」の外を変更しない。必要なら `orca-master blocked` で相談する。
2. 依頼されていない機能を足さない。関係のない箇所のリファクタリングをしない。

## マスターへの報告（CC が担当）

agmsg でマスターに送る。件名と本文の要素:

| 件名 | 送るとき | 本文に書くこと |
|------|---------|--------------|
| `orca-master report` | Phase が終わったとき | Phase 番号、コミット hash、レビュー結果（APPROVE / 指摘数）、次の Phase |
| `orca-master blocked` | 進めないとき | 何が足りないか、範囲外の変更が必要か |
| `orca-master needs-human` | ユーザーの判断が要るとき | 判断事項と選択肢（2〜4 個） |

送ったら、続けてマスターのペインを起こす（`kickoff-template.md` の「マスターの起こし方」）。起こしたあとも届いたとは決めつけず、返信が来るまで自分の担当で進められる作業を続ける。

## agmsg の使い方（全エージェント）

1. 自分の agmsg 名はマスターか CC から指定されたもの（`<slug>-cc`・`<slug>-codex` など）を使う。`whoami.sh` で名前を決めない。
2. 送受信は名前を書いて実行する: `~/.agents/skills/agmsg/scripts/send.sh <team> <自分> <相手> "<本文>"`、`~/.agents/skills/agmsg/scripts/inbox.sh <team> <自分>`。
3. 自動配信は動かない前提で、送ったら相手のペインを `orca terminal send` で起こす（`~/.claude/skills/goal-feed/references/orca-protocol.md` の 6 節）。

## 実データ遮断 hook の下での作業（W1e 以降、経営分析リポジトリ）

Claude Code には `.claude/hooks/guard_private_data.py` が PreToolUse で効いている。事故を減らす補助であり、遮断の証明ではない。Codex には効かないので、Codex は `AGENTS.md` の禁止パス節に従う。

1. 保護パスの語（`input_original/` などのスラッシュ付き）をコマンド文字列に入れると、文章の一部でも Bash が拒否される。コミットメッセージ・agmsg の本文・レビューの追記は Write でファイルに書き、`git commit -F <file>`、`send.sh ... "$(cat <file>)"` で渡す。heredoc で書かない
2. 拒否されても回避を試みない（言い換え・符号化・変数経由・スクリプト経由で同じアクセスをしない）。正当な作業が止まったら、合成の再現例と件数を添えて CC がマスターに `orca-master blocked` を送る
3. 実データのある checkout（main など）では、範囲を指定しない Grep・Glob・`grep -r .` は拒否される。`docs/`・`src/` のように範囲を指定する
4. hook の判定エラー（「入力または判定エラーのため拒否」）は fail-closed の結果で、誤検知の可能性がある。上と同じく再現例を添えて報告する
5. settings.json の hook エントリを外す・無効にするのは院長の判断に限る。エージェントは変更しない
