#!/usr/bin/env python3
"""Utility script to update the OTRS web application using HTTP releases."""

import argparse
import os
import sys
import traceback
from pathlib import Path

# 导入云效更新包管理器
from utils.update_package import ReleasePackageManager, ReleaseDownloadError, PackageExtractionError
from utils.yunxiao_update_package import YunxiaoReleasePackageManager, YunxiaoReleaseDownloadError, YunxiaoPackageExtractionError


def parse_args():
    parser = argparse.ArgumentParser(description='Update OTRS web application from GitHub release assets or Aliyun Yunxiao')
    parser.add_argument('--repo', required=True, help='Repository in <owner>/<name> format for GitHub or project ID for Yunxiao')
    parser.add_argument('--target', help='Git tag to deploy (defaults to latest release when omitted)')
    parser.add_argument('--working-dir', default=None, help='Project root directory (defaults to script parent)')
    parser.add_argument('--download-dir', default=None, help='Directory to cache downloaded releases')
    parser.add_argument('--preserve', default='.env,uploads,database_backups,logs,db/otrs_data.db',
                        help='Comma separated relative paths that will be preserved during sync')
    parser.add_argument('--skip-deps', action='store_true', help='Skip dependency installation step')
    parser.add_argument('--pip-extra-args', default='', help='Extra args passed to pip install')
    parser.add_argument('--force-reinstall', action='store_true', help='Force reinstall even if version is the same')
    parser.add_argument('--source', default='github', choices=['github', 'yunxiao'], help='Update source: github or yunxiao')
    parser.add_argument('--use-ssh', action='store_true', help='Use SSH instead of HTTPS to fetch updates from Yunxiao')
    return parser.parse_args()


def _build_preserve_list(raw_value: str):
    return [item.strip() for item in raw_value.split(',') if item.strip()]


def main():
    print("🔄 OTRS Web Application Update Script")
    print("=" * 50)
    
    args = parse_args()
    project_root = Path(args.working_dir or Path(__file__).resolve().parent.parent).resolve()
    if not project_root.exists():
        raise SystemExit(f"Project directory not found: {project_root}")

    download_dir = Path(args.download_dir or (project_root / 'instance' / 'releases')).resolve()
    preserve_paths = _build_preserve_list(args.preserve)

    env = os.environ.copy()
    
    # 根据更新源选择不同的Token和处理方式
    if args.source == 'yunxiao':
        token = env.get('YUNXIAO_TOKEN')
        if token:
            print('🔐 Using Yunxiao token from environment for release download')
        elif not args.use_ssh:
            print('⚠️  No Yunxiao token found')
    else:
        token = env.get('GITHUB_TOKEN')
        if token:
            print('🔐 Using GitHub token from environment for release download')
        else:
            print('⚠️  No GitHub token found - may encounter rate limiting')

    # 根据更新源选择不同的包管理器
    if args.source == 'yunxiao':
        manager = YunxiaoReleasePackageManager(
            repo=args.repo,
            token=token,
            project_root=project_root,
            download_root=download_dir,
            preserve_paths=preserve_paths,
            use_ssh=args.use_ssh  # 传递SSH使用标志
        )
    else:
        manager = ReleasePackageManager(
            repo=args.repo,
            token=token,  # 传递token，即使为None也没关系
            project_root=project_root,
            download_root=download_dir,
            preserve_paths=preserve_paths,
        )

    print(f"📁 Working directory: {project_root}")
    print(f"📦 Release cache: {download_dir}")
    if args.use_ssh:
        print("🔑 Using SSH for code fetching")
    if args.force_reinstall:
        print("🔁 Force reinstall requested – proceeding without local version checks")
    else:
        print("🔍 Checking for updates...")

    # 0. Backup database before update
    print("🛡️  Creating database backup...")
    database_candidates = [
        project_root / 'db' / 'otrs_data.db',
        project_root / 'instance' / 'otrs_web.db',
    ]
    backup_dir = project_root / 'database_backups'
    backup_path = manager.backup_database(database_candidates, backup_dir)
    if backup_path:
        print(f"✅ Database backup created: {backup_path.name}")
    else:
        print("ℹ️  No database file detected for backup")

    # 1. Fetch release metadata
    try:
        print("🔍 Fetching release metadata...")
        if args.source == 'yunxiao':
            metadata = manager.fetch_release_metadata(args.target)
        else:
            metadata = manager.fetch_release_metadata(args.target)
    except (ReleaseDownloadError, YunxiaoReleaseDownloadError) as exc:
        raise SystemExit(f"❌ Fetching release metadata failed: {exc}") from exc

    target_version = args.target or metadata.tag_name
    print(f"🎯 Preparing to install release: {target_version}")

    # 2. Download archive
    try:
        print("⬇️  Downloading release archive...")
        archive_path = manager.download_release_archive(metadata, target_version)
    except (ReleaseDownloadError, YunxiaoReleaseDownloadError) as exc:
        raise SystemExit(f"❌ Downloading release archive failed: {exc}") from exc

    print(f"✅ Downloaded archive: {archive_path}")

    # 3. Extract archive
    try:
        print("📦 Extracting release archive...")
        source_root = manager.extract_archive(archive_path)
    except (PackageExtractionError, YunxiaoPackageExtractionError) as exc:
        raise SystemExit(f"❌ Archive extraction failed: {exc}") from exc

    print(f"✅ Extracted to: {source_root}")

    # 4. Apply update
    try:
        print("🚀 Applying update...")
        manager.apply_update(source_root, skip_deps=args.skip_deps, pip_extra_args=args.pip_extra_args)
    except Exception as exc:
        raise SystemExit(f"❌ Update apply failed: {exc}") from exc

    print("🎉 Update completed successfully!")
    print("🔄 Please restart the application for changes to take effect")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        sys.exit("🛑 Update cancelled by user")
    except Exception:
        traceback.print_exc()
        sys.exit(1)