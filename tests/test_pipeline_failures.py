import os
import stat
import subprocess
import tempfile
import unittest
from datetime import datetime
from unittest import mock

from src import run_pipeline
from src import __main__ as backup

TODAY = datetime.now().strftime("%Y-%m-%d")
EXPIRED = "2000-01-01"


class PipelineFailureTest(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = tmp.name
        self.bin_dir = os.path.join(self.root, "bin")
        os.makedirs(self.bin_dir)

        path = mock.patch.dict(os.environ, {"PATH": self.bin_dir + os.pathsep + os.environ["PATH"]})
        path.start()
        self.addCleanup(path.stop)

        notify = mock.patch.object(backup, "notify")
        self.notify = notify.start()
        self.addCleanup(notify.stop)

        self.config = mock.Mock(
            BACKUP_DIR=os.path.join(self.root, "backup"),
            LOG_DIR=os.path.join(self.root, "logs"),
            DB_ENABLE=True, DB_HOSTNAME="localhost", DB_PORT=3306, DB_USERNAME="user", DB_PASSWORD="pass",
            DB_IGNORES=[], DB_TABLE_IGNORES=[], DB_KEEP_DAYS=7,
            FULL_ENABLE=True, FULL_IGNORES=[], FULL_KEEP_DAYS=7, FULL_IDENTITY=None, FULL_HOSTNAME="host",
            FULL_PORT=22, FULL_USERNAME="user", FULL_HOST_KEY_CHECKING="yes", FULL_FROM="/", FULL_PASSPHRASE="",
        )

    def fake_executable(self, name, body):
        path = os.path.join(self.bin_dir, name)
        with open(path, "w") as f:
            f.write("#!/bin/sh\n" + body + "\n")
        os.chmod(path, os.stat(path).st_mode | stat.S_IXUSR)

    def touch(self, *parts):
        path = os.path.join(self.config.BACKUP_DIR, *parts)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "wb") as f:
            f.write(b"old")
        return path

    def titles(self):
        return [call.args[1] for call in self.notify.call_args_list]

    def test_mysqldump_failure_is_reported_and_keeps_old_dump(self):
        self.fake_executable("mysqldump", "exit 1")
        old_dump = self.touch("DB", EXPIRED, "db", "table.sql.gz")
        connection = mock.MagicMock(open=True)
        connection.cursor.return_value.__enter__.return_value.fetchall.return_value = [
            {"TABLE_SCHEMA": "db", "TABLE_NAME": "table"}
        ]

        with mock.patch.object(backup, "get_connection", return_value=connection):
            with self.assertRaises(SystemExit) as cm:
                backup.DBBackup().process(self.config)

        self.assertEqual(cm.exception.code, 1)
        self.notify.assert_called_once_with(
            self.config, ":x: Backup failed.", 0xFF0000, "mysqldump command failed. (db-table)")
        self.assertNotIn(":o: Backup complete!", self.titles())
        self.assertFalse(os.path.exists(os.path.join(self.config.BACKUP_DIR, "DB", TODAY, "db", "table.sql.gz")))
        self.assertTrue(os.path.exists(old_dump))

    def test_tar_failure_is_reported_and_keeps_old_archive(self):
        self.fake_executable("tar", 'echo "tar: boom" >&2\nexit 2')
        old_archive = self.touch("FULL", EXPIRED + ".tar.gz")
        real_run_pipeline = run_pipeline

        def fake_rsync(command, **kwargs):
            if "./rsync.sh" in command:
                return subprocess.CompletedProcess(command, 0)
            return real_run_pipeline(command, **kwargs)

        with mock.patch.object(backup, "run_pipeline", side_effect=fake_rsync):
            with self.assertRaises(SystemExit) as cm:
                backup.FullBackup().process(self.config)

        self.assertEqual(cm.exception.code, 1)
        self.notify.assert_called_once_with(self.config, ":x: Backup failed.", 0xFF0000, "tar command failed.")
        self.assertNotIn(":o: Backup complete!", self.titles())
        self.assertTrue(os.path.exists(old_archive))

    def test_run_pipeline_reports_a_failing_first_stage(self):
        self.assertNotEqual(run_pipeline("false | cat").returncode, 0)
        self.assertEqual(run_pipeline("true | cat").returncode, 0)


if __name__ == "__main__":
    unittest.main()
