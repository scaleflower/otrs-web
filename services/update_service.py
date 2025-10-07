"""Service for handling application auto-update lifecycle."""

import json
import os
import subprocess
import sys
import threading
from datetime import datetime
from pathlib import Path
from typing import Optional

import requests
from flask import current_app

from models import db, AppUpdateStatus


class UpdateService:
    """Manage GitHub release polling and local update execution"""

    def __init__(self):
        self.app = None
        self._update_thread = None
        self._lock = threading.Lock()
        self._restart_timer = None

    # ------------------------------------------------------------------
    # Initialization helpers
    # ------------------------------------------------------------------
    def initialize(self, app):
        """Bind Flask application for later context usage"""
        self.app = app

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def get_status(self):
        """Return serialized status information"""
        with self._ensure_app_context():
            status = AppUpdateStatus.query.first()
            if not status:
                return {
                    'current_version': self._config('APP_VERSION', '0.0.0'),
                    'status': 'unknown'
                }
            payload = status.to_dict()
            payload['update_enabled'] = bool(self._config('APP_UPDATE_ENABLED', True))
            payload['repo'] = self._config('APP_UPDATE_REPO')
            payload['poll_interval'] = self._config('APP_UPDATE_POLL_INTERVAL', 3600)
            payload['is_updating'] = self.is_update_running()
            payload['restart_scheduled'] = bool(self._restart_timer and self._restart_timer.is_alive())
            return payload

    def acknowledge_notification(self):
        """Mark update notification as acknowledged by client"""
        with self._ensure_app_context():
            status = AppUpdateStatus.query.first()
            if status:
                status.notified_at = datetime.utcnow()
                db.session.commit()
            return status.to_dict() if status else None

    def check_for_updates(self, force=False):
        """Poll GitHub Releases and persist status"""
        if not self._config('APP_UPDATE_ENABLED', True):
            return None

        with self._ensure_app_context():
            repo = self._config('APP_UPDATE_REPO')
            token = self._config('APP_UPDATE_GITHUB_TOKEN')
            headers = {
                'Accept': 'application/vnd.github+json',
                'User-Agent': 'otrs-web-update-service'
            }
            if token:
                headers['Authorization'] = f'Bearer {token}'

            status = AppUpdateStatus.query.first()
            if not status:
                status = AppUpdateStatus(current_version=self._config('APP_VERSION', '0.0.0'))
                db.session.add(status)

            url = f'https://api.github.com/repos/{repo}/releases/latest'
            try:
                response = requests.get(url, headers=headers, timeout=10)
            except requests.RequestException as err:
                self._record_error(f'Failed to contact GitHub: {err}')
                return None

            if response.status_code == 404:
                status.latest_version = status.current_version
                status.status = 'up_to_date'
                status.last_checked_at = datetime.utcnow()
                status.last_error = None
                db.session.commit()
                return status.to_dict()
            elif response.status_code == 200:
                try:
                    payload = response.json()
                except json.JSONDecodeError as err:
                    self._record_error(f'GitHub response parse error: {err}')
                    return None
            else:
                self._record_error(
                    f'GitHub API error {response.status_code}: {response.text[:200]}'
                )
                return None

            latest_version = payload.get('tag_name') or payload.get('name')
            if not latest_version:
                self._record_error('Missing tag_name in GitHub release payload')
                return None

            status.latest_version = latest_version
            status.release_name = payload.get('name')
            status.release_body = payload.get('body')
            status.release_url = payload.get('html_url')
            status.published_at = self._parse_datetime(payload.get('published_at'))
            status.last_checked_at = datetime.utcnow()
            status.last_error = None

            current_version = status.current_version or '0.0.0'
            if latest_version != current_version:
                status.status = 'update_available'
                if force:
                    status.notified_at = None
            else:
                status.status = 'up_to_date'

            db.session.commit()
            return status.to_dict()

    def trigger_update(self, target_version: Optional[str] = None):
        """Kick off background update execution"""
        if not self._config('APP_UPDATE_ENABLED', True):
            raise RuntimeError('Auto-update disabled')

        with self._ensure_app_context():
            status = AppUpdateStatus.query.first()
            if not status:
                raise RuntimeError('Update status not initialized')

            if self.is_update_running():
                raise RuntimeError('Update already in progress')

            target = target_version or status.latest_version or status.current_version
            if not target:
                raise RuntimeError('No target version supplied')

            status.status = 'updating'
            status.last_update_started_at = datetime.utcnow()
            status.last_error = None
            db.session.commit()

            thread = threading.Thread(target=self._run_update_job, args=(target,), daemon=True)
            thread.start()
            self._update_thread = thread
            return {'message': 'Update started', 'target_version': target}

    def is_update_running(self) -> bool:
        thread = self._update_thread
        return bool(thread and thread.is_alive())

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _run_update_job(self, target_version):
        with self._ensure_app_context():
            status = AppUpdateStatus.query.first()
            repo = self._config('APP_UPDATE_REPO')
            branch = self._config('APP_UPDATE_BRANCH')
            script_path = Path(self._config('APP_UPDATE_SCRIPT', 'scripts/update_app.py'))
            if not script_path.is_absolute():
                base_dir = Path(self.app.root_path).parent
                script_path = (base_dir / script_path).resolve()

            env = os.environ.copy()
            token = self._config('APP_UPDATE_GITHUB_TOKEN')
            if token:
                env['GITHUB_TOKEN'] = token

            if not script_path.exists():
                self._finalize_failure(status, f'Update script not found: {script_path}')
                return

            command = [
                sys.executable,
                str(script_path),
                f'--repo={repo}',
                f'--branch={branch}',
                f'--target={target_version}'
            ]

            try:
                result = subprocess.run(
                    command,
                    capture_output=True,
                    text=True,
                    env=env,
                    cwd=Path(self.app.root_path).parent,
                    check=False,
                )
            except Exception as err:  # pragma: no cover (subprocess failure path)
                self._finalize_failure(status, f'Update execution error: {err}')
                return

            if result.returncode != 0:
                error_message = (
                    f'Update script failed with code {result.returncode}.\n'
                    f'STDOUT: {result.stdout}\nSTDERR: {result.stderr}'
                )
                self._finalize_failure(status, error_message)
                return

            # Assume success, update current version and prepare restart
            status.current_version = target_version
            status.status = 'restarting'
            status.last_update_completed_at = datetime.utcnow()
            db.session.commit()

            delay = max(1, int(self._config('APP_UPDATE_RESTART_DELAY', 5) or 5))
            self._schedule_restart(delay)

    def _finalize_failure(self, status, message):
        status.status = 'update_failed'
        status.last_error = message[:2000]
        status.last_update_completed_at = datetime.utcnow()
        db.session.commit()

    def _record_error(self, message):
        with self._ensure_app_context():
            status = AppUpdateStatus.query.first()
            if not status:
                status = AppUpdateStatus(current_version=self._config('APP_VERSION', '0.0.0'))
                db.session.add(status)
            status.last_error = message[:2000]
            status.last_checked_at = datetime.utcnow()
            if status.status != 'updating':
                status.status = 'error'
            db.session.commit()

    def _ensure_app_context(self):
        if not self.app:
            raise RuntimeError('UpdateService is not initialized with Flask app')
        return self.app.app_context()

    @staticmethod
    def _parse_datetime(value):
        if not value:
            return None
        try:
            if value.endswith('Z'):
                value = value.replace('Z', '+00:00')
            return datetime.fromisoformat(value)
        except ValueError:
            return None

    def _config(self, key, default=None):
        if self.app:
            return self.app.config.get(key, default)
        return current_app.config.get(key, default)
