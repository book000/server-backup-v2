# GEMINI.md

## 目的
- Gemini CLI 向けのコンテキストと作業方針を定義する。

## 出力スタイル
- 言語: 日本語
- トーン: 簡潔で事実ベース
- 形式: Markdown

## 共通ルール
- 会話は日本語で行う。
- PR とコミットは Conventional Commits に従う。
- PR タイトルとコミット本文の言語: PR タイトルは Conventional Commits 形式（英語推奨）。PR 本文は日本語。コミットは Conventional Commits 形式（description は日本語）。
- 日本語と英数字の間には半角スペースを入れる。

## プロジェクト概要
Linux サーバーの定期バックアップツール。MySQL/MariaDB のデータベースバックアップと SSH/rsync を使用したフルバックアップを実行します。

### 技術スタック
- **言語**: Python 3.9+
- **フレームワーク**: None (CLI tool)
- **パッケージマネージャー**: pip
- **主要な依存関係**:
  - PyMySQL 1.1.2
  - requests 2.32.5
  - setuptools 80.10.1

## コーディング規約
- フォーマット: 既存設定（ESLint / Prettier / formatter）に従う。
- 命名規則: 既存のコード規約に従う。
- コメント言語: 日本語
- エラーメッセージ: 英語

### 開発コマンド
```bash
# install
pip install -U -r requirements.txt

```

## 注意事項
- 認証情報やトークンはコミットしない。
- ログに機密情報を出力しない。
- 既存のプロジェクトルールがある場合はそれを優先する。

## リポジトリ固有
- Discord 通知機能
- MySQL データベースバックアップ
- SSH キーベース認証
- systemd サービス統合
- Docker コンテナ対応