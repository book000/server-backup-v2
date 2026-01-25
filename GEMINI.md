# Gemini CLI 作業方針

## 目的

このドキュメントは、Gemini CLI が server-backup-v2 プロジェクトで作業する際のコンテキストと作業方針を定義します。

## 出力スタイル

- **言語**: 日本語で応答する
- **トーン**: 簡潔かつ技術的に正確な情報を提供
- **形式**: 必要に応じてコードブロック、リスト、表を使用して見やすく整理

## 共通ルール

- **会話言語**: 日本語
- **コミットメッセージ**: [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/) に従う
  - `<type>(<scope>): <description>` 形式
  - `<description>` は日本語で記載
  - 例: `feat: データベースバックアップの圧縮機能を追加`
- **ブランチ命名**: [Conventional Branch](https://conventional-branch.github.io) に従う
  - `<type>/<description>` 形式
  - `<type>` は短縮形（feat, fix）を使用
- **日本語と英数字の間**: 半角スペースを挿入する

## プロジェクト概要

- **プロジェクト名**: server-backup-v2
- **目的**: Linux サーバのバックアップを定期的に自動実行するツール
- **主な機能**:
  - DBBackup: MySQL/MariaDB データベースの差分バックアップ
  - FullBackup: SSH と rsync による逆差分フルバックアップ
  - Discord Webhook 経由での成功・失敗通知
  - バックアップ保持期間に基づく古いバックアップの自動削除
- **技術スタック**:
  - 言語: Python 3.9+
  - パッケージマネージャー: pip
  - 主な依存関係: PyMySQL 1.1.2, requests 2.32.5, setuptools 80.10.1
  - ランタイムツール: MySQL クライアント, rsync, SSH, expect, tar, gzip
  - コンテナ化: Docker（slim Python 3 ベースイメージ）
  - CI/CD: GitHub Actions
  - 自動化: systemd サービスとタイマー（毎日 08:00 実行）
- **ライセンス**: MIT License (Copyright 2021 Tomachi)
- **リポジトリ**: https://github.com/book000/server-backup-v2

## コーディング規約

- **コード内コメント**: 日本語で記載
- **エラーメッセージ**: 英語で記載
- **docstring**: 日本語で記載
- **フォーマット**: PEP 8 に従う
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

# データベースバックアップのみ実行
python -m src -f config.json -m db

# フルバックアップのみ実行
python -m src -f config.json -m full

# Python 構文チェック
python -m py_compile src/*.py

# Docker Compose で実行
docker-compose up

# systemd サービスのインストール
./SystemdFiles/install-systemd.sh

# systemd タイマーの有効化と開始
systemctl enable server-backup-v2.timer
systemctl start server-backup-v2.timer

# systemd タイマーの状態確認
systemctl status server-backup-v2.timer
```

## アーキテクチャ概要

### ディレクトリ構造

```
server-backup-v2/
├── src/                          # メインの Python ソースコード
│   ├── __init__.py              # ユーティリティ関数
│   ├── __main__.py              # メインバックアップロジック
│   ├── config.py                # 設定パーサー
│   └── rsync.sh                 # SSH/rsync ラッパースクリプト
├── SystemdFiles/                # systemd サービス設定
├── .github/workflows/           # GitHub Actions ワークフロー
├── Dockerfile                   # コンテナイメージ定義
├── requirements.txt             # Python 依存関係
└── README-ja.md                 # 日本語ドキュメント
```

### 主要クラス

- **BaseBackup**: バックアップ処理のベースクラス
- **DBBackup**: データベースバックアップを担当するクラス
- **FullBackup**: フルバックアップを担当するクラス
- **Config**: 設定ファイル（config.json）のパーサー

### ユーティリティ関数

- `get_connection()`: MySQL/MariaDB 接続の取得
- `notify()`: Discord への通知送信
- `log()`: ログファイルへの出力
- `byte_format()`: バイト数のフォーマット
- `get_directory_size()`: ディレクトリサイズの取得

## 注意事項

### セキュリティ / 機密情報

- `config.json` に Discord Bot トークン、データベースパスワード、SSH 認証情報が含まれるため、Git にコミットしない（`.gitignore` で除外済み）。
- ログに認証情報や機密情報を出力しない。
- Discord 通知には機密情報を含めない。
- SSH 秘密鍵とパスフレーズは安全に管理する。

### 既存ルールの優先

- 既存のコーディングスタイルとパターンを尊重する
- PEP 8 に準拠したコードを書く
- 日本語でコメントと docstring を記載
- エラーメッセージは英語で記載

### 既知の制約

- テストフレームワークは現在未使用（CI で Docker ビルドと Hadolint linting のみ）
- 動作確認は実際の設定ファイルでバックアップ処理を実行して行う
- Renovate による依存関係の自動更新が有効（既存の Renovate PR には追加コミットや更新を行わない）

## リポジトリ固有

- このプロジェクトは Python 3.9+ で動作し、Docker コンテナとしても利用可能。
- バックアップは systemd タイマーで定期実行される（デフォルト: 毎日 08:00）。
- データベースバックアップには mysqldump と gzip を使用。
- フルバックアップは rsync の逆差分バックアップ戦略を採用（最新版と backup-dir を保持）。
- Renovate による依存関係の自動更新が有効。
- バックアップ対象サーバには以下の権限設定が必要：
  - **DB バックアップ**: SELECT, FILE, SHOW VIEW, SUPER, PROCESS, LOCK TABLES 権限
  - **フルバックアップ**: パスワードなし sudo rsync の設定（`sudoers` に特別なエントリが必要）
- 設定ファイル `config.json` には認証情報が含まれるため、Git にコミットしない。
- ログファイルとバックアップファイルは `.gitignore` で除外されている。
- CI/CD では GitHub Actions で Docker イメージをビルドし、Docker Hub（book000/server-backup-v2）にパブリッシュする。
