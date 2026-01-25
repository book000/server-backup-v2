# GitHub Copilot Instructions

## プロジェクト概要

- 目的: Linux サーバのバックアップを定期的に行うためのツール
- 主な機能:
  - DBBackup: MySQL や MariaDB のデータベースバックアップ（差分バックアップ対応）
  - FullBackup: SSH と rsync を用いた逆差分フルバックアップ（圧縮対応）
  - Discord へのバックアップステータス通知
  - バックアップ保持ポリシー管理
- 対象ユーザー: Linux サーバ管理者、システム管理者

## 共通ルール

- 会話は日本語で行う。
- コミットメッセージは [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/) に従う。
  - `<type>(<scope>): <description>` 形式
  - `<description>` は日本語で記載
  - 例: `feat: ユーザー認証機能を追加`
- ブランチ命名は [Conventional Branch](https://conventional-branch.github.io) に従う。
  - `<type>/<description>` 形式
  - `<type>` は短縮形（feat, fix, docs など）を使用
  - 例: `feat/add-user-auth`
- 日本語と英数字の間には半角スペースを挿入する。

## 技術スタック

- 言語: Python 3.9+
- パッケージマネージャー: pip
- 主な依存関係:
  - PyMySQL 1.1.2: MySQL/MariaDB データベース接続
  - requests 2.32.5: Discord API 通知用の HTTP クライアント
  - setuptools 80.10.1: パッケージ管理
- ランタイムツール: MySQL クライアント, rsync, SSH, expect, tar, gzip
- コンテナ化: Docker（slim Python 3 ベースイメージ）
- CI/CD: GitHub Actions
- 自動化: systemd サービスとタイマー

## コーディング規約

- コード内コメント: 日本語で記載
- エラーメッセージ: 英語で記載
- docstring: 日本語で記載（既存のスタイルに従う）
- 命名規則: PEP 8 に従う
  - クラス名: PascalCase（例: `DBBackup`）
  - 関数名・変数名: snake_case（例: `get_connection`）
  - 定数: UPPER_SNAKE_CASE（例: `BACKUP_DIR`）
- インデント: スペース 4 つ
- 最大行長: 79 文字を推奨

## 開発コマンド

```bash
# 依存関係のインストール
pip install -U -r requirements.txt

# バックアップ実行（両方）
python -m src -f config.json

# データベースバックアップのみ
python -m src -f config.json -m db

# フルバックアップのみ
python -m src -f config.json -m full

# Docker Compose で実行
docker-compose up

# systemd サービスのインストール
./SystemdFiles/install-systemd.sh

# systemd タイマーの有効化
systemctl enable server-backup-v2.timer

# systemd タイマーの開始
systemctl start server-backup-v2.timer
```

## テスト方針

- テストフレームワーク: 現在未使用
- CI/CD:
  - GitHub Actions で Docker ビルドを実行
  - Hadolint による Dockerfile の静的解析
- 動作確認: 実際の設定ファイルでバックアップ処理を実行して確認

## セキュリティ / 機密情報

- `config.json` に Discord Bot トークン、データベースパスワード、SSH 認証情報が含まれるため、Git にコミットしない（`.gitignore` で除外済み）。
- ログに認証情報や機密情報を出力しない。
- Discord 通知には機密情報を含めない。
- SSH 秘密鍵とパスフレーズは安全に管理する。

## ドキュメント更新

コード変更時には以下のドキュメントを更新する：

- `README.md`: 英語版ドキュメント
- `README-ja.md`: 日本語版ドキュメント（主要ドキュメント）
- `config.json` の設定項目を変更した場合は、両 README の Configuration セクションを更新

## リポジトリ固有

- このプロジェクトは Python 3.9+ で動作し、Docker コンテナとしても利用可能です。
- バックアップは systemd タイマーで定期実行されます（デフォルト: 毎日 08:00）。
- データベースバックアップには mysqldump と gzip を使用します。
- フルバックアップは rsync の逆差分バックアップ戦略を採用しています（最新版と backup-dir を保持）。
- Renovate による依存関係の自動更新が有効です。既存の Renovate PR には追加コミットや更新を行わない。
- バックアップサーバには以下の権限設定が必要です：
  - DB バックアップ: SELECT, FILE, SHOW VIEW, SUPER, PROCESS, LOCK TABLES 権限
  - フルバックアップ: パスワードなし sudo rsync の設定（`sudoers` に特別なエントリが必要）
