"""
LIFE OS — Database Service Module (Part 4)
Handles SQLite database connection, table schemas, parameterized queries, and alert records.
"""

import os
import sqlite3
from datetime import datetime

# Database directory and path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_DIR = os.path.join(BASE_DIR, 'database')
DB_PATH = os.path.join(DB_DIR, 'life_os.db')


def get_db_connection():
    """Establishes a connection to the SQLite database with Row factory enabled and busy timeout set."""
    if not os.path.exists(DB_DIR):
        os.makedirs(DB_DIR, exist_ok=True)

    conn = sqlite3.connect(DB_PATH, timeout=20.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db():
    """
    Safely initializes tables and seeds baseline demonstration patient, vitals, and device status if empty.
    Handles schema migrations safely without destroying existing data.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. Create Patients Table if missing
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS patients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            age INTEGER NOT NULL,
            emergency_contact TEXT,
            location TEXT DEFAULT 'Pune, Maharashtra',
            latitude REAL DEFAULT 18.5204,
            longitude REAL DEFAULT 73.8567,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Schema migration check: ensure emergency_contact, location, latitude, longitude exist on patients table
    cursor.execute("PRAGMA table_info(patients)")
    columns = [row['name'] for row in cursor.fetchall()]
    if 'emergency_contact' not in columns:
        cursor.execute("ALTER TABLE patients ADD COLUMN emergency_contact TEXT;")
    if 'location' not in columns:
        cursor.execute("ALTER TABLE patients ADD COLUMN location TEXT DEFAULT 'Pune, Maharashtra';")
    if 'latitude' not in columns:
        cursor.execute("ALTER TABLE patients ADD COLUMN latitude REAL DEFAULT 18.5204;")
    if 'longitude' not in columns:
        cursor.execute("ALTER TABLE patients ADD COLUMN longitude REAL DEFAULT 73.8567;")
    conn.commit()

    # 2. Create Vital Records Table if missing
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS vital_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id TEXT NOT NULL,
            heart_rate INTEGER NOT NULL,
            spo2 INTEGER NOT NULL,
            temperature REAL NOT NULL,
            movement_status TEXT NOT NULL,
            source TEXT DEFAULT 'SIMULATED',
            recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (patient_id) REFERENCES patients (patient_id) ON DELETE CASCADE
        )
    ''')

    # Schema migration check: ensure source column exists on vital_records table
    cursor.execute("PRAGMA table_info(vital_records)")
    vr_cols = [row['name'] for row in cursor.fetchall()]
    if 'source' not in vr_cols:
        cursor.execute("ALTER TABLE vital_records ADD COLUMN source TEXT DEFAULT 'SIMULATED';")
    conn.commit()

    # 3. Create Devices Table for Heartbeat Tracking (Part 3 & 8)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS devices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_id TEXT UNIQUE NOT NULL,
            patient_id TEXT NOT NULL,
            source TEXT DEFAULT 'SIMULATED',
            last_error TEXT,
            last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (patient_id) REFERENCES patients (patient_id) ON DELETE CASCADE
        )
    ''')

    # Schema migration check: ensure source and last_error columns exist on devices table
    cursor.execute("PRAGMA table_info(devices)")
    dev_cols = [row['name'] for row in cursor.fetchall()]
    if 'source' not in dev_cols:
        cursor.execute("ALTER TABLE devices ADD COLUMN source TEXT DEFAULT 'SIMULATED';")
    if 'last_error' not in dev_cols:
        cursor.execute("ALTER TABLE devices ADD COLUMN last_error TEXT;")
    conn.commit()

    # 4. Create Alerts Table for Emergency Detection Engine (Part 4)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id TEXT NOT NULL,
            alert_type TEXT NOT NULL,
            severity TEXT NOT NULL,
            message TEXT NOT NULL,
            triggered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status TEXT NOT NULL DEFAULT 'ACTIVE',
            acknowledged_at TIMESTAMP,
            resolved_at TIMESTAMP,
            FOREIGN KEY (patient_id) REFERENCES patients (patient_id) ON DELETE CASCADE
        )
    ''')

    # 5. Create Emergency Events Table for Location-Aware Emergency Response (Part 6)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS emergency_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            alert_id INTEGER NOT NULL,
            patient_id TEXT NOT NULL,
            location TEXT NOT NULL,
            latitude REAL,
            longitude REAL,
            selected_facility TEXT,
            response_status TEXT NOT NULL DEFAULT 'CREATED',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (alert_id) REFERENCES alerts (id) ON DELETE CASCADE,
            FOREIGN KEY (patient_id) REFERENCES patients (patient_id) ON DELETE CASCADE
        )
    ''')

    conn.commit()

    # 6. Seed Default Test Patient P001 if missing
    cursor.execute("SELECT * FROM patients WHERE patient_id = ?", ('P001',))
    patient = cursor.fetchone()

    if not patient:
        cursor.execute('''
            INSERT INTO patients (patient_id, name, age, emergency_contact, location, latitude, longitude)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', ('P001', 'Demo Patient', 30, 'Demo Contact', 'Pune, Maharashtra', 18.5204, 73.8567))
        conn.commit()
    else:
        # Ensure P001 location is set if null
        p_dict = dict(patient)
        if not p_dict.get('location'):
            cursor.execute('''
                UPDATE patients 
                SET location = 'Pune, Maharashtra', latitude = 18.5204, longitude = 73.8567 
                WHERE patient_id = 'P001'
            ''')
            conn.commit()

    # 7. Seed Initial Vital Record for P001 if missing
    cursor.execute("SELECT COUNT(*) as count FROM vital_records WHERE patient_id = ?", ('P001',))
    count = cursor.fetchone()['count']

    if count == 0:
        cursor.execute('''
            INSERT INTO vital_records (patient_id, heart_rate, spo2, temperature, movement_status)
            VALUES (?, ?, ?, ?, ?)
        ''', ('P001', 82, 98, 36.8, 'Normal'))
        conn.commit()

    # 8. Seed Default Device LIFEOS-001 if missing
    cursor.execute("SELECT * FROM devices WHERE device_id = ?", ('LIFEOS-001',))
    device = cursor.fetchone()

    if not device:
        cursor.execute('''
            INSERT INTO devices (device_id, patient_id, last_seen)
            VALUES (?, ?, ?)
        ''', ('LIFEOS-001', 'P001', datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        conn.commit()

    conn.close()


# =========================================================================
# Patient CRUD Helper Functions
# =========================================================================

def add_patient(patient_id, name, age, emergency_contact=''):
    """Adds a new patient record to the database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO patients (patient_id, name, age, emergency_contact)
        VALUES (?, ?, ?, ?)
    ''', (patient_id.strip(), name.strip(), int(age), emergency_contact.strip() if emergency_contact else ''))
    conn.commit()
    conn.close()
    return get_patient(patient_id)


def get_patient(patient_id):
    """Retrieves a patient record by patient_id."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM patients WHERE patient_id = ?", (patient_id.strip(),))
    patient = cursor.fetchone()
    conn.close()
    return dict(patient) if patient else None


def get_all_patients():
    """Retrieves all registered patients."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM patients ORDER BY created_at DESC")
    patients = cursor.fetchall()
    conn.close()
    return [dict(p) for p in patients]


# =========================================================================
# Vital Records CRUD Helper Functions
# =========================================================================

def add_vital_record(patient_id, heart_rate, spo2, temperature, movement_status, source='SIMULATED'):
    """Inserts a vital record into the database for an existing patient."""
    conn = get_db_connection()
    cursor = conn.cursor()

    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    cursor.execute('''
        INSERT INTO vital_records (patient_id, heart_rate, spo2, temperature, movement_status, source, recorded_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (
        patient_id.strip(),
        int(heart_rate),
        int(spo2),
        float(temperature),
        str(movement_status).strip(),
        str(source).strip(),
        timestamp
    ))

    conn.commit()
    conn.close()
    return get_latest_vital_record(patient_id)


def get_latest_vital_record(patient_id):
    """Retrieves the most recent vital record for a given patient_id."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM vital_records 
        WHERE patient_id = ? 
        ORDER BY recorded_at DESC, id DESC 
        LIMIT 1
    ''', (patient_id.strip(),))
    record = cursor.fetchone()
    conn.close()
    return dict(record) if record else None


def get_recent_vital_records(patient_id, limit=20):
    """Retrieves recent vital records for a given patient_id, ordered newest first."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM vital_records 
        WHERE patient_id = ? 
        ORDER BY recorded_at DESC, id DESC 
        LIMIT ?
    ''', (patient_id.strip(), limit))
    records = cursor.fetchall()
    conn.close()
    return [dict(r) for r in records]


# =========================================================================
# Device Status & Heartbeat Helper Functions (Part 3 & 8)
# =========================================================================

def update_device_heartbeat(device_id, patient_id, source='SIMULATED', last_error=None):
    """Updates or inserts the device heartbeat timestamp and status metadata."""
    conn = get_db_connection()
    cursor = conn.cursor()
    now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    cursor.execute("SELECT * FROM devices WHERE device_id = ?", (device_id.strip(),))
    existing = cursor.fetchone()

    if existing:
        cursor.execute('''
            UPDATE devices 
            SET patient_id = ?, source = ?, last_error = ?, last_seen = ? 
            WHERE device_id = ?
        ''', (patient_id.strip(), str(source).strip(), str(last_error) if last_error else None, now_str, device_id.strip()))
    else:
        cursor.execute('''
            INSERT INTO devices (device_id, patient_id, source, last_error, last_seen)
            VALUES (?, ?, ?, ?, ?)
        ''', (device_id.strip(), patient_id.strip(), str(source).strip(), str(last_error) if last_error else None, now_str))

    conn.commit()
    conn.close()
    return get_device_status(device_id)


def get_device_status(device_id='LIFEOS-001', timeout_seconds=20):
    """
    Evaluates whether a device is currently CONNECTED, OFFLINE, ERROR, or NOT_CONFIGURED
    based on heartbeat, data source, and errors.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM devices WHERE device_id = ?", (device_id.strip(),))
    device = cursor.fetchone()
    conn.close()

    if not device:
        return {
            'device_id': device_id,
            'patient_id': 'NOT_CONFIGURED',
            'connection_status': 'NOT_CONFIGURED',
            'data_source': 'NONE',
            'last_communication': 'Never',
            'last_error': 'Device not configured',
            'disclaimer': 'Software connection indicator only. Does not guarantee physical patient safety.'
        }

    device_dict = dict(device)
    last_seen_str = device_dict['last_seen']
    last_error = device_dict.get('last_error')
    source = device_dict.get('source', 'SIMULATED')

    try:
        last_seen_dt = datetime.strptime(last_seen_str, '%Y-%m-%d %H:%M:%S')
        elapsed = (datetime.now() - last_seen_dt).total_seconds()
        is_connected = elapsed <= timeout_seconds
    except Exception:
        is_connected = False

    if last_error:
        connection_status = 'ERROR'
    elif is_connected:
        connection_status = 'CONNECTED'
    else:
        connection_status = 'OFFLINE'

    return {
        'device_id': device_dict['device_id'],
        'patient_id': device_dict['patient_id'],
        'connection_status': connection_status,
        'data_source': source,
        'last_error': last_error,
        'last_communication': last_seen_str,
        'disclaimer': 'Software connection indicator only. Does not guarantee physical patient safety.'
    }


# =========================================================================
# Alert Engine Helper Functions (Part 4)
# =========================================================================

def create_alert_record(patient_id, alert_type, severity, message):
    """Inserts a new alert record into the database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    cursor.execute('''
        INSERT INTO alerts (patient_id, alert_type, severity, message, triggered_at, status)
        VALUES (?, ?, ?, ?, ?, 'ACTIVE')
    ''', (patient_id.strip(), alert_type.strip(), severity.strip(), message.strip(), now_str))

    alert_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return get_alert_by_id(alert_id)


def get_alert_by_id(alert_id):
    """Retrieves an alert record by alert_id."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM alerts WHERE id = ?", (int(alert_id),))
    alert = cursor.fetchone()
    conn.close()
    return dict(alert) if alert else None


def get_active_alerts(patient_id):
    """Retrieves all ACTIVE or ACKNOWLEDGED (non-resolved) alerts for a patient."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM alerts 
        WHERE patient_id = ? AND status IN ('ACTIVE', 'ACKNOWLEDGED')
        ORDER BY triggered_at DESC, id DESC
    ''', (patient_id.strip(),))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_all_alerts_for_patient(patient_id, limit=50):
    """Retrieves all alert history for a patient, ordered newest first."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM alerts 
        WHERE patient_id = ? 
        ORDER BY triggered_at DESC, id DESC 
        LIMIT ?
    ''', (patient_id.strip(), limit))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def has_active_alert_of_type(patient_id, alert_type):
    """Checks if an ACTIVE or ACKNOWLEDGED alert of a specific type already exists for a patient."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT COUNT(*) as count FROM alerts 
        WHERE patient_id = ? AND alert_type = ? AND status IN ('ACTIVE', 'ACKNOWLEDGED')
    ''', (patient_id.strip(), alert_type.strip()))
    count = cursor.fetchone()['count']
    conn.close()
    return count > 0


def acknowledge_alert_record(alert_id):
    """Marks an alert as ACKNOWLEDGED."""
    conn = get_db_connection()
    cursor = conn.cursor()
    now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    cursor.execute('''
        UPDATE alerts 
        SET status = 'ACKNOWLEDGED', acknowledged_at = ? 
        WHERE id = ? AND status = 'ACTIVE'
    ''', (now_str, int(alert_id)))

    updated = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return get_alert_by_id(alert_id) if updated else None


def resolve_alert_record(alert_id):
    """Marks an alert as RESOLVED."""
    conn = get_db_connection()
    cursor = conn.cursor()
    now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    cursor.execute('''
        UPDATE alerts 
        SET status = 'RESOLVED', resolved_at = ? 
        WHERE id = ? AND status IN ('ACTIVE', 'ACKNOWLEDGED')
    ''', (now_str, int(alert_id)))

    updated = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return get_alert_by_id(alert_id) if updated else None


# =========================================================================
# Emergency Event Helper Functions (Part 6)
# =========================================================================

def create_emergency_event_record(alert_id, patient_id, location, latitude=None, longitude=None, selected_facility=None, response_status='CREATED'):
    """Inserts a new emergency event record into the database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    cursor.execute('''
        INSERT INTO emergency_events (
            alert_id, patient_id, location, latitude, longitude, selected_facility, response_status, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        int(alert_id),
        patient_id.strip(),
        location.strip(),
        float(latitude) if latitude is not None else None,
        float(longitude) if longitude is not None else None,
        selected_facility.strip() if selected_facility else None,
        response_status.strip(),
        now_str,
        now_str
    ))

    event_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return get_emergency_event_by_id(event_id)


def get_emergency_event_by_id(event_id):
    """Retrieves an emergency event by its ID."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM emergency_events WHERE id = ?", (int(event_id),))
    event = cursor.fetchone()
    conn.close()
    return dict(event) if event else None


def get_emergency_event_by_alert_id(alert_id):
    """Retrieves an existing emergency event for a given alert_id."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM emergency_events WHERE alert_id = ? ORDER BY id DESC LIMIT 1", (int(alert_id),))
    event = cursor.fetchone()
    conn.close()
    return dict(event) if event else None


def get_all_emergency_events_for_patient(patient_id=None, limit=50):
    """Retrieves emergency events, optionally filtered by patient_id."""
    conn = get_db_connection()
    cursor = conn.cursor()
    if patient_id:
        cursor.execute('''
            SELECT * FROM emergency_events 
            WHERE patient_id = ? 
            ORDER BY created_at DESC, id DESC 
            LIMIT ?
        ''', (patient_id.strip(), limit))
    else:
        cursor.execute('''
            SELECT * FROM emergency_events 
            ORDER BY created_at DESC, id DESC 
            LIMIT ?
        ''', (limit,))
    events = cursor.fetchall()
    conn.close()
    return [dict(e) for e in events]


def update_emergency_event_status(event_id, response_status, selected_facility=None):
    """Updates the status and optional selected facility for an emergency event."""
    conn = get_db_connection()
    cursor = conn.cursor()
    now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    if selected_facility:
        cursor.execute('''
            UPDATE emergency_events 
            SET response_status = ?, selected_facility = ?, updated_at = ? 
            WHERE id = ?
        ''', (response_status.strip(), selected_facility.strip(), now_str, int(event_id)))
    else:
        cursor.execute('''
            UPDATE emergency_events 
            SET response_status = ?, updated_at = ? 
            WHERE id = ?
        ''', (response_status.strip(), now_str, int(event_id)))

    updated = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return get_emergency_event_by_id(event_id) if updated else None


def update_patient_location(patient_id, location, latitude=None, longitude=None):
    """Updates a patient's registered location details."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE patients 
        SET location = ?, latitude = ?, longitude = ? 
        WHERE patient_id = ?
    ''', (
        location.strip(),
        float(latitude) if latitude is not None else None,
        float(longitude) if longitude is not None else None,
        patient_id.strip()
    ))
    conn.commit()
    conn.close()
    return get_patient(patient_id)

