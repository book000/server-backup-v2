import os
import re
import shutil
import subprocess
from argparse import ArgumentParser
from datetime import datetime, timedelta
from typing import List, Optional

from pymysql import MySQLError
from pymysql.cursors import DictCursor

from src import byte_format, get_connection, get_directory_size, log, notify
from src.config import Config


def list_date_dirs(db_root: str) -> List[str]:
    """
    List the ``YYYY-MM-DD`` directories of the DB backup.

    Args:
        db_root (str): ``<backup>/DB`` directory holding the date directories

    Returns:
        List[str]: Directory names, oldest first. Entries that are not
        zero-padded date directories and symlinks are ignored.
    """
    dirs = []
    for name in sorted(os.listdir(db_root)):
        path = os.path.join(db_root, name)
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}", name) and os.path.isdir(path) and not os.path.islink(path):
            dirs.append(name)
    return dirs


def find_previous_backup(db_root: str,
                         today: str,
                         database: str,
                         table: str) -> Optional[str]:
    """
    Find the newest dump of a table taken before ``today``.

    The search is per table because a dump identical to its predecessor is
    deleted, so the previous date directory may not contain the table.

    Args:
        db_root (str): ``<backup>/DB`` directory holding the date directories
        today (str): Current run date as ``YYYY-MM-DD``; this and later dates are ignored
        database (str): Database name
        table (str): Table name

    Returns:
        Optional[str]: Path of ``<table>.sql.gz`` in the newest earlier date directory
        that has it, or ``None`` when there is none.
    """
    for date in reversed(list_date_dirs(db_root)):
        if date >= today:
            continue
        path = os.path.join(db_root, date, database, table + ".sql.gz")
        if os.path.exists(path):
            return path
    return None


def prune_expired_date_dir(db_root: str, date: str) -> int:
    """
    Delete the files of an expired date directory, except the newest dump of each table.

    A table that did not change is not saved again, so its newest dump may
    only exist in an old date directory and must outlive ``keep_days``.

    Args:
        db_root (str): ``<backup>/DB`` directory holding the date directories
        date (str): Expired date directory name (``YYYY-MM-DD``)

    Returns:
        int: Number of dumps kept because no later date directory has the same table.
    """
    date_dir = os.path.join(db_root, date)
    later_dirs = [name for name in list_date_dirs(db_root) if name > date]
    kept = 0
    for dirpath, _, filenames in os.walk(date_dir, topdown=False):
        for name in filenames:
            path = os.path.join(dirpath, name)
            relative = os.path.relpath(path, date_dir)
            has_newer = any(os.path.exists(os.path.join(db_root, later, relative)) for later in later_dirs)
            if name.endswith(".sql.gz") and not has_newer:
                kept += 1
            else:
                os.remove(path)
        if not os.listdir(dirpath):
            os.rmdir(dirpath)
    return kept


class BaseBackup:
    """
    Base class of backup jobs.
    """

    def process(self,
                config: Config):
        """
        Run the backup.

        Args:
            config (Config): Loaded configuration
        """
        raise NotImplementedError


class DBBackup(BaseBackup):
    """
    Per-table MySQL/MariaDB dump: ``<backup>/DB/<YYYY-MM-DD>/<database>/<table>.sql.gz``.

    A dump identical to the newest earlier dump of the same table is deleted, so a
    table can be missing from a date directory.
    """

    def process(self,
                config: Config):
        """
        Dump every table with ``mysqldump``, then run the expired-backup cleanup.

        The cleanup deletes dumps in date directories older than ``db.keep_days``,
        except the newest dump of every table. It runs only after all dumps succeeded.

        Does nothing when ``db.enable`` is false. Exits with status 1 after
        notifying Discord on failure.

        Args:
            config (Config): Loaded configuration
        """
        TODAY = datetime.now().strftime('%Y-%m-%d')
        BACKUP_DIR = os.path.join(config.BACKUP_DIR, "DB", TODAY)
        if not os.path.exists(BACKUP_DIR):
            os.makedirs(BACKUP_DIR)
        LOG_FILE = os.path.join(config.LOG_DIR, "DB", TODAY + ".log")
        if not os.path.exists(os.path.dirname(LOG_FILE)):
            os.makedirs(os.path.dirname(LOG_FILE))

        log(LOG_FILE, "[INFO] DBBackup")

        if not config.DB_ENABLE:
            log(LOG_FILE, "[INFO] DBBackup is disabled")
            return

        log(LOG_FILE, "[INFO] Fetch databases & tables")
        databases = {}
        connection = None
        try:
            connection = get_connection(
                config.DB_HOSTNAME,
                config.DB_PORT,
                config.DB_USERNAME,
                config.DB_PASSWORD
            )
            with connection.cursor(cursor=DictCursor) as cursor:
                if not connection.open:
                    log(LOG_FILE, "[Error] Failed to connect to the database.")
                    notify(config, ":x: Backup failed.", 0xFF0000, "Failed to connect to the database.")
                    exit(1)

                cursor.execute("SELECT * FROM INFORMATION_SCHEMA.TABLES")
                results = cursor.fetchall()

                for result in results:
                    if result["TABLE_SCHEMA"] not in databases:
                        databases[result["TABLE_SCHEMA"]] = []
                    databases[result["TABLE_SCHEMA"]].append(result["TABLE_NAME"])
        except MySQLError as e:
            log(LOG_FILE, "Error: Database operation failed. (MySQLError)")
            log(LOG_FILE, e.args.__str__())
            notify(config, ":x: Backup failed.", 0xFF0000, "Database operation failed.")
            exit(1)
        finally:
            if connection is not None:
                connection.close()

        log(LOG_FILE, "[INFO] Creating conf file.")
        with open(os.path.join(BACKUP_DIR, "conf"), "w") as f:
            f.write("[mysqldump]\n")
            f.write("host=\"{0}\"\n".format(config.DB_HOSTNAME))
            f.write("port={0}\n".format(config.DB_PORT))
            f.write("user=\"{0}\"\n".format(config.DB_USERNAME))
            f.write("password=\"{0}\"".format(config.DB_PASSWORD))
        os.chmod(os.path.join(BACKUP_DIR, "conf"), 0o600)
        log(LOG_FILE, "[INFO] Created.")

        log(LOG_FILE, "[INFO] Starting backup")
        all_size = 0
        count = 0
        error = False
        for database in databases:
            log(LOG_FILE, "[INFO] Database: %s" % database)

            if next(filter(lambda x: x in database, config.DB_IGNORES), None) is not None:
                log(LOG_FILE, "[INFO] Ignored: %s" % next(filter(lambda x: x in database, config.DB_IGNORES), None))
                continue

            for table in databases[database]:
                log(LOG_FILE, "[INFO] Table: %s" % table)

                if next(filter(lambda x: x in table, config.DB_TABLE_IGNORES), None) is not None:
                    log(LOG_FILE,
                        "[INFO] Ignored: %s" % next(filter(lambda x: x in table, config.DB_TABLE_IGNORES), None))
                    continue

                backup_path = os.path.join(BACKUP_DIR, database, table + ".sql.gz")
                if not os.path.exists(os.path.dirname(backup_path)):
                    os.makedirs(os.path.dirname(backup_path))
                command = "mysqldump --defaults-file={0} --single-transaction {1} {2} | gzip > {3}".format(
                    os.path.join(BACKUP_DIR, "conf"),
                    database,
                    table,
                    backup_path
                )
                result = subprocess.run(command, shell=True)
                if result.returncode != 0:
                    log(LOG_FILE, "[Error] Backup failed.")
                    notify(config, ":x: Backup failed.", 0xFF0000, "mysqldump command failed. ({0})".format(
                        database + "-" + table
                    ))
                    error = True
                    continue

                prev_path = find_previous_backup(os.path.join(config.BACKUP_DIR, "DB"), TODAY, database, table)
                if prev_path is not None:
                    try:
                        diff_result = subprocess.run(
                            ["zdiff", "-q", "--ignore-matching-lines=^-- Dump completed", prev_path, backup_path]
                        )
                        diff_code = diff_result.returncode
                        diff_error = "exit code {0}".format(diff_code)
                    except OSError as e:
                        diff_code = None
                        diff_error = str(e)
                    if diff_code == 0:
                        log(LOG_FILE, "[Info] Backup skipped. (No difference)")
                        os.remove(backup_path)
                        continue
                    if diff_code != 1:
                        log(LOG_FILE, "[Error] Comparison failed ({0}); keeping the dump: {1}".format(
                            diff_error,
                            backup_path
                        ))

                filesize = os.path.getsize(backup_path) if os.path.exists(backup_path) else 0
                filesize_formatted = byte_format(filesize, 2)

                log(LOG_FILE, "[INFO] %s-%s.sql.gz -> %s" % (database, table, filesize_formatted))

                count += 1
                all_size += filesize

        os.unlink(os.path.join(BACKUP_DIR, "conf"))

        if error:
            log(LOG_FILE, "[INFO] One of the backups failed.")
            exit(1)

        log(LOG_FILE, "[INFO] Backup finished.")

        notify(config, ":o: Backup complete!", 0x008000, "Table count: {0}\nSize: {1}".format(
            count,
            byte_format(all_size, 2)
        ))

        # Delete expired files
        log(LOG_FILE, "[INFO] Deleting expired files")
        for file in os.listdir(os.path.join(config.BACKUP_DIR, "DB")):
            file_path = os.path.join(config.BACKUP_DIR, "DB", file)
            if not os.path.isdir(file_path) or os.path.islink(file_path):
                continue
            try:
                file_date = datetime.strptime(file, "%Y-%m-%d")
            except ValueError:
                log(LOG_FILE, "[INFO] Skipping non-date directory %s" % file)
                continue
            if file_date >= datetime.now() - timedelta(days=config.DB_KEEP_DAYS):
                continue
            kept = prune_expired_date_dir(os.path.join(config.BACKUP_DIR, "DB"), file)
            log(LOG_FILE, "[INFO] Pruned %s (kept %d newest dumps)" % (file, kept))

        log(LOG_FILE, "[INFO] Deleted expired files")


class FullBackup(BaseBackup):
    """
    Reverse-differential full backup over SSH and rsync.

    ``<backup>/FULL/latest`` mirrors the remote; files changed or deleted by a run are moved
    to ``<backup>/FULL/<YYYY-MM-DD>/`` and archived as ``<YYYY-MM-DD>.tar.gz``.
    """

    def process(self,
                config: Config):
        """
        Run ``rsync.sh``, archive the day's changes with ``tar``, then run the expired-backup cleanup.

        Does nothing when ``full.enable`` is false. Exits with status 1 after
        notifying Discord on failure.

        Args:
            config (Config): Loaded configuration
        """
        TODAY = datetime.now().strftime('%Y-%m-%d')
        BACKUP_DIR = os.path.join(config.BACKUP_DIR, "FULL")
        if not os.path.exists(BACKUP_DIR):
            os.makedirs(BACKUP_DIR)
        LOG_FILE = os.path.join(config.LOG_DIR, "FULL", TODAY + ".log")
        if not os.path.exists(os.path.dirname(LOG_FILE)):
            os.makedirs(os.path.dirname(LOG_FILE))

        log(LOG_FILE, "FullBackup")

        if not config.FULL_ENABLE:
            log(LOG_FILE, "[INFO] FullBackup is disabled")
            return

        log(LOG_FILE, "[INFO] Creating ignores file.")
        with open(os.path.join(BACKUP_DIR, "ignores"), "w") as f:
            f.write("\n".join(config.FULL_IGNORES))
        log(LOG_FILE, "[INFO] Created.")

        log(LOG_FILE, "[INFO] Starting backup")
        identity_arg = "" if config.FULL_IDENTITY is None else f"-i '{config.FULL_IDENTITY}'"
        command = f"set -o pipefail; ./rsync.sh -h '{config.FULL_HOSTNAME}' -r '{config.FULL_PORT}' -u '{config.FULL_USERNAME}' {identity_arg} -k '{config.FULL_HOST_KEY_CHECKING}' -f '{config.FULL_FROM}' -o '{BACKUP_DIR}' 2>&1 | tee -a {LOG_FILE} "
        print(command)
        result = subprocess.run(command, shell=True, executable="/bin/bash", cwd=os.path.dirname(__file__),
                                env={**os.environ, "SSH_PASSPHRASE": str(config.FULL_PASSPHRASE)})
        if result.returncode != 0:
            log(LOG_FILE, "[Error] Backup (rsync) failed.")
            notify(config, ":x: Backup failed.", 0xFF0000, "rsync command failed.")
            exit(1)

        os.unlink(os.path.join(BACKUP_DIR, "ignores"))

        today_size = get_directory_size(os.path.join(BACKUP_DIR, TODAY))

        command = "tar --remove-file -czvf {0} {1} 2>&1 | tee -a {2}".format(
            os.path.join(BACKUP_DIR, TODAY + ".tar.gz"),
            os.path.join(BACKUP_DIR, TODAY + "/"),
            LOG_FILE
        )
        result = subprocess.run(command, shell=True, cwd=os.path.dirname(__file__))
        if result.returncode != 0:
            log(LOG_FILE, "[Error] Backup (tar) failed.")
            notify(config, ":x: Backup failed.", 0xFF0000, "tar command failed.")
            exit(1)

        log(LOG_FILE, "[INFO] Backup finished.")
        latest_size = get_directory_size(os.path.join(BACKUP_DIR, "latest"))
        today_tar_size = os.path.getsize(os.path.join(BACKUP_DIR, TODAY + ".tar.gz"))

        notify(config, ":o: Backup complete!", 0x008000, "Today size: {0} (tar.gz: {1})\nLatest size: {2}".format(
            byte_format(today_size, 2),
            byte_format(today_tar_size, 2),
            byte_format(latest_size, 2)
        ))

        # Delete expired files
        log(LOG_FILE, "[INFO] Deleting expired files")
        for file in os.listdir(BACKUP_DIR):
            if len(file) not in (len("YYYY-MM-DD"), len("YYYY-MM-DD.tar.gz")):
                continue
            file_path = os.path.join(BACKUP_DIR, file)
            if os.path.isfile(file_path) and file.endswith(".tar.gz"):
                file_date = datetime.strptime(file, "%Y-%m-%d.tar.gz")
                if file_date >= datetime.now() - timedelta(days=config.FULL_KEEP_DAYS):
                    continue
                log(LOG_FILE, "[INFO] Deleting file %s" % file)
                os.remove(file_path)
            if not os.path.isdir(file_path):
                continue
            file_date = datetime.strptime(file, "%Y-%m-%d")
            if file_date >= datetime.now() - timedelta(days=config.FULL_KEEP_DAYS):
                continue
            log(LOG_FILE, "[INFO] Deleting dir %s" % file)
            shutil.rmtree(file_path)

        log(LOG_FILE, "[INFO] Deleted expired files")


parser = ArgumentParser(description="A tool for backup Linux servers on a regular basis.")

parser.add_argument("-f", "--config-file", help="Configuration file path", default="config.json")
parser.add_argument("-m", "--mode", help="Backup mode", choices=["db", "full"])

if __name__ == "__main__":
    args = parser.parse_args()
    conf = Config(args.config_file)

    if not args.mode or args.mode == "db":
        DBBackup().process(conf)
    if not args.mode or args.mode == "full":
        FullBackup().process(conf)
