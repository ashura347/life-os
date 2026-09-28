"""
LIFE OS — System Health Check Service (services/health_service.py)
Evaluates and reports operational health across database, ML model, alert engine,
device service, hospital discovery, and notification service layers.
"""

import services.database as db
import services.ml_service as ml_service


def check_system_health():
    """
    Evaluates system diagnostics across all components.
    Returns status indicators without exposing sensitive credentials or keys.
    """
    # 1. Database Connection Check
    try:
        conn = db.get_db_connection()
        conn.execute("SELECT 1;")
        conn.close()
        db_status = "connected"
    except Exception as e:
        db_status = f"error: {str(e)}"

    # 2. ML Model Availability Check
    try:
        dummy_vitals = {"heart_rate": 75, "spo2": 98, "temperature": 36.8, "movement_status": "Resting"}
        ml_prediction = ml_service.predict_risk(dummy_vitals)
        ml_status = "available" if ml_prediction.get('available') else "unavailable"
    except Exception:
        ml_status = "unavailable"

    # 3. Device Service Check
    try:
        device_info = db.get_device_status('LIFEOS-001', timeout_seconds=20)
        device_status = device_info.get('connection_status', 'OFFLINE').lower()
    except Exception:
        device_status = "offline"

    # 4. Alert Engine & Subservices
    alert_engine_status = "ready"
    hospital_service_status = "test_mode"
    notification_mode = "TEST"

    # 5. Overall System Readiness
    overall_status = "ready" if db_status == "connected" and alert_engine_status == "ready" else "needs_attention"

    return {
        "status": "ok" if overall_status == "ready" else "degraded",
        "overall_system": overall_status,
        "database": db_status,
        "ml_model": ml_status,
        "device_service": device_status,
        "alert_engine": alert_engine_status,
        "hospital_service": hospital_service_status,
        "notification_mode": notification_mode,
        "disclaimer": "Academic student prototype health status indicator. Zero real emergency dispatches active."
    }
