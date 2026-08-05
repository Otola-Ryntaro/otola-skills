# ドメイン定義（正本は vault `config.md`）

正本: `~/Obsidian/LLM_Wiki/config.md`「ドメイン定義」節。ここには要点を転記する。ドメイン追加時は vault 側 `config.md` に行を足し、`wiki/domains/<キー>.md` ハブを作るのが正しい手順（このファイルへの追記だけでは不十分）。

## 5 ドメイン（2026-07-03 時点）

| キー | 表示名 | 説明 | 主な源 |
|---|---|---|---|
| `medical-science` | 医療・科学 | 耳鼻科・難聴・エビデンス医療・一般科学 | Paper_Serch / Otoiro_articles / コラム |
| `society-thought` | 思想・社会・倫理 | 科学論・医療倫理・社会批評・心理 | 既存vaultコラム22本 |
| `investment` | 投資・経済 | 株式・市場分析 | Stock_Analysis系 |
| `ai-tech` | AI・技術 | LLM・Claude Code・開発 | Web収集中心 |
| `clinic-management` | クリニック経営 | 医療機関の経営・連携・集患・地域連携の戦略と実務 | Otoiro_website ほか開業/経営プロジェクト |

`clinic-management` は複数の開業/経営プロジェクトで共通利用する横断軸。新規ページ追加時は既存ページとの重複を確認する。

## 重要な訂正: 「6 ドメイン」ではなく 5 ドメイン + 1 横断トラックハブ

`docs/20260703_rebuild_review.md` は「6 domain hub」と記載しているが、`wiki/domains/` の実ファイルを確認したところ：

- 上記 5 ドメインの domain-hub（`ai-tech.md` `clinic-management.md` `investment.md` `medical-science.md` `society-thought.md`）
- `補聴器メルマガ.md`（`type: domain-hub` だが `domain: [medical-science, clinic-management]` の**横断トラックハブ (MOC)** であり、独立した6番目のドメインではない）

新規スキルで「6ドメイン」という前提を書かないこと。ドメインは 5、横断トラックハブは別概念として扱う。

## 収穫元（既存資産・参照のみ／コピーしない）

vault `config.md` の「収穫元」節を参照。プロジェクト別の価値評価（★★★等）とパスが記載されている。定期的に変わりうるため、このファイルには転記しない。
