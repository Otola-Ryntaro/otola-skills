# wiki-common/references/ の使い方

このディレクトリは **単独では発動しないスキル `wiki-common` の中身**。他の wiki 系スキルからは `Skill(skill: "wiki-common")` ではなく、**Read ツールで直接このディレクトリ内のファイルを読む**。

```
Read: ~/.claude/skills/wiki-common/references/confidence-table.md
Read: ~/.claude/skills/wiki-common/references/frontmatter-schema.md
Read: ~/.claude/skills/wiki-common/references/domain-definitions.md
Read: ~/.claude/skills/wiki-common/references/html-style-guide.md
```

## ファイル一覧

| ファイル | 内容 | 主な参照元スキル |
|---|---|---|
| `confidence-table.md` | 資料種別×confidence 上限の判定基準 | wiki-in（取込系）、wiki-seed（収集系） |
| `frontmatter-schema.md` | wiki ページの frontmatter 標準 | wiki-in、wiki-care、wiki-seed |
| `domain-definitions.md` | ドメイン定義（5ドメイン＋横断トラックハブの区別） | wiki-in、wiki-seed |
| `html-style-guide.md` | HTML 可視化のスタイルガイド | wiki-view（旧 wiki-visualize） |

## DRY 運用ルール

- これらのファイルの内容を他スキルの SKILL.md にコピーしない。「詳細は `~/.claude/skills/wiki-common/references/xxx.md` を参照」の1行で済ませる
- vault 側の正本（`~/Obsidian/LLM_Wiki/CLAUDE.md`、`config.md`）が変更されたら、このディレクトリの該当ファイルも追従更新する
- 旧スキル（wiki-extract / wiki-clip / wiki-prospect 等）の改変・削除は REB-012（旧スキル一括廃止）で行う。本チケット（REB-008）では一切触らない
