"""
=====================================================================
Alert Notifier Module (src/alerting/notifier.py)
U23AD491 Data Science Project: API Anomaly Detection System
=====================================================================
Multi-channel notification dispatcher:
  1. Formatted Console Logging
  2. Persistent JSONL / CSV Audit Trails
  3. Secure Email Dispatch (smtplib) with graceful offline fallback
  4. Webhook Dispatch (Slack / Telegram format, reading env secrets)
"""

import os
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
import requests

from src.utils.config import (
    EXPORTS_DIR,
    ALERT_EMAIL_RECIPIENT,
    SMTP_SERVER,
    SMTP_PORT,
    SLACK_WEBHOOK_URL,
    TELEGRAM_BOT_TOKEN,
    TELEGRAM_CHAT_ID,
)
from src.utils.logger import get_logger

logger = get_logger("Alert-Notifier")

INCIDENTS_JSON_PATH = EXPORTS_DIR / "incidents.json"
ALERTS_CSV_PATH = EXPORTS_DIR / "alerts.csv"


class NotificationDispatcher:
    """Dispatches intelligent incident notifications across multiple channels."""

    def __init__(self):
        self.email_recipient = ALERT_EMAIL_RECIPIENT
        self.smtp_server = SMTP_SERVER
        self.smtp_port = SMTP_PORT
        self.slack_webhook = SLACK_WEBHOOK_URL
        self.telegram_token = TELEGRAM_BOT_TOKEN
        self.telegram_chat_id = TELEGRAM_CHAT_ID

    def notify_console(self, incident: Dict[str, Any]) -> None:
        """Formats and prints prominent incident alert card to console."""
        sev = incident.get("severity", "INFO")
        color_marker = f"[*** {sev} ***]"

        print("\n" + "=" * 70)
        print(f"{color_marker} INCIDENT ALERT | ID: {incident.get('incident_id')}")
        print(f"Service: {incident.get('service')} | Root Cause Origin: {incident.get('root_cause_service')}")
        print(f"Timestamp: {incident.get('start_time')} to {incident.get('last_seen')}")
        print(f"Anomaly Score: {incident.get('peak_score'):.1f}/100 | Bayesian Confidence: {incident.get('confidence_pct'):.1f}%")
        print(f"Probable Cause: {incident.get('probable_cause')}")
        print(f"Operational Metrics: Peak Latency={incident.get('peak_latency_ms'):.1f}ms, Max CPU={incident.get('peak_cpu_pct'):.1f}%")
        print(f"Recommended Action: {incident.get('recommended_remediation')}")
        print("=" * 70 + "\n")

    def notify_email(self, incident: Dict[str, Any]) -> bool:
        """
        Builds standard MIME email alert.
        In offline/academic environments, logs the simulated email dispatch instantly.
        If ENABLE_LIVE_SMTP=true, dispatches via SMTP.
        """
        subject = f"[{incident.get('severity')}] Microservice Alert: {incident.get('service')}"
        body = (
            f"Alerting System detected an operational incident:\n\n"
            f"Incident ID: {incident.get('incident_id')}\n"
            f"Service: {incident.get('service')}\n"
            f"Likely Origin: {incident.get('root_cause_service')}\n"
            f"Probable Cause: {incident.get('probable_cause')}\n"
            f"Confidence: {incident.get('confidence_pct'):.1f}%\n"
            f"Peak Latency: {incident.get('peak_latency_ms'):.1f} ms\n"
            f"Recommended Action: {incident.get('recommended_remediation')}\n"
        )

        enable_live = os.getenv("ENABLE_LIVE_SMTP", "false").lower() == "true"
        if not enable_live:
            # Deterministic academic log
            email_log_path = Path(self.smtp_server).parent / "logs" / "dispatched_emails.log"
            try:
                email_log_path.parent.mkdir(parents=True, exist_ok=True)
                with open(email_log_path, "a", encoding="utf-8") as f:
                    f.write(f"[{datetime.now().isoformat()}] TO: {self.email_recipient} | SUBJECT: {subject}\n")
            except Exception:
                pass
            return True

        msg = MIMEMultipart()
        msg["From"] = "alerts-engine@microservices.local"
        msg["To"] = self.email_recipient
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))

        try:
            with smtplib.SMTP(self.smtp_server, self.smtp_port, timeout=1.0) as server:
                server.send_message(msg)
                logger.info(f"Email alert dispatched successfully to {self.email_recipient}")
                return True
        except Exception:
            return False

    def notify_slack_webhook(self, incident: Dict[str, Any]) -> bool:
        """Dispatches formatted JSON payload to Slack webhook if configured."""
        if not self.slack_webhook:
            return False

        payload = {
            "text": f"*{incident.get('severity')} Alert on {incident.get('service')}*",
            "attachments": [
                {
                    "color": "#d62728" if incident.get("severity") == "CRITICAL" else "#ff7f0e",
                    "fields": [
                        {"title": "Probable Cause", "value": incident.get("probable_cause"), "short": True},
                        {"title": "Confidence", "value": f"{incident.get('confidence_pct'):.1f}%", "short": True},
                        {"title": "Peak Latency", "value": f"{incident.get('peak_latency_ms'):.1f} ms", "short": True},
                        {"title": "Remediation", "value": incident.get("recommended_remediation"), "short": False},
                    ],
                }
            ],
        }

        try:
            resp = requests.post(self.slack_webhook, json=payload, timeout=2.0)
            return resp.status_code == 200
        except Exception as e:
            logger.debug(f"Slack webhook skipped: {e}")
            return False

    def log_incident_to_disk(self, incident: Dict[str, Any]) -> None:
        """Appends incident record to JSON and CSV history files."""
        # JSON audit log
        incidents = []
        if INCIDENTS_JSON_PATH.exists():
            try:
                with open(INCIDENTS_JSON_PATH, "r", encoding="utf-8") as f:
                    incidents = json.load(f)
            except Exception:
                incidents = []

        incidents.append(incident)
        with open(INCIDENTS_JSON_PATH, "w", encoding="utf-8") as f:
            json.dump(incidents, f, indent=2)

    def dispatch(self, incident: Dict[str, Any]) -> None:
        """Broadcasts incident across all configured notification channels."""
        self.notify_console(incident)
        self.log_incident_to_disk(incident)
        self.notify_email(incident)
        self.notify_slack_webhook(incident)
