---
name: idea-relay
description: |
  Orca 上で Claude Code と Codex を agmsg でつなぎ、ユーザーがすべてのやり取りを読んで「送る・一文足す・止める」を決めながら、アイデアや方針を合議でブラッシュアップするスキル。
  Kanary Relay の考え方（人間はループから外れず、コピペだけをなくす）を CLI で再現する。Claude が発想を広げ、Codex が細部を詰めて落とし穴を指摘し、ユーザーが毎回読んで方向を直す。
  成果は検証可能な成功条件つきの探索メモ（codex/plans/YYYYMMDD_<slug>_explore.md）で、orca-master や goal-feed の入力になる。
  発動条件: (1) /idea-relay コマンド (2)「Codex と合議してアイデアを練りたい」「方針を相談しながら詰めたい」「Relay みたいに Claude と Codex をつないで」「探索的に検討したい」等のキーワード (3) orca-master が探索段階と判定して誘導したとき。
  使用しないケース: 方針が決まっていて実装に入れる作業（→ orca-master / goal-feed）/ コードのレビューだけ欲しいとき（→ codex-second-opinion）/ Orca の外で動かすとき。
allowed-tools: Read, Write, Bash, AskUserQuestion
---

# idea-relay — 人間が間に入る Claude × Codex 合議

自動化された合議は速いが、誤解や的外れな前提がそのまま進む。人間が間に入って毎回読むと、誤解に気づき、足りない文脈を一文足し、ときには「解く問題が違う」と気づいて止められる。
このスキルは、その「読む」部分を残したまま、コピペと窓の切り替えだけを agmsg と Orca に任せる。

```text
ユーザー（全メッセージを読み、送る／一文足す／止めるを決める）
   ↑↓ 毎回確認
メインペインの Claude Code（発想を広げる役＋中継）
   ↑↓ agmsg ＋ orca terminal send
同じ worktree の Codex ペイン（細部を詰める役・ファイルは編集しない）
```

## 原則

1. **何も自動では届かない。** Claude → Codex も Codex → Claude も、ユーザーが中身を読んで送ると決めてから届ける。例外は、ユーザーが「次の N 往復は任せる」と明示したときだけ（N 往復が終わったら必ず確認に戻る）。
2. **要約しない。** Codex の返答は全文をそのまま見せる。要点の抜き出しは全文の後に添えるだけにする。
3. **振り分けを決めない。** どの指摘を採るかはユーザーが決める。Claude は自分の意見を言ってよいが、決定として扱わない。
4. **コードは触らない。** Claude も Codex も、合議中はリポジトリのファイルを編集しない。書いてよいのは `.work/idea-relay/<slug>/` と最終の探索メモだけ。

## 参照ファイル

- `references/codex-brief.md` — Codex に最初に読ませる役割と返信ルール。起動時に絶対パスで読ませる

## 状態とログ

`.work/idea-relay/<slug>/` に置く（`.work/` が `.gitignore` に無ければ追加を提案）。

- `state.json` — `team`・`claude_agent`・`codex_agent`・`codex_handle`・`round`・`auto_rounds_left`
- `log.md` — 全往復の記録。送った文面は、ユーザーが足した一文も含めて、実際に届けた形のまま追記する

会話が要約されたり中断したりしたら、まず state.json と log.md を読んで現在地を復元する。

## 手順

### Step 0 — 準備

1. `orca worktree current --json` で Orca の管理下にいることを確認する。管理下になければ止めてユーザーに伝える。
2. 議題を一行の slug にし、ユーザーから次を聞き取る（足りなければ 1 問ずつ質問する）: 解きたい問題、分かっている制約、すでに捨てた案、ゴールの形（例: 方針 1 つと成功条件）。
3. Claude 側の agmsg 名を決める。`whoami.sh` が 1 つの名前を返せばそれを使い、`multiple=true` なら候補から使う名前をユーザーに選んでもらう（または `<slug>-claude` で `join.sh <team> <slug>-claude claude-code "$(pwd)"`）。決めた名前は state.json の `claude_agent` に記録し、以後は名前を明示して使う。
4. Codex を同じ worktree に起動する。新しい worktree は作らない（コードを変えないため）。

   ```text
   orca terminal create --worktree active --title relay-codex --command "codex" --json
   orca terminal wait --terminal <handle> --for tui-idle --timeout-ms 60000 --json
   ```

   `satisfied: true` を確認してから、Codex に次を送る（`--wait-submit 10` で `turn_started` を確認）:

   ```text
   ~/.claude/skills/idea-relay/references/codex-brief.md を読んで、その役割で合議に参加して。あなたの agmsg 名は <slug>-codex。~/.agents/skills/agmsg/scripts/join.sh <team> <slug>-codex codex "$(pwd)" で参加し（登録済みなら不要）、whoami.sh で名前を決めないこと。最初のメッセージが届くまで待って
   ```

   agmsg は worktree や同じリポジトリの名前を 1 つのプロジェクトにまとめて登録するため、`whoami.sh` は複数の名前を返して判定できないことがある。また自動配信はユーザーの方針で止めてあり、worktree では設定ファイルも来ない。だから Claude 側も Codex 側も、送受信は毎回名前を書いて実行し、送ったら相手を `orca terminal send` で起こす。

### Step 1 — 広げる（Claude の番）

Claude として候補を 3 つ以上出し、それぞれの狙い・利点・弱点・確かめ方を書く。ここで 1 つに絞らない。
書いた文面を全文見せ、**送信ゲート**に進む。

### 送信ゲート（Claude → Codex、毎回）

`AskUserQuestion` で選んでもらう:

- **このまま送る**
- **一文足して送る** — 足す文をユーザーに書いてもらい、`ユーザーより:` の見出しを付けて文面の末尾に加える
- **書き直す** — 何を変えるか聞いて Claude が書き直し、もう一度このゲートへ
- **送らない／方向を変える** — 送らずに Step 0 の論点整理に戻る

送ると決まったら:

1. 文面の先頭行を `idea-relay round <N> from claude` にして、`send.sh <team> <claude_agent> <codex_agent> "<文面>"` で送る。
2. 続けて `orca terminal send --terminal <codex_handle> --text '~/.agents/skills/agmsg/scripts/inbox.sh <team> <codex_agent> で受信を確認して、idea-relay のメッセージに答えて。返信は ~/.agents/skills/agmsg/scripts/send.sh <team> <codex_agent> <claude_agent> で送ること' --enter --wait-submit 10 --json` で Codex を起こす。`turn_started` が確認できなければ `orca terminal read --screen` で画面を見て判断する（無反応を理由に重ねて送らない）。
3. log.md に追記し、state.json の round を進める。

### 返答待ち（ブロッキング・前面ポーリング禁止）

`~/.claude/skills/goal-feed/references/orca-protocol.md` 7 節と同じく、待機は `run_in_background` で 1 本だけ起動し、前面でポーリングしない（ループや Monitor は使わない）。タイムアウトは下の 20 分に合わせる。待機が戻ったら受信を 1 回確認する。

```bash
# run_in_background で起動する
orca terminal wait --terminal <codex_handle> --for tui-idle --timeout-ms 1200000 --json
# 待機が戻ったら実行する
~/.agents/skills/agmsg/scripts/inbox.sh <team> <claude_agent> > .work/idea-relay/<slug>/inbox-<N>.txt 2>&1
```

`inbox.sh` は読んだ時点で既読にするので、出力は必ずファイルに残してから読む。

- ファイルに `idea-relay round` で始まる返答がある → 受信ゲートへ。`idea-relay` 以外のメッセージが混ざっていたらユーザーに知らせる。
- 返答がない → `orca terminal read --terminal <codex_handle> --screen --json` で画面を見る。まだ考えている途中なら、もう一度 wait から繰り返す（合計 20 分まで）。入力待ちなのに送っていないなら、送信手順の 2 の文面で 1 回だけ起こし直す。20 分を超えたら状況をユーザーに伝え、待つか起こし直すかを聞く。

### 受信ゲート（Codex → Claude、毎回）

Codex の返答を**全文そのまま**見せ、その後に Claude の受け止め（同意する点・反論したい点）を短く添える。`AskUserQuestion`:

- **Claude に返して続ける** — Step 1 と同じ要領で Claude が応答を書き、送信ゲートへ
- **一文足して返す** — ユーザーの文脈を加えてから Claude が応答を書く
- **方向を変える** — ユーザーの指示で論点を組み替え、Claude が新しい問いを書く
- **まとめに入る** — Step 2 へ

ユーザーが「次の N 往復は任せる」と言ったら、state.json の `auto_rounds_left` に N を入れ、その間だけ両ゲートを省略する（log.md には残す）。0 になったら受信ゲートに戻る。

### Step 2 — まとめる

1. Claude が探索メモの草案を書く。構成:
   - 採用する方針（1 つ）と、その理由
   - 捨てた案と、捨てた理由
   - 検証できる成功条件
   - 独立して進められる作業の分け方（orca-master の Step 1 にそのまま渡せる粒度）
   - 未解決の論点と、誰がいつ決めるか
2. 送信ゲートを通して Codex に最終確認を頼む（`idea-relay final review`）。返答は受信ゲートで見せる。
3. ユーザーが確定したら `codex/plans/YYYYMMDD_<slug>_explore.md` に Write する（同名があれば `_v2` を付ける）。
4. 次の行き先を聞く: orca-master で実装に入る／goal-feed にこのメモを渡す／ここで終える。

### Step 3 — 片付け

Codex ペインは、ユーザーの了承を得てから `orca terminal close --terminal <codex_handle> --json` で閉じる。`.work/idea-relay/<slug>/` は残す（log.md が議論の記録になる）。

ペインを閉じたら、この合議のために登録した agmsg の名前も外す。

- `~/.agents/skills/agmsg/scripts/leave.sh <team> <codex_agent>`（`<slug>-codex`）
- Claude 側をこの合議のために新しく作った（`<slug>-claude` など）なら、それも `leave.sh` で外す。前から使っている名前（例: `playground_cc`）は外さない
- チームをこの合議のために新しく作ったなら、上の 2 つで最後の 1 人が抜けた時点でチームも消える。プロジェクト共通の既存チームはたたまない
- `~/.agents/skills/agmsg/scripts/team.sh <team>` で残りを確かめる。メッセージ履歴と log.md は残る
