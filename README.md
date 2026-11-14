# server-backup-v2

[日本語の README](README-ja.md)

A tool that backs up Linux servers on a regular basis. It is a Python 3 rewrite of [book000/server-backup](https://github.com/book000/server-backup), made easier to reuse elsewhere.

## Features

- `DBBackup`: per-table MySQL and MariaDB dumps (`mysqldump` piped to `gzip`)
- `FullBackup`: reverse differential full backup of a remote server using SSH and rsync
- Success and failure notifications to a Discord channel through a Bot

## Requirements

- A Discord Bot token and a channel the Bot can write to
- Python 3.9+ and the packages in [requirements.txt](requirements.txt) (`PyMySQL`, `requests`, `setuptools`)
- On the machine that runs the tool: `mysqldump`, `gzip`, `tar`, `du`, `rsync`, `ssh` and `expect`. The [Dockerfile](Dockerfile) installs the ones that are not part of the base image.

## Installation

1. Clone the repository: `git clone https://github.com/book000/server-backup-v2.git`
2. Install the dependencies: `pip install -U -r requirements.txt`

## Configuration

The config file is JSON and defaults to `config.json` (it contains secrets and is git-ignored). A key without a default below is required, and the tool exits with an error if it is missing. All values are strings unless noted otherwise.

- `name`: Name of this backup set. It must not contain a space or `/`. It is used in the default directories below.
- `discord`: Discord notification settings
  - `token`: Bot token
  - `channel`: ID of the channel to notify
  - `footer`: Footer text of notifications. The key must be present (no default). Passing JSON `null` is rejected as well.
- `dir`: Data directories (created if missing; relative paths are resolved against the working directory)
  - `backup`: Backup destination (default: `/data/backups/<name>/`)
  - `logs`: Log destination (default: `/data/logs/<name>/`)
- `db`: Database backup settings. The keys below `enable` are only read when `enable` is true.
  - `enable`: Enable the database backup (boolean, default: `false`)
  - `keep_days`: Days to keep backups (integer, default: `30`). Dumps in date directories older than this are deleted after each backup run, except the newest dump of each table (see [Output layout](#output-layout)).
  - `hostname`: DB host name
  - `port`: DB port number (integer)
  - `username`: DB user name
  - `password`: DB password
  - `ignores`: Exclusions
    - `db`: Database exclusion list (list, default: `[]`). Matching is by substring: a database is skipped when any entry is contained in its name (for example, the entry `mysql` skips `mysql` and `mysql_backup`, but not `sql`).
    - `table`: Table exclusion list (list, default: `[]`). Same matching rule as `db`.
- `full`: Full backup settings. The keys below `enable` are only read when `enable` is true.
  - `enable`: Enable the full backup (boolean, default: `false`)
  - `keep_days`: Days to keep backups (integer, default: `30`). Expired `<YYYY-MM-DD>.tar.gz` archives and date directories are deleted after each run.
  - `hostname`: Host name of the server to back up
  - `port`: SSH port number (integer)
  - `username`: SSH user name
  - `identity`: Path to the SSH private key. Required, and `chmod 600` is applied to it on every run.
  - `passphrase`: Passphrase of the private key. Required.
  - `from`: Directory on the remote server to back up (default: `/`)
  - `ignores`: Patterns to exclude, passed to `rsync --exclude-from` (list, default: `[]`)

### Server Settings

#### DB Backup

Grant the backup user the following privileges globally.

- SELECT
- FILE
- SHOW VIEW
- SUPER
- PROCESS
- LOCK TABLES

#### Full Backup

The backup runs `rsync` on the remote server through `sudo` so that it can read every file. The SSH user therefore needs to run `sudo rsync` without a TTY and without a password.

Add the following to the `sudoers` file on the remote server with `visudo`.

```
Defaults!/usr/bin/rsync !requiretty
USERNAME ALL=(ALL) NOPASSWD: /usr/bin/rsync
```

`USERNAME` must be the user name used to log in to the remote server. Anyone who logs in over SSH with this account can then read every file that root can read. If this is a security concern, do not use this feature.

Host keys are not verified (`StrictHostKeyChecking=no` in `src/rsync.sh`).

## Usage

```bash
# Run both backups (the DB backup first, then the full backup)
python -m src -f config.json

# Run only one of them
python -m src -f config.json -m db
python -m src -f config.json -m full
```

A backup that is disabled in the config is skipped. On a failure, the tool notifies Discord and exits with status 1.

### Output layout

```
<dir.backup>/
├── DB/<YYYY-MM-DD>/<database>/<table>.sql.gz
└── FULL/
    ├── latest/              # mirror of the remote `from` directory
    └── <YYYY-MM-DD>.tar.gz  # files changed or deleted by that day's run
<dir.logs>/
├── DB/<YYYY-MM-DD>.log
└── FULL/<YYYY-MM-DD>.log
```

The DB backup does not keep a table whose dump is identical to its most recent earlier backup (ignoring the `Dump completed` line), so a table can be missing from a date directory. Look for it in the newest earlier date directory that has it. The retention cleanup keeps the newest dump of every table even when its date directory is older than `db.keep_days`.

### Docker

The image runs the DB backup and then the full backup with the config file at `$CONFIG_LOCATION` (default: `/data/config.json`). [docker-compose.yml](docker-compose.yml) builds the image and mounts these host paths:

| Host | Container |
|---|---|
| `./configs/config.json` | `/data/config.json` |
| `./configs/keys/id_rsa` | `/data/keys/identity-file` (set `full.identity` to this path) |
| `./backups/` | `/data/backups/` |
| `./logs/` | `/data/logs/` |

```bash
docker compose up
```

### systemd

`SystemdFiles/install-systemd.sh` fills in the working directory of `server-backup-v2.service`, copies the service and timer to `/etc/systemd/system/`, then enables and starts the timer. The timer runs daily at 08:00.

The service runs as root. It first runs `git pull` in the working directory, then `venv/bin/python -m src`, so create a virtual environment named `venv` in the repository and install the dependencies into it first.

```bash
./SystemdFiles/install-systemd.sh
systemctl status server-backup-v2.timer
```

## Known limitations

- `<YYYY-MM-DD>.tar.gz` is an uncompressed tar archive.

## License

[MIT License](LICENSE)
