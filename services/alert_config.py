"""
LIFE OS — Prototype Alert Engine Configuration (services/alert_config.py)

NOTICE AND SAFETY DISCLAIMER:
Prototype alert configuration — requires clinical validation.
These threshold values and escalation rules are defined for software prototype
demonstration and system validation. They do not constitute clinically certified
universal medical diagnostic thresholds.
"""

# Safety Disclaimer Banner String
ALERT_SYSTEM_DISCLAIMER = (
    "Prototype alert configuration — requires clinical validation. "
    "Alert states reflect rule-based software threshold checks, not a clinical diagnosis."
)

# Persistence Rule: Number of consecutive abnormal readings required before auto-escalation
# Prevents single noisy sensor pings from triggering false positive alerts.
CONSECUTIVE_ABNORMAL_REQUIRED = 2

# Deduplication Setting: Avoid creating duplicate active alerts for ongoing conditions
PREVENT_DUPLICATE_ACTIVE_ALERTS = True

# Prototype Threshold Settings
THRESHOLDS = {
    'HEART_RATE': {
        'HIGH_CRITICAL': 120,   # > 120 BPM -> CRITICAL
        'HIGH_WARNING': 100,    # > 100 BPM -> WARNING
        'LOW_WARNING': 50,      # < 50 BPM  -> WARNING
        'LOW_CRITICAL': 40,      # < 40 BPM  -> CRITICAL
    },
    'SPO2': {
        'LOW_CRITICAL': 90,     # < 90% SpO2 -> CRITICAL
        'LOW_WARNING': 95,      # < 95% SpO2 -> WARNING
    },
    'TEMPERATURE': {
        'HIGH_CRITICAL': 38.5,  # > 38.5 °C  -> CRITICAL
        'HIGH_WARNING': 37.8,   # > 37.8 °C  -> WARNING
        'LOW_WARNING': 35.5,    # < 35.5 °C  -> WARNING
    }
}
