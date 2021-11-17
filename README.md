# server-backup-v2

[日本語の README はこちらから](README-ja.md)

A tool for backup Linux servers on a regular basis. This is a rewrite of [book000/server-backup](https://github.com/book000/server-backup) in Python3 to make it easier to divert to others.

## Features

- `DBBackup`: Database backup for MySQL and MariaDB
- `FullBackup`: Reverse differential full backup using SSH and rsync

## Requirements

- Vaild Discord Bot token and Writeable message channel
- Python 3.9+
- [requirements.txt](requirements.txt): `PyMySQL`

## Installation

1. Clone from GitHub repository: `git clone https://github.com/book000/server-backup-v2.git`
2. Install the dependency package from `requirements.txt`: `pip install -U -r requirements.txt`

## Configuration

### Local Settings

The default config file is `config.json`. If not specified, string type and required.

- `discord`: Discord notification settings
  - `token`: Bot token
  - `channel`: Channel ID for notification
- `dir`: Data storage directory setting
  - `backup`: Backup destination directory (Default: `backup/`)
  - `logs`: Logs destination directory (Default: `logs/`)
- `db`: Database backup settings
  - `enable`: If enable database backup (boolean、Default: false)
  - `keep_days`: Number of days to keep the backup (int、Default: 30)
  - `hostname`: DB Hostname
  - `port`: DB Port number
  - `username`: DB Username
  - `password`: DB Password
- `full`: Full backup settings
  - `enable`: If enable full backup (boolean、Default: false)
  - `keep_days`: Number of days to keep the backup (int、Default: 30)
  - `hostname`: Hostname
  - `port`: Port
  - `username`: Username
  - `password`: Password
  - `identity`: Public key path
  - `passphrase`: Passphrase of the public key
  - `from`: Directory to back up (Default: `/`)
  - `ignores`: Directory files to exclude (list、Default: `[]`)

### Server Settings

#### DB Backup

The following permissions need to be set globally for the backup user account.

- SELECT
- FILE
- SHOW VIEW
- SUPER
- PROCESS
- LOCK TABLES

#### Full Backup

Backups are done with `rsync` and `sudo` is used to back up all files.  
For this reason, you need to be able to use `sudo rsync` with no-tty and no-password.

Add the following to the `sudoers` file on the remote server with `visudo`.

```
Defaults!/usr/bin/rsync !requiretty
USERNAME ALL=(ALL) NOPASSWD: /usr/bin/rsync
```

`USERNAME` must be the username to log in to the remote server.  
This setting will allow you to retrieve all files that can be viewed as root (sudo) in the event of a successful SSH login with this account. If you are concerned about security issues, we recommend that you do not use this feature.

## License

The license for this project is [MIT License](LICENSE).
