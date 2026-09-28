"""
LIFE OS — Database Module
Handles SQLite database connection, table initialization, and sample data seeding.
"""

import os
import sqlite3
from datetime import datetime

# Path to database directory and file
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_DIR = os.path.join(BASE_DIR, 'database')
DB_PATH = os.path.join(DB_DIR, 'life_os.db')


def get_db_connection():
    """Establishes and returns a connection to the SQLite database."""
    # Ensure database directory exists
    if not os.path.exists(DB_DIR):
        os.makedirs(DB_DIR, exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initializes tables and seeds initial sample patient and vital data if empty."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Create Patients Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS patients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            age INTEGER NOT NULL,
            emergency_contact_name TEXT,
            emergency_contact_phone TEXT,
            emergency_contact_relation TEXT,
            monitoring_status TEXT NOT NULL DEFAULT 'ACTIVE',
            patient_status TEXT NOT NULL DEFAULT 'NORMAL',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Create Vitals Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS vitals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id TEXT NOT NULL,
            heart_rate INTEGER NOT NULL,
            spo2 INTEGER NOT NULL,
            temperature REAL NOT NULL,
            movement TEXT NOT NULL,
            patient_status TEXT NOT NULL DEFAULT 'NORMAL',
            device_status TEXT NOT NULL DEFAULT 'CONNECTED',
            is_simulated INTEGER NOT NULL DEFAULT 1,
            recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (patient_id) REFERENCES patients (patient_id)
        )
    ''')

    conn.commit()

    # Check if default patient exists
    cursor.execute("SELECT * FROM patients WHERE patient_id = ?", ('PAT-2026-001',))
    patient = cursor.fetchone()

    if not patient:
        cursor.execute('''
            INSERT INTO patients (
                patient_id, name, age, 
                emergency_contact_name, emergency_contact_phone, emergency_contact_relation,
                monitoring_status, patient_status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            'PAT-2026-001',
            'Alex Mercer',
            45,
            'Sarah Mercer',
            '+1 (555) 234-5678',
            'Spouse',
            'ACTIVE',
            'NORMAL'
        ))
        conn.commit()

    # Seed initial vitals if empty
    cursor.execute("SELECT COUNT(*) as count FROM vitals WHERE patient_id = ?", ('PAT-2026-001',))
    count = cursor.fetchone()['count']

    if count == 0:
        cursor.execute('''
            INSERT INTO vitals (
                patient_id, heart_rate, spo2, temperature, movement, patient_status, device_status, is_simulated
            ) VALUES (?, ?, ?, ?, ?, ?, ?, 1)
        ''', (
            'PAT-2026-001',
            82,
            98,
            36.8,
            'Normal',
            'NORMAL',
            'CONNECTED'
        ))
        conn.commit()

    conn.close()


def get_patient(patient_id='PAT-2026-001'):
    """Retrieves patient details by patient_id."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM patients WHERE patient_id = ?", (patient_id,))
    patient = cursor.fetchone()
    conn.close()
    return dict(patient) if patient else None


def get_latest_vitals(patient_id='PAT-2026-001'):
    """Retrieves the most recent vital reading for a patient."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM vitals WHERE patient_id = ? ORDER BY recorded_at DESC, id DESC LIMIT 1",
        (patient_id,)
    )
    vital = cursor.fetchone()
    conn.close()
    return dict(vital) if vital else None


def get_vital_history(patient_id='PAT-2026-001', limit=10):
    """Retrieves vital reading history for a patient."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM vitals WHERE patient_id = ? ORDER BY recorded_at DESC, id DESC LIMIT ?",
        (patient_id, limit)
    )
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def add_vital_reading(patient_id, heart_rate, spo2, temperature, movement, patient_status='NORMAL', device_status='CONNECTED'):
    """Inserts a new simulated/test vital reading into the database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO vitals (
            patient_id, heart_rate, spo2, temperature, movement, patient_status, device_status, is_simulated, recorded_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?)
    ''', (
        patient_id,
        heart_rate,
        spo2,
        temperature,
        movement,
        patient_status,
        device_status,
        datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    ))

    # Optionally update overall patient status
    cursor.execute("UPDATE patients SET patient_status = ? WHERE patient_id = ?", (patient_status, patient_id))

    conn.commit()
    conn.close()


if __name__ == '__main__':
    # Initialize DB when run directly
    init_db()
    print("Database initialized successfully at:", DB_PATH)
