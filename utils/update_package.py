"""
Utilities for downloading, extracting and applying application update packages.

This module centralises the HTTP based update workflow so it can be reused by
both the background update service and the standalone ``scripts/update_app.py``.
"""

from __future__ import annotations

import json
import os
import shutil
import sys
import tarfile
import tempfile
import traceback
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional, Sequence

import requests


class ReleaseDownloadError(RuntimeError):
    """Raised when release metadata or package download fails."""


class PackageExtractionError(RuntimeError):
    """Raised when a release archive cannot be safely extracted."""


@dataclass
class ReleaseMetadata:
    """Simple container for release metadata used during updates."""

    tag_name: str
    name: Optional[str]
    body: Optional[str]
    html_url: Optional[str]
    published_at: Optional[str]
    tarball_url: Optional[str]
    zipball_url: Optional[str]

    @classmethod
    def from_payload(cls, payload: dict) -> "ReleaseMetadata":
        """Build metadata object from GitHub API payload."""
        return cls(
            tag_name=payload.get("tag_name") or payload.get("name") or "",
            name=payload.get("name"),
            body=payload.get("body"),
            html_url=payload.get("html_url"),
            published_at=payload.get("published_at"),
            tarball_url=payload.get("tarball_url"),
            zipball_url=payload.get("zipball_url"),
        )

    def to_json(self) -> str:
        """Return JSON string for logging or persistence."""
        return json.dumps(
            {
                "tag_name": self.tag_name,
                "name": self.name,
                "html_url": self.html_url,
                "published_at": self.published_at,
                "tarball_url": self.tarball_url,
                "zipball_url": self.zipball_url,
            },
            ensure_ascii=False,
        )


class ReleasePackageManager:
    """Handle HTTP based release lookups and filesystem synchronisation."""

    USER_AGENT = "otrs-web-update-agent"

    def __init__(
        self,
        repo: str,
        token: Optional[str],
        project_root: Path,
        download_root: Path,
        preserve_paths: Optional[Sequence[str]] = None,
        session: Optional[requests.Session] = None,
        timeout: int = 30,
    ) -> None:
        self.repo = repo
        self.token = token
        self.project_root = project_root
        self.download_root = download_root
        self.download_root.mkdir(parents=True, exist_ok=True)
        self.preserve_paths = tuple(preserve_paths or ())
        self._session = session or requests.Session()
        self._timeout = timeout

    # ------------------------------------------------------------------
    # Release metadata & download
    # ------------------------------------------------------------------
    def fetch_release_metadata(self, target_version: Optional[str]) -> ReleaseMetadata:
        """Retrieve release metadata from GitHub for the target version."""
        headers = {
            "Accept": "application/vnd.github+json",
            "User-Agent": self.USER_AGENT,
        }
        
        # 只有在token有效时才添加到请求头
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"

        if target_version:
            url = f"https://api.github.com/repos/{self.repo}/releases/tags/{target_version}"
        else:
            url = f"https://api.github.com/repos/{self.repo}/releases/latest"

        print(f"🔍 Fetching release metadata from: {url}")
        response = self._session.get(url, headers=headers, timeout=self._timeout)
        
        # 处理API速率限制
        if response.status_code == 403:
            # 检查是否是速率限制问题
            if response.headers.get('X-RateLimit-Remaining') == '0':
                reset_time = response.headers.get('X-RateLimit-Reset')
                error_msg = f"GitHub API rate limit exceeded. Rate limit will reset at {reset_time}."
                if not self.token:
                    error_msg += " 请设置GITHUB_TOKEN环境变量以提高速率限制。"
                raise ReleaseDownloadError(error_msg)
        
        if response.status_code != 200:
            raise ReleaseDownloadError(
                f"GitHub release lookup failed ({response.status_code}): {response.text[:200]}"
            )

        try:
            payload = response.json()
        except json.JSONDecodeError as exc:  # pragma: no cover
            raise ReleaseDownloadError(f"GitHub response decoding failed: {exc}") from exc

        metadata = ReleaseMetadata.from_payload(payload)
        if not metadata.tag_name:
            raise ReleaseDownloadError("GitHub release payload missing tag name")
        if not metadata.tarball_url and not metadata.zipball_url:
            raise ReleaseDownloadError("GitHub release payload missing tarball/zipball URLs")
        
        print(f"✅ Successfully fetched release metadata for: {metadata.tag_name}")
        return metadata

    def download_release_archive(self, metadata: ReleaseMetadata, target_version: str) -> Path:
        """Download tarball/zipball for the release and return archive path."""
        headers = {"User-Agent": self.USER_AGENT}
        # 只有在token有效时才添加到请求头
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"

        download_url = metadata.tarball_url or metadata.zipball_url
        if not download_url:
            raise ReleaseDownloadError("Release metadata does not contain a download URL")

        archive_ext = ".tar.gz" if metadata.tarball_url else ".zip"
        archive_dir = self.download_root / target_version
        archive_dir.mkdir(parents=True, exist_ok=True)
        archive_path = archive_dir / f"{target_version}{archive_ext}"

        print(f"⬇️  Downloading release archive from: {download_url}")
        print(f"📂 Saving to: {archive_path}")

        with self._session.get(download_url, headers=headers, timeout=self._timeout, stream=True) as response:
            # 处理API速率限制
            if response.status_code == 403:
                # 检查是否是速率限制问题
                if response.headers.get('X-RateLimit-Remaining') == '0':
                    reset_time = response.headers.get('X-RateLimit-Reset')
                    error_msg = f"GitHub API rate limit exceeded. Rate limit will reset at {reset_time}."
                    if not self.token:
                        error_msg += " 请设置GITHUB_TOKEN环境变量以提高速率限制。"
                    raise ReleaseDownloadError(error_msg)
            
            if response.status_code != 200:
                raise ReleaseDownloadError(
                    f"Failed to download release archive ({response.status_code}): {response.text[:200]}"
                )
            with archive_path.open("wb") as handle:
                total_size = int(response.headers.get('content-length', 0))
                downloaded = 0
                for chunk in response.iter_content(chunk_size=1024 * 1024):
                    if chunk:
                        handle.write(chunk)
                        downloaded += len(chunk)
                        if total_size > 0:
                            percent = (downloaded / total_size) * 100
                            print(f"\r📥 Download progress: {percent:.1f}%", end='', flush=True)
                print()  # New line after progress

        print(f"✅ Successfully downloaded release archive")
        return archive_path

    # ------------------------------------------------------------------
    # Extraction & synchronisation
    # ------------------------------------------------------------------
    def extract_archive(self, archive_path: Path) -> Path:
        """Extract the release archive and return the root directory containing the code."""
        print(f"📦 Extracting archive: {archive_path}")
        temp_dir = Path(tempfile.mkdtemp(prefix="otrs_release_"))
        print(f"📂 Extraction directory: {temp_dir}")

        if archive_path.suffix == ".zip":
            return self._extract_zip(archive_path, temp_dir)
        if archive_path.suffixes[-2:] == [".tar", ".gz"] or archive_path.suffix == ".tgz":
            return self._extract_tar(archive_path, temp_dir)

        raise PackageExtractionError(f"Unsupported archive format: {archive_path.name}")

    def _extract_tar(self, archive_path: Path, dest_dir: Path) -> Path:
        """Extract tar archives safely and return root directory."""
        try:
            with tarfile.open(archive_path, "r:gz") as tar:
                members = tar.getmembers()
                print(f"🔍 Validating {len(members)} archive members...")
                self._validate_members(members, dest_dir)
                print("✅ Archive validation passed")
                print("📤 Extracting files...")
                tar.extractall(dest_dir)
                print("✅ Extraction completed")
        except (tarfile.TarError, OSError) as exc:
            raise PackageExtractionError(f"Failed to extract tar archive: {exc}") from exc

        return self._discover_root_dir(dest_dir)

    def _extract_zip(self, archive_path: Path, dest_dir: Path) -> Path:
        """Extract zip archives and return root directory."""
        import zipfile

        try:
            with zipfile.ZipFile(archive_path, "r") as zf:
                members = zf.infolist()
                print(f"🔍 Validating {len(members)} archive members...")
                self._validate_members(members, dest_dir, zip_mode=True, zip_file=zf)
                print("✅ Archive validation passed")
                print("📤 Extracting files...")
                zf.extractall(dest_dir)
                print("✅ Extraction completed")
        except (zipfile.BadZipFile, OSError) as exc:
            raise PackageExtractionError(f"Failed to extract zip archive: {exc}") from exc

        return self._discover_root_dir(dest_dir)

    def _validate_members(
        self,
        members: Iterable,
        dest_dir: Path,
        zip_mode: bool = False,
        zip_file: Optional["zipfile.ZipFile"] = None,
    ) -> None:
        """Prevent path traversal attacks during extraction."""
        dest_root = dest_dir.resolve()
        for member in members:
            name = member.filename if zip_mode else member.name
            member_path = dest_root / name
            try:
                resolved = member_path.resolve()
            except FileNotFoundError:
                # Parent directories may not exist yet; resolve parent
                resolved = member_path.parent.resolve()
            if not str(resolved).startswith(str(dest_root)):
                raise PackageExtractionError(f"Blocked unsafe path traversal for member: {name}")
            if zip_mode and zip_file and zip_file.getinfo(name).is_dir():
                continue
            if not zip_mode and getattr(member, "isdir", lambda: False)():
                continue

    def _discover_root_dir(self, dest_dir: Path) -> Path:
        """Return the first directory inside extraction directory."""
        entries = [child for child in dest_dir.iterdir() if child.is_dir()]
        if not entries:
            raise PackageExtractionError("Unable to locate root directory inside extracted archive")
        print(f"📁 Root directory in archive: {entries[0]}")
        return entries[0]

    def sync_to_project(self, source_root: Path) -> None:
        """Synchronise extracted files into the project directory."""
        print(f"🔁 Synchronising files from {source_root} to {self.project_root}")
        synced_files = 0
        skipped_files = 0
        
        for root, dirs, files in os.walk(source_root):
            rel_root = os.path.relpath(root, source_root)
            if rel_root == ".":
                rel_root = ""

            # Skip preserved directories entirely
            if rel_root and self._should_preserve(rel_root):
                print(f"⏭️  Skipping preserved directory: {rel_root}")
                dirs[:] = []
                skipped_files += len(files)
                continue

            dest_root = self.project_root if not rel_root else self.project_root / rel_root
            dest_root.mkdir(parents=True, exist_ok=True)

            # Filter directories in-place to honour preserved paths
            original_dirs_count = len(dirs)
            dirs[:] = [
                d for d in dirs if not self._should_preserve(os.path.join(rel_root, d) if rel_root else d)
            ]
            skipped_dirs = original_dirs_count - len(dirs)

            for file_name in files:
                rel_file = os.path.join(rel_root, file_name) if rel_root else file_name
                if self._should_preserve(rel_file):
                    print(f"⏭️  Skipping preserved file: {rel_file}")
                    skipped_files += 1
                    continue
                src_path = Path(root) / file_name
                dest_path = dest_root / file_name
                dest_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src_path, dest_path)
                synced_files += 1

        print(f"✅ Synchronisation completed: {synced_files} files copied, {skipped_files} files skipped")

    # ------------------------------------------------------------------
    # Misc utilities
    # ------------------------------------------------------------------
    def backup_database(self, database_candidates: Sequence[Path], backup_dir: Path) -> Optional[Path]:
        """Copy the first existing database file to a backup directory."""
        print("🛡️  Creating database backup...")
        backup_dir.mkdir(parents=True, exist_ok=True)
        for candidate in database_candidates:
            if candidate.exists():
                timestamp = os.environ.get("UPDATE_TIMESTAMP")
                if not timestamp:
                    from datetime import datetime

                    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
                backup_path = backup_dir / f"backup_{candidate.stem}_{timestamp}.db"
                print(f"💾 Backing up database from {candidate} to {backup_path}")
                shutil.copy2(candidate, backup_path)
                print("✅ Database backup completed")
                return backup_path
        print("ℹ️  No database file detected for backup")
        return None

    def install_dependencies(self, pip_command: Sequence[str], env: Optional[dict] = None) -> None:
        """Run dependency installation via subprocess."""
        print(f"📦 Installing dependencies with command: {' '.join(pip_command)}")
        self._run_subprocess(pip_command, env=env)
        print("✅ Dependencies installed successfully")

    def run_migration(
        self,
        script_path: Path,
        env: Optional[dict] = None,
        python_executable: Optional[str] = None,
    ) -> None:
        """Execute migration script if present."""
        if script_path.exists():
            print(f"🛠️  Running migration script: {script_path}")
            interpreter = python_executable or sys.executable
            self._run_subprocess([interpreter, str(script_path)], env=env)
            print(f"✅ Migration script {script_path.name} completed")

    def _run_subprocess(self, command: Sequence[str], env: Optional[dict] = None) -> None:
        """Execute command and raise an informative error on failure."""
        import subprocess

        if not command:
            return

        command = list(command)
        print(f"🔧 Executing command: {' '.join(command)}")
        try:
            result = subprocess.run(
                command,
                cwd=self.project_root,
                env=env,
                check=False,
                capture_output=True,
                text=True,
            )
        except OSError as exc:
            raise RuntimeError(f"Failed to execute command {' '.join(command)}: {exc}") from exc

        if result.returncode != 0:
            error_msg = "Command failed ({code}): {cmd}\nSTDOUT: {stdout}\nSTDERR: {stderr}".format(
                code=result.returncode,
                cmd=" ".join(command),
                stdout=result.stdout or "<empty>",
                stderr=result.stderr or "<empty>",
            )
            print(f"❌ {error_msg}")
            raise RuntimeError(error_msg)
        
        if result.stdout:
            print(f"📄 Command output:\n{result.stdout}")
        print("✅ Command executed successfully")

    def _should_preserve(self, relative_path: str) -> bool:
        """Check if a relative path should be preserved during sync."""
        normalized = relative_path.replace("\\", "/").strip("/")
        for preserved in self.preserve_paths:
            preserved_norm = preserved.replace("\\", "/").strip("/")
            if not preserved_norm:
                continue
            if normalized == preserved_norm or normalized.startswith(f"{preserved_norm}/"):
                return True
        return False