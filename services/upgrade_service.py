"""
Upgrade Service - Handles application upgrades
"""

import os
import shutil
import subprocess
import requests
import tempfile
import tarfile
import zipfile
from datetime import datetime
from pathlib import Path


class UpgradeService:
    """Service for handling application upgrades"""

    def __init__(self, app=None):
        self.app = app
        self.app_root = None
        self.backup_dir = None
        self.upgrade_log = []

        if app:
            self.init_app(app)

    def init_app(self, app):
        """Initialize service with Flask app"""
        self.app = app
        self.app_root = os.getcwd()
        self.backup_dir = os.path.join(self.app_root, 'upgrade_backups')
        os.makedirs(self.backup_dir, exist_ok=True)

    def log_message(self, message, level='INFO'):
        """Log upgrade message"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_entry = f"[{timestamp}] [{level}] {message}"
        self.upgrade_log.append(log_entry)
        print(log_entry)

    def get_upgrade_log(self):
        """Get current upgrade log"""
        return self.upgrade_log

    def clear_upgrade_log(self):
        """Clear upgrade log"""
        self.upgrade_log = []

    def create_backup(self):
        """Create backup of current application"""
        try:
            self.log_message("Creating backup of current application...")

            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_name = f"backup_{timestamp}"
            backup_path = os.path.join(self.backup_dir, backup_name)

            # Create backup directory
            os.makedirs(backup_path, exist_ok=True)

            # Files and directories to backup
            items_to_backup = [
                'app.py',
                'blueprints',
                'services',
                'models',
                'templates',
                'static',
                'config',
                'utils',
                'requirements.txt',
                '.env'
            ]

            for item in items_to_backup:
                src = os.path.join(self.app_root, item)
                if os.path.exists(src):
                    dst = os.path.join(backup_path, item)
                    if os.path.isdir(src):
                        shutil.copytree(src, dst, dirs_exist_ok=True)
                    else:
                        shutil.copy2(src, dst)

            self.log_message(f"Backup created successfully at: {backup_path}")
            return True, backup_path

        except Exception as e:
            self.log_message(f"Error creating backup: {e}", 'ERROR')
            return False, str(e)

    def download_release(self, download_url, is_tarball=True):
        """Download release package"""
        try:
            self.log_message(f"Downloading release from: {download_url}")

            response = requests.get(download_url, stream=True, timeout=300)
            response.raise_for_status()

            # Create temporary file
            suffix = '.tar.gz' if is_tarball else '.zip'
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
                for chunk in response.iter_content(chunk_size=8192):
                    tmp_file.write(chunk)
                tmp_path = tmp_file.name

            self.log_message(f"Release downloaded to: {tmp_path}")
            return True, tmp_path

        except Exception as e:
            self.log_message(f"Error downloading release: {e}", 'ERROR')
            return False, str(e)

    def extract_release(self, archive_path, extract_to):
        """Extract release archive"""
        try:
            self.log_message(f"Extracting release to: {extract_to}")

            os.makedirs(extract_to, exist_ok=True)

            if archive_path.endswith('.tar.gz'):
                with tarfile.open(archive_path, 'r:gz') as tar:
                    tar.extractall(extract_to)
            elif archive_path.endswith('.zip'):
                with zipfile.ZipFile(archive_path, 'r') as zip_ref:
                    zip_ref.extractall(extract_to)
            else:
                raise Exception("Unsupported archive format")

            # Find the extracted directory (usually has a prefix)
            extracted_dirs = [d for d in os.listdir(extract_to) if os.path.isdir(os.path.join(extract_to, d))]
            if extracted_dirs:
                actual_extract_path = os.path.join(extract_to, extracted_dirs[0])
                self.log_message(f"Release extracted to: {actual_extract_path}")
                return True, actual_extract_path
            else:
                return True, extract_to

        except Exception as e:
            self.log_message(f"Error extracting release: {e}", 'ERROR')
            return False, str(e)

    def install_dependencies(self, requirements_file):
        """Install Python dependencies"""
        try:
            self.log_message("Installing dependencies...")

            if not os.path.exists(requirements_file):
                self.log_message("requirements.txt not found, skipping dependency installation", 'WARNING')
                return True, "No requirements.txt found"

            result = subprocess.run(
                ['pip', 'install', '-r', requirements_file],
                capture_output=True,
                text=True,
                timeout=300
            )

            if result.returncode == 0:
                self.log_message("Dependencies installed successfully")
                return True, result.stdout
            else:
                self.log_message(f"Error installing dependencies: {result.stderr}", 'ERROR')
                return False, result.stderr

        except Exception as e:
            self.log_message(f"Error installing dependencies: {e}", 'ERROR')
            return False, str(e)

    def update_application_files(self, source_dir):
        """Update application files from extracted release"""
        try:
            self.log_message("Updating application files...")

            # Files and directories to update
            items_to_update = [
                'app.py',
                'blueprints',
                'services',
                'models',
                'templates',
                'static',
                'config',
                'utils',
                'requirements.txt'
            ]

            for item in items_to_update:
                src = os.path.join(source_dir, item)
                dst = os.path.join(self.app_root, item)

                if os.path.exists(src):
                    # Remove existing file/directory
                    if os.path.exists(dst):
                        if os.path.isdir(dst):
                            shutil.rmtree(dst)
                        else:
                            os.remove(dst)

                    # Copy new file/directory
                    if os.path.isdir(src):
                        shutil.copytree(src, dst)
                    else:
                        shutil.copy2(src, dst)

                    self.log_message(f"Updated: {item}")

            self.log_message("Application files updated successfully")
            return True, "Files updated"

        except Exception as e:
            self.log_message(f"Error updating files: {e}", 'ERROR')
            return False, str(e)

    def restore_backup(self, backup_path):
        """Restore application from backup"""
        try:
            self.log_message(f"Restoring backup from: {backup_path}")

            items_to_restore = [
                'app.py',
                'blueprints',
                'services',
                'models',
                'templates',
                'static',
                'config',
                'utils',
                'requirements.txt'
            ]

            for item in items_to_restore:
                src = os.path.join(backup_path, item)
                dst = os.path.join(self.app_root, item)

                if os.path.exists(src):
                    # Remove current file/directory
                    if os.path.exists(dst):
                        if os.path.isdir(dst):
                            shutil.rmtree(dst)
                        else:
                            os.remove(dst)

                    # Restore from backup
                    if os.path.isdir(src):
                        shutil.copytree(src, dst)
                    else:
                        shutil.copy2(src, dst)

            self.log_message("Backup restored successfully")
            return True, "Backup restored"

        except Exception as e:
            self.log_message(f"Error restoring backup: {e}", 'ERROR')
            return False, str(e)

    def perform_upgrade(self, download_url, is_tarball=True):
        """Perform complete upgrade process"""
        backup_path = None
        temp_extract_dir = None
        temp_archive = None

        try:
            self.clear_upgrade_log()
            self.log_message("=== Starting Upgrade Process ===")

            # Step 1: Create backup
            success, result = self.create_backup()
            if not success:
                return False, f"Backup failed: {result}"
            backup_path = result

            # Step 2: Download release
            success, result = self.download_release(download_url, is_tarball)
            if not success:
                return False, f"Download failed: {result}"
            temp_archive = result

            # Step 3: Extract release
            temp_extract_dir = tempfile.mkdtemp()
            success, result = self.extract_release(temp_archive, temp_extract_dir)
            if not success:
                return False, f"Extraction failed: {result}"
            extracted_path = result

            # Step 4: Install dependencies
            requirements_file = os.path.join(extracted_path, 'requirements.txt')
            success, result = self.install_dependencies(requirements_file)
            if not success:
                self.log_message("Dependency installation failed, rolling back...", 'ERROR')
                self.restore_backup(backup_path)
                return False, f"Dependency installation failed: {result}"

            # Step 5: Update application files
            success, result = self.update_application_files(extracted_path)
            if not success:
                self.log_message("File update failed, rolling back...", 'ERROR')
                self.restore_backup(backup_path)
                return False, f"File update failed: {result}"

            # Clean up temporary files
            if temp_archive and os.path.exists(temp_archive):
                os.remove(temp_archive)
            if temp_extract_dir and os.path.exists(temp_extract_dir):
                shutil.rmtree(temp_extract_dir)

            self.log_message("=== Upgrade Completed Successfully ===")
            self.log_message("Please restart the application to apply changes")

            return True, "Upgrade completed successfully. Please restart the application."

        except Exception as e:
            self.log_message(f"Unexpected error during upgrade: {e}", 'ERROR')

            # Attempt to restore backup
            if backup_path:
                self.log_message("Attempting to restore backup...", 'WARNING')
                self.restore_backup(backup_path)

            # Clean up temporary files
            if temp_archive and os.path.exists(temp_archive):
                os.remove(temp_archive)
            if temp_extract_dir and os.path.exists(temp_extract_dir):
                shutil.rmtree(temp_extract_dir)

            return False, f"Upgrade failed: {e}"

    def get_backup_list(self):
        """Get list of available backups"""
        try:
            backups = []
            if os.path.exists(self.backup_dir):
                for item in os.listdir(self.backup_dir):
                    item_path = os.path.join(self.backup_dir, item)
                    if os.path.isdir(item_path) and item.startswith('backup_'):
                        stat_info = os.stat(item_path)
                        backups.append({
                            'name': item,
                            'path': item_path,
                            'created_at': datetime.fromtimestamp(stat_info.st_mtime).strftime('%Y-%m-%d %H:%M:%S'),
                            'size': self._get_dir_size(item_path)
                        })

            # Sort by created_at descending
            backups.sort(key=lambda x: x['created_at'], reverse=True)
            return backups

        except Exception as e:
            print(f"Error getting backup list: {e}")
            return []

    def _get_dir_size(self, path):
        """Get directory size in bytes"""
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(path):
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                if os.path.exists(filepath):
                    total_size += os.path.getsize(filepath)
        return total_size


# Global instance
upgrade_service = UpgradeService()
