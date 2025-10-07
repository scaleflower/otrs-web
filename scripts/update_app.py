#!/usr/bin/env python3
"""Utility script to update the OTRS web application from GitHub releases/tag."""

import argparse
import os
import subprocess
import sys
from pathlib import Path


def run_command(command, cwd, env=None):
    """Execute shell command and raise exception on failure"""
    print(f"➡️  Running: {' '.join(command)}")
    result = subprocess.run(command, cwd=cwd, env=env, check=False, text=True)
    if result.returncode != 0:
        raise RuntimeError(
            f"Command failed (code {result.returncode}): {' '.join(command)}\n"
            f"STDOUT: {result.stdout}\nSTDERR: {result.stderr}"
        )
    return result


def parse_args():
    parser = argparse.ArgumentParser(description='Update OTRS web application from GitHub')
    parser.add_argument('--repo', required=True, help='GitHub repo in <owner>/<name> format')
    parser.add_argument('--branch', default='main', help='Fallback branch to checkout when no target given')
    parser.add_argument('--target', help='Git tag/branch to checkout')
    parser.add_argument('--working-dir', default=None, help='Project root directory (defaults to script parent)')
    parser.add_argument('--skip-deps', action='store_true', help='Skip dependency installation step')
    parser.add_argument('--pip-extra-args', default='', help='Extra args passed to pip install')
    return parser.parse_args()


def main():
    args = parse_args()
    project_root = Path(args.working_dir or Path(__file__).resolve().parent.parent)
    if not project_root.exists():
        raise SystemExit(f"Project directory not found: {project_root}")

    print(f"📁 Working directory: {project_root}")

    env = os.environ.copy()
    github_token = env.get('GITHUB_TOKEN')
    if github_token:
        env['GIT_ASKPASS'] = 'echo'
        print('🔐 Using GitHub token from environment')

    git_dir = project_root / '.git'
    if not git_dir.exists():
        raise SystemExit('This script must be executed inside a git repository')

    # 1. Fetch latest refs
    run_command(['git', 'fetch', '--tags', '--prune'], cwd=project_root, env=env)

    # 2. Ensure working tree is clean to avoid losing changes
    status_result = subprocess.run(['git', 'status', '--porcelain'], cwd=project_root, text=True, capture_output=True)
    if status_result.stdout.strip():
        print('⚠️  Working tree has uncommitted changes. They will remain on disk but may block checkout.')

    target_ref = args.target or args.branch
    print(f"🔄 Checking out {target_ref}")
    run_command(['git', 'checkout', target_ref], cwd=project_root, env=env)

    # 3. Pull latest changes for the target reference if using branch
    if args.target is None:
        run_command(['git', 'pull', '--ff-only'], cwd=project_root, env=env)

    # 4. Install/upgrade dependencies
    if not args.skip_deps:
        pip_args = ['-m', 'pip', 'install', '-r', 'requirements.txt']
        if args.pip_extra_args:
            pip_args.extend(args.pip_extra_args.split())
        print('📦 Installing dependencies')
        run_command([sys.executable] + pip_args, cwd=project_root, env=env)
    else:
        print('⏭️  Skipping dependency installation')

    # 5. Run optional migration scripts if present
    migrations = [
        project_root / 'upgrade_statistics_log_columns.py',
        project_root / 'upgrade_database_with_new_records_count.py'
    ]
    for script in migrations:
        if script.exists():
            print(f"🛠️  Executing migration script: {script.name}")
            run_command([sys.executable, str(script)], cwd=project_root, env=env)

    print('✅ Update completed successfully')
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except Exception as exc:  # pragma: no cover - interactive script error handling
        print(f"❌ Update failed: {exc}")
        sys.exit(1)
