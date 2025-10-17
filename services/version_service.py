"""
Version Management Service - Handles version detection and comparison
"""

import requests
import os
from packaging import version as pkg_version
from datetime import datetime, timedelta


class VersionService:
    """Service for handling version detection and comparison"""

    def __init__(self, app=None):
        self.app = app
        self.current_version = None
        self.github_repo = None
        self.yunxiao_repo = None
        self.cache_duration = timedelta(hours=1)
        self.last_check = None
        self.cached_latest_version = None

        if app:
            self.init_app(app)

    def init_app(self, app):
        """Initialize service with Flask app"""
        self.app = app
        self.current_version = app.config.get('APP_VERSION', '1.0.0')
        self.github_repo = os.environ.get('APP_UPDATE_REPO', 'scaleflower/otrs-web')
        self.yunxiao_repo = os.environ.get('APP_UPDATE_YUNXIAO_REPO', '')

    def get_current_version(self):
        """Get current application version"""
        return self.current_version

    def compare_versions(self, version1, version2):
        """
        Compare two version strings
        Returns: -1 if version1 < version2, 0 if equal, 1 if version1 > version2
        """
        try:
            v1 = pkg_version.parse(version1)
            v2 = pkg_version.parse(version2)

            if v1 < v2:
                return -1
            elif v1 > v2:
                return 1
            else:
                return 0
        except Exception as e:
            print(f"Error comparing versions: {e}")
            return 0

    def check_for_updates(self, force=False):
        """
        Check if a new version is available
        Returns: dict with update information
        """
        # Use cache if available and not expired
        if not force and self.cached_latest_version and self.last_check:
            if datetime.now() - self.last_check < self.cache_duration:
                return self._prepare_update_info(self.cached_latest_version)

        # Get latest version from configured source
        update_source = os.environ.get('APP_UPDATE_SOURCE', 'github')

        if update_source == 'yunxiao':
            latest_info = self._get_latest_from_yunxiao()
        else:
            latest_info = self._get_latest_from_github()

        if latest_info:
            self.cached_latest_version = latest_info
            self.last_check = datetime.now()

        return self._prepare_update_info(latest_info)

    def _get_latest_from_github(self):
        """Get latest release information from GitHub"""
        try:
            api_url = f"https://api.github.com/repos/{self.github_repo}/releases/latest"
            headers = {}

            # Add GitHub token if available
            github_token = os.environ.get('APP_UPDATE_GITHUB_TOKEN')
            if github_token:
                headers['Authorization'] = f'token {github_token}'

            response = requests.get(api_url, headers=headers, timeout=10)
            response.raise_for_status()

            data = response.json()

            return {
                'version': data['tag_name'].lstrip('v'),
                'name': data['name'],
                'body': data['body'],
                'published_at': data['published_at'],
                'html_url': data['html_url'],
                'tarball_url': data['tarball_url'],
                'zipball_url': data['zipball_url'],
                'source': 'github'
            }

        except requests.exceptions.RequestException as e:
            print(f"Error fetching GitHub releases: {e}")
            return None
        except Exception as e:
            print(f"Error parsing GitHub release data: {e}")
            return None

    def _get_latest_from_yunxiao(self):
        """Get latest release information from Yunxiao (Aliyun Codeup)"""
        try:
            # Yunxiao API endpoint for tags
            api_url = f"https://codeup.aliyun.com/api/v4/projects/{self.yunxiao_repo}/repository/tags"
            headers = {}

            # Add Yunxiao token if available
            yunxiao_token = os.environ.get('APP_UPDATE_YUNXIAO_TOKEN')
            if yunxiao_token:
                headers['PRIVATE-TOKEN'] = yunxiao_token

            response = requests.get(api_url, headers=headers, timeout=10)
            response.raise_for_status()

            data = response.json()

            if data and len(data) > 0:
                latest = data[0]  # First tag is the latest

                return {
                    'version': latest['name'].lstrip('v'),
                    'name': latest['name'],
                    'body': latest.get('message', ''),
                    'published_at': latest.get('commit', {}).get('created_at', ''),
                    'html_url': f"https://codeup.aliyun.com/{self.yunxiao_repo}/-/tags/{latest['name']}",
                    'tarball_url': f"https://codeup.aliyun.com/{self.yunxiao_repo}/-/archive/{latest['name']}/{latest['name']}.tar.gz",
                    'zipball_url': f"https://codeup.aliyun.com/{self.yunxiao_repo}/-/archive/{latest['name']}/{latest['name']}.zip",
                    'source': 'yunxiao'
                }

            return None

        except requests.exceptions.RequestException as e:
            print(f"Error fetching Yunxiao tags: {e}")
            return None
        except Exception as e:
            print(f"Error parsing Yunxiao tag data: {e}")
            return None

    def _prepare_update_info(self, latest_info):
        """Prepare update information response"""
        if not latest_info:
            return {
                'update_available': False,
                'current_version': self.current_version,
                'latest_version': None,
                'error': 'Unable to fetch latest version information'
            }

        latest_version = latest_info['version']
        comparison = self.compare_versions(self.current_version, latest_version)

        return {
            'update_available': comparison < 0,
            'current_version': self.current_version,
            'latest_version': latest_version,
            'release_name': latest_info.get('name', ''),
            'release_notes': latest_info.get('body', ''),
            'published_at': latest_info.get('published_at', ''),
            'download_url': latest_info.get('html_url', ''),
            'tarball_url': latest_info.get('tarball_url', ''),
            'zipball_url': latest_info.get('zipball_url', ''),
            'source': latest_info.get('source', 'unknown'),
            'is_newer': comparison < 0,
            'is_same': comparison == 0,
            'is_older': comparison > 0
        }

    def get_version_history(self, limit=10):
        """Get version history from GitHub or Yunxiao"""
        update_source = os.environ.get('APP_UPDATE_SOURCE', 'github')

        if update_source == 'yunxiao':
            return self._get_version_history_from_yunxiao(limit)
        else:
            return self._get_version_history_from_github(limit)

    def _get_version_history_from_github(self, limit=10):
        """Get version history from GitHub releases"""
        try:
            api_url = f"https://api.github.com/repos/{self.github_repo}/releases"
            headers = {}

            github_token = os.environ.get('APP_UPDATE_GITHUB_TOKEN')
            if github_token:
                headers['Authorization'] = f'token {github_token}'

            params = {'per_page': limit}
            response = requests.get(api_url, headers=headers, params=params, timeout=10)
            response.raise_for_status()

            releases = response.json()

            history = []
            for release in releases:
                history.append({
                    'version': release['tag_name'].lstrip('v'),
                    'name': release['name'],
                    'body': release['body'],
                    'published_at': release['published_at'],
                    'html_url': release['html_url']
                })

            return history

        except Exception as e:
            print(f"Error fetching version history from GitHub: {e}")
            return []

    def _get_version_history_from_yunxiao(self, limit=10):
        """Get version history from Yunxiao tags"""
        try:
            api_url = f"https://codeup.aliyun.com/api/v4/projects/{self.yunxiao_repo}/repository/tags"
            headers = {}

            yunxiao_token = os.environ.get('APP_UPDATE_YUNXIAO_TOKEN')
            if yunxiao_token:
                headers['PRIVATE-TOKEN'] = yunxiao_token

            params = {'per_page': limit}
            response = requests.get(api_url, headers=headers, params=params, timeout=10)
            response.raise_for_status()

            tags = response.json()

            history = []
            for tag in tags:
                history.append({
                    'version': tag['name'].lstrip('v'),
                    'name': tag['name'],
                    'body': tag.get('message', ''),
                    'published_at': tag.get('commit', {}).get('created_at', ''),
                    'html_url': f"https://codeup.aliyun.com/{self.yunxiao_repo}/-/tags/{tag['name']}"
                })

            return history

        except Exception as e:
            print(f"Error fetching version history from Yunxiao: {e}")
            return []


# Global instance
version_service = VersionService()
