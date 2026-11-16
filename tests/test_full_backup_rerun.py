import glob
import os
import shlex
import subprocess
import tarfile
import tempfile
import unittest
from types import SimpleNamespace
from unittest import mock

from src import run_pipeline
from src import __main__ as backup


class FullBackupRerunTest(unittest.TestCase):
    def test_empty_rerun_preserves_first_archive(self):
        with tempfile.TemporaryDirectory() as root:
            config = SimpleNamespace(
                BACKUP_DIR=root, LOG_DIR=root, FULL_ENABLE=True,
                FULL_IGNORES=[], FULL_IDENTITY=None, FULL_HOSTNAME="host",
                FULL_PORT=22, FULL_USERNAME="user", FULL_HOST_KEY_CHECKING="yes",
                FULL_FROM="/source", FULL_PASSPHRASE="", FULL_KEEP_DAYS=30,
            )
            runs = []

            def fake_rsync(command, **kwargs):
                if "./rsync.sh" not in command:
                    return run_pipeline(command, **kwargs)
                args = shlex.split(command)
                diff = os.path.join(root, "FULL", args[args.index("-n") + 1])
                os.makedirs(os.path.join(root, "FULL", "latest"), exist_ok=True)
                if not runs:
                    with open(os.path.join(diff, "old-version.txt"), "wb") as f:
                        f.write(b"old content")
                runs.append(diff)
                return subprocess.CompletedProcess(command, 0)

            with mock.patch.object(backup, "run_pipeline", side_effect=fake_rsync), \
                    mock.patch.object(backup, "notify"):
                backup.FullBackup().process(config)
                first = glob.glob(os.path.join(root, "FULL", "*.tar.gz"))[0]
                with open(first, "rb") as f:
                    original = f.read()
                backup.FullBackup().process(config)

            self.assertEqual(len(glob.glob(os.path.join(root, "FULL", "*.tar.gz"))), 2)
            with open(first, "rb") as f:
                self.assertEqual(f.read(), original)
            with tarfile.open(first) as archive:
                member = next(m for m in archive.getmembers() if m.name.endswith("/old-version.txt"))
                self.assertEqual(archive.extractfile(member).read(), b"old content")


if __name__ == "__main__":
    unittest.main()
