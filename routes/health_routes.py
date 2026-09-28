"""
LIFE OS — System Health REST API Blueprint (routes/health_routes.py)
Provides GET /api/health for system diagnostics and integration verification.
"""

from flask import Blueprint, jsonify
import services.health_service as health_service

health_bp = Blueprint('health_bp', __name__)


@health_bp.route('/api/health', methods=['GET'])
def get_system_health_api():
    """
    GET /api/health
    Returns operational health status across database, ML model, device tracking,
    alert engine, hospital service, and notification test mode.
    """
    health_info = health_service.check_system_health()
    status_code = 200 if health_info.get('status') == 'ok' else 503
    return jsonify(health_info), status_code
