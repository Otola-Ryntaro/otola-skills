# Browser Use CLI コマンドリファレンス

バイナリパス: `~/.browser-use-env/bin/browser-use`

## セッション・起動オプション

| オプション | 説明 |
|-----------|------|
| `--headed` | ブラウザウィンドウを表示 |
| `--profile [name]` | Real Chrome プロファイルで起動（既存ログイン利用可） |
| `--cdp-url <url>` | 既存Chrome に CDP 接続 |
| `--connect` | 実行中Chrome を自動検出して接続 |
| `--session <name>` | 名前付きセッション（並列テスト用） |
| `--json` | JSON 出力 |

## ナビゲーション

| コマンド | 説明 |
|---------|------|
| `open <url>` | URL に遷移 |
| `back` | 前のページに戻る |
| `scroll down` | 下にスクロール |
| `scroll up` | 上にスクロール |
| `scroll down --amount 1000` | ピクセル指定スクロール |

## 状態確認

| コマンド | 説明 |
|---------|------|
| `state` | URL・タイトル・クリック可能要素一覧（番号付き） |
| `screenshot [path]` | スクリーンショット（パス指定で保存） |
| `screenshot --full path.png` | フルページスクリーンショット |

## インタラクション

| コマンド | 説明 |
|---------|------|
| `click <index>` | 番号指定でクリック |
| `click <x> <y>` | 座標指定でクリック |
| `type "text"` | フォーカス中の要素にテキスト入力 |
| `input <index> "text"` | 要素をクリックしてテキスト入力 |
| `keys "Enter"` | キー送信 |
| `keys "Control+a"` | キーコンビネーション |
| `select <index> "value"` | ドロップダウン選択 |
| `upload <index> <path>` | ファイルアップロード |
| `hover <index>` | ホバー |
| `dblclick <index>` | ダブルクリック |
| `rightclick <index>` | 右クリック |

## タブ管理

| コマンド | 説明 |
|---------|------|
| `switch <tab>` | タブ切り替え（インデックス指定） |
| `close-tab` | 現在のタブを閉じる |
| `close-tab <tab>` | 指定タブを閉じる |

## Cookie 操作

| コマンド | 説明 |
|---------|------|
| `cookies get` | Cookie 取得 |
| `cookies set <name> <value>` | Cookie 設定 |
| `cookies clear` | Cookie クリア |
| `cookies export <file>` | Cookie エクスポート |
| `cookies import <file>` | Cookie インポート |

オプション: `--url`, `--domain`, `--secure`, `--same-site`, `--expires`

## 待機

| コマンド | 説明 |
|---------|------|
| `wait selector "css"` | 要素が表示されるまで待機 |
| `wait text "文字列"` | テキストが表示されるまで待機 |
| `wait selector ".loading" --state hidden` | 要素が非表示になるまで待機 |

## データ取得

| コマンド | 説明 |
|---------|------|
| `get title` | ページタイトル |
| `get html` | HTML ソース |
| `get text <index>` | 要素のテキスト |
| `get value <index>` | 要素の値 |
| `get attributes <index>` | 要素の属性 |
| `get bbox <index>` | 要素のバウンディングボックス |

## JavaScript 実行

| コマンド | 説明 |
|---------|------|
| `eval "js code"` | JavaScript を実行 |

## セッション管理

| コマンド | 説明 |
|---------|------|
| `sessions` | アクティブセッション一覧 |
| `close` | ブラウザを閉じてデーモン停止 |
| `close --all` | 全セッションを閉じる |

## 要素特定の流れ

1. `state` で番号付き要素一覧を取得
2. 操作対象の番号（index）を確認
3. `click <index>` / `input <index> "text"` で操作

> **注意**: Playwright CLI の `ref` とは異なり、`state` で表示される数値インデックスを使用する
