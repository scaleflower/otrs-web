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
from datetime import datetime
from pathlib import Path
from typing import Iterable, Optional, Sequence

import requests
# Import the shared archive validation utility
from .archive_utils import validate_members, ArchiveValidationError


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
                safe_members = validate_members(members, dest_dir)
                print("✅ Archive validation passed")
                print("📤 Extracting files...")
                # 手动提取tar成员以增强安全性，避免使用extractall方法
                for member in safe_members:
                    member_path = dest_dir / member.name
                    if member.isdir():
                        member_path.mkdir(parents=True, exist_ok=True)
                        continue
                    if not member.isfile():
                        continue
                    member_path.parent.mkdir(parents=True, exist_ok=True)
                    extracted = tar.extractfile(member)
                    if extracted is None:
                        continue
                    with extracted, member_path.open("wb") as target_handle:
                        shutil.copyfileobj(extracted, target_handle)
                    if member.mode:
                        try:
                            os.chmod(member_path, member.mode)
                        except OSError:
                            pass
                print("✅ Extraction completed")
        except (tarfile.TarError, OSError) as exc:
            raise PackageExtractionError(f"Failed to extract tar archive: {exc}") from exc
        except ArchiveValidationError as exc:
            raise PackageExtractionError(f"Archive validation failed: {exc}") from exc

        return self._discover_root_dir(dest_dir)

    def _extract_zip(self, archive_path: Path, dest_dir: Path) -> Path:
        """Extract zip archives and return root directory."""
        import zipfile

        try:
            with zipfile.ZipFile(archive_path, "r") as zf:
                members = zf.infolist()
                print(f"🔍 Validating {len(members)} archive members...")
                safe_members = validate_members(members, dest_dir, zip_mode=True)
                print("✅ Archive validation passed")
                print("📤 Extracting files...")
                # 手动提取zip成员以增强安全性，避免使用extractall方法
                for member in safe_members:
                    name = member.filename
                    member_path = dest_dir / name
                    if member.is_dir():
                        member_path.mkdir(parents=True, exist_ok=True)
                        continue
                    member_path.parent.mkdir(parents=True, exist_ok=True)
                    with zf.open(member, "r") as source, member_path.open("wb") as target:
                        shutil.copyfileobj(source, target)
                    perm = member.external_attr >> 16
                    if perm:
                        try:
                            os.chmod(member_path, perm)
                        except OSError:
                            pass
                print("✅ Extraction completed")
        except (zipfile.BadZipFile, OSError) as exc:
            raise PackageExtractionError(f"Failed to extract zip archive: {exc}") from exc
        except ArchiveValidationError as exc:
            raise PackageExtractionError(f"Archive validation failed: {exc}") from exc

        return self._discover_root_dir(dest_dir)

    # The _validate_members method has been removed as we now use the shared
    # archive_utils.validate_members function for security validation

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

        for item in source_root.rglob("*"):
            relative_path = item.relative_to(source_root)
            target_path = self.project_root / relative_path

            # Skip preserved paths
            if any(str(relative_path).startswith(preserved) for preserved in self.preserve_paths):
                print(f"🔒 Skipping preserved path: {relative_path}")
                continue

            if item.is_file():
                target_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(item, target_path)
                synced_files += 1
            elif item.is_dir():
                target_path.mkdir(parents=True, exist_ok=True)

        print(f"✅ Synchronisation completed ({synced_files} files copied)")

    # ------------------------------------------------------------------
    # Misc utilities
    # ------------------------------------------------------------------
    def backup_database(self, candidates: Iterable[Path], backup_dir: Path) -> Optional[Path]:
        """Create a timestamped backup of the database file if present."""
        backup_dir.mkdir(parents=True, exist_ok=True)

        for candidate in candidates:
            if candidate.is_file():
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_path = backup_dir / f"backup_{timestamp}.db"
                shutil.copy2(candidate, backup_path)
                return backup_path
        return None

    def apply_update(self, source_root: Path, skip_deps: bool = False, pip_extra_args: str = "") -> None:
        """Replace the current application with the downloaded release."""
        from datetime import datetime

        print(f"🔄 Applying update from: {source_root}")
        print(f"📍 Project root: {self.project_root}")

        # 1. Preserve files/directories according to config
        preserved = {}
        with tempfile.TemporaryDirectory(prefix="otrs_preserve_") as temp_root_s:
            temp_root = Path(temp_root_s)

            print("🔒 Preserving files:")
            for relative_path in self.preserve_paths:
                source_path = self.project_root / relative_path
                if source_path.exists():
                    dest_path = temp_root / relative_path.replace("/", "_").replace("\\", "_")
                    if source_path.is_dir():
                        shutil.copytree(source_path, dest_path, dirs_exist_ok=True)
                    else:
                        dest_path.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(source_path, dest_path)
                    preserved[relative_path] = dest_path
                    print(f"   📁 {relative_path}")

            # 2. Replace project directory with downloaded release
            print("🗑️  Removing old application files...")
            for item in self.project_root.iterdir():
                # Skip preserved paths
                if any(str(item.relative_to(self.project_root)).startswith(p) for p in self.preserve_paths):
                    continue

                if item.is_dir():
                    shutil.rmtree(item)
                else:
                    item.unlink()

            print("📋 Copying new application files...")
            for item in source_root.iterdir():
                dest = self.project_root / item.name
                if item.is_dir():
                    shutil.copytree(item, dest, dirs_exist_ok=True)
                else:
                    shutil.copy2(item, dest)

            # 3. Restore preserved files
            print("🔓 Restoring preserved files:")
            for relative_path, temp_path in preserved.items():
                dest_path = self.project_root / relative_path
                if temp_path.is_dir():
                    shutil.copytree(temp_path, dest_path, dirs_exist_ok=True)
                else:
                    dest_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(temp_path, dest_path)
                print(f"   📁 {relative_path}")

        # 4. Install or upgrade dependencies
        if not skip_deps:
            self._update_dependencies(pip_extra_args)

        print("✅ Application update completed")

    def _update_dependencies(self, pip_extra_args: str) -> None:
        """Install or upgrade Python dependencies."""
        import subprocess

        print("🐍 Updating Python dependencies...")
        cmd = [sys.executable, "-m", "pip", "install", "-r", str(self.project_root / "requirements.txt")]
        if pip_extra_args:
            cmd.extend(pip_extra_args.split())

        try:
            result = subprocess.run(
                cmd,
                cwd=str(self.project_root),
                capture_output=True,
                text=True,
                timeout=300
            )
            if result.returncode != 0:
                print(f"⚠️  Dependency update had issues (exit code {result.returncode})")
                print("STDOUT:", result.stdout)
                print("STDERR:", result.stderr)
            else:
                print("✅ Dependencies updated successfully")
        except subprocess.TimeoutExpired:
            print("⚠️  Dependency update timed out after 5 minutes")
        except Exception as exc:
            print(f"⚠️  Dependency update failed: {exc}")

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