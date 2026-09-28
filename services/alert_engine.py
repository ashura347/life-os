"""
LIFE OS — Emergency Detection & Alert Engine Service (services/alert_engine.py)

Evaluates vital telemetry records against prototype rules, persistence requirements,
and deduplication filters to generate system alerts and derive patient status.
"""

import services.database as db
from services.alert_config import (
    THRESHOLDS,
    CONSECUTIVE_ABNORMAL_REQUIRED,
    PREVENT_DUPLICATE_ACTIVE_ALERTS,
    ALERT_SYSTEM_DISCLAIMER
)


def validate_vitals(reading):
    """Validates that vital reading dict contains required numeric fields."""
    if not isinstance(reading, dict):
        return False, "Vital reading must be a dictionary."

    required_keys = ['heart_rate', 'spo2', 'temperature']
    for key in required_keys:
        if key not in reading:
            return False, f"Missing required vital field: '{key}'."
        val = reading[key]
        if val is None or isinstance(val, bool) or not isinstance(val, (int, float)):
            return False, f"Field '{key}' must be a numeric value."

    return True, "Valid"


def evaluate_vital_reading(patient_id, vital_record):
    """
    Evaluates a new vital reading against prototype rules.
    Considers persistence across consecutive readings and checks deduplication filters.
    """
    valid, msg = validate_vitals(vital_record)
    if not valid:
        return {'alert_created': False, 'error': msg, 'patient_status': get_patient_system_status(patient_id)}

    patient = db.get_patient(patient_id)
    if not patient:
        return {'alert_created': False, 'error': f"Patient '{patient_id}' not found.", 'patient_status': 'NORMAL'}

    # Fetch recent readings to evaluate persistence (consecutive abnormal readings)
    recent_readings = db.get_recent_vital_records(patient_id, limit=CONSECUTIVE_ABNORMAL_REQUIRED)
    
    # If we don't have enough history, prepend current reading
    if not recent_readings:
        recent_readings = [vital_record]

    created_alert = None

    # 1. Check Heart Rate Escalation Rules
    hr_alert = _check_heart_rate_rules(patient_id, recent_readings)
    if hr_alert:
        created_alert = hr_alert

    # 2. Check SpO2 Escalation Rules (If no higher severity alert already created)
    if not created_alert or created_alert['severity'] != 'CRITICAL':
        spo2_alert = _check_spo2_rules(patient_id, recent_readings)
        if spo2_alert:
            created_alert = spo2_alert

    # 3. Check Temperature Escalation Rules (If no higher severity alert already created)
    if not created_alert or created_alert['severity'] != 'CRITICAL':
        temp_alert = _check_temp_rules(patient_id, recent_readings)
        if temp_alert:
            created_alert = temp_alert

    # Compute updated overall patient status based on active alerts
    patient_status = get_patient_system_status(patient_id)

    return {
        'alert_created': created_alert is not None,
        'alert': created_alert,
        'patient_status': patient_status,
        'disclaimer': ALERT_SYSTEM_DISCLAIMER
    }


def _check_heart_rate_rules(patient_id, recent_readings):
    """Evaluates heart rate persistence rules across recent readings."""
    if len(recent_readings) < CONSECUTIVE_ABNORMAL_REQUIRED:
        return None

    # Check Critical High HR Persistence (> 120 BPM)
    crit_threshold = THRESHOLDS['HEART_RATE']['HIGH_CRITICAL']
    if all(r['heart_rate'] > crit_threshold for r in recent_readings[:CONSECUTIVE_ABNORMAL_REQUIRED]):
        alert_type = 'HIGH_HEART_RATE_CRITICAL'
        if PREVENT_DUPLICATE_ACTIVE_ALERTS and db.has_active_alert_of_type(patient_id, alert_type):
            return None
        hr = recent_readings[0]['heart_rate']
        msg = f"CRITICAL: High heart rate detected ({hr} BPM > {crit_threshold} BPM) across {CONSECUTIVE_ABNORMAL_REQUIRED} consecutive readings."
        return db.create_alert_record(patient_id, alert_type, 'CRITICAL', msg)

    # Check Warning High HR Persistence (> 100 BPM)
    warn_threshold = THRESHOLDS['HEART_RATE']['HIGH_WARNING']
    if all(r['heart_rate'] > warn_threshold for r in recent_readings[:CONSECUTIVE_ABNORMAL_REQUIRED]):
        alert_type = 'HIGH_HEART_RATE_WARNING'
        if PREVENT_DUPLICATE_ACTIVE_ALERTS and db.has_active_alert_of_type(patient_id, alert_type):
            return None
        hr = recent_readings[0]['heart_rate']
        msg = f"WARNING: Elevated heart rate detected ({hr} BPM > {warn_threshold} BPM) across {CONSECUTIVE_ABNORMAL_REQUIRED} consecutive readings."
        return db.create_alert_record(patient_id, alert_type, 'WARNING', msg)

    return None


def _check_spo2_rules(patient_id, recent_readings):
    """Evaluates SpO2 persistence rules across recent readings."""
    if len(recent_readings) < CONSECUTIVE_ABNORMAL_REQUIRED:
        return None

    # Check Critical Low SpO2 Persistence (< 90%)
    crit_threshold = THRESHOLDS['SPO2']['LOW_CRITICAL']
    if all(r['spo2'] < crit_threshold for r in recent_readings[:CONSECUTIVE_ABNORMAL_REQUIRED]):
        alert_type = 'LOW_SPO2_CRITICAL'
        if PREVENT_DUPLICATE_ACTIVE_ALERTS and db.has_active_alert_of_type(patient_id, alert_type):
            return None
        spo2 = recent_readings[0]['spo2']
        msg = f"CRITICAL: Low oxygen saturation detected ({spo2}% < {crit_threshold}%) across {CONSECUTIVE_ABNORMAL_REQUIRED} consecutive readings."
        return db.create_alert_record(patient_id, alert_type, 'CRITICAL', msg)

    # Check Warning Low SpO2 Persistence (< 95%)
    warn_threshold = THRESHOLDS['SPO2']['LOW_WARNING']
    if all(r['spo2'] < warn_threshold for r in recent_readings[:CONSECUTIVE_ABNORMAL_REQUIRED]):
        alert_type = 'LOW_SPO2_WARNING'
        if PREVENT_DUPLICATE_ACTIVE_ALERTS and db.has_active_alert_of_type(patient_id, alert_type):
            return None
        spo2 = recent_readings[0]['spo2']
        msg = f"WARNING: Sub-optimal oxygen saturation ({spo2}% < {warn_threshold}%) across {CONSECUTIVE_ABNORMAL_REQUIRED} consecutive readings."
        return db.create_alert_record(patient_id, alert_type, 'WARNING', msg)

    return None


def _check_temp_rules(patient_id, recent_readings):
    """Evaluates body temperature persistence rules across recent readings."""
    if len(recent_readings) < CONSECUTIVE_ABNORMAL_REQUIRED:
        return None

    # Check Critical High Temperature Persistence (> 38.5 °C)
    crit_threshold = THRESHOLDS['TEMPERATURE']['HIGH_CRITICAL']
    if all(r['temperature'] > crit_threshold for r in recent_readings[:CONSECUTIVE_ABNORMAL_REQUIRED]):
        alert_type = 'HIGH_TEMP_CRITICAL'
        if PREVENT_DUPLICATE_ACTIVE_ALERTS and db.has_active_alert_of_type(patient_id, alert_type):
            return None
        temp = recent_readings[0]['temperature']
        msg = f"CRITICAL: High fever detected ({temp}°C > {crit_threshold}°C) across {CONSECUTIVE_ABNORMAL_REQUIRED} consecutive readings."
        return db.create_alert_record(patient_id, alert_type, 'CRITICAL', msg)

    # Check Warning High Temperature Persistence (> 37.8 °C)
    warn_threshold = THRESHOLDS['TEMPERATURE']['HIGH_WARNING']
    if all(r['temperature'] > warn_threshold for r in recent_readings[:CONSECUTIVE_ABNORMAL_REQUIRED]):
        alert_type = 'HIGH_TEMP_WARNING'
        if PREVENT_DUPLICATE_ACTIVE_ALERTS and db.has_active_alert_of_type(patient_id, alert_type):
            return None
        temp = recent_readings[0]['temperature']
        msg = f"WARNING: Mild fever detected ({temp}°C > {warn_threshold}°C) across {CONSECUTIVE_ABNORMAL_REQUIRED} consecutive readings."
        return db.create_alert_record(patient_id, alert_type, 'WARNING', msg)

    return None


def get_patient_system_status(patient_id):
    """
    Derives the software patient alert state ('NORMAL', 'WARNING', 'CRITICAL')
    based on the presence of un-resolved active alerts in SQLite.
    """
    active_alerts = db.get_active_alerts(patient_id)
    if not active_alerts:
        return 'NORMAL'

    severities = [a['severity'] for a in active_alerts]
    if 'CRITICAL' in severities:
        return 'CRITICAL'
    if 'WARNING' in severities:
        return 'WARNING'

    return 'NORMAL'


def get_active_alerts(patient_id):
    """Retrieves active non-resolved alerts for a patient."""
    return db.get_active_alerts(patient_id)


def get_alert_history(patient_id, limit=50):
    """Retrieves alert history for a patient."""
    return db.get_all_alerts_for_patient(patient_id, limit)


def acknowledge_alert(alert_id):
    """Marks an alert as ACKNOWLEDGED."""
    return db.acknowledge_alert_record(alert_id)


def resolve_alert(alert_id):
    """Marks an alert as RESOLVED."""
    return db.resolve_alert_record(alert_id)
