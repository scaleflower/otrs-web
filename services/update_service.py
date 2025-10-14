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
from packaging import version

import requests
from flask import current_app

from models import db, AppUpdateStatus
from models.update_log import UpdateLog, UpdateStepLog, UpdateLogStatus, UpdateLogStep, init_update_log_models
from utils.update_package import (
    ReleaseDownloadError,
    ReleasePackageManager,
    PackageExtractionError,
)
# 添加对阿里云云效的支持
from utils.yunxiao_update_package import (
    YunxiaoReleaseDownloadError,
    YunxiaoReleasePackageManager,
    YunxiaoPackageExtractionError,
)
from services import system_config_service


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
            # 添加云效相关配置
            payload['update_source'] = self._config('APP_UPDATE_SOURCE', 'github')  # github or yunxiao
            payload['update_use_ssh'] = self._config('APP_UPDATE_USE_SSH', False)   # 是否使用SSH方式
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
        """Manually check for updates from GitHub Releases or Yunxiao"""
        if not self._config('APP_UPDATE_ENABLED', True):
            return {'success': False, 'error': 'Auto-update disabled'}

        # 检查更新源配置
        update_source = self._config('APP_UPDATE_SOURCE', 'github')
        
        # 如果配置为同时检查两个源
        if update_source == 'both':
            return self._check_both_updates()
        elif update_source == 'yunxiao':
            return self._check_yunxiao_updates()
        else:
            return self._check_github_updates()

    def _check_both_updates(self):
        """同时检查GitHub和云效的更新"""
        github_result = self._check_github_updates()
        yunxiao_result = self._check_yunxiao_updates()
        
        # 如果任一检查失败，返回错误
        if not github_result.get('success', False):
            return github_result
        if not yunxiao_result.get('success', False):
            return yunxiao_result
            
        # 合并两个结果
        combined_result = {
            'success': True,
            'status': 'multiple_updates_available',
            'sources': {
                'github': github_result,
                'yunxiao': yunxiao_result
            },
            'message': '检查完成，可从多个源中选择更新'
        }
        
        return combined_result

    def _check_github_updates(self):
        """检查GitHub更新"""
        with self._ensure_app_context():
            repo = self._config('APP_UPDATE_REPO')
            # 使用system_config_service实例获取GitHub Token
            try:
                from services import system_config_service
                token = system_config_service.get_config_value('APP_UPDATE_GITHUB_TOKEN')
            except Exception:
                token = None
            
            # 构建请求头，即使没有token也继续执行
            headers = {
                'Accept': 'application/vnd.github+json',
                'User-Agent': 'otrs-web-update-service'
            }
            
            # 如果有token则添加到请求头
            if token and token != 'your_github_token_here':
                headers['Authorization'] = f'Bearer {token}'
            elif token == 'your_github_token_here':
                print("⚠️  检测到默认的GitHub Token，请设置有效的APP_UPDATE_GITHUB_TOKEN环境变量以避免速率限制")

            status = AppUpdateStatus.query.first()
            if not status:
                status = AppUpdateStatus(current_version=self._config('APP_VERSION', '0.0.0'))
                db.session.add(status)

            # 首先尝试获取最新的Release
            url = f'https://api.github.com/repos/{repo}/releases/latest'
            try:
                response = requests.get(url, headers=headers, timeout=10)
                if response.status_code == 200:
                    payload = response.json()
                    latest_version = payload.get('tag_name', '').lstrip('v')
                    if latest_version:
                        # 处理成功获取Release的情况
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
                                'source': 'github',
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
                                'source': 'github',
                                'message': 'You are using the latest version'
                            }
            except requests.RequestException as err:
                print(f"❌ Failed to contact GitHub Releases: {err}")
            
            # 如果获取Release失败，尝试获取最新的标签
            url = f'https://api.github.com/repos/{repo}/tags'
            try:
                response = requests.get(url, headers=headers, timeout=10)
                if response.status_code == 200:
                    tags = response.json()
                    if tags:
                        # 获取第一个标签作为最新标签（GitHub API返回按时间倒序排列）
                        latest_tag = tags[0]
                        latest_version = latest_tag.get('name', '').lstrip('v')
                        if latest_version:
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
                                    'tag_name': latest_tag.get('name'),
                                    'source': 'github',
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
                                    'source': 'github',
                                    'message': 'You are using the latest version'
                                }
            except requests.RequestException as err:
                error_msg = f'Failed to contact GitHub: {err}'
                print(f"❌ {error_msg}")
                return {
                    'success': False,
                    'error': error_msg
                }
            
            # 如果API返回401错误，说明Token无效
            if response.status_code == 401:
                print("❌ GitHub API error 401: Bad credentials")
                return {
                    'success': False,
                    'error': 'GitHub API error 401: Bad credentials',
                    'status_code': 401
                }
            
            # 如果API速率受限
            if response.status_code == 403 and 'rate limit' in response.text.lower():
                print("⚠️  GitHub API rate limit exceeded")
                return {
                    'success': False,
                    'error': 'GitHub API rate limit exceeded',
                    'status_code': 403
                }

            if response.status_code != 200:
                error_msg = f'GitHub API request failed with status {response.status_code}'
                print(f"❌ {error_msg}")
                return {
                    'success': False,
                    'error': error_msg,
                    'status_code': response.status_code
                }

            error_msg = 'Invalid data received from GitHub'
            print(f"❌ {error_msg}")
            return {
                'success': False,
                'error': error_msg
            }

    def _check_yunxiao_updates(self):
        """检查阿里云云效更新"""
        with self._ensure_app_context():
            repo = self._config('APP_UPDATE_REPO')
            token = self._config('APP_UPDATE_YUNXIAO_TOKEN')
            use_ssh = self._config('APP_UPDATE_USE_SSH', False)
            
            # 如果使用SSH方式，不需要token
            if not use_ssh:
                if not token:
                    print("⚠️  未配置云效访问Token，可能遇到API速率限制")
            else:
                print("🔐 使用SSH方式进行代码拉取")

            status = AppUpdateStatus.query.first()
            if not status:
                status = AppUpdateStatus(current_version=self._config('APP_VERSION', '0.0.0'))
                db.session.add(status)

            # 创建云效包管理器实例
            manager = YunxiaoReleasePackageManager(
                repo=repo,
                token=token,
                project_root=Path(self.app.root_path),
                download_root=Path(self.app.instance_path) / 'releases',
                use_ssh=use_ssh  # 传递SSH使用标志
            )

            # 获取更新信息
            try:
                metadata = manager.fetch_release_metadata(None)
            except YunxiaoReleaseDownloadError as err:
                error_msg = f'Failed to contact Aliyun Yunxiao: {err}'
                self._record_error(error_msg)
                return {'success': False, 'error': error_msg}

            latest_version = metadata.tag_name
            if not latest_version:
                error_msg = 'Missing tag_name in Yunxiao release payload'
                self._record_error(error_msg)
                return {'success': False, 'error': error_msg}

            status.latest_version = latest_version
            status.release_name = metadata.name
            status.release_body = metadata.body
            status.release_url = metadata.html_url
            status.published_at = self._parse_datetime(metadata.published_at)
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
                    'release_name': metadata.name,
                    'release_notes': metadata.body,
                    'release_url': metadata.html_url,
                    'published_at': self._format_datetime(metadata.published_at),
                    'source': 'yunxiao',
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
                    'source': 'yunxiao',
                    'message': 'You are using the latest version'
                }

    def trigger_update(self, target_version: Optional[str] = None, force_reinstall: bool = False, source: str = 'github'):
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
                print(f"🔄 强制重新安装版本 {target}")
            elif target_version == current_version:
                raise RuntimeError(f'Already using version {target_version}. Use force reinstall to reapply')

            # 记录更新日志
            update_id = str(uuid.uuid4())
            update_log = UpdateLog(
                update_id=update_id,
                target_version=target,
                source=source,  # 记录更新源
                force_reinstall=force_reinstall
            )
            db.session.add(update_log)
            db.session.flush()  # 获取update_log.id

            # 定义更新步骤
            update_steps = [
                (UpdateLogStep.BACKUP_DATABASE.value, "备份数据库", 1),
                (UpdateLogStep.FETCH_REPOSITORY.value, "获取版本元数据", 2),
                (UpdateLogStep.CHECKOUT_VERSION.value, "下载更新包", 3),
                (UpdateLogStep.PULL_CHANGES.value, "同步更新文件", 4),
                (UpdateLogStep.INSTALL_DEPENDENCIES.value, "安装依赖包", 5),
                (UpdateLogStep.RUN_MIGRATIONS.value, "执行数据库迁移", 6),
                (UpdateLogStep.RESTART_APPLICATION.value, "重启应用程序", 7)
            ]
            
            # 为每个步骤创建UpdateStepLog记录
            for step_name, step_description, step_order in update_steps:
                step_log = UpdateStepLog(
                    update_log_id=update_log.id,
                    step_name=step_name,
                    step_order=step_order
                )
                db.session.add(step_log)

            db.session.commit()
            
            # 发送更新开始事件
            self._send_update_start_event(update_log)

            # 启动后台更新线程
            self._update_thread = threading.Thread(
                target=self._execute_update,
                args=(target, force_reinstall, source, update_log.id),
                daemon=True
            )
            self._update_thread.start()

            return {
                'success': True,
                'message': f'Update to version {target} started',
                'update_log_id': update_log.id
            }

    def _send_update_start_event(self, update_log: UpdateLog):
        """Send update start event for real-time updates"""
        try:
            import json
            from pathlib import Path
            
            progress_dir = Path('db') / 'update_progress'
            progress_dir.mkdir(exist_ok=True)
            
            progress_file = progress_dir / f"{update_log.id}_start.json"
            progress_data = {
                'update_log_id': update_log.id,
                'status': 'started',
                'target_version': update_log.target_version,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            with open(progress_file, 'w', encoding='utf-8') as f:
                json.dump(progress_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"⚠️ Warning: Failed to send update start event: {e}")

    def _execute_update(self, target_version: str, force_reinstall: bool, source: str, update_log_id: str):
        """Execute the actual update process in background thread"""
        with self._ensure_app_context():
            try:
                # Get update log
                update_log = UpdateLog.query.filter_by(id=update_log_id).first()
                if not update_log:
                    print(f"❌ Update log not found for id: {update_log_id}")
                    return
                
                # Update system information
                update_log.system_platform = sys.platform
                update_log.python_version = sys.version.split()[0]
                db.session.commit()
                
                # Execute update with logging
                self._execute_update_with_logging(target_version, force_reinstall, source, update_log)
                
            except Exception as e:
                print(f"❌ Update job failed: {e}")
                import traceback
                traceback.print_exc()
                try:
                    update_log = UpdateLog.query.filter_by(id=update_log_id).first()
                    if update_log:
                        update_log.mark_failed(f"Update job execution failed: {str(e)}")
                        db.session.commit()
                except:
                    pass

    def _execute_update_with_logging(self, target_version: str, force_reinstall: bool, source: str, update_log: UpdateLog):
        """Execute update with detailed step logging"""
        repo = self._config('APP_UPDATE_REPO')
        project_root = Path.cwd()
        download_dir = self._resolve_download_dir(project_root)
        preserve_paths = self._resolve_preserve_paths()
        token = self._config('APP_UPDATE_GITHUB_TOKEN')
        env = os.environ.copy()
        if token and token != 'your_github_token_here':
            env['GITHUB_TOKEN'] = token

        manager = ReleasePackageManager(
            repo=repo,
            token=token if token != 'your_github_token_here' else None,  # 只有在token有效时才传递
            project_root=project_root,
            download_root=download_dir,
            preserve_paths=preserve_paths,
        )

        try:
            # Step 1: backup database
            self._send_step_start_event(update_log, UpdateLogStep.BACKUP_DATABASE.value)
            backup_candidates = [
                project_root / 'db' / 'otrs_data.db',
                project_root / 'instance' / 'otrs_web.db',
            ]
            backup_dir = project_root / (self._config('BACKUP_FOLDER', 'database_backups') or 'database_backups')
            backup_path = manager.backup_database(backup_candidates, backup_dir)
            backup_message = f'数据库备份完成: {backup_path.name}' if backup_path else '未检测到数据库文件，跳过备份'
            self._update_step_status(update_log, UpdateLogStep.BACKUP_DATABASE.value, backup_message)

            # Step 2: fetch release metadata
            self._send_step_start_event(update_log, UpdateLogStep.FETCH_REPOSITORY.value)
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
            self._send_step_start_event(update_log, UpdateLogStep.CHECKOUT_VERSION.value)
            archive_path = manager.download_release_archive(metadata, resolved_target)
            self._update_step_status(
                update_log,
                UpdateLogStep.CHECKOUT_VERSION.value,
                f'下载更新包成功: {archive_path.name}',
            )

            # Step 4: extract and sync files
            self._send_step_start_event(update_log, UpdateLogStep.PULL_CHANGES.value)
            source_root = manager.extract_archive(archive_path)
            manager.sync_to_project(source_root)
            self._update_step_status(
                update_log,
                UpdateLogStep.PULL_CHANGES.value,
                '更新包解压并同步到项目目录完成',
            )

            # Step 5: install dependencies (optional)
            self._send_step_start_event(update_log, UpdateLogStep.INSTALL_DEPENDENCIES.value)
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
            self._send_step_start_event(update_log, UpdateLogStep.RUN_MIGRATIONS.value)
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
            import traceback
            traceback.print_exc()
            self._finalize_failure_with_logging(update_log, f'Update execution error: {err}')

    def _send_step_start_event(self, update_log: UpdateLog, step_name: str):
        """Send step start event for real-time updates"""
        try:
            import json
            from pathlib import Path
            
            progress_dir = Path('db') / 'update_progress'
            progress_dir.mkdir(exist_ok=True)
            
            progress_file = progress_dir / f"{update_log.id}.json"
            progress_data = {
                'update_log_id': update_log.id,
                'step_name': step_name,
                'status': 'started',
                'timestamp': datetime.utcnow().isoformat()
            }
            
            with open(progress_file, 'w', encoding='utf-8') as f:
                json.dump(progress_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"⚠️ Warning: Failed to send step start event: {e}")

    def is_update_running(self):
        """Check if an update is currently running"""
        thread = self._update_thread
        return bool(thread and thread.is_alive())

    def _ensure_app_context(self):
        """Ensure we have a Flask app context"""
        if not self.app:
            raise RuntimeError('UpdateService is not initialized with Flask app')
        return self.app.app_context()

    @staticmethod
    def _parse_datetime(value):
        """Parse datetime from string"""
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
        """比较语义化版本号，使用packaging库进行可靠比较"""
        if current == latest:
            return False  # 版本相同，不需要更新
        
        try:
            # 使用packaging.version进行版本比较
            current_ver = version.parse(current)
            latest_ver = version.parse(latest)
            return latest_ver > current_ver
        except version.InvalidVersion:
            # 如果无法解析为标准版本号，回退到原始比较逻辑
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
            current_parts = [int(x) for x in current_clean.split('.')]
            latest_parts = [int(x) for x in latest_clean.split('.')]
            
            # 按段比较版本号
            for current_part, latest_part in zip(current_parts, latest_parts):
                if latest_part > current_part:
                    return True
                if latest_part < current_part:
                    return False
            
            # 如果前面的段都相同，但latest有更多段，则认为是更新的版本
            return len(latest_parts) > len(current_parts)

    def _record_error(self, message: str):
        """Record error in update status"""
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

    def _update_step_status(self, update_log: UpdateLog, step_name: str, output: str = ''):
        """Update step status in update log"""
        step_log = UpdateStepLog.query.filter_by(
            update_log_id=update_log.id, 
            step_name=step_name
        ).first()
        
        if step_log:
            step_log.mark_completed(output)
            update_log.completed_steps += 1
            db.session.commit()
            print(f"✅ Step completed: {step_name}")
            
            # 发送实时更新事件
            self._send_progress_event(update_log, step_log, 'completed', output)

    def _mark_step_completed(self, update_log: UpdateLog, step_name: str, output: str = ''):
        """Mark step as completed in update log"""
        self._update_step_status(update_log, step_name, output)

    def _send_progress_event(self, update_log: UpdateLog, step_log: UpdateStepLog, status: str, output: str = ''):
        """Send progress event for real-time updates"""
        try:
            # 这里可以集成WebSocket或其他实时通信机制
            # 当前实现使用简单的文件方式存储进度，供前端轮询获取
            import json
            from pathlib import Path
            
            progress_dir = Path('db') / 'update_progress'
            progress_dir.mkdir(exist_ok=True)
            
            progress_file = progress_dir / f"{update_log.id}.json"
            progress_data = {
                'update_log_id': update_log.id,
                'step_name': step_log.step_name,
                'step_order': step_log.step_order,
                'status': status,
                'output': output,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            with open(progress_file, 'w', encoding='utf-8') as f:
                json.dump(progress_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            # 忽略进度更新错误，不影响主流程
            print(f"⚠️ Warning: Failed to send progress event: {e}")

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
        
        # 清理进度文件
        self._cleanup_progress_files(update_log.id)
        
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
        
        # 清理进度文件
        self._cleanup_progress_files(update_log.id)

    def _cleanup_progress_files(self, update_log_id: int):
        """Clean up progress files"""
        try:
            from pathlib import Path
            import os
            
            progress_dir = Path('db') / 'update_progress'
            if progress_dir.exists():
                # 删除与该更新相关的所有进度文件
                for progress_file in progress_dir.glob(f"{update_log_id}*.json"):
                    try:
                        os.remove(progress_file)
                    except Exception:
                        pass  # 忽略删除错误
        except Exception:
            pass  # 忽略清理错误

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
            log = UpdateLog.query.filter_by(id=update_id).first()
            if not log:
                return None
            
            log_data = log.to_dict()
            log_data['steps'] = [step.to_dict() for step in log.steps]
            return log_data

    def _config(self, key, default=None):
        """Get configuration value"""
        # 尝试在应用上下文中从系统配置服务获取配置
        try:
            from services import system_config_service
            db_value = system_config_service.get_config_value(key)
            if db_value is not None:
                return db_value
        except:
            # 如果无法获取数据库配置，则继续使用应用配置
            pass
            
        # 然后从应用配置获取
        if self.app:
            return self.app.config.get(key, default)
        return current_app.config.get(key, default)