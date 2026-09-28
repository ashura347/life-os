"""
LIFE OS — Demo Mode Routes & REST API Blueprint (routes/demo_routes.py)
Provides interactive Demo Mode controls and simulation endpoints.
"""

from flask import Blueprint, jsonify, request, render_template
import services.database as db
import services.demo_service as demo_service
import services.health_service as health_service

demo_bp = Blueprint('demo_bp', __name__)


@demo_bp.route('/api/demo/scenario', methods=['POST'])
def trigger_demo_scenario_api():
    """
    POST /api/demo/scenario
    Executes a demonstration simulation scenario.
    
    Expected JSON Payload: {"scenario": "normal" | "warning" | "critical" | "emergency" | "reset", "patient_id": "P001" (optional)}
    """
    data = request.get_json(silent=True) or {}
    scenario = data.get('scenario', 'normal')
    patient_id = data.get('patient_id', 'P001')

    result = demo_service.run_demo_scenario(scenario, patient_id)

    status_code = 200 if result.get('success') else 400
    return jsonify(result), status_code


@demo_bp.route('/demo')
def demo_page():
    """
    GET /demo
    Renders the interactive Demo Control Panel for live presentations and walkthroughs.
    """
    patient = db.get_patient('P001')
    health = health_service.check_system_health()
    return render_template(
        'demo.html',
        patient=patient,
        health=health
    )
