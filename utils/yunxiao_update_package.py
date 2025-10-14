"""
Utilities for downloading, extracting and applying application update packages from Aliyun Yunxiao (CodeUp).

This module extends the update capability to support Aliyun Yunxiao as an alternative to GitHub.
"""

from __future__ import annotations

import json
import os
import shutil
import sys
import tarfile
import tempfile
import traceback
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional, Sequence
from datetime import datetime

import requests


class YunxiaoReleaseDownloadError(RuntimeError):
    """Raised when release metadata or package download fails from Yunxiao."""


class YunxiaoPackageExtractionError(RuntimeError):
    """Raised when a release archive cannot be safely extracted."""


@dataclass
class YunxiaoReleaseMetadata:
    """Simple container for Yunxiao release metadata used during updates."""

    tag_name: str
    name: Optional[str]
    body: Optional[str]
    html_url: Optional[str]
    published_at: Optional[str]
    tarball_url: Optional[str]
    zipball_url: Optional[str]

    @classmethod
    def from_payload(cls, payload: dict) -> "YunxiaoReleaseMetadata":
        """Build metadata object from Yunxiao API payload."""
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


class YunxiaoReleasePackageManager:
    """Handle HTTP based release lookups and filesystem synchronisation for Yunxiao."""

    USER_AGENT = "otrs-web-yunxiao-update-agent"

    def __init__(
        self,
        repo: str,
        token: Optional[str],
        project_root: Path,
        download_root: Path,
        preserve_paths: Optional[Sequence[str]] = None,
        session: Optional[requests.Session] = None,
        timeout: int = 30,
        use_ssh: bool = False,
    ) -> None:
        self.repo = repo
        self.token = token
        self.project_root = project_root
        self.download_root = download_root
        self.download_root.mkdir(parents=True, exist_ok=True)
        self.preserve_paths = tuple(preserve_paths or ())
        self._session = session or requests.Session()
        self._timeout = timeout
        self.use_ssh = use_ssh  # 是否使用SSH方式

    # ------------------------------------------------------------------
    # Release metadata & download
    # ------------------------------------------------------------------
    def fetch_release_metadata(self, target_version: Optional[str]) -> YunxiaoReleaseMetadata:
        """Retrieve release metadata from Yunxiao for the target version."""
        # 如果使用SSH方式，则跳过HTTP API调用
        if self.use_ssh:
            # SSH方式下，我们通过git命令获取最新tag
            try:
                # 获取最新的tag
                if target_version:
                    tag = target_version
                else:
                    # 获取最新的tag
                    result = subprocess.run(
                        ['git', 'ls-remote', '--tags', f'git@codeup.aliyun.com:{self.repo}.git'],
                        capture_output=True,
                        text=True,
                        cwd=self.project_root
                    )
                    if result.returncode != 0:
                        raise YunxiaoReleaseDownloadError(f"Failed to list remote tags: {result.stderr}")
                    
                    # 解析tags输出，获取最新的tag
                    tags = result.stdout.strip().split('\n')
                    if not tags or tags == ['']:
                        raise YunxiaoReleaseDownloadError("No tags found in repository")
                    
                    # 简单地获取最后一个tag（实际项目中可能需要更复杂的版本比较）
                    tag = tags[-1].split('/')[-1] if '/' in tags[-1] else tags[-1].split()[-1]
                
                return YunxiaoReleaseMetadata(
                    tag_name=tag,
                    name=f"Release {tag}",
                    body=f"Release {tag} from Yunxiao",
                    html_url=f"https://codeup.aliyun.com/{self.repo}/tags/{tag}",
                    published_at=datetime.now().isoformat(),
                    tarball_url=None,  # SSH模式下不使用tarball
                    zipball_url=None   # SSH模式下不使用zipball
                )
            except Exception as e:
                raise YunxiaoReleaseDownloadError(f"Failed to fetch release metadata via SSH: {e}")

        # HTTP API方式
        headers = {
            "User-Agent": self.USER_AGENT,
        }
        
        # 只有在token有效时才添加到请求头
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"

        if target_version:
            # Yunxiao API endpoint for specific tag
            url = f"https://codeup.aliyun.com/api/v3/projects/{self.repo}/repository/tags/{target_version}"
        else:
            # Yunxiao API endpoint for latest release
            url = f"https://codeup.aliyun.com/api/v3/projects/{self.repo}/releases/latest"

        print(f"🔍 Fetching release metadata from Yunxiao: {url}")
        response = self._session.get(url, headers=headers, timeout=self._timeout)
        
        if response.status_code != 200:
            raise YunxiaoReleaseDownloadError(
                f"Yunxiao release lookup failed ({response.status_code}): {response.text[:200]}"
            )

        try:
            payload = response.json()
        except json.JSONDecodeError as exc:  # pragma: no cover
            raise YunxiaoReleaseDownloadError(f"Yunxiao response decoding failed: {exc}") from exc

        metadata = YunxiaoReleaseMetadata.from_payload(payload)
        if not metadata.tag_name:
            raise YunxiaoReleaseDownloadError("Yunxiao release payload missing tag name")
        if not metadata.tarball_url and not metadata.zipball_url:
            raise YunxiaoReleaseDownloadError("Yunxiao release payload missing tarball/zipball URLs")
        
        print(f"✅ Successfully fetched release metadata for: {metadata.tag_name}")
        return metadata

    def download_release_archive(self, metadata: YunxiaoReleaseMetadata, target_version: str) -> Path:
        """Download tarball/zipball for the release and return archive path."""
        # 如果使用SSH方式，则通过git clone获取代码
        if self.use_ssh:
            return self._download_via_ssh(target_version)
        
        # HTTP API方式
        headers = {"User-Agent": self.USER_AGENT}
        # 只有在token有效时才添加到请求头
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"

        download_url = metadata.tarball_url or metadata.zipball_url
        if not download_url:
            raise YunxiaoReleaseDownloadError("Release metadata does not contain a download URL")

        archive_ext = ".tar.gz" if metadata.tarball_url else ".zip"
        archive_dir = self.download_root / target_version
        archive_dir.mkdir(parents=True, exist_ok=True)
        archive_path = archive_dir / f"{target_version}{archive_ext}"

        print(f"⬇️  Downloading release archive from Yunxiao: {download_url}")
        print(f"📂 Saving to: {archive_path}")

        with self._session.get(download_url, headers=headers, timeout=self._timeout, stream=True) as response:
            if response.status_code != 200:
                raise YunxiaoReleaseDownloadError(
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

    def _download_via_ssh(self, target_version: str) -> Path:
        """通过SSH方式获取代码"""
        print(f"🔐 Using SSH to fetch release: {target_version}")
        
        # 创建临时目录用于存放代码
        temp_dir = Path(tempfile.mkdtemp(prefix="otrs_update_ssh_"))
        try:
            # 克隆指定tag的代码
            repo_url = f"git@codeup.aliyun.com:{self.repo}.git"
            print(f"📋 Cloning repository: {repo_url}")
            
            # 克隆指定tag
            result = subprocess.run(
                ['git', 'clone', '--branch', target_version, '--depth', '1', repo_url, str(temp_dir)],
                capture_output=True,
                text=True,
                cwd=self.project_root
            )
            
            if result.returncode != 0:
                raise YunxiaoReleaseDownloadError(f"Failed to clone repository: {result.stderr}")
            
            # 创建tar.gz归档文件
            archive_dir = self.download_root / target_version
            archive_dir.mkdir(parents=True, exist_ok=True)
            archive_path = archive_dir / f"{target_version}.tar.gz"
            
            print(f"📦 Creating archive: {archive_path}")
            # 创建归档
            with tarfile.open(archive_path, "w:gz") as tar:
                tar.add(temp_dir, arcname=f"otrs-web-{target_version}")
            
            print(f"✅ Successfully created release archive via SSH")
            return archive_path
        except Exception as e:
            # 清理临时目录
            if temp_dir.exists():
                shutil.rmtree(temp_dir, ignore_errors=True)
            raise YunxiaoReleaseDownloadError(f"Failed to download via SSH: {e}")
        finally:
            # 清理临时目录
            if temp_dir.exists():
                shutil.rmtree(temp_dir, ignore_errors=True)

    # ------------------------------------------------------------------
    # Extraction & synchronisation
    # ------------------------------------------------------------------
    def extract_archive(self, archive_path: Path) -> Path:
        """Extract the release archive and return the root directory containing the code."""
        print(f"📦 Extracting archive: {archive_path}")

        if archive_path.suffixes[-2:] == [".tar", ".gz"]:
            opener, mode = tarfile.open, "r:gz"
        elif archive_path.suffix == ".zip":
            # Delayed import since zipfile is unused with tarball releases
            import zipfile
            opener, mode = zipfile.ZipFile, "r"
        else:
            raise YunxiaoPackageExtractionError(f"Unsupported archive format: {archive_path}")

        temp_dir = Path(tempfile.mkdtemp(prefix="otrs_update_"))
        try:
            with opener(archive_path, mode) as handle:
                print(f"📂 Extracting to temporary directory: {temp_dir}")
                # 修复tarfile.extractall安全问题
                if mode == "r:gz":
                    members = handle.getmembers()
                    # 验证成员安全性
                    for member in members:
                        member_path = temp_dir / member.name
                        try:
                            resolved = member_path.resolve()
                        except FileNotFoundError:
                            # Parent directories may not exist yet; resolve parent
                            resolved = member_path.parent.resolve()
                        if not str(resolved).startswith(str(temp_dir.resolve())):
                            raise YunxiaoPackageExtractionError(f"Blocked unsafe path traversal for member: {member.name}")
                    # 只提取已验证的成员
                    handle.extractall(path=temp_dir, members=members)
                else:
                    handle.extractall(path=temp_dir)

                # GitHub tarballs have a top-level directory like "owner-repo-shorthash"
                # We want to return the actual code root, not that wrapper dir
                candidates = list(temp_dir.iterdir())
                if len(candidates) == 1 and candidates[0].is_dir():
                    return candidates[0]
                return temp_dir
        except Exception as exc:
            shutil.rmtree(temp_dir, ignore_errors=True)
            raise YunxiaoPackageExtractionError(f"Archive extraction failed: {exc}") from exc

    def backup_database(self, candidates: Iterable[Path], backup_dir: Path) -> Optional[Path]:
        """Create a timestamped backup of the database file if present."""
        backup_dir.mkdir(exponents=True, exist_ok=True)

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

            # 3. Restore preserved files/directories
            print("🔓 Restoring preserved files:")
            for relative_path, temp_path in preserved.items():
                dest_path = self.project_root / relative_path
                dest_path.parent.mkdir(parents=True, exist_ok=True)
                
                if temp_path.is_dir():
                    shutil.copytree(temp_path, dest_path, dirs_exist_ok=True)
                else:
                    shutil.copy2(temp_path, dest_path)
                print(f"   📁 {relative_path}")

        # 4. Install dependencies if not skipped
        if not skip_deps:
            print("⚙️  Installing/updating Python dependencies...")
            cmd = [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"]
            if pip_extra_args:
                cmd.extend(pip_extra_args.split())
            
            env = os.environ.copy()
            result = subprocess.run(cmd, cwd=self.project_root, env=env)
            if result.returncode != 0:
                raise RuntimeError(f"Pip install failed with exit code {result.returncode}")

        print("✅ Update successfully applied!")