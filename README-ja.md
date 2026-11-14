# server-backup-v2

[English README](README.md)

Linux サーバのバックアップを定期的に行うためのツールです。[book000/server-backup](https://github.com/book000/server-backup) を Python 3 で書き直し、他でも流用しやすくしたものです。

英語版の [README.md](README.md) が正本で、このファイルはその日本語訳です。

## Features

- `DBBackup`: MySQL / MariaDB のテーブル単位のダンプ (`mysqldump` を `gzip` に渡す)
- `FullBackup`: SSH と rsync を用いた、リモートサーバの逆差分フルバックアップ
- Discord Bot による、成功・失敗の通知

## Requirements

- Discord Bot のトークンと、Bot が書き込み可能なチャンネル
- Python 3.9+ と [requirements.txt](requirements.txt) のパッケージ (`PyMySQL`, `requests`, `setuptools`)
- ツールを実行するマシンに `mysqldump`, `gzip`, `tar`, `du`, `rsync`, `ssh`, `expect`。ベースイメージに含まれないものは [Dockerfile](Dockerfile) でインストールしています。

## Installation

1. リポジトリをクローンする: `git clone https://github.com/book000/server-backup-v2.git`
2. 依存パッケージをインストールする: `pip install -U -r requirements.txt`

## Configuration

設定ファイルは JSON で、デフォルトは `config.json` です (機密情報を含むため git の管理対象外です)。以下でデフォルト値の記載がないキーは必須で、未設定の場合はエラーで終了します。特に記載がない値は文字列です。

- `name`: このバックアップセットの名前。空白と `/` は使えません。下記のデフォルトのディレクトリ名に使われます。
- `discord`: Discord 通知設定
  - `token`: Bot トークン
  - `channel`: 通知先チャンネルの ID
  - `footer`: 通知のフッター文字列。キー自体が必須です (デフォルトなし)。JSON の `null` も拒否されます。
- `dir`: データ保存ディレクトリ (存在しなければ作成。相対パスは実行時のカレントディレクトリ基準)
  - `backup`: バックアップ保存先 (デフォルト: `/data/backups/<name>/`)
  - `logs`: ログ保存先 (デフォルト: `/data/logs/<name>/`)
- `db`: データベースバックアップ設定。`enable` 以外のキーは `enable` が true のときだけ読み込まれます。
  - `enable`: データベースバックアップを有効にするか (boolean、デフォルト: `false`)
  - `keep_days`: バックアップを保持する日数 (整数、デフォルト: `30`)。これより古い日付ディレクトリのダンプは、各テーブルの最新ダンプを除き、バックアップ実行のたびに削除されます ([Output layout](#output-layout) を参照)。
  - `hostname`: DB のホスト名
  - `port`: DB のポート番号 (整数)
  - `username`: DB のユーザー名
  - `password`: DB のパスワード
  - `ignores`: 除外設定
    - `db`: 除外するデータベースのリスト (list、デフォルト: `[]`)。部分一致で判定され、データベース名がいずれかの要素に含まれていればスキップされます (例: 要素 `mysql` は `mysql` と `sql` をスキップ)。
    - `table`: 除外するテーブルのリスト (list、デフォルト: `[]`)。判定は `db` と同じです。
- `full`: フルバックアップ設定。`enable` 以外のキーは `enable` が true のときだけ読み込まれます。
  - `enable`: フルバックアップを有効にするか (boolean、デフォルト: `false`)
  - `keep_days`: バックアップを保持する日数 (整数、デフォルト: `30`)。現状は削除処理が `.tar.gz` を削除しないため、自分で削除してください ([Known limitations](#known-limitations) を参照)。
  - `hostname`: バックアップ対象サーバのホスト名
  - `port`: SSH のポート番号 (整数)
  - `username`: SSH のユーザー名
  - `identity`: SSH 秘密鍵のパス。必須で、実行のたびに `chmod 600` が適用されます。
  - `passphrase`: 秘密鍵のパスフレーズ。必須です。
  - `from`: リモートサーバ上のバックアップ対象ディレクトリ (デフォルト: `/`)
  - `ignores`: 除外パターン。`rsync --exclude-from` に渡されます (list、デフォルト: `[]`)

### Server Settings

#### DB Backup

バックアップ用ユーザーには、以下の権限をグローバルで付与してください。

- SELECT
- FILE
- SHOW VIEW
- SUPER
- PROCESS
- LOCK TABLES

#### Full Backup

全ファイルを読み取るため、リモートサーバ上で `sudo` 経由の `rsync` を実行します。そのため SSH ユーザーは、TTY なしかつパスワードなしで `sudo rsync` を実行できる必要があります。

リモートサーバの `sudoers` ファイルに、`visudo` で以下を追記してください。

```
Defaults!/usr/bin/rsync !requiretty
USERNAME ALL=(ALL) NOPASSWD: /usr/bin/rsync
```

`USERNAME` にはリモートサーバへのログインに使うユーザー名を指定します。このアカウントで SSH ログインできる人は、root が読み取れるすべてのファイルを取得できるようになります。セキュリティ上の懸念がある場合は、この機能を使わないでください。

ホストキーは検証されません (`src/rsync.sh` の `StrictHostKeyChecking=no`)。

## Usage

```bash
# 両方のバックアップを実行する (DB バックアップ、フルバックアップの順)
python -m src -f config.json

# どちらか一方だけ実行する
python -m src -f config.json -m db
python -m src -f config.json -m full
```

設定で無効にしているバックアップはスキップされます。失敗した場合は Discord に通知し、終了コード 1 で終了します。

### Output layout

```
<dir.backup>/
├── DB/<YYYY-MM-DD>/<database>/<table>.sql.gz
└── FULL/
    ├── latest/              # リモートの `from` ディレクトリのミラー
    └── <YYYY-MM-DD>.tar.gz  # その日の実行で変更・削除されたファイル
<dir.logs>/
├── DB/<YYYY-MM-DD>.log
└── FULL/<YYYY-MM-DD>.log
```

DB バックアップは、ダンプが直近の過去のバックアップと同一のテーブル (`Dump completed` の行は無視) を保持しません。そのため、日付ディレクトリにテーブルが存在しないことがあります。その場合は、そのテーブルを持つ最も新しい過去の日付ディレクトリを探してください。保持期間の削除処理は、日付ディレクトリが `db.keep_days` より古くても、各テーブルの最新ダンプを残します。

### Docker

イメージは `$CONFIG_LOCATION` (デフォルト: `/data/config.json`) の設定ファイルで、DB バックアップ、フルバックアップの順に実行します。[docker-compose.yml](docker-compose.yml) はイメージをビルドし、次のホストパスをマウントします。

| ホスト | コンテナ |
|---|---|
| `./configs/config.json` | `/data/config.json` |
| `./configs/keys/id_rsa` | `/data/keys/identity-file` (`full.identity` にこのパスを指定) |
| `./backups/` | `/data/backups/` |
| `./logs/` | `/data/logs/` |

```bash
docker compose up
```

### systemd

`SystemdFiles/install-systemd.sh` は `server-backup-v2.service` の作業ディレクトリを書き換え、service と timer を `/etc/systemd/system/` にコピーして、timer を有効化・開始します。timer は毎日 08:00 に実行されます。

service は root で動作し、作業ディレクトリで `git pull` を実行したあと `venv/bin/python -m src` を実行します。事前にリポジトリ内に `venv` という名前の仮想環境を作成し、依存パッケージをインストールしておいてください。

```bash
./SystemdFiles/install-systemd.sh
systemctl status server-backup-v2.timer
```

## Known limitations

- フルバックアップの期限切れ削除処理は `<YYYY-MM-DD>.tar.gz` をスキップするため、古いアーカイブは自動では削除されません。
- `<YYYY-MM-DD>.tar.gz` は圧縮されていない tar アーカイブです。

## License

[MIT License](LICENSE)
