import os
import shutil
import subprocess
from argparse import ArgumentParser
from datetime import datetime, timedelta

from pymysql import MySQLError
from pymysql.cursors import DictCursor

from src import byte_format, get_connection, get_directory_size, log, notify
from src.config import Config


class BaseBackup:
    """
    バックアップのベースクラス
    """

    def process(self,
                config: Config):
        """
        バックアップ処理
        """
        raise NotImplementedError


class DBBackup(BaseBackup):
    """
    データベースバックアップ
    """

    def process(self,
                config: Config):
        """
        データベースバックアップ処理
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

        command = "ls -l | awk '{ print $9 }' | tail -n 1"
        result = subprocess.run(command, cwd=BACKUP_DIR, shell=True)
        prev_date = None if result.returncode == 0 else result.stdout.decode("utf-8").strip()  # 前回バックアップした日付 (なければNone)
        log(LOG_FILE, "[INFO] PrevDate: {}".format(prev_date))

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
            if connection is not None:
                connection.close()
            log(LOG_FILE, "Error: Database operation failed. (MySQLError)")
            log(LOG_FILE, e.args.__str__())
            notify(config, ":x: Backup failed.", 0xFF0000, "Database operation failed.")
            exit(1)

        log(LOG_FILE, "[INFO] Creating conf file.")
        with open(os.path.join(BACKUP_DIR, "conf"), "w") as f:
            f.write("[mysqldump]\n")
            f.write("host=\"{0}\"\n".format(config.DB_HOSTNAME))
            f.write("port={0}\n".format(config.DB_PORT))
            f.write("user=\"{0}\"\n".format(config.DB_USERNAME))
            f.write("password=\"{0}\"".format(config.DB_PASSWORD))
        os.chmod(os.path.join(BACKUP_DIR, "conf"), 0o644)
        log(LOG_FILE, "[INFO] Created.")

        log(LOG_FILE, "[INFO] Starting backup")
        all_size = 0
        count = 0
        error = False
        for database in databases:
            log(LOG_FILE, "[INFO] Database: %s" % database)

            if next(filter(lambda x: database in x, config.DB_IGNORES), None) is not None:
                log(LOG_FILE, "[INFO] Ignored: %s" % next(filter(lambda x: database in x, config.DB_IGNORES), None))
                continue

            for table in databases[database]:
                log(LOG_FILE, "[INFO] Table: %s" % table)

                if next(filter(lambda x: table in x, config.DB_TABLE_IGNORES), None) is not None:
                    log(LOG_FILE,
                        "[INFO] Ignored: %s" % next(filter(lambda x: table in x, config.DB_TABLE_IGNORES), None))
                    continue

                backup_path = os.path.join(BACKUP_DIR, database + "-" + table + ".sql.gz")
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

                if prev_date is not None:
                    diff_result = subprocess.run("zdiff -q --ignore-matching-lines=\"Dump completed\" {0} {1}".format(
                        os.path.join(BACKUP_DIR, prev_date),
                        backup_path
                    ))
                    if diff_result.returncode == 0:
                        log(LOG_FILE, "[Info] Backup skipped. (No difference)")
                        os.remove(backup_path)
                        continue

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
            if not file.endswith(".sql.gz"):
                continue
            file_path = os.path.join(config.BACKUP_DIR, "DB", file)
            if not os.path.isdir(file_path):
                continue
            file_date = datetime.strptime(file, "%Y-%m-%d")
            if file_date >= datetime.now() - timedelta(days=config.DB_KEEP_DAYS):
                continue
            log(LOG_FILE, "[INFO] Deleting %s" % file)
            shutil.rmtree(file_path)

        log(LOG_FILE, "[INFO] Deleted expired files")


class FullBackup(BaseBackup):
    """
    全体ディレクトリ/ファイル逆差分バックアップ
    """

    def process(self,
                config: Config):
        """
        データベースバックアップ処理
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
        command = f"./rsync.sh -h '{config.FULL_HOSTNAME}' -r '{config.FULL_PORT}' -u '{config.FULL_USERNAME}' -i '{config.FULL_IDENTITY}' -p '{config.FULL_PASSPHRASE}' -f '{config.FULL_FROM}' -o '{BACKUP_DIR}' 2>&1 | tee -a {LOG_FILE}"
        print(command)
        result = subprocess.run(command, shell=True, cwd=os.path.dirname(__file__))
        if result.returncode != 0:
            log(LOG_FILE, "[Error] Backup failed.")
            notify(config, ":x: Backup failed.", 0xFF0000, "rsync command failed.")
            exit(1)

        os.unlink(os.path.join(BACKUP_DIR, "ignores"))

        command = "tar --remove-file cvf {0} {1}".format(
            os.path.join(BACKUP_DIR, TODAY + ".tar.gz"),
            os.path.join(BACKUP_DIR, TODAY + "/")
        )
        result = subprocess.run(command, shell=True, cwd=os.path.dirname(__file__))
        if result.returncode != 0:
            log(LOG_FILE, "[Error] Backup failed.")
            notify(config, ":x: Backup failed.", 0xFF0000, "tar command failed.")
            exit(1)

        log(LOG_FILE, "[INFO] Backup finished.")
        latest_size = get_directory_size(os.path.join(BACKUP_DIR, "latest"))
        today_size = get_directory_size(os.path.join(BACKUP_DIR, TODAY))

        notify(config, ":o: Backup complete!", 0x008000, "Today size: {0}\nLatest size: {1}".format(
            byte_format(today_size, 2),
            byte_format(latest_size, 2)
        ))

        # Delete expired files
        log(LOG_FILE, "[INFO] Deleting expired files")
        for file in os.listdir(BACKUP_DIR):
            if len(file) != 10:
                continue
            file_path = os.path.join(BACKUP_DIR, file)
            if not os.path.isdir(file_path):
                continue
            file_date = datetime.strptime(file, "%Y-%m-%d")
            if file_date >= datetime.now() - timedelta(days=config.FULL_KEEP_DAYS):
                continue
            log(LOG_FILE, "[INFO] Deleting %s" % file)
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
