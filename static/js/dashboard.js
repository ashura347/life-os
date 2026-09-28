/**
 * LIFE OS — Patient Monitoring & Emergency Response System
 * Client-side Dashboard JavaScript Engine (Part 5 AI/ML Engine)
 * Handles 3-second periodic polling for vitals, device status, active alerts, & ML risk predictions.
 */

document.addEventListener('DOMContentLoaded', () => {
    // DOM Elements
    const mobileToggle = document.getElementById('mobile-toggle');
    const sidebar = document.querySelector('.sidebar');
    const btnSimulatePulse = document.getElementById('btn-simulate-pulse');
    const btnAutoToggle = document.getElementById('btn-auto-toggle');
    const autoStatusText = document.getElementById('auto-status');
    const lastUpdatedSpan = document.getElementById('last-updated-time');
    const lastCommSpan = document.getElementById('last-comm-time');

    // Vital Display Elements
    const valHeartRate = document.getElementById('val-heart-rate');
    const valSpo2 = document.getElementById('val-spo2');
    const valTemp = document.getElementById('val-temperature');
    const valMovement = document.getElementById('val-movement');
    const spo2Progress = document.getElementById('spo2-progress');

    // Status Badge & Pill Elements
    const patientStatusBadge = document.getElementById('patient-status-badge');
    const activeAlertsNum = document.getElementById('active-alerts-num');
    const alertsCountPill = document.getElementById('alerts-count-pill');
    const deviceStatusPill = document.getElementById('device-status-pill');
    const deviceStatusText = document.getElementById('device-status-text');

    // AI/ML Assessment DOM Elements (Part 5)
    const mlRiskCategory = document.getElementById('ml-risk-category');
    const mlConfidence = document.getElementById('ml-confidence');
    const mlConfFill = document.getElementById('ml-conf-fill');
    const mlAvailable = document.getElementById('ml-available');
    const mlAnalysisTime = document.getElementById('ml-analysis-time');
    const mlVersion = document.getElementById('ml-version');

    let pollInterval = null;
    let isPolling = true;

    // 1. Mobile Navigation Sidebar Toggle
    if (mobileToggle && sidebar) {
        mobileToggle.addEventListener('click', () => {
            sidebar.classList.toggle('open');
        });
    }

    // 2. Real-Time Timestamp Clock Updater
    function updateLiveTimestamp() {
        const now = new Date();
        const formattedTime = now.toISOString().replace('T', ' ').substring(0, 19);
        if (lastUpdatedSpan && !lastUpdatedSpan.dataset.customTime) {
            lastUpdatedSpan.textContent = formattedTime;
        }
    }
    setInterval(updateLiveTimestamp, 1000);

    // 3. Poll Latest Vitals from Server (GET /api/vitals/P001/latest) & Trigger ML Prediction
    async function fetchLatestVitals() {
        try {
            const response = await fetch('/api/vitals/P001/latest');
            if (!response.ok) return;

            const data = await response.json();
            if (data.success && data.vitals) {
                const vitals = data.vitals;
                const status = data.patient_status || 'NORMAL';

                if (valHeartRate) animateValueUpdate(valHeartRate, vitals.heart_rate);
                if (valSpo2) animateValueUpdate(valSpo2, vitals.spo2);
                if (valTemp) animateValueUpdate(valTemp, parseFloat(vitals.temperature).toFixed(1));
                if (valMovement) valMovement.textContent = vitals.movement_status;

                if (spo2Progress) spo2Progress.style.width = `${vitals.spo2}%`;

                if (lastUpdatedSpan) {
                    lastUpdatedSpan.textContent = vitals.recorded_at;
                    lastUpdatedSpan.dataset.customTime = "true";
                }

                // Update Patient Alert System Status Badge (Part 4 Rule Engine)
                if (patientStatusBadge) {
                    patientStatusBadge.textContent = `RULE ENGINE STATUS: ${status}`;
                    patientStatusBadge.className = `badge status-badge status-${status.toLowerCase()}`;
                }

                // Execute AI/ML Prediction via POST /api/ml/predict (Part 5)
                fetchMlPrediction(vitals);
            }
        } catch (error) {
            console.error('Error fetching latest vitals:', error);
        }
    }

    // 4. Fetch AI/ML Risk Prediction (POST /api/ml/predict)
    async function fetchMlPrediction(vitalRecord) {
        try {
            const payload = {
                patient_id: 'P001',
                heart_rate: vitalRecord.heart_rate,
                spo2: vitalRecord.spo2,
                temperature: vitalRecord.temperature,
                movement_status: vitalRecord.movement_status || 'Normal'
            };

            const response = await fetch('/api/ml/predict', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            if (!response.ok) return;

            const data = await response.json();
            if (data.success) {
                const cat = data.risk_category || 'LOW_RISK';
                const confPercent = Math.round((data.confidence || 0.95) * 100);

                if (mlRiskCategory) {
                    mlRiskCategory.innerHTML = `<i class="fa-solid fa-chart-pie"></i> ${cat}`;
                    mlRiskCategory.className = `badge ml-risk-badge ml-risk-${cat.toLowerCase()}`;
                }

                if (mlConfidence) mlConfidence.textContent = `${confPercent}%`;
                if (mlConfFill) mlConfFill.style.width = `${confPercent}%`;
                if (mlVersion) mlVersion.textContent = data.model_version || 'prototype-v1';

                if (mlAvailable) {
                    if (data.available) {
                        mlAvailable.className = 'ml-val-text text-green';
                        mlAvailable.innerHTML = '<i class="fa-solid fa-circle-check"></i> ONLINE';
                    } else {
                        mlAvailable.className = 'ml-val-text text-amber';
                        mlAvailable.innerHTML = '<i class="fa-solid fa-triangle-exclamation"></i> OFFLINE';
                    }
                }

                if (mlAnalysisTime) {
                    mlAnalysisTime.innerHTML = `<i class="fa-regular fa-clock"></i> ${data.timestamp || vitalRecord.recorded_at}`;
                }
            }
        } catch (error) {
            console.error('Error fetching ML prediction:', error);
        }
    }

    // 5. Poll Active Alerts from Server (GET /api/alerts/P001/active)
    async function fetchActiveAlerts() {
        try {
            const response = await fetch('/api/alerts/P001/active');
            if (!response.ok) return;

            const data = await response.json();
            if (data.success) {
                const count = data.active_alerts_count || 0;
                if (activeAlertsNum) activeAlertsNum.textContent = `${count} Active Alert(s)`;
                if (alertsCountPill) {
                    alertsCountPill.className = `status-indicator-pill ${count > 0 ? 'red' : 'green'}`;
                }
            }
        } catch (error) {
            console.error('Error fetching active alerts:', error);
        }
    }

    // 6. Poll Device Connection Status from Server (GET /api/device/status)
    async function fetchDeviceStatus() {
        try {
            const response = await fetch('/api/device/status?device_id=LIFEOS-001');
            if (!response.ok) return;

            const data = await response.json();
            if (data.success) {
                const status = data.connection_status; // "CONNECTED", "OFFLINE", "ERROR", "NOT_CONFIGURED"
                const lastComm = data.last_communication;
                const source = data.data_source || 'SIMULATED';

                if (deviceStatusText) deviceStatusText.textContent = status;
                if (lastCommSpan) lastCommSpan.textContent = lastComm;

                const sourceElement = document.getElementById('device-source-text');
                if (sourceElement) sourceElement.textContent = source;

                if (deviceStatusPill) {
                    let colorClass = 'red';
                    if (status === 'CONNECTED') colorClass = 'green';
                    else if (status === 'ERROR') colorClass = 'amber';
                    deviceStatusPill.className = `status-indicator-pill ${colorClass}`;
                }
            }
        } catch (error) {
            console.error('Error fetching device status:', error);
        }
    }

    // 7. Combined Refresh Tick
    function refreshDashboardData() {
        fetchLatestVitals();
        fetchActiveAlerts();
        fetchDeviceStatus();
    }

    // Start 3-Second Periodic Polling
    pollInterval = setInterval(refreshDashboardData, 3000);

    // Manual Refresh / Sensor Read Button Handler
    if (btnSimulatePulse) {
        btnSimulatePulse.addEventListener('click', async () => {
            btnSimulatePulse.disabled = true;
            btnSimulatePulse.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Refreshing...';
            await refreshDashboardData();
            setTimeout(() => {
                btnSimulatePulse.disabled = false;
                btnSimulatePulse.innerHTML = '<i class="fa-solid fa-rotate"></i> Manual Sensor Read';
            }, 500);
        });
    }

    // Auto-Poll Toggle Button Handler
    if (btnAutoToggle) {
        btnAutoToggle.addEventListener('click', () => {
            isPolling = !isPolling;
            if (isPolling) {
                autoStatusText.textContent = 'ON';
                btnAutoToggle.classList.remove('btn-outline');
                btnAutoToggle.classList.add('btn-primary');
                refreshDashboardData();
                pollInterval = setInterval(refreshDashboardData, 3000);
            } else {
                autoStatusText.textContent = 'OFF';
                btnAutoToggle.classList.remove('btn-primary');
                btnAutoToggle.classList.add('btn-outline');
                clearInterval(pollInterval);
            }
        });
    }
});

// Helper for subtle value flash on update
function animateValueUpdate(element, newValue) {
    if (element.textContent !== String(newValue)) {
        element.style.transition = 'color 0.2s ease, transform 0.2s ease';
        element.style.color = '#0284c7';
        element.style.transform = 'scale(1.1)';
        element.textContent = newValue;

        setTimeout(() => {
            element.style.color = '';
            element.style.transform = '';
        }, 300);
    }
}

// Global Helper for triggering location-aware emergency response workflow (Part 6)
function triggerEmergencyWorkflow(alertId) {
    if (!alertId) return;
    if (confirm('Initiate location-aware emergency response workflow for Alert #' + alertId + '? (TEST MODE)')) {
        fetch('/api/emergency-events', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ alert_id: alertId })
        })
        .then(res => res.json())
        .then(data => {
            if (data.success && data.event_id) {
                window.location.href = '/emergency/' + data.event_id;
            } else {
                alert('Error initiating emergency workflow: ' + (data.error || 'Unknown error'));
            }
        })
        .catch(err => alert('Failed to contact server: ' + err));
    }
}

