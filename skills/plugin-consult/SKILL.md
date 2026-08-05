---
name: plugin-consult
description: >
  現在のタスクに合う knowledge-work プラグイン（engineering / product-management /
  enterprise-search / data / design / pdf-viewer / marketing / small-business / canva）を
  提案し、使い方（そのまま呼ぶ / SKILL.md 直読み / プロジェクト単位で有効化）まで案内する
  コンシェルジュスキル。
  発動条件:
  (1) /plugin-consult コマンド
  (2) 「使えるプラグインある？」「プラグイン相談」「このタスクに合うスキルは？」等のキーワード
  (3) タスク内容が references/catalog.md の早見表に明確に合致し、該当プラグインのスキルを
      ユーザーが使っていない様子のとき（能動提案。1会話1回まで）
allowed-tools: Read, Glob, Grep, Bash, AskUserQuestion
---

# plugin-consult: プラグイン提案コンシェルジュ

タスク内容と `references/catalog.md` を照合し、合うプラグイン・スキルを根拠付きで提案する。
**押し売りしない**: 明確に合うものがなければ「該当なし」と正直に言って終わる。能動提案は1会話につき1回まで。

## Phase 1: 照合

1. `references/catalog.md` を Read する（このスキルと同じディレクトリ配下）。
2. ユーザーのタスク・依頼内容を早見表と照合し、候補を最大2プラグイン・3スキルに絞る。
3. コネクタ前提のもの（enterprise-search / small-business の大半 / canva）は、
   接続状況を確認せずに「使えます」と言わない。前提条件として明示する。

## Phase 2: 状態確認

候補プラグインの現在の状態を確認する:

```bash
claude plugin list 2>/dev/null | grep -A2 <plugin-name>
```

- **有効（enabled）**: そのままスキルを呼べる。スキル名を伝えて誘導する。
- **無効（disabled）または未インストール**: Phase 3 の選択肢を出す。

## Phase 3: 提案と適用

AskUserQuestion で以下から選ばせる（有効化済みなら不要）:

1. **今すぐ使う（Read 方式）**: 再起動不要。
   `~/.claude/plugins/cache/knowledge-work-plugins/<plugin>/<version>/skills/<skill>/SKILL.md`
   を Read して、その内容に従ってその場で実行する。
2. **プロジェクト単位で有効化**: `claude plugin install <plugin>@knowledge-work-plugins --scope project`
   （またはプロジェクトの `.claude/settings.json` の `enabledPlugins` に追記）。
   **スキル一覧への反映はセッション再起動後**であることを必ず伝え、今回は Read 方式で続行する。
3. **見送り**: 何もしない。

## 制約

- カタログにないプラグインを推測で提案しない。marketplace に他のプラグイン（figma, zapier 等）も
  あることは知っているが、提案するのはカタログ掲載の9つのみ。カタログ外が欲しそうなら
  「マーケットプレイスに他にもある」と伝えて /plugin を案内する。
- プラグインの install / enable / disable は必ずユーザー確認を取ってから実行する。
- カタログが実態と食い違っていたら（プラグイン更新等）、その場で実物を確認し、カタログの更新を提案する。
