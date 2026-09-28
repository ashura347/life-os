"""
LIFE OS — Demo Mode Service Module (services/demo_service.py)
Handles pre-configured demonstration scenarios (NORMAL, WARNING, CRITICAL, EMERGENCY, RESET)
for safe live walkthroughs. OPERATES STRICTLY IN TEST MODE.
"""

import services.database as db
import services.alert_engine as alert_engine
import services.ml_service as ml_service
import services.emergency_service as emergency_service


def run_demo_scenario(scenario_type="normal", patient_id="P001"):
    """
    Executes a pre-configured prototype demonstration scenario.
    
    Supported scenarios:
    - 'normal': Posts standard normal vitals (75 BPM, 98% SpO2, 36.8°C).
    - 'warning': Posts elevated warning vitals (108 BPM, 94% SpO2, 37.9°C).
    - 'critical': Posts consecutive critical vitals (125 BPM, 91% SpO2, 38.6°C) to trigger Rule Engine alert.
    - 'emergency': Escalates active alert to Emergency Response Event with Pune facility lookup & test notification.
    - 'reset': Resolves active alerts/events, resetting patient system status to NORMAL.
    """
    scenario = str(scenario_type).lower().strip()
    patient = db.get_patient(patient_id)
    if not patient:
        db.add_patient(patient_id, 'Demo Patient', 30, 'Demo Contact')
        db.update_patient_location(patient_id, 'Pune, Maharashtra', 18.5204, 73.8567)
        patient = db.get_patient(patient_id)

    if scenario == 'normal':
        # 1. Post normal vitals
        vitals = db.add_vital_record(patient_id, heart_rate=75, spo2=98, temperature=36.8, movement_status='Resting')
        db.update_device_heartbeat('LIFEOS-001', patient_id)
        alert_eval = alert_engine.evaluate_vital_reading(patient_id, vitals)
        ml_eval = ml_service.predict_risk(vitals)

        return {
            "success": True,
            "scenario": "normal",
            "message": "Demo Scenario 'NORMAL' executed. Vital reading saved. No alert triggered.",
            "vitals": vitals,
            "patient_status": alert_engine.get_patient_system_status(patient_id),
            "alert_created": alert_eval.get('alert_created', False),
            "ml_risk": ml_eval.get('risk_category'),
            "disclaimer": "DEMO / TEST MODE ONLY. Zero real emergency services or SMS dispatches triggered."
        }

    elif scenario == 'warning':
        # 2. Post warning vitals
        vitals = db.add_vital_record(patient_id, heart_rate=108, spo2=94, temperature=37.9, movement_status='Moving')
        db.update_device_heartbeat('LIFEOS-001', patient_id)
        alert_eval = alert_engine.evaluate_vital_reading(patient_id, vitals)
        ml_eval = ml_service.predict_risk(vitals)

        return {
            "success": True,
            "scenario": "warning",
            "message": "Demo Scenario 'WARNING' executed. Warning vitals ingested.",
            "vitals": vitals,
            "patient_status": alert_engine.get_patient_system_status(patient_id),
            "alert_created": alert_eval.get('alert_created', False),
            "ml_risk": ml_eval.get('risk_category'),
            "disclaimer": "DEMO / TEST MODE ONLY. Zero real emergency services or SMS dispatches triggered."
        }

    elif scenario == 'critical':
        # 3. Post consecutive critical vitals to satisfy persistence rule
        db.add_vital_record(patient_id, heart_rate=125, spo2=91, temperature=38.6, movement_status='Restless')
        vitals = db.add_vital_record(patient_id, heart_rate=128, spo2=90, temperature=38.7, movement_status='Restless')
        db.update_device_heartbeat('LIFEOS-001', patient_id)
        alert_eval = alert_engine.evaluate_vital_reading(patient_id, vitals)
        ml_eval = ml_service.predict_risk(vitals)

        return {
            "success": True,
            "scenario": "critical",
            "message": "Demo Scenario 'CRITICAL' executed. Consecutive abnormal readings triggered Critical Alert.",
            "vitals": vitals,
            "patient_status": alert_engine.get_patient_system_status(patient_id),
            "alert_created": alert_eval.get('alert_created', False),
            "alert_id": alert_eval.get('alert_id'),
            "ml_risk": ml_eval.get('risk_category'),
            "disclaimer": "DEMO / TEST MODE ONLY. Zero real emergency services or SMS dispatches triggered."
        }

    elif scenario == 'emergency':
        # 4. Trigger Emergency Event for active alert
        active_alerts = alert_engine.get_active_alerts(patient_id)
        if not active_alerts:
            # If no active alert exists, create one first
            alert_rec = db.create_alert_record(
                patient_id=patient_id,
                alert_type='HIGH_HEART_RATE_CRITICAL',
                severity='CRITICAL',
                message='Critical pulse anomaly (128 BPM) detected consecutively.'
            )
            alert_id = alert_rec['id']
        else:
            alert_id = active_alerts[0]['id']

        em_result = emergency_service.create_emergency_event(alert_id)
        return {
            "success": True,
            "scenario": "emergency",
            "message": f"Demo Scenario 'EMERGENCY' executed. Emergency Event #{em_result.get('event_id')} created.",
            "event": em_result,
            "patient_status": alert_engine.get_patient_system_status(patient_id),
            "disclaimer": "DEMO / TEST MODE ONLY. Zero real emergency services or SMS dispatches triggered."
        }

    elif scenario == 'reset':
        # 5. Resolve active alerts & emergency events
        active_alerts = alert_engine.get_active_alerts(patient_id)
        for a in active_alerts:
            db.resolve_alert_record(a['id'])

        raw_events = db.get_all_emergency_events_for_patient(patient_id)
        for e in raw_events:
            db.update_emergency_event_status(e['id'], response_status='RESOLVED', selected_facility='Demo Reset')

        vitals = db.add_vital_record(patient_id, heart_rate=75, spo2=98, temperature=36.8, movement_status='Resting')
        return {
            "success": True,
            "scenario": "reset",
            "message": "Demo Scenario 'RESET' executed. All active alerts and emergency events marked RESOLVED. System status reset to NORMAL.",
            "patient_status": alert_engine.get_patient_system_status(patient_id),
            "disclaimer": "DEMO / TEST MODE ONLY. Zero real emergency services or SMS dispatches triggered."
        }

    else:
        return {
            "success": False,
            "error": f"Unknown scenario type '{scenario}'. Supported: 'normal', 'warning', 'critical', 'emergency', 'reset'.",
            "code": "INVALID_SCENARIO"
        }
