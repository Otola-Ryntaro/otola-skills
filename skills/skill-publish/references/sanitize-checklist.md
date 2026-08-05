# sanitize-checklist — 公開前サニタイズ手順

公開対象フォルダ（コピー後の otola-skills 側）に対して上から順に実行する。
正本（Skill-library）には一切変更を加えないこと。

## 1. 絶対パス

```bash
grep -rn "/Users/tkojima" <対象フォルダ>
```

| 元の表記 | 置換後 |
|---------|--------|
| `/Users/tkojima/claude code/<プロジェクト>/...` | `<YOUR_PROJECT_ROOT>/...` |
| `/Users/tkojima/.claude/skills/...` | `~/.claude/skills/...` |
| `/Users/tkojima/Obsidian/...` | `<YOUR_VAULT>/...` |
| その他の `/Users/tkojima/...` | `~/...` か `<YOUR_...>` 表記で文脈に合わせる |

置換後にその手順が成立するか読み直す。成立しないなら該当スキルは除外して報告。

## 2. 個人情報・ペルソナ

```bash
grep -rn "音良林太郎\|Otola\|otola\|persona" <対象フォルダ>
```

- **OK（残す）**: Author 表記・クレジット（例: `音良林太郎 (Otola Ryntaro)`、`@Otola_ryntaro`）
- **要対応**: ペルソナ設定ファイル（persona_*.md）、「わたし＝ノンエンジニア/クリニック経営」等の
  個人前提がスキルの動作条件に組み込まれた記述 → 汎用化できるなら書き換え、できないなら除外
- **禁止**: 実名・メールアドレス・GitHub 別アカウント名（TKojima85th 等）は絶対に含めない

## 3. 秘匿情報

```bash
grep -rn "sk-ant\|sk-proj\|API_KEY=\|ghp_\|Bearer \|password" <対象フォルダ>
```

1 件でも実物らしきものがヒットしたら**公開を中止**してユーザーに報告。
（ドキュメント中の `$GEMINI_API_KEY` のような環境変数参照や、明らかなサンプル値は OK）

## 4. ドメイン固有情報

クリニック名・患者情報・取引先・内部 URL・未公開サービスの戦略記述が無いか、
SKILL.md と references/ を目視で 1 パス確認する（grep では拾いきれないため）。

## 5. 最終確認

```bash
cd <otola-skillsルート>
grep -rn "/Users/tkojima" --exclude-dir=.git . | grep -v "skills/skill-publish" | wc -l   # 0 であること（skill-publish 自身の手順記載は除外）
```
