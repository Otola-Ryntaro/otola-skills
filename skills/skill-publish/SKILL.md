---
name: skill-publish
description: 自作スキル・コマンドを公開リポジトリ otola-skills（github.com/Otola-Ryntaro/otola-skills）へ手動同期するスキル。Skill-library を供給元とし、自作判定チェック → サニタイズ（絶対パス・ペルソナ情報・秘匿情報のスキャンと置換）→ コピー → PUBLISH_LIST.md / README 更新 → commit → push（毎回ユーザー確認）まで面倒を見る。発動条件 (1) /skill-publish [スキル名] コマンド (2)「スキルを公開して」「otola-skills に追加/反映して」「公開リポを更新」「今日作ったスキルを公開」等のキーワード (3) 新スキル完成後に「これも公開する？」の文脈。使用しないケース：非自作スキルの公開（SuperClaude 由来等は対象外）／project-skills のクリニック・事業固有スキル（公開リスク高、明示指示がある場合のみ個別判断）／Skill-library 内部の整理だけで公開不要な場合。
---

# skill-publish — 自作スキルの公開リポジトリ同期

<!--
  where: Skill-library/global-skills/skill-publish/（実働ミラー: ~/.claude/skills/skill-publish/）
  what : Skill-library の自作スキルを public リポ otola-skills へサニタイズ付きで手動同期する
  why  : 公開は不可逆な外部行為なので、自作判定・秘匿情報スキャン・push 前確認を毎回同じ手順で通すため
-->

## 前提

- 供給元（正本）: `~/claude code/Evironment/Skill-library/`（global-skills / global-commands）
- 公開先: `~/claude code/otola-skills/` → `github.com/Otola-Ryntaro/otola-skills`（public）
- 公開台帳: `otola-skills/PUBLISH_LIST.md`（公開済みスキルの唯一の記録。ここに無い＝未公開）
- 自作判定の正本: `Skill-library/README.md` の「オリジナル（自作）判定」セクション

## フロー

### Step 1: 対象の特定

- 引数や会話でスキル名が指定されていればそれを対象にする。
- 無指定なら `PUBLISH_LIST.md` と Skill-library を突き合わせ、次の 2 種類を一覧提示して選んでもらう:
  - **未公開**: global-skills / global-commands にあるが台帳に無いもの（非自作・初回除外リスト該当は除く）
  - **更新あり**: 台帳に記録された最終同期日以降に正本側が変更されたもの
    （`diff -r` で公開先と比較するのが確実）

### Step 2: 自作判定（新規公開のみ）

`Skill-library/README.md` の 4 基準でチェックし、判定根拠とともにユーザーに公開可否を確認する:
1. 日本語で書かれ、固有ドメイン（自分の業務・運用）に言及しているか
2. SuperClaude 特有 frontmatter（category / personas / mcp-servers、"Context Framework Note"）が**無い**か
3. version / LICENSE 表記が既知の配布物と一致して**いない**か
4. SOURCE.md（外部出典明記）が**無い**か

判定があいまいなら公開しない側に倒し、ユーザーに理由を添えて相談する。

### Step 3: サニタイズスキャン

`references/sanitize-checklist.md` を Read し、対象スキルのフォルダ全体に対して実行する。
要点: 絶対パス（`/Users/tkojima`）は汎用表記へ置換、ペルソナ・個人環境前提の記述は除去または汎用化、
API キー痕跡はヒットしたら公開中止して報告。**置換で意味が壊れる場合はそのスキルを除外して報告する。**
置換は公開先へのコピーに対してのみ行い、**正本（Skill-library）は書き換えない。**

### Step 4: コピーと台帳更新

1. スキルは `otola-skills/skills/<name>/`、コマンドは `otola-skills/commands/<name>.md` へコピー
   （更新の場合は公開先フォルダを一旦削除してからコピーし、削除済みファイルの残骸を防ぐ）
2. コピー後にサニタイズ置換を適用
3. `PUBLISH_LIST.md` に「スキル名 / 供給元パス / 同期日 / サニタイズ内容」を追記または更新
4. `README.md` のスキル一覧表を更新（新規追加時）

### Step 5: commit と push

1. `git diff` / `git status` を提示して内容をユーザーに確認してもらう
2. 承認後 commit（メッセージ例: `feat: <skill名> を公開` / `update: <skill名> を同期`）
3. **push は公開行為なので、commit とは別に毎回ユーザー確認を取ってから実行する**

## 検証（毎回）

- 公開先全体で `grep -r "/Users/tkojima" .`（.git 除く）が 0 件
- `grep -rn "sk-ant\|sk-proj\|API_KEY=\|ghp_" .`（.git 除く）が 0 件
- `PUBLISH_LIST.md` の件数 = `skills/` のフォルダ数 + `commands/` のファイル数

## 運用メモ

- 公開先リポが手元に無い場合: `gh repo clone Otola-Ryntaro/otola-skills "~/claude code/otola-skills"`
- 初回除外リスト（ペルソナ組込みのため保留中）: user-guide / tech-intro-writer / source-explainer。
  公開したくなったらサニタイズ版を別途設計する。
- 正本の変更はあくまで Evironment 側で行い、otola-skills には手を入れない（一方向同期）。
