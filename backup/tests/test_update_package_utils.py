#!/usr/bin/env python3
"""Unit tests for HTTP release update helper utilities."""

import tarfile
import tempfile
import unittest
from pathlib import Path

from utils.update_package import ReleasePackageManager


class ReleasePackageManagerTests(unittest.TestCase):
    """Tests covering core utility behaviours used during HTTP updates."""

    def setUp(self):
        self.workspace = tempfile.TemporaryDirectory()
        root = Path(self.workspace.name)
        self.project_root = root / "project"
        self.project_root.mkdir()
        self.download_root = root / "downloads"
        self.manager = ReleasePackageManager(
            repo="demo/repo",
            token=None,
            project_root=self.project_root,
            download_root=self.download_root,
            preserve_paths=(".env", "uploads"),
        )

    def tearDown(self):
        self.workspace.cleanup()

    def test_sync_to_project_preserves_configured_paths(self):
        """Ensure sync avoids overwriting preserved files and folders."""
        original_env = self.project_root / ".env"
        original_env.write_text("keep this value", encoding="utf-8")

        uploads_dir = self.project_root / "uploads"
        uploads_dir.mkdir()
        (uploads_dir / "existing.txt").write_text("existing upload", encoding="utf-8")

        source_root = Path(self.workspace.name) / "extracted" / "package"
        (source_root / "static").mkdir(parents=True)
        (source_root / "static" / "app.js").write_text("console.log('new');", encoding="utf-8")
        (source_root / "app.py").write_text("# new app content", encoding="utf-8")
        (source_root / ".env").write_text("new value", encoding="utf-8")
        (source_root / "uploads").mkdir()
        (source_root / "uploads" / "new.txt").write_text("should not copy", encoding="utf-8")

        self.manager.sync_to_project(source_root)

        self.assertTrue((self.project_root / "static" / "app.js").exists())
        self.assertEqual(
            (self.project_root / "app.py").read_text(encoding="utf-8"),
            "# new app content",
        )
        self.assertEqual(original_env.read_text(encoding="utf-8"), "keep this value")
        self.assertFalse((self.project_root / "uploads" / "new.txt").exists())

    def test_backup_database_creates_copy_when_file_exists(self):
        """Verify database backups are placed in the expected directory."""
        db_dir = self.project_root / "db"
        db_dir.mkdir()
        db_file = db_dir / "otrs_data.db"
        db_file.write_text("sample data", encoding="utf-8")

        backup_dir = self.project_root / "database_backups"
        backup_path = self.manager.backup_database([db_file], backup_dir)

        self.assertIsNotNone(backup_path)
        self.assertTrue(backup_path.exists())
        self.assertEqual(backup_path.read_text(encoding="utf-8"), "sample data")

    def test_extract_archive_returns_root_directory(self):
        """Extraction should yield the root folder inside the archive."""
        archive_root = Path(self.workspace.name) / "archives"
        archive_root.mkdir()
        archive_path = archive_root / "release.tar.gz"

        payload_dir = Path(self.workspace.name) / "payload_root"
        payload_dir.mkdir()
        (payload_dir / "module.py").write_text("print('hello')", encoding="utf-8")

        with tarfile.open(archive_path, "w:gz") as tar:
            tar.add(payload_dir, arcname="package-123")

        extracted_root = self.manager.extract_archive(archive_path)

        self.assertTrue(extracted_root.is_dir())
        self.assertEqual(
            (extracted_root / "module.py").read_text(encoding="utf-8"),
            "print('hello')",
        )


if __name__ == "__main__":
    unittest.main()
