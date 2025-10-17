"""
Upgrade Blueprint - Handles upgrade management routes
"""

from flask import Blueprint, render_template, request, jsonify
from services import version_service, upgrade_service
import os

upgrade_bp = Blueprint('upgrade', __name__, url_prefix='/upgrade')


@upgrade_bp.route('/')
def upgrade_page():
    """Upgrade management page"""
    return render_template('upgrade.html')


@upgrade_bp.route('/api/check-update', methods=['GET'])
def api_check_update():
    """Check for available updates"""
    try:
        force = request.args.get('force', 'false').lower() == 'true'
        update_info = version_service.check_for_updates(force=force)

        return jsonify({
            'success': True,
            'data': update_info
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@upgrade_bp.route('/api/version-history', methods=['GET'])
def api_version_history():
    """Get version history"""
    try:
        limit = int(request.args.get('limit', 10))
        history = version_service.get_version_history(limit=limit)

        return jsonify({
            'success': True,
            'data': history
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@upgrade_bp.route('/api/start-upgrade', methods=['POST'])
def api_start_upgrade():
    """Start upgrade process"""
    try:
        data = request.get_json()
        download_url = data.get('download_url')
        is_tarball = data.get('is_tarball', True)

        if not download_url:
            return jsonify({
                'success': False,
                'error': 'Download URL is required'
            }), 400

        # Perform upgrade
        success, message = upgrade_service.perform_upgrade(download_url, is_tarball)

        return jsonify({
            'success': success,
            'message': message,
            'log': upgrade_service.get_upgrade_log()
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'log': upgrade_service.get_upgrade_log()
        }), 500


@upgrade_bp.route('/api/upgrade-log', methods=['GET'])
def api_upgrade_log():
    """Get current upgrade log"""
    try:
        return jsonify({
            'success': True,
            'log': upgrade_service.get_upgrade_log()
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@upgrade_bp.route('/api/backup-list', methods=['GET'])
def api_backup_list():
    """Get list of backups"""
    try:
        backups = upgrade_service.get_backup_list()

        return jsonify({
            'success': True,
            'data': backups
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@upgrade_bp.route('/api/restore-backup', methods=['POST'])
def api_restore_backup():
    """Restore from backup"""
    try:
        data = request.get_json()
        backup_path = data.get('backup_path')

        if not backup_path:
            return jsonify({
                'success': False,
                'error': 'Backup path is required'
            }), 400

        # Verify backup path exists
        if not os.path.exists(backup_path):
            return jsonify({
                'success': False,
                'error': 'Backup path does not exist'
            }), 404

        # Restore backup
        success, message = upgrade_service.restore_backup(backup_path)

        return jsonify({
            'success': success,
            'message': message
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@upgrade_bp.route('/api/config', methods=['GET'])
def api_get_config():
    """Get upgrade configuration"""
    try:
        config = {
            'update_source': os.environ.get('APP_UPDATE_SOURCE', 'github'),
            'github_repo': os.environ.get('APP_UPDATE_REPO', 'scaleflower/otrs-web'),
            'yunxiao_repo': os.environ.get('APP_UPDATE_YUNXIAO_REPO', ''),
            'auto_check_enabled': os.environ.get('APP_UPDATE_AUTO_CHECK', 'true').lower() == 'true',
            'check_interval_hours': int(os.environ.get('APP_UPDATE_CHECK_INTERVAL', '24'))
        }

        return jsonify({
            'success': True,
            'data': config
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
