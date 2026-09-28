"""
LIFE OS — Patient Monitoring System (Part 3)
Python ESP32 Simulator Script (esp32/simulated_device.py)

Description:
  Simulates an ESP32 microcontroller sending HTTP POST pings to the Flask API.
  Sends periodic heartbeat pings (POST /api/device/heartbeat) and sensor vitals
  (POST /api/vitals) over Wi-Fi/HTTP.

Usage:
  python esp32/simulated_device.py [--url HTTP_URL] [--interval SECONDS]
"""

import sys
import time
import random
import json
import urllib.request
import urllib.error

# Server configuration defaults
SERVER_URL = "http://127.0.0.1:5000"
DEVICE_ID = "LIFEOS-001"
PATIENT_ID = "P001"
INTERVAL = 3  # Seconds between telemetry pings


def post_json(endpoint, data):
    """Sends an HTTP POST request with JSON payload using standard library."""
    url = f"{SERVER_URL}{endpoint}"
    json_bytes = json.dumps(data).encode('utf-8')
    req = urllib.request.Request(
        url,
        data=json_bytes,
        headers={'Content-Type': 'application/json'}
    )

    try:
        with urllib.request.urlopen(req, timeout=5) as response:
            res_body = response.read().decode('utf-8')
            return response.status, json.loads(res_body)
    except urllib.error.HTTPError as e:
        res_body = e.read().decode('utf-8')
        return e.code, json.loads(res_body) if res_body else {}
    except urllib.error.URLError as e:
        return 0, {'error': 'Connection Failed', 'message': str(e.reason)}


def send_heartbeat():
    """Sends device heartbeat to POST /api/device/heartbeat."""
    payload = {
        'device_id': DEVICE_ID,
        'patient_id': PATIENT_ID
    }
    status, body = post_json('/api/device/heartbeat', payload)
    print(f"[ESP32 Heartbeat] HTTP {status} -> {body.get('message', body)}")
    return status == 200


def send_vitals():
    """Generates simulated telemetry and posts to POST /api/vitals."""
    hr = max(60, min(120, 82 + random.randint(-4, 5)))
    spo2 = max(94, min(100, 98 + random.randint(-1, 1)))
    temp = round(max(36.0, min(38.2, 36.8 + random.uniform(-0.2, 0.2))), 1)
    movements = ['Normal', 'Resting', 'Active']
    movement = random.choice(movements)

    payload = {
        'patient_id': PATIENT_ID,
        'heart_rate': hr,
        'spo2': spo2,
        'temperature': temp,
        'movement_status': movement
    }

    status, body = post_json('/api/vitals', payload)
    print(f"[ESP32 Telemetry] HR: {hr} BPM | SpO2: {spo2}% | Temp: {temp}°C | Motion: {movement} -> HTTP {status}")
    return status == 201


def main():
    print("=" * 60)
    print("  LIFE OS — ESP32 Simulated Device Client Running")
    print(f"  Target Server : {SERVER_URL}")
    print(f"  Device ID     : {DEVICE_ID}")
    print(f"  Patient ID    : {PATIENT_ID}")
    print(f"  Ping Interval : {INTERVAL}s")
    print("  NOTICE        : All measurements are SIMULATED TEST DATA.")
    print("=" * 60)

    count = 0
    try:
        while True:
            count += 1
            print(f"\n--- [Tick #{count}] ---")
            send_heartbeat()
            send_vitals()
            time.sleep(INTERVAL)
    except KeyboardInterrupt:
        print("\n[ESP32 Simulator] Stopped by user.")


if __name__ == '__main__':
    main()
