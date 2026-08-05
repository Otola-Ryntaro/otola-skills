# Fake/Test Pattern Check

テスト不正・その場しのぎコードの全体チェックを実行します。

## Step 1: スキルのインストール

以下の2つをプロジェクトにインストールする：

```bash
npx skills add dagster-io/erk@fake-driven-testing -y
npx skills add bobmatnyc/claude-mpm-skills@testing-anti-patterns -y
```

## Step 2: スキル内容の読み込み

インストールされた以下のファイルを Read して、チェック観点を把握する：

- `.agents/skills/fake-driven-testing/` 配下の `.md` ファイル
- `.agents/skills/testing-anti-patterns/` 配下の `.md` ファイル

## Step 3: プロジェクト全体のコードチェック

把握したスキルの観点で、プロジェクトのソースコードを総ざらいする。

### fake-driven-testing の観点（実装コード側）

以下のパターンを検出する：
- テスト入力値をハードコードして返すだけの実装（例: `if input == "test" return expected`）
- テスト環境かどうかで分岐しているコード（例: `if process.env.NODE_ENV === 'test'`）
- 実際の処理をせず固定値を返す関数
- テスト専用の特殊ロジックが本番コードに混入している箇所

### testing-anti-patterns の観点（テストコード側）

以下のパターンを検出する：
- 何も検証していないテスト（`expect(true).toBe(true)` など）
- 常にパスするアサーション
- テスト対象を確認せずに成功するテスト
- 意味のないモックやスタブ

## Step 4: レポート出力

現在時刻を取得して、以下のパスにレポートを書き出す：

`docs/(Y_M_D_H_M)_codecheck.md`

### レポートフォーマット

```markdown
# テスト不正チェックレポート
実行日時: (YYYY年M月D日 H:M)

## サマリー
- 検出件数（Critical）: X件
- 検出件数（Major）: X件
- 検出件数（Minor）: X件

## 検出一覧

### [Critical / Major / Minor] ファイルパス:行番号
**種別**: fake-driven-testing / testing-anti-patterns
**内容**: 具体的な問題の説明
**該当コード**:
```コード```
**推奨対応**: 具体的な修正方法

---
```

`docs/` ディレクトリが存在しない場合は先に作成すること。

## Step 5: 後片付けコマンドの表示

チェック完了後、以下のメッセージを必ず表示する：

---

✅ チェック完了。レポートを `docs/(timestamp)_codecheck.md` に出力しました。

**スキルを削除するには、以下をターミナルでコピペ実行してください：**

```bash
rm -rf .agents/skills/fake-driven-testing
rm -rf .agents/skills/testing-anti-patterns
```

---
