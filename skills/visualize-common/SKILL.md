---
name: visualize-common
description: >
  スキル可視化 HTML（-visualize / manual-todo / レポート系）の共通正本。
  ダークテーマ CSS・アクションファースト構成規約・base64 スクショギャラリー部品を提供する
  参照専用アセット集であり、単独では発動しない。
  shime / manual-todo / source-explainer / tech-intro-writer / user-guide などの
  HTML 生成スキルが SKILL.md からこの正本を参照する。
---

# visualize-common — 可視化 HTML 共通正本

<!--
  where: Skill-library/global-skills/visualize-common/（実働ミラー: ~/.claude/skills/visualize-common/）
  what : スキル群の HTML 可視化に共通する CSS・構成・スクショ埋め込みの正本
  why  : 各スキルのテンプレが独自進化して「開いても何をすべきか分からない HTML」になるのを防ぐ
-->

## 位置づけ

- **参照専用**。ユーザーが `/visualize-common` として呼ぶことはない（wiki-common と同じ位置づけ）。
- スキル可視化系（ダークテーマ）の正本はここ。**wiki 系（ライトテーマ・JS 禁止）の正本は別**で、
  `wiki-common/references/html-style-guide.md` を参照すること。

## 収録物

| ファイル | 内容 |
|---------|------|
| `references/style-guide.md` | ダークテーマ CSS 正本（`:root` 変数・共通コンポーネント語彙・JS ポリシー） |
| `references/action-first.md` | セクション順序の固定規約（アクションファースト）＋文章量ガイドライン |
| `references/screenshot-embed.md` | base64 スクショギャラリー部品（HTML 断片・sips/base64 手順・サイズ規約・収集元パス） |
| `assets/base-template.html` | 正本スケルトン。新規テンプレ作成・既存テンプレ改訂時の見本 |

## 参照方法（各スキル向け）

各スキルの SKILL.md に次のように書き、HTML 生成時に該当 reference を Read する:

```text
HTML の CSS・構成・スクショ埋め込みは visualize-common 正本に従う:
- ~/.claude/skills/visualize-common/references/style-guide.md
- ~/.claude/skills/visualize-common/references/action-first.md
- ~/.claude/skills/visualize-common/references/screenshot-embed.md
```

テンプレは各スキルが自分の `assets/` に持ち続ける（**差し替え方式は維持**。include 機構は作らない）。
正本の CSS 変更時は、各スキルのテンプレへ手動でコピー同期する。

## ヒーロー画像規約（project-hero 連携）

対象プロジェクトの直下に `assets/hero.png`（project-hero スキルが生成、1280×640）が存在する場合、
可視化 HTML のヘッダーでは **📂プロジェクト名表記の直上に** ヒーロー画像を表示する:

```html
<img src="（hero.png を base64 化した data URI）" alt="project hero"
     style="width:100%;max-width:960px;border-radius:12px;display:block;margin:0 auto 12px;">
```

- 画像は base64 埋込（可視化 HTML は単一ファイル自己完結の原則を維持）
- `assets/hero.png` が無いプロジェクトでは何も表示しない（従来どおり📂プロジェクト名のみ）

## 更新時の注意

- `references/style-guide.md` の `:root` 変数ブロックを変更したら、参照スキル
  （shime / manual-todo / source-explainer / tech-intro-writer / user-guide）のテンプレも同期し、
  各スキルを 1 回生成して回帰確認すること。
- 正本は `Skill-library/global-skills/visualize-common/`。変更後は
  `cp -R` で `~/.claude/skills/visualize-common/` へミラーする（symlink ではない）。
