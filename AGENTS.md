# AI エージェント作業方針

## 目的

このドキュメントは、AI エージェント（Claude Code 以外の汎用エージェント）が server-backup-v2 プロジェクトで作業する際の基本方針を定義します。

## 基本方針

- **会話言語**: 日本語
- **コード内コメント**: 日本語
- **エラーメッセージ**: 英語
- **日本語と英数字の間**: 半角スペースを挿入する
- **コミットメッセージ**: [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/) に従う
  - `<type>(<scope>): <description>` 形式
  - `<description>` は日本語で記載
  - 例: `feat: データベースバックアップの圧縮機能を追加`
  - 例: `fix: ログファイルのパス生成エラーを修正`
- **ブランチ命名**: [Conventional Branch](https://conventional-branch.github.io) に従う
  - `<type>/<description>` 形式
  - `<type>` は短縮形（feat, fix, docs など）を使用
  - 例: `feat/add-compression`, `fix/log-path-error`

## 判断記録のルール

判断プロセスは以下の形式で記録する：

1. **判断内容の要約**: 何を決定したかを明確に記載
2. **検討した代替案**: 他にどのような選択肢があったかを列挙
3. **採用した案とその理由**: なぜその案を選んだかを説明
4. **前提条件・仮定・不確実性**: 判断の前提となる条件や不確実な要素を明示

**重要**: 前提・仮定・不確実性を明示すること。仮定を事実のように扱ってはならない。

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
  - 主な依存関係: PyMySQL, requests, setuptools
  - コンテナ化: Docker
  - CI/CD: GitHub Actions
  - 自動化: systemd サービスとタイマー
- **ライセンス**: MIT License
- **リポジトリ**: https://github.com/book000/server-backup-v2

## 開発手順（概要）

1. **プロジェクト理解**:
   - `README-ja.md` を読んでプロジェクトの目的と機能を理解
   - `src/` ディレクトリ内のコードを確認して実装パターンを把握

2. **依存関係インストール**:
   ```bash
   pip install -U -r requirements.txt
   ```

3. **変更実装**:
   - 既存のコーディングスタイルに従う
   - PEP 8 に準拠したコードを書く
   - 日本語でコメントと docstring を記載
   - エラーメッセージは英語で記載

4. **動作確認**:
   - Python 構文チェック: `python -m py_compile src/*.py`
   - 実際の設定ファイルでバックアップ処理を実行して確認

5. **コミット**:
   - Conventional Commits に従ったメッセージを作成
   - センシティブな情報が含まれていないことを確認

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
```

## セキュリティ / 機密情報

- `config.json` に Discord Bot トークン、データベースパスワード、SSH 認証情報が含まれるため、Git にコミットしない（`.gitignore` で除外済み）。
- ログに認証情報や機密情報を出力しない。
- Discord 通知には機密情報を含めない。
- SSH 秘密鍵とパスフレーズは安全に管理する。

## ドキュメント更新

コード変更時には以下のドキュメントを適宜更新する：

- `README.md`: 英語版ドキュメント
- `README-ja.md`: 日本語版ドキュメント（主要ドキュメント）
- 設定項目を変更した場合は、両 README の Configuration セクションを更新

## リポジトリ固有

- このプロジェクトは Python 3.9+ で動作し、Docker コンテナとしても利用可能。
- バックアップは systemd タイマーで定期実行される（デフォルト: 毎日 08:00）。
- データベースバックアップには mysqldump と gzip を使用。
- フルバックアップは rsync の逆差分バックアップ戦略を採用（最新版と backup-dir を保持）。
- Renovate による依存関係の自動更新が有効。既存の Renovate PR には追加コミットや更新を行わない。
- バックアップ対象サーバには以下の権限設定が必要：
  - **DB バックアップ**: SELECT, FILE, SHOW VIEW, SUPER, PROCESS, LOCK TABLES 権限
  - **フルバックアップ**: パスワードなし sudo rsync の設定（`sudoers` に特別なエントリが必要）
- 設定ファイル `config.json` には認証情報が含まれるため、Git にコミットしない。
- ログファイルとバックアップファイルは `.gitignore` で除外されている。
