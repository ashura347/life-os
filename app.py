"""
LIFE OS — Patient Monitoring & Emergency Response System (Part 7)
Flask Server Main Module
"""

from flask import Flask, render_template, redirect, url_for
import services.database as db
import services.alert_engine as alert_engine
import services.ml_service as ml_service
import services.emergency_service as emergency_service
import services.health_service as health_service
from routes.patient_routes import patient_bp
from routes.vital_routes import vital_bp
from routes.device_routes import device_bp
from routes.alert_routes import alert_bp
from routes.ml_routes import ml_bp
from routes.emergency_routes import emergency_bp
from routes.health_routes import health_bp
from routes.demo_routes import demo_bp

app = Flask(__name__)

# Register Blueprints
app.register_blueprint(patient_bp)
app.register_blueprint(vital_bp)
app.register_blueprint(device_bp)
app.register_blueprint(alert_bp)
app.register_blueprint(ml_bp)
app.register_blueprint(emergency_bp)
app.register_blueprint(health_bp)
app.register_blueprint(demo_bp)

# Safely initialize database schemas & seed baseline P001 patient & device status
with app.app_context():
    db.init_db()


@app.route('/')
def index():
    """Redirect root endpoint to the main patient monitoring dashboard."""
    return redirect(url_for('dashboard'))


@app.route('/dashboard')
def dashboard():
    """
    Renders the main LIFE OS Patient Monitoring Dashboard.
    Retrieves patient P001 ('Demo Patient'), latest vitals, device status, alert engine state,
    AI/ML risk assessment, active emergency events, and system health diagnostics.
    """
    patient = db.get_patient('P001')
    vitals = db.get_latest_vital_record('P001')
    device = db.get_device_status('LIFEOS-001', timeout_seconds=20)
    active_alerts = alert_engine.get_active_alerts('P001')
    patient_status = alert_engine.get_patient_system_status('P001')
    latest_alert = active_alerts[0] if active_alerts else None

    # AI/ML Advisory Assessment
    ml_result = ml_service.predict_risk(vitals) if vitals else ml_service.predict_risk({})

    # Location-Aware Emergency Events
    raw_events = db.get_all_emergency_events_for_patient('P001', limit=10)
    emergency_events = [emergency_service.get_emergency_event_details(e['id']) for e in raw_events]
    emergency_events = [e for e in emergency_events if e]
    latest_event = emergency_events[0] if emergency_events else None

    # System Integration & Health Diagnostics
    health = health_service.check_system_health()

    return render_template(
        'dashboard.html',
        patient=patient,
        vitals=vitals,
        device=device,
        active_alerts=active_alerts,
        latest_alert=latest_alert,
        patient_status=patient_status,
        ml=ml_result,
        emergency_events=emergency_events,
        latest_event=latest_event,
        health=health
    )


@app.route('/patient')
def patient():
    """Renders the detailed Patient Profile page for P001."""
    patient_info = db.get_patient('P001')
    latest_vitals = db.get_latest_vital_record('P001')
    vital_history = db.get_recent_vital_records('P001', limit=10)
    device_status = db.get_device_status('LIFEOS-001', timeout_seconds=20)
    patient_status = alert_engine.get_patient_system_status('P001')
    return render_template(
        'patient.html',
        patient=patient_info,
        vitals=latest_vitals,
        history=vital_history,
        device=device_status,
        patient_status=patient_status
    )


if __name__ == '__main__':
    print("Starting LIFE OS Server (Part 7 Integration & Demo Mode) on http://127.0.0.1:5000 ...")
    app.run(debug=True, host='127.0.0.1', port=5000)
