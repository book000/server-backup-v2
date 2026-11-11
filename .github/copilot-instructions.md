# Copilot code review instructions

Read `AGENTS.md` at the repository root first; it is the source of truth for structure, commands and conventions.

## Language

Write review comments, and expect all deliverables (code comments, docstrings, docs, commit messages, PR text), in English.
Runtime log, error and notification messages are English too. `README-ja.md` is an intentional Japanese translation of `README.md`.

## Review checklist

- Shell injection: config values (host names, paths, credentials) are interpolated into `subprocess.run(..., shell=True)` command strings in `src/__main__.py` (`mysqldump`, `tar`, `rsync.sh`) and `src/__init__.py` (`du`). Flag unquoted or unvalidated new interpolation.
- Every `subprocess.run` result is checked through `returncode`; failures follow the existing pattern: `log()`, `notify()` to Discord, then `exit(1)`.
- DB connections are closed in `finally`; files are opened with `with`.
- Exceptions are not swallowed silently.
- Retention deletion (`shutil.rmtree` / `os.remove`) must match the real directory and file names and must not delete valid backups.
- Secrets (`config.json`, the temporary `conf` file with the DB password, SSH key details) are never committed, logged or sent to Discord, and the `conf` file is removed after use.
- New config keys are documented in `README.md` and `README-ja.md`.
- Commit and PR titles follow Conventional Commits.

## Do not flag

- `shell=True` as such, when there is no concrete injection concern.
- The absence of automated tests (CI only builds the Docker image and runs hadolint).
- Minor overruns of the 79-character line length.
