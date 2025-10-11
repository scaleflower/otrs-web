"""Service for handling application auto-update lifecycle."""

import json
import os
import re
import signal
import subprocess
import sys
import threading
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List

import requests
from flask import current_app

from models import db, AppUpdateStatus
from models.update_log import UpdateLog, UpdateStepLog, UpdateLogStatus, UpdateLogStep, init_update_log_models
from utils.update_package import (
    ReleaseDownloadError,
    ReleasePackageManager,
    PackageExtractionError,
)


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

    def trigger_update(self, target_version: Optional[str] = None, force_reinstall: bool = False):
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

            # 获取当前版本
            current_version = status.current_version or '0.0.0'

            # 检查是否强制重新安装当前版本
            if force_reinstall:
                print(f"🔄 Forced reinstall of current version: {target}")
            else:
                # 正常更新检查：如果目标版本与当前版本相同，不允许更新
                if target == current_version and not force_reinstall:
                    raise RuntimeError(f'Already using version {target}. Use force_reinstall=True to reinstall.')

            # 创建更新日志记录
            update_log = self._create_update_log(target, current_version, force_reinstall)
            
            status.status = 'updating'
            status.last_update_started_at = datetime.utcnow()
            status.last_error = None
            db.session.commit()

            thread = threading.Thread(target=self._run_update_job_with_logging, args=(target, force_reinstall, update_log.update_id), daemon=True)
            thread.start()
            self._update_thread = thread
            return {
                'message': 'Update started', 
                'target_version': target, 
                'force_reinstall': force_reinstall,
                'update_id': update_log.update_id
            }

    def is_update_running(self) -> bool:
        thread = self._update_thread
        return bool(thread and thread.is_alive())

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
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
            # 对于复杂版本格式，如果清理后的版本不同，应该允许更新
            return latest_clean != current_clean

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

    def _create_update_log(self, target_version: str, current_version: str, force_reinstall: bool) -> UpdateLog:
        """Create a new update log record"""
        update_id = str(uuid.uuid4())
        
        update_log = UpdateLog(
            update_id=update_id,
            target_version=target_version,
            current_version=current_version,
            force_reinstall=force_reinstall,
            system_platform=sys.platform,
            python_version=sys.version.split()[0]
        )
        
        # Define update steps
        update_steps = [
            (UpdateLogStep.BACKUP_DATABASE.value, "备份数据库", 1),
            (UpdateLogStep.FETCH_REPOSITORY.value, "获取版本元数据", 2),
            (UpdateLogStep.CHECKOUT_VERSION.value, "下载更新包", 3),
            (UpdateLogStep.PULL_CHANGES.value, "同步更新文件", 4),
            (UpdateLogStep.INSTALL_DEPENDENCIES.value, "安装依赖包", 5),
            (UpdateLogStep.RUN_MIGRATIONS.value, "执行数据库迁移", 6),
            (UpdateLogStep.RESTART_APPLICATION.value, "重启应用程序", 7)
        ]
        
        update_log.total_steps = len(update_steps)
        
        db.session.add(update_log)
        db.session.commit()
        
        # Create step records
        for step_name, step_description, step_order in update_steps:
            step_log = UpdateStepLog(
                update_log_id=update_log.id,
                step_name=step_name,
                step_order=step_order
            )
            db.session.add(step_log)
        
        db.session.commit()
        return update_log

    def _run_update_job_with_logging(self, target_version: str, force_reinstall: bool, update_id: str):
        """Run update job with detailed logging"""
        with self._ensure_app_context():
            try:
                # Get update log
                update_log = UpdateLog.query.filter_by(update_id=update_id).first()
                if not update_log:
                    print(f"❌ Update log not found for update_id: {update_id}")
                    return
                
                # Update system information
                update_log.system_platform = sys.platform
                update_log.python_version = sys.version.split()[0]
                db.session.commit()
                
                # Execute update with logging
                self._execute_update_with_logging(target_version, force_reinstall, update_log)
                
            except Exception as e:
                print(f"❌ Update job failed: {e}")
                try:
                    update_log = UpdateLog.query.filter_by(update_id=update_id).first()
                    if update_log:
                        update_log.mark_failed(f"Update job execution failed: {str(e)}")
                        db.session.commit()
                except:
                    pass

    def _execute_update_with_logging(self, target_version: str, force_reinstall: bool, update_log: UpdateLog):
        """Execute update with detailed step logging"""
        repo = self._config('APP_UPDATE_REPO')
        project_root = Path.cwd()
        download_dir = self._resolve_download_dir(project_root)
        preserve_paths = self._resolve_preserve_paths()
        token = self._config('APP_UPDATE_GITHUB_TOKEN')
        env = os.environ.copy()
        if token:
            env['GITHUB_TOKEN'] = token

        manager = ReleasePackageManager(
            repo=repo,
            token=token,
            project_root=project_root,
            download_root=download_dir,
            preserve_paths=preserve_paths,
        )

        try:
            # Step 1: backup database
            backup_candidates = [
                project_root / 'db' / 'otrs_data.db',
                project_root / 'instance' / 'otrs_web.db',
            ]
            backup_dir = project_root / (self._config('BACKUP_FOLDER', 'database_backups') or 'database_backups')
            backup_path = manager.backup_database(backup_candidates, backup_dir)
            backup_message = f'数据库备份完成: {backup_path.name}' if backup_path else '未检测到数据库文件，跳过备份'
            self._update_step_status(update_log, UpdateLogStep.BACKUP_DATABASE.value, backup_message)

            # Step 2: fetch release metadata
            metadata = manager.fetch_release_metadata(target_version)
            resolved_target = metadata.tag_name or target_version
            if resolved_target and update_log.target_version != resolved_target:
                update_log.target_version = resolved_target
                db.session.commit()
            status = AppUpdateStatus.query.first()
            if status:
                status.latest_version = metadata.tag_name or resolved_target
                status.release_name = metadata.name
                status.release_body = metadata.body
                status.release_url = metadata.html_url
                status.published_at = self._parse_datetime(metadata.published_at)
                db.session.commit()
            self._update_step_status(
                update_log,
                UpdateLogStep.FETCH_REPOSITORY.value,
                f'获取版本元数据成功: {resolved_target}',
            )

            # Step 3: download archive
            archive_path = manager.download_release_archive(metadata, resolved_target)
            self._update_step_status(
                update_log,
                UpdateLogStep.CHECKOUT_VERSION.value,
                f'下载更新包成功: {archive_path.name}',
            )

            # Step 4: extract and sync files
            source_root = manager.extract_archive(archive_path)
            manager.sync_to_project(source_root)
            self._update_step_status(
                update_log,
                UpdateLogStep.PULL_CHANGES.value,
                '更新包解压并同步到项目目录完成',
            )

            # Step 5: install dependencies (optional)
            install_deps = self._config_bool('APP_UPDATE_INSTALL_DEPENDENCIES', default=True)
            if install_deps:
                pip_command = [sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt']
                extra_args = self._config('APP_UPDATE_PIP_ARGS')
                if extra_args:
                    pip_command.extend(extra_args.split())
                manager.install_dependencies(pip_command, env=env)
                deps_message = '依赖安装完成'
            else:
                deps_message = '根据配置跳过依赖安装'
            self._update_step_status(
                update_log,
                UpdateLogStep.INSTALL_DEPENDENCIES.value,
                deps_message,
            )

            # Step 6: run migrations (optional)
            run_migrations = self._config_bool('APP_UPDATE_RUN_MIGRATIONS', default=True)
            migration_outputs = []
            if run_migrations:
                migration_scripts = self._resolve_migration_scripts(project_root)
                for script_path in migration_scripts:
                    if script_path.exists():
                        manager.run_migration(script_path, env=env)
                        migration_outputs.append(f'执行迁移脚本: {script_path.name}')
                if not migration_outputs:
                    migration_outputs.append('未发现迁移脚本')
            else:
                migration_outputs.append('根据配置跳过迁移')
            self._update_step_status(
                update_log,
                UpdateLogStep.RUN_MIGRATIONS.value,
                '; '.join(migration_outputs),
            )

            # Finalize
            self._finalize_success_with_logging(update_log, resolved_target)

        except (ReleaseDownloadError, PackageExtractionError, RuntimeError) as err:
            self._finalize_failure_with_logging(update_log, str(err))
        except Exception as err:  # pragma: no cover - unexpected error path
            self._finalize_failure_with_logging(update_log, f'Update execution error: {err}')

    def _update_step_status(self, update_log: UpdateLog, step_name: str, output: str = None):
        """Update step status in the log"""
        step_log = UpdateStepLog.query.filter_by(
            update_log_id=update_log.id, 
            step_name=step_name
        ).first()
        
        if step_log:
            step_log.mark_completed(output)
            update_log.completed_steps += 1
            db.session.commit()
            print(f"✅ Step completed: {step_name}")

    def _resolve_download_dir(self, project_root: Path) -> Path:
        """Resolve download directory from configuration"""
        raw_path = self._config('APP_UPDATE_DOWNLOAD_DIR')
        if not raw_path:
            return (project_root / 'instance' / 'releases').resolve()
        candidate = Path(raw_path)
        if not candidate.is_absolute():
            candidate = project_root / candidate
        return candidate.resolve()

    def _resolve_preserve_paths(self) -> List[str]:
        """Load preserve paths list from configuration"""
        raw = self._config('APP_UPDATE_PRESERVE_PATHS', '.env,uploads,database_backups,logs,db/otrs_data.db')
        if isinstance(raw, (list, tuple)):
            return [str(item).strip() for item in raw if str(item).strip()]
        if not raw:
            return []
        return [segment.strip() for segment in str(raw).split(',') if segment.strip()]

    def _resolve_migration_scripts(self, project_root: Path) -> List[Path]:
        """Determine migration scripts to execute after update"""
        raw = self._config('APP_UPDATE_MIGRATION_SCRIPTS')
        scripts: List[Path] = []
        if raw:
            candidates = raw if isinstance(raw, (list, tuple)) else str(raw).split(',')
            for entry in candidates:
                entry_str = str(entry).strip()
                if not entry_str:
                    continue
                path = Path(entry_str)
                if not path.is_absolute():
                    path = project_root / path
                scripts.append(path)
        else:
            scripts = [
                project_root / 'upgrade_statistics_log_columns.py',
                project_root / 'upgrade_database_with_new_records_count.py'
            ]
        return scripts

    def _config_bool(self, key: str, default: bool = False) -> bool:
        """Helper to read boolean configuration values"""
        value = self._config(key)
        if value is None:
            return default
        if isinstance(value, bool):
            return value
        return str(value).strip().lower() in ('1', 'true', 'yes', 'on')

    def _finalize_success_with_logging(self, update_log: UpdateLog, target_version: str):
        """Finalize successful update with logging"""
        # Update AppUpdateStatus
        status = AppUpdateStatus.query.first()
        if status:
            status.current_version = target_version
            status.status = 'restarting'
            status.last_update_completed_at = datetime.utcnow()
        
        self._update_step_status(
            update_log,
            UpdateLogStep.RESTART_APPLICATION.value,
            '已计划应用重启',
        )
        
        # Update log
        update_log.mark_completed()
        
        # Try to get commit information
        try:
            self._capture_commit_info(update_log)
        except Exception as e:
            print(f"⚠️ Failed to capture commit info: {e}")
        
        db.session.commit()
        
        delay = max(1, int(self._config('APP_UPDATE_RESTART_DELAY', 5) or 5))
        self._schedule_restart(delay)

    def _finalize_failure_with_logging(self, update_log: UpdateLog, message: str):
        """Finalize failed update with logging"""
        # Update AppUpdateStatus
        status = AppUpdateStatus.query.first()
        if status:
            status.status = 'update_failed'
            status.last_error = message[:2000]
            status.last_update_completed_at = datetime.utcnow()
        
        # Update log
        update_log.mark_failed(message)
        
        db.session.commit()

    def _capture_commit_info(self, update_log: UpdateLog):
        """Capture current commit information"""
        try:
            result = subprocess.run(
                ['git', 'log', '-1', '--pretty=format:%H|%s|%an|%ai'],
                capture_output=True,
                text=True,
                cwd=Path.cwd(),
                check=True
            )
            
            if result.stdout:
                commit_hash, message, author, date_str = result.stdout.split('|', 3)
                commit_date = datetime.fromisoformat(date_str.replace(' ', 'T'))
                
                update_log.set_commit_info(commit_hash, message, author, commit_date)
                
        except Exception as e:
            print(f"⚠️ Failed to capture commit info: {e}")

    def get_update_logs(self, limit: int = 50) -> List[Dict]:
        """Get recent update logs"""
        with self._ensure_app_context():
            logs = UpdateLog.query.order_by(UpdateLog.started_at.desc()).limit(limit).all()
            return [log.to_dict() for log in logs]

    def get_update_log_details(self, update_id: str) -> Optional[Dict]:
        """Get detailed update log with steps"""
        with self._ensure_app_context():
            log = UpdateLog.query.filter_by(update_id=update_id).first()
            if not log:
                return None
            
            log_data = log.to_dict()
            log_data['steps'] = [step.to_dict() for step in log.steps]
            return log_data

    def _config(self, key, default=None):
        if self.app:
            return self.app.config.get(key, default)
        return current_app.config.get(key, default)
