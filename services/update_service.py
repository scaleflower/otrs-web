"""Service for handling application auto-update lifecycle."""

import json
import os
import re
import signal
import subprocess
import sys
import threading
import time
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

    def check_for_updates(self):
        """Manually check for updates from GitHub Releases"""
        if not self._config('APP_UPDATE_ENABLED', True):
            return {'success': False, 'error': 'Auto-update disabled'}

        with self._ensure_app_context():
            repo = self._config('APP_UPDATE_REPO')
            token = self._config('APP_UPDATE_GITHUB_TOKEN')
            
            # 检查是否有Token
            if not token or token == 'your_github_token_here':
                return {
                    'success': False, 
                    'error': 'GitHub Token未配置，请设置有效的APP_UPDATE_GITHUB_TOKEN环境变量',
                    'help_url': 'https://github.com/settings/tokens',
                    'error_type': 'token_missing'
                }
            
            headers = {
                'Accept': 'application/vnd.github+json',
                'User-Agent': 'otrs-web-update-service',
                'Authorization': f'Bearer {token}'
            }

            status = AppUpdateStatus.query.first()
            if not status:
                status = AppUpdateStatus(current_version=self._config('APP_VERSION', '0.0.0'))
                db.session.add(status)

            url = f'https://api.github.com/repos/{repo}/releases/latest'
            try:
                response = requests.get(url, headers=headers, timeout=10)
            except requests.RequestException as err:
                error_msg = f'Failed to contact GitHub: {err}'
                self._record_error(error_msg)
                return {'success': False, 'error': error_msg}

            if response.status_code == 404:
                status.latest_version = status.current_version
                status.status = 'up_to_date'
                status.last_checked_at = datetime.utcnow()
                status.last_error = None
                db.session.commit()
                return {
                    'success': True,
                    'status': 'up_to_date',
                    'current_version': status.current_version,
                    'latest_version': status.current_version,
                    'message': 'No releases found in repository'
                }
            elif response.status_code == 200:
                try:
                    payload = response.json()
                except json.JSONDecodeError as err:
                    error_msg = f'GitHub response parse error: {err}'
                    self._record_error(error_msg)
                    return {'success': False, 'error': error_msg}
            else:
                error_msg = f'GitHub API error {response.status_code}: {response.text[:200]}'
                self._record_error(error_msg)
                return {'success': False, 'error': error_msg}

            latest_version = payload.get('tag_name') or payload.get('name')
            if not latest_version:
                error_msg = 'Missing tag_name in GitHub release payload'
                self._record_error(error_msg)
                return {'success': False, 'error': error_msg}

            status.latest_version = latest_version
            status.release_name = payload.get('name')
            status.release_body = payload.get('body')
            status.release_url = payload.get('html_url')
            status.published_at = self._parse_datetime(payload.get('published_at'))
            status.last_checked_at = datetime.utcnow()
            status.last_error = None

            current_version = status.current_version or '0.0.0'
            # 使用语义化版本号比较
            if self._compare_versions(current_version, latest_version):
                status.status = 'update_available'
                db.session.commit()
                return {
                    'success': True,
                    'status': 'update_available',
                    'current_version': current_version,
                    'latest_version': latest_version,
                    'release_name': payload.get('name'),
                    'release_notes': payload.get('body'),
                    'release_url': payload.get('html_url'),
                    'published_at': self._format_datetime(payload.get('published_at')),
                    'message': f'New version {latest_version} is available!'
                }
            else:
                status.status = 'up_to_date'
                db.session.commit()
                return {
                    'success': True,
                    'status': 'up_to_date',
                    'current_version': current_version,
                    'latest_version': latest_version,
                    'message': 'You are using the latest version'
                }

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
            
            # 修复路径计算：使用当前工作目录
            if not script_path.is_absolute():
                # 使用当前工作目录作为基础路径
                base_dir = Path.cwd()
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
                    cwd=Path.cwd(),  # 使用当前工作目录
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

    @staticmethod
    def _format_datetime(value):
        """Format datetime for API response"""
        if not value:
            return None
        try:
            if isinstance(value, datetime):
                return value.isoformat()
            elif isinstance(value, str):
                # Parse and reformat
                parsed = UpdateService._parse_datetime(value)
                return parsed.isoformat() if parsed else value
            return str(value)
        except:
            return str(value) if value else None

    @staticmethod
    def _compare_versions(current, latest):
        """比较语义化版本号，支持多种版本格式"""
        if current == latest:
            return False  # 版本相同，不需要更新
        
        # 清理版本号，提取数字版本部分
        def clean_version(version):
            if not version:
                return "0.0.0"
            
            # 移除所有非数字和点号的前缀和后缀
            # 支持格式: v1.2.3, release/v1.2.6, 1.2.3-beta, etc.
            version_str = str(version).strip()
            
            # 查找版本号模式：数字.数字.数字
            match = re.search(r'(\d+\.\d+\.\d+)', version_str)
            if match:
                return match.group(1)
            
            # 如果没有找到完整的三段版本号，尝试查找两段或一段
            match = re.search(r'(\d+\.\d+)', version_str)
            if match:
                return match.group(1) + '.0'
            
            match = re.search(r'(\d+)', version_str)
            if match:
                return match.group(1) + '.0.0'
            
            return "0.0.0"
        
        current_clean = clean_version(current)
        latest_clean = clean_version(latest)
        
        # 如果清理后的版本相同，则不需要更新
        if current_clean == latest_clean:
            return False
        
        # 分割版本号为数字部分
        def parse_version_parts(version_str):
            parts = version_str.split('.')
            parsed = []
            for part in parts:
                try:
                    parsed.append(int(part))
                except ValueError:
                    parsed.append(0)
            # 确保至少有3个部分
            while len(parsed) < 3:
                parsed.append(0)
            return parsed
        
        try:
            current_parts = parse_version_parts(current_clean)
            latest_parts = parse_version_parts(latest_clean)
            
            # 逐级比较版本号
            for i in range(max(len(current_parts), len(latest_parts))):
                current_part = current_parts[i] if i < len(current_parts) else 0
                latest_part = latest_parts[i] if i < len(latest_parts) else 0
                
                if latest_part > current_part:
                    return True  # 有更新
                elif latest_part < current_part:
                    return False  # 版本回退，不更新
            
            return False  # 版本相同
        except:
            # 如果解析失败，回退到字符串比较
            return latest != current

    def _schedule_restart(self, delay_seconds):
        """Schedule application restart after successful update"""
        def restart_application():
            try:
                print(f"🔄 Application restart scheduled in {delay_seconds} seconds...")
                time.sleep(delay_seconds)
                
                # Log restart attempt
                print("🚀 Attempting application restart...")
                
                # Get current process information
                current_pid = os.getpid()
                current_script = sys.argv[0] if sys.argv else 'app.py'
                
                # Check if we're in development mode (Flask debug mode)
                is_development = self._config('DEBUG', False) or self._config('ENV') == 'development'
                
                if is_development:
                    print("🔧 Development mode detected - using subprocess restart")
                    # In development mode, use subprocess to start new instance
                    subprocess.Popen([
                        sys.executable, current_script
                    ], cwd=os.getcwd())
                    # Give new process time to start
                    time.sleep(3)
                    # Exit current process gracefully
                    print("✅ New process started, exiting current process...")
                    sys.exit(0)
                elif sys.platform == "win32":
                    # Windows restart logic for production
                    print("🖥️  Windows platform detected")
                    subprocess.Popen([
                        sys.executable, current_script
                    ], cwd=os.getcwd())
                    time.sleep(2)
                    os.kill(current_pid, signal.SIGTERM)
                else:
                    # Linux/macOS restart logic for production
                    print("🐧 Unix-like platform detected")
                    os.execv(sys.executable, [sys.executable, current_script])
                    
            except Exception as e:
                print(f"❌ Restart failed: {e}")
                # Log the error but don't crash the update service
                try:
                    with self._ensure_app_context():
                        status = AppUpdateStatus.query.first()
                        if status:
                            status.last_error = f"Restart failed: {str(e)[:2000]}"
                            db.session.commit()
                except:
                    pass
        
        # Start restart timer in background thread
        self._restart_timer = threading.Thread(target=restart_application, daemon=True)
        self._restart_timer.start()
        print(f"✅ Restart scheduled in {delay_seconds} seconds")

    def _config(self, key, default=None):
        if self.app:
            return self.app.config.get(key, default)
        return current_app.config.get(key, default)
