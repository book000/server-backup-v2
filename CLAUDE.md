# Claude Code 作業方針

## 目的

このドキュメントは、Claude Code が server-backup-v2 プロジェクトで作業する際の方針とプロジェクト固有のルールを定義します。

## 判断記録のルール

判断は必ずレビュー可能な形で記録すること：

1. **判断内容の要約**: 何を決定したかを明確に記載
2. **検討した代替案**: 他にどのような選択肢があったかを列挙
3. **採用しなかった案とその理由**: なぜその案を選ばなかったかを説明
4. **前提条件・仮定・不確実性**: 判断の前提となる条件や不確実な要素を明示
5. **他エージェントによるレビュー可否**: 判断が妥当かどうか他のエージェントに確認できるか示す

**重要**: 前提・仮定・不確実性を明示すること。仮定を事実のように扱ってはならない。

## プロジェクト概要

- **プロジェクト名**: server-backup-v2
- **目的**: Linux サーバのバックアップを定期的に自動実行するツール
- **主な機能**:
  - DBBackup: MySQL/MariaDB データベースの差分バックアップ
  - FullBackup: SSH と rsync による逆差分フルバックアップ
  - Discord Bot 経由での成功・失敗通知
  - バックアップ保持期間に基づく古いバックアップの自動削除
- **ライセンス**: MIT License (Copyright 2021 Tomachi)
- **リポジトリ**: https://github.com/book000/server-backup-v2

## 重要ルール

- **会話言語**: 日本語
- **コード内コメント**: 日本語で記載する。
- **エラーメッセージ**: 原則英語で記載する。
- **日本語と英数字の間**: 半角スペースを挿入しなければならない。
- **コミットメッセージ**: [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/) に従う。`<description>` は日本語で記載。
  - 例: `feat: データベースバックアップの圧縮機能を追加`
  - 例: `fix: ログファイルのパス生成エラーを修正`

## 環境のルール

- **ブランチ命名**: [Conventional Branch](https://conventional-branch.github.io) に従う。`<type>` は短縮形（feat, fix）で記載。
  - 例: `feat/add-compression`, `fix/log-path-error`
- **GitHub リポジトリ調査**: テンポラリディレクトリに git clone して、そこでコード検索する。
- **実行環境**: Windows 環境だが、Git Bash で動作している。bash コマンドを使用する。PowerShell コマンドを使用する場合は、明示的に `powershell -Command ...` か `pwsh -Command ...` を使用する。
- **Renovate PR**: Renovate が作成した既存のプルリクエストに対して、追加コミットや更新を行ってはならない。

## Git Worktree について

このプロジェクトでは Git Worktree を採用していません。通常の Git ブランチ管理を使用します。

## コード改修時のルール

- **日本語と英数字の間隔**: 日本語と英数字の間には、半角スペースを挿入しなければならない。
- **エラーメッセージの絵文字**: 既存のエラーメッセージに絵文字がある場合は、統一して設定する。絵文字はエラーメッセージに即した一文字の絵文字である必要がある。
- **TypeScript プロジェクト**: このプロジェクトは Python なので該当しないが、TypeScript プロジェクトにおいて `skipLibCheck` を有効にして回避することは絶対にしてはならない。
- **docstring**: 関数やクラスには、docstring を記載・更新する。日本語で記載する必要がある。

## 相談ルール

Codex CLI や Gemini CLI の他エージェントに相談することができる。以下の観点で使い分ける：

### Codex CLI (ask-codex)

- 実装コードに対するソースコードレビュー
- 関数設計、モジュール内部の実装方針などの局所的な技術判断
- アーキテクチャ、モジュール間契約、パフォーマンス／セキュリティといった全体影響の判断
- 実装の正当性確認、機械的ミスの検出、既存コードとの整合性確認

### Gemini CLI (ask-gemini)

- SaaS 仕様、言語・ランタイムのバージョン差、料金・制限・クォータといった、最新の適切な情報が必要な外部依存の判断
- 外部一次情報の確認、最新仕様の調査、外部前提条件の検証

### 指摘への対応ルール

他エージェントが指摘・異議を提示した場合、Claude Code は必ず以下のいずれかを行う。黙殺・無言での不採用は禁止する。

- 指摘を受け入れ、判断を修正する
- 指摘を退け、その理由を明示する

以下は必ず実施する：

- 他エージェントの提案を鵜呑みにせず、その根拠や理由を理解する
- 自身の分析結果と他エージェントの意見が異なる場合は、双方の視点を比較検討する
- 最終的な判断は、両者の意見を総合的に評価した上で、自身で下す

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

## アーキテクチャと主要ファイル

### ディレクトリ構造

```
server-backup-v2/
├── src/                          # メインの Python ソースコード
│   ├── __init__.py              # ユーティリティ関数
│   ├── __main__.py              # メインバックアップロジック
│   ├── config.py                # 設定パーサー
│   └── rsync.sh                 # SSH/rsync ラッパースクリプト
├── SystemdFiles/                # systemd サービス設定
│   ├── server-backup-v2.service # systemd サービスファイル
│   ├── server-backup-v2.timer   # systemd タイマー（毎日 08:00）
│   └── install-systemd.sh       # インストールスクリプト
├── .github/workflows/           # GitHub Actions ワークフロー
│   ├── docker.yml               # Docker ビルドとパブリッシュ
│   ├── hadolint-ci.yml          # Dockerfile リンティング
│   └── add-reviewer.yml         # 自動レビュアー追加
├── Dockerfile                   # コンテナイメージ定義
├── docker-compose.yml           # Docker Compose 設定
├── entrypoint.sh                # コンテナエントリーポイント
├── requirements.txt             # Python 依存関係
├── renovate.json                # Renovate Bot 設定
├── README.md                    # 英語ドキュメント
└── README-ja.md                 # 日本語ドキュメント
```

### 主要クラスとモジュール

- **BaseBackup**: バックアップ処理のベースクラス
- **DBBackup**: データベースバックアップを担当するクラス
- **FullBackup**: フルバックアップを担当するクラス
- **Config**: 設定ファイル（config.json）のパーサー
- **ユーティリティ関数**:
  - `get_connection()`: MySQL/MariaDB 接続の取得
  - `notify()`: Discord への通知送信
  - `log()`: ログファイルへの出力
  - `byte_format()`: バイト数のフォーマット
  - `get_directory_size()`: ディレクトリサイズの取得

## 実装パターン

### 推奨パターン

- **ログ出力**: `log(LOG_FILE, "[INFO] メッセージ")` を使用
- **Discord 通知**: `notify("タイトル", "色", "メッセージ")` を使用
- **データベース接続**: `get_connection(hostname, port, username, password)` でコネクションプールを取得
- **ディレクトリ作成**: `os.makedirs(path)` で必要に応じてディレクトリを作成
- **バックアップファイル命名**: `YYYY-MM-DD` 形式の日付を使用

### 非推奨パターン

- ハードコーディングされたパス（設定ファイルから読み込む）
- 直接の print 文（log 関数を使用）
- 例外の無視（適切にログ出力と Discord 通知を行う）

## テスト

### テスト方針

- 現在、専用のテストフレームワークは使用していない。
- CI/CD では以下を実施：
  - GitHub Actions で Docker ビルドを検証
  - Hadolint による Dockerfile の静的解析
- 変更後は実際の設定ファイルでバックアップ処理を実行して動作確認を行う。

### 追加テスト条件

新しい機能を追加する場合：

1. 設定ファイルのサンプルを用意
2. 実際のバックアップ処理を実行して動作確認
3. ログファイルの内容を確認
4. Discord 通知が正しく送信されることを確認

## ドキュメント更新ルール

### 更新対象

- `README.md`: 英語版ドキュメント
- `README-ja.md`: 日本語版ドキュメント（主要ドキュメント）
- `config.json` サンプル（リポジトリには含まれないが、ドキュメントで説明）

### 更新タイミング

- 新しい設定項目を追加した場合
- 機能を追加・変更した場合
- 依存関係を変更した場合
- インストール・実行手順を変更した場合

## 作業チェックリスト

### 新規改修時

1. プロジェクトについて詳細に探索し理解すること
2. 作業を行うブランチが適切であること。すでに PR を提出しクローズされたブランチでないこと
3. 最新のリモートブランチに基づいた新規ブランチであること
4. PR がクローズされ、不要となったブランチは削除されていること
5. プロジェクトで指定されたパッケージマネージャ（pip）により、依存パッケージをインストールしたこと

### コミット・プッシュする前

1. コミットメッセージが [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/) に従っていること。`<description>` は日本語で記載。
2. コミット内容にセンシティブな情報が含まれていないこと
3. Python コードの構文エラーがないこと（`python -m py_compile src/*.py` で確認）
4. 動作確認を行い、期待通り動作すること

### プルリクエストを作成する前

1. プルリクエストの作成をユーザーから依頼されていること
2. コミット内容にセンシティブな情報が含まれていないこと
3. コンフリクトする恐れが無いこと

### プルリクエストを作成したあと

1. コンフリクトが発生していないこと
2. PR 本文の内容は、ブランチの現在の状態を、今までのこの PR での更新履歴を含むことなく、最新の状態のみ、漏れなく日本語で記載されていること。この PR を見たユーザーが、最終的にどのような変更を含む PR なのかをわかりやすく、細かく記載されていること
3. `gh pr checks <PR ID> --watch` で GitHub Actions CI を待ち、その結果がエラーとなっていないこと。成功している場合でも、ログを確認し、誤って成功扱いになっていないこと。もし GitHub Actions が動作しない場合は、ローカルで CI と同等のテストを行い、CI が成功することを保証しなければならない
4. `request-review-copilot` コマンドが存在する場合、`request-review-copilot https://github.com/$OWNER/$REPO/pull/$PR_NUMBER` で GitHub Copilot へレビューを依頼すること。レビュー依頼は自動で行われる場合もあるし、制約により `request-review-copilot` を実行しても GitHub Copilot がレビューしないケースがある
5. 10 分以内に投稿される GitHub Copilot レビューへの対応を行うこと。対応したら、レビューコメントそれぞれに対して返信を行うこと。レビュアーに GitHub Copilot がアサインされていない場合はスキップして構わない
6. `/code-review:code-review` によるコードレビューを実施したこと。コードレビュー内容に対しては、**スコアが 50 以上の指摘事項** に対して対応すること

## リポジトリ固有

- このプロジェクトは Python 3.9+ で動作し、Docker コンテナとしても利用可能。
- バックアップは systemd タイマーで定期実行される（デフォルト: 毎日 08:00）。
- データベースバックアップには mysqldump と gzip を使用。
- フルバックアップは rsync の逆差分バックアップ戦略を採用（最新版と backup-dir を保持）。
- Renovate による依存関係の自動更新が有効。既存の Renovate PR には追加コミットや更新を行わない。
- バックアップ対象サーバには以下の権限設定が必要：
  - **DB バックアップ**: SELECT, FILE, SHOW VIEW, SUPER, PROCESS, LOCK TABLES 権限
  - **フルバックアップ**: パスワードなし sudo rsync の設定（`sudoers` に特別なエントリが必要）
- 設定ファイル `config.json` には Discord Bot トークン、データベースパスワード、SSH 認証情報が含まれるため、Git にコミットしない（`.gitignore` で除外済み）。
- ログファイルとバックアップファイルは `.gitignore` で除外されている。
