# AGENTS.md

Guidance for AI coding agents and contributors. `CLAUDE.md` imports this file, and `.github/copilot-instructions.md` adds the review checklist.

## Language

- All deliverables are written in **English**: commit messages, PR/Issue titles and bodies, review comments, code comments and docstrings, and documentation (`README.md`, `AGENTS.md`, etc.).
- `README-ja.md` is intentionally kept as a Japanese translation of `README.md`. Update it whenever `README.md` changes.
- Exceptions (keep as is): quotations, technical identifiers, generated files, and external source text.
- Runtime messages (logs, errors, Discord notifications) are English.
- Do not rewrite Git history to change the language of past commits.

## Overview

A Python tool that backs up Linux servers on a regular basis.

- `DBBackup`: dumps every MySQL/MariaDB table to `<backup>/DB/<YYYY-MM-DD>/<database>/<table>.sql.gz`.
- `FullBackup`: reverse differential backup over SSH and rsync into `<backup>/FULL/latest`, with each day's changes archived as `<YYYY-MM-DD>.tar.gz`.
- Both report success or failure to a Discord channel and have a cleanup step that deletes backups older than `keep_days`; the full backup cleanup currently skips `<YYYY-MM-DD>.tar.gz` (see `Known limitations` in `README.md`), so do not assume old full-backup archives are removed.

## Commands

```bash
pip install -U -r requirements.txt        # install dependencies
python -m py_compile src/*.py             # syntax check (there is no test, lint or format tool)
python -m src -f config.json              # run both backups; add -m db or -m full to run one
docker compose up                         # run in Docker (needs ./configs/config.json and ./configs/keys/id_rsa)
./SystemdFiles/install-systemd.sh         # install and start the systemd timer (daily 08:00)
```

CI only builds the Docker image (`.github/workflows/docker.yml`, reusable workflow from `book000/templates`) and lints the Dockerfile with hadolint (`hadolint-ci.yml`). There are no automated tests.

## Structure

- `src/__main__.py`: CLI entry point (`-f` config path, `-m db|full`), `BaseBackup`, `DBBackup`, `FullBackup`.
- `src/__init__.py`: helpers `get_connection`, `byte_format`, `log`, `get_directory_size`, `send_discord_message`, `notify`.
- `src/config.py`: `Config` loads the JSON config into upper-case attributes. `getValue(key, default)` exits when a key without a default is missing, so a new required key needs no extra check. Keys under `db` and `full` are read only when the matching `enable` is true; otherwise the attributes are `None`.
- `src/rsync.sh`: wraps `rsync` over SSH with `expect` to answer the key passphrase prompt. `FullBackup` runs it with `src/` as the working directory.
- `SystemdFiles/`: `server-backup-v2.service` (runs as root, `git pull` then `venv/bin/python -m src`), the daily timer and the installer.
- `Dockerfile`, `entrypoint.sh`: the container runs the `db` backup and then the `full` backup with `$CONFIG_LOCATION` (default `/data/config.json`).
- `README.md` / `README-ja.md`: documents the config keys, so update them when you add or change one.

## Conventions

- Python 3.9+, 4-space indent, PEP 8 naming (PascalCase classes, snake_case functions and variables, UPPER_SNAKE_CASE constants). A line length of 79 is a guideline; existing code exceeds it.
- Write a docstring for every function and class, and keep `Args` and `Returns` in sync with the code.
- Log through `log(LOG_FILE, "[INFO] ...")` (not `print`). On failure, `log`, then `notify(config, ":x: Backup failed.", 0xFF0000, "<reason>")`, then `exit(1)`. Success uses `":o: Backup complete!"` and `0x008000`.
- Commands are run with `subprocess.run(..., shell=True)` and values from the config are interpolated into the command strings, so quote and validate them carefully.
- Commits follow [Conventional Commits](https://www.conventionalcommits.org/); branches follow [Conventional Branch](https://conventional-branch.github.io) short form (`feat/...`, `fix/...`).
- Do not commit to Renovate PRs.

## Safety

- Never run a backup against a real server or database to test a change. Use a scratch directory and a config that points to disposable targets.
- `config.json` and `configs/` hold the Discord token, DB password and SSH key details and are git-ignored. Never commit them, and never log or notify secret values.
- `backups/` and `logs/` are git-ignored.
