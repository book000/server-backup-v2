# server-backup-v2

[Click here for English README](README.md)

Linux サーバのバックアップを定期的に行うためのツールです。[book000/server-backup](https://github.com/book000/server-backup) を Python3 で書き直し他でも流用しやすくしたものです。

## Features

- `DBBackup`: MySQL や MariaDB のデータベースバックアップ
- `FullBackup`: SSH と rsync を用いた逆差分フルバックアップ

## Requirements

- 有効な Discord Botトークンと書き込み可能なメッセージチャネル
- Python 3.9+
- [requirements.txt](requirements.txt): `PyMySQL`

## Installation

1. GitHub リポジトリからクローンする: `git clone https://github.com/book000/server-backup-v2.git`
2. `requirements.txt` から依存関係パッケージをインストールする: `pip install -U -r requirements.txt`

## Configuration

### Local Settings

デフォルトの設定ファイルは `config.json` です。明記していない場合文字列型で必須

- `discord`: Discord 通知系設定
  - `token`: Bot トークン
  - `channel`: 通知先チャンネル
- `dir`: データ保存ディレクトリ設定
  - `backup`: バックアップ保存先ディレクトリ (デフォルト: `backup/`)
  - `logs`: ログファイル保存先ディレクトリ (デフォルト: `logs/`)
- `db`: データベースバックアップ設定
  - `enable`: データベースバックアップを有効にするか (boolean、デフォルト: false)
  - `keep_days`: バックアップを保持する期間日数 (int、デフォルト: 30)
  - `hostname`: ホスト名
  - `port`: ポート番号
  - `username`: ユーザー名
  - `password`: パスワード
- `full`: フルバックアップ設定
  - `enable`: フルバックアップを有効にするか (boolean、デフォルト: false)
  - `keep_days`: バックアップを保持する期間日数 (int、デフォルト: 30)
  - `hostname`: ホスト名
  - `port`: ポート番号
  - `username`: ユーザー名
  - `password`: パスワード
  - `identity`: 公開鍵パス
  - `passphrase`: 公開鍵のパスフレーズ
  - `from`: バックアップするディレクトリ (デフォルト: `/`)
  - `ignores`: 除外するディレクトリ・ファイル (list、デフォルト: `[]`)

### Server Settings

#### DB Backup

バックアップ用ユーザーアカウントには、以下の権限をグローバルで振る必要があります。

- データ: SELECT
- データ: FILE
- 構造: SHOW VIEW
- 管理: SUPER
- 管理: PROCESS
- 管理: LOCK TABLES

#### Full Backup

バックアップは `rsync` で行われ、また全ファイルをバックアップするために `sudo` を用いています。  
このため、tty なしでかつ `sudo rsync` をパスワード無しで利用できる必要があります。

以下の内容をリモートサーバの `sudoers` ファイルに `visudo` で追記してください。

```
Defaults!/usr/bin/rsync !requiretty
USERNAME ALL=(ALL) NOPASSWD: /usr/bin/rsync
```

`USERNAME` にはリモートサーバにログインするユーザ名を指定する必要があります。  
この設定を行うと、万が一このアカウントで SSH ログインが成功してしまった場合 root (sudo) で閲覧できるすべてのファイルを取得できるようになります。セキュリティの問題を懸念するのであれば、この機能を利用しないことをお勧めします。

## License

このプロジェクトのライセンスは [MIT License](LICENSE) です。
