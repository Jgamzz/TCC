import gzip
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.backup_mysql import backup_database


class BackupTests(unittest.TestCase):
    def test_creates_compressed_dump_and_removes_expired_backups(self):
        with tempfile.TemporaryDirectory() as directory:
            old_backup = Path(directory) / "sgpv-old.sql.gz"
            old_backup.touch()
            old_time = 1
            os.utime(old_backup, (old_time, old_time))

            def mock_dump(*args, stdout, **kwargs):
                stdout.write(b"sql dump")
                return type("Result", (), {"returncode": 0, "stderr": b""})()

            with (
                patch.dict(os.environ, {"DB_BACKUP_DIR": directory}),
                patch("scripts.backup_mysql.subprocess.run", side_effect=mock_dump),
            ):
                created = backup_database()

            self.assertTrue(created.exists())
            with gzip.open(created, "rb") as backup_file:
                self.assertEqual(backup_file.read(), b"sql dump")
            self.assertFalse(old_backup.exists())


if __name__ == "__main__":
    unittest.main()
