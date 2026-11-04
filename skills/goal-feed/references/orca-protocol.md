# Orca 連携プロトコル（goal-feed / goal-feed-impl / orca-master 共通の正本）

CC と Codex を Orca 上で組ませるときの、worktree・agmsg・ペイン入力・待機・片付けの手順。
Claude 側と Codex 側の両スキルがこのファイルを参照する。手順を変えるときはここだけを直す。

```text
[Orca] CC（ユーザーと話すペイン）
   │  orca worktree create / orca agent launch / orca terminal send・wait
   └─ Orca worktree <slug>: Codex（/goal 実装）
        ↑ agmsg（本文） + orca terminal send（起こす）を双方向で使う
```

## 役割の分担

- **worktree を作るのは CC だけ。** Codex は `git worktree add` も `orca worktree create` もしない。
- **agmsg は本文の運び役、`orca terminal send` は相手を起こす役。** agmsg だけでは相手は動かない。送ったら必ず起こす。
- **後片付けの判断は CC が持つ。** Codex は判断しない。

## 1. 前提チェック（欠けていたら止まる）

```bash
orca status --json            # runtime.reachable が true。起動していなければ orca open --json
echo "$ORCA_TERMINAL_HANDLE"  # 空なら Orca のターミナルの中にいない
orca worktree current --json  # 配置の判定に使う（次節）
```

`$ORCA_TERMINAL_HANDLE` が空のときは、Codex が CC を起こせないので進めない。Orca のターミナルで起動し直すようユーザーに伝える。
リポジトリが Orca に未登録なら `orca repo add --path "<repo>" --json` で登録する。

## 2. 配置の決定

| `orca worktree current` の結果 | 配置 | やること |
|-------------------------------|------|---------|
| `isMainWorktree: true` | 単独起動 | 3 節で worktree と Codex を作る |
| リンク worktree で、kickoff に Codex のハンドルがある | orca-master 配下 | 作らない。渡された worktree・ハンドル・名前を使う |
| リンク worktree で、kickoff がない | 既存 worktree の再開 | `.goalfeed/state.json` から復元する。無ければユーザーに確認する |

## 3. worktree と Codex の起動（単独起動のとき）

`<slug>` は goal の SLUG。goal-feed-impl は `ticket_index.md` の親ディレクトリ名から決める。

```bash
PRIMARY="$(git rev-parse --show-toplevel)"
BASE="$(git branch --show-current)"

# 1. 自分の名前を先に登録する（TEAM の決め方は 4 節）
~/.agents/skills/agmsg/scripts/join.sh "$TEAM" "<slug>-cc" claude-code "$PRIMARY"

# 2. worktree を作る。--base-branch で未 push のローカルコミットも含める
orca worktree create --repo path:"$PRIMARY" --name <slug> --base-branch "$BASE" \
  --comment "goal-feed: <一行要約>" --json
# result.worktree.id と result.worktree.path を worktree_id / task_worktree に記録する

# 3. 相手の名前も CC が登録する。send.sh は未登録の宛先を拒否するため、Codex の起動より先に行う
~/.agents/skills/agmsg/scripts/join.sh "$TEAM" "<slug>-codex" codex "<task_worktree>"

# 4. ベースの確認
git -C "<task_worktree>" merge-base --is-ancestor "$(git rev-parse HEAD)" HEAD

# 5. Codex を起動する。--surface terminal は省かない（チャットで開くと terminal send で起こせない）
orca agent launch --agent codex --surface terminal --worktree id:<worktree_id> \
  --prompt '<5 節のブリーフ>' --json
# result.outcome.handle を codex_handle に記録する。result.prompt.outcome が handed-to-terminal か journaled であること
```

`BASE` が既定ブランチでないときは、積み上げ作業になるのでユーザーに確認してから進める。

**worktree に来ないもの。** 未コミットのファイルと `.gitignore` 対象（`.env`・`node_modules`・`.godot` など）は来ない。

- 入力のレポートやチケットが未コミットなら、作成前にコミットするかをユーザーに確認する
- 環境の再現は Codex に任せ、ブリーフの「準備」に書く

**CC の立ち位置。** CC は今のペインに残り、worktree を絶対パスで扱う。

- git は `git -C "<task_worktree>" ...`、ファイルは `<task_worktree>/...` の絶対パスで読み書きする
- `codex/plans/`・`codex/reviews/` の成果物は `<task_worktree>` の下に書く。コミットは Codex に任せる
- CC は `<task_worktree>` の git 状態を変えない（checkout・stash・変異テストをしない）。動かして確かめたいときは detach した別 worktree を使う
- `.goalfeed/` は CC の cwd に置く（単独起動なら本体、orca-master 配下なら worktree）

## 4. agmsg の名前

Orca の worktree は本体と同じプロジェクトとして登録されるうえ、`<slug>-cc` を足すと本体の `whoami.sh` も `multiple=true` になる。だから次を守る。

- 名前は `<slug>-cc`・`<slug>-codex`。登録後は `whoami.sh` を使わず、毎回名前を書く
- `TEAM` は、本体で `whoami.sh "$PRIMARY" claude-code` が返すチーム。複数ならユーザーに選んでもらう。未参加ならリポジトリのディレクトリ名を使う（`join.sh` が作る）
- 既に登録済みの名前は join しない（`team.sh "$TEAM"` で確認する）
- 本文にバッククォートを入れない（シェルが展開する）。長い本文はファイルに書き、`"$(cat <file>)"` で渡す

```bash
~/.agents/skills/agmsg/scripts/send.sh "$TEAM" <自分> <相手> "<件名と本文>"
~/.agents/skills/agmsg/scripts/inbox.sh "$TEAM" <自分> > .goalfeed/inbox-<日時>.txt   # 読むと既読になるので必ず保存する
```

## 5. Codex へのブリーフ（`--prompt` に入れる文）

```text
goal-feed の Codex 担当です。最初に ~/.claude/skills/goal-feed/references/orca-protocol.md を読み、その手順に従って。
worktree はこの場所です。新しい worktree・ブランチは作らないこと。
agmsg: チーム <TEAM>、あなたは <slug>-codex、相手は <slug>-cc（どちらも登録済み。whoami.sh は使わない）。
CC のターミナル: <cc_handle>。
準備: <環境の再現に必要な作業。無ければ「なし」>
受信を確認して、<$goal-feed | $goal-feed-impl <ticket_index のパス>> で依頼に対応して。
```

`<cc_handle>` は CC 自身の `$ORCA_TERMINAL_HANDLE`。

## 6. 相手を起こす

送信のたびに、agmsg の直後に実行する。

```bash
# CC → Codex
orca terminal send --terminal <codex_handle> --enter --wait-submit 10 --json \
  --text '~/.agents/skills/agmsg/scripts/inbox.sh <TEAM> <slug>-codex で受信を確認して対応して'

# Codex → CC
orca terminal send --terminal <cc_handle> --enter --json \
  --text '~/.agents/skills/agmsg/scripts/inbox.sh <TEAM> <slug>-cc で受信を確認して、goal-feed のメッセージに対応して'
```

文面のルール:

- 先頭に `/` を置かない。Codex が slash command と解釈する
- Codex にスキルを使わせる指示は `$agmsg` `$ticket-gen` と書く
- `/goal resume` などの slash command は文末に置く（例: `...Phase <N> のレビューを返信済み。指摘対応のうえ次へ進んで /goal resume`）

送信結果の扱い（無反応を理由に同じ文を重ねて送らない）:

| 結果 | 動作 |
|------|------|
| `result.send.prompt.stages` に `turn_started` がある | 届いた。待機へ |
| `stages` が `input_accepted` で止まった | 未確定であって失敗ではない。`orca terminal read --terminal <handle> --screen --json` で見る |
| `agent_prompt_blocked` | 許可メニューが出ている。画面を読み、答えるときは `--text` と `--enter` を別コマンドで送る。判断が要るならユーザーに聞く |
| `terminal_handle_stale` | `orca terminal list --worktree id:<worktree_id> --json` で取り直し、state を更新して新しいハンドルだけを使う |
| 通信エラーで受付が不明 | 同じコマンドに `--retry-request <id>` を付けて再送する |

## 7. 待機と停滞の判定（CC 側）

待つのは Codex の手が止まる瞬間。時間の経過では判断しない。`run_in_background` で 1 本だけ起動し、前面でポーリングしない。

```bash
orca terminal wait --terminal <codex_handle> --for tui-idle --timeout-ms 3300000 --json
```

待機中に Codex から起こされたら、そのまま受信を処理する。待機が後から戻っても、次の判定で「新着なし」になるだけで害はない。

戻ったら `inbox.sh` を 1 回実行し、次で分ける。

| 状況 | 判定 | 動作 |
|------|------|------|
| 新着あり | 正常 | 該当 Phase を処理し、`stall_count` を 0 に戻す |
| `error.code: timeout` | Codex はまだ作業中。**停滞ではない** | 待機を起動し直す |
| idle で新着なし | 停滞の疑い | `--screen` で読む。質問待ちなら答え、報告忘れなら 6 節の文で 1 回起こす。`stall_count` を +1 |
| `status` が running でない | Codex が落ちた | `orca agent launch` でブリーフを再投入し、`ticket_index.md` の続きから再開させる |
| `stall_count >= 3` | ユーザー判断 | `.goalfeed/needs-human.md` に追記し、ユーザーに確認する |

## 8. Codex 側の動き

- 起動時は、ブリーフの worktree・名前・`cc_handle` をそのまま使う。`whoami.sh` と worktree の作成はしない
- メッセージを送ったら 6 節の文で CC を起こす
- 自己レビューと検証を済ませてからレビュー依頼を送り、CC を起こして手を止める。`sleep` で待たない。CC が返信して起こす（レビュー中に同じ差分を書き換えないため）
- 後片付けと `/shime` は CC が行う。`goal-feed session closed`（goal-feed-impl なら `goal-feed-impl session closed`）を受けたら `/goal` を complete にして止まる

## 9. カードの更新

Phase の節目に、worktree のカードへ状況を出す。失敗しても作業は止めない。

```bash
orca worktree set --worktree id:<worktree_id> --comment "Phase <N> レビュー完了" --workspace-status in-progress --json
```

状態の値は `todo` / `in-progress` / `in-review` / `completed`。ユーザーの判断待ちは `--unread` を付けて知らせる。

## 10. 片付け

手順は `review-protocol.md` の G-5b。`git worktree lock` は使わない（Orca のカードと `/shime` の削除条件で保護する）。
worktree の削除はユーザーが `!` で実行する。

```bash
orca worktree rm --worktree id:<worktree_id> --json
```
