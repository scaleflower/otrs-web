#!/usr/bin/env python3
"""Utility script to update the OTRS web application using HTTP releases."""

import argparse
import os
import sys
from pathlib import Path

from utils.update_package import ReleasePackageManager, ReleaseDownloadError, PackageExtractionError


def parse_args():
    parser = argparse.ArgumentParser(description='Update OTRS web application from GitHub release assets')
    parser.add_argument('--repo', required=True, help='GitHub repo in <owner>/<name> format')
    parser.add_argument('--target', help='Git tag to deploy (defaults to latest release when omitted)')
    parser.add_argument('--working-dir', default=None, help='Project root directory (defaults to script parent)')
    parser.add_argument('--download-dir', default=None, help='Directory to cache downloaded releases')
    parser.add_argument('--preserve', default='.env,uploads,database_backups,logs,db/otrs_data.db',
                        help='Comma separated relative paths that will be preserved during sync')
    parser.add_argument('--skip-deps', action='store_true', help='Skip dependency installation step')
    parser.add_argument('--pip-extra-args', default='', help='Extra args passed to pip install')
    parser.add_argument('--force-reinstall', action='store_true', help='Force reinstall even if version is the same')
    return parser.parse_args()


def _build_preserve_list(raw_value: str):
    return [item.strip() for item in raw_value.split(',') if item.strip()]


def main():
    args = parse_args()
    project_root = Path(args.working_dir or Path(__file__).resolve().parent.parent).resolve()
    if not project_root.exists():
        raise SystemExit(f"Project directory not found: {project_root}")

    download_dir = Path(args.download_dir or (project_root / 'instance' / 'releases')).resolve()
    preserve_paths = _build_preserve_list(args.preserve)

    env = os.environ.copy()
    token = env.get('GITHUB_TOKEN')
    if token:
        print('🔐 Using GitHub token from environment for release download')

    manager = ReleasePackageManager(
        repo=args.repo,
        token=token,
        project_root=project_root,
        download_root=download_dir,
        preserve_paths=preserve_paths,
    )

    print(f"📁 Working directory: {project_root}")
    print(f"📦 Release cache: {download_dir}")
    if args.force_reinstall:
        print("🔁 Force reinstall requested – proceeding without local version checks")

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
        metadata = manager.fetch_release_metadata(args.target)
    except ReleaseDownloadError as exc:
        raise SystemExit(f"❌ Fetching release metadata failed: {exc}") from exc

    target_version = args.target or metadata.tag_name
    print(f"🔍 Preparing to install release: {target_version}")

    # 2. Download archive
    try:
        archive_path = manager.download_release_archive(metadata, target_version)
    except ReleaseDownloadError as exc:
        raise SystemExit(f"❌ Downloading release archive failed: {exc}") from exc

    print(f"⬇️  Downloaded archive: {archive_path}")

    # 3. Extract archive
    try:
        source_root = manager.extract_archive(archive_path)
    except PackageExtractionError as exc:
        raise SystemExit(f"❌ Extracting release archive failed: {exc}") from exc

    print(f"🗂️  Extracted release contents into: {source_root}")

    # 4. Sync files into project
    print("🔁 Synchronising release files into project directory...")
    manager.sync_to_project(source_root)

    # 5. Install dependencies
    if args.skip_deps:
        print("⏭️  Skipping dependency installation as requested")
    else:
        pip_command = [sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt']
        if args.pip_extra_args:
            pip_command.extend(args.pip_extra_args.split())
        print("📦 Installing Python dependencies...")
        manager.install_dependencies(pip_command, env=env)
        print("✅ Dependencies installed")

    # 6. Run optional migrations
    migrations = [
        project_root / 'upgrade_statistics_log_columns.py',
        project_root / 'upgrade_database_with_new_records_count.py',
    ]
    for script_path in migrations:
        if script_path.exists():
            print(f"🛠️  Running migration script: {script_path.name}")
            manager.run_migration(script_path, env=env)

    print("✅ Update completed successfully")
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except Exception as exc:  # pragma: no cover - interactive script error handling
        print(f"❌ Update failed: {exc}")
        sys.exit(1)
