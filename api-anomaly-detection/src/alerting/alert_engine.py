"""
=====================================================================
Intelligent Alerting Engine (src/alerting/alert_engine.py)
U23AD491 Data Science Project: API Anomaly Detection System
=====================================================================
Features:
  1. Anomaly score normalization (0 - 100)
  2. Multi-tier Dynamic Severity Classification (INFO, WARNING, CRITICAL)
  3. Bayesian Confidence Score Calibration
  4. Temporal Deduplication & Incident Grouping
  5. Alert Cooldown / Rate-Limiting (Prevents Alert Fatigue)
  6. Heuristic & Correlation Root-Cause Inference
  7. Microservice Dependency Topology Awareness
  8. Streaming Replay Mode over Historical Telemetry
  9. Benchmark against Naive Static-Threshold Alerting
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

from src.utils.config import (
    PROCESSED_DATA_DIR,
    EXPORTS_DIR,
    SERVICE_DEPENDENCIES,
    COOLDOWN_MINUTES,
    NAIVE_LATENCY_THRESHOLD_MS,
    NAIVE_ERROR_RATE_THRESHOLD,
)
from src.utils.logger import get_logger
from src.alerting.notifier import NotificationDispatcher

logger = get_logger("Alert-Engine")


class IntelligentAlertEngine:
    """Production-grade alerting engine featuring Bayesian scoring and root-cause analysis."""

    def __init__(self, cooldown_minutes: int = COOLDOWN_MINUTES):
        self.cooldown_minutes = cooldown_minutes
        self.notifier = NotificationDispatcher()
        self.active_incidents: Dict[str, Dict[str, Any]] = {}
        self.last_alert_time: Dict[str, datetime] = {}
        self.closed_incidents: List[Dict[str, Any]] = []

    def compute_bayesian_confidence(self, latency_ms: float, has_5xx: bool, ensemble_score: float) -> float:
        """
        Calculates calibrated Bayesian confidence score:
          - Combines empirical posterior P(Anomaly | Signals) with ML ensemble score.
        """
        # Baseline posterior probabilities derived in Phase 2
        if latency_ms > 350.0 and has_5xx:
            bayes_prob = 0.923
        elif has_5xx:
            bayes_prob = 0.441
        elif latency_ms > 350.0:
            bayes_prob = 0.350
        else:
            bayes_prob = 0.150

        # Weighted combination: 60% Bayesian evidence + 40% ML ensemble score
        ml_prob = ensemble_score / 100.0
        combined = (bayes_prob * 0.60) + (ml_prob * 0.40)
        confidence_pct = min(99.0, max(15.0, combined * 100.0))
        return round(confidence_pct, 1)

    def determine_severity(
        self, score: float, duration_min: float, error_rate: float, latency_ms: float
    ) -> str:
        """
        Dynamic severity classifier considering impact, magnitude, and persistence.
        """
        if score >= 85.0 or error_rate >= 0.20 or latency_ms > 1200.0 or duration_min >= 45.0:
            return "CRITICAL"
        elif score >= 65.0 or error_rate >= 0.05 or latency_ms > 450.0:
            return "WARNING"
        else:
            return "INFO"

    def infer_root_cause(
        self,
        service: str,
        latency_ms: float,
        cpu_pct: float,
        memory_mb: float,
        error_rate: float,
        req_count: int,
        timestamp: datetime,
    ) -> Tuple[str, str, str]:
        """
        Infers probable root cause and remediation based on metric patterns & dependencies.
        Returns: (probable_cause, root_cause_service, recommended_remediation)
        """
        root_cause_service = service

        # 1. Dependency Analysis: Check if downstream dependencies are also failing
        downstream = SERVICE_DEPENDENCIES.get(service, [])
        for dep in downstream:
            if dep in self.active_incidents:
                root_cause_service = dep
                return (
                    f"Cascading failure propagated from upstream dependency '{dep}'",
                    dep,
                    f"Check health and logs for {dep} before investigating {service}.",
                )

        # 2. Heuristic Pattern Rules
        if cpu_pct >= 90.0:
            return (
                "CPU Saturation (Thread pool exhaustion or infinite compute loop)",
                root_cause_service,
                "Scale out replica pods and inspect top thread CPU profiles via profiler.",
            )
        elif memory_mb >= 550.0:
            return (
                "Gradual Memory Leak (Heap bloat / uncollected references)",
                root_cause_service,
                "Perform heap dump, inspect GC logs, and trigger rolling restart.",
            )
        elif error_rate >= 0.25:
            return (
                "Downstream Service or Database Connection Pool Exhaustion",
                root_cause_service,
                "Inspect DB connection pools, circuit breakers, and database latency.",
            )
        elif req_count <= 2:
            return (
                "Service Outage or Ingress Gateway Routing Drop",
                root_cause_service,
                "Verify API gateway routing rules, DNS resolution, and ingress controller.",
            )
        elif req_count >= 500:
            return (
                "Traffic Surge / Flash Sale (Excessive concurrency queuing)",
                root_cause_service,
                "Activate auto-scaler HPA, enforce rate-limiting, and enable edge CDN caching.",
            )
        else:
            return (
                "Transient Latency Spike (I/O Wait or Major Garbage Collection Pause)",
                root_cause_service,
                "Monitor for recurring spikes and review recent code deployment diffs.",
            )

    def process_telemetry_event(self, row: pd.Series) -> Optional[Dict[str, Any]]:
        """
        Processes a single streaming telemetry observation.
        Applies deduplication, Bayesian confidence, and cooldown management.
        """
        svc = row["service"]
        timestamp = pd.to_datetime(row["timestamp"])
        is_anom = int(row.get("pred_MajorityVotingEnsemble", 0))
        score = float(row.get("ensemble_score", 50.0))
        lat = float(row["response_time_ms"])
        cpu = float(row["cpu_percent"])
        mem = float(row["memory_mb"])
        req_cnt = int(row["request_count"])
        has_5xx = int(row["status_code"]) >= 500
        err_rate = float(row.get("rolling_error_rate", 0.0))

        # Check if an ongoing incident exists for this service
        incident = self.active_incidents.get(svc)

        if is_anom:
            if incident is None:
                # Open NEW incident
                confidence = self.compute_bayesian_confidence(lat, has_5xx, score)
                cause, root_svc, remed = self.infer_root_cause(svc, lat, cpu, mem, err_rate, req_cnt, timestamp)
                severity = self.determine_severity(score, 5.0, err_rate, lat)
                incident_id = f"INC-{svc[:3].upper()}-{int(timestamp.timestamp()) % 100000}"

                incident = {
                    "incident_id": incident_id,
                    "service": svc,
                    "root_cause_service": root_svc,
                    "start_time": timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                    "last_seen": timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                    "duration_minutes": 5.0,
                    "peak_score": round(score, 1),
                    "peak_latency_ms": round(lat, 1),
                    "peak_cpu_pct": round(cpu, 1),
                    "confidence_pct": confidence,
                    "severity": severity,
                    "probable_cause": cause,
                    "recommended_remediation": remed,
                    "event_count": 1,
                    "alert_dispatched": False,
                }
                self.active_incidents[svc] = incident
            else:
                # UPDATE existing incident (Deduplication)
                incident["last_seen"] = timestamp.strftime("%Y-%m-%d %H:%M:%S")
                incident["duration_minutes"] += 5.0
                incident["peak_score"] = max(incident["peak_score"], round(score, 1))
                incident["peak_latency_ms"] = max(incident["peak_latency_ms"], round(lat, 1))
                incident["peak_cpu_pct"] = max(incident["peak_cpu_pct"], round(cpu, 1))
                incident["event_count"] += 1
                # Re-evaluate severity
                incident["severity"] = self.determine_severity(
                    incident["peak_score"], incident["duration_minutes"], err_rate, incident["peak_latency_ms"]
                )

            # Check Cooldown before triggering notification
            last_alert = self.last_alert_time.get(svc)
            can_alert = False
            if last_alert is None:
                can_alert = True
            else:
                elapsed_min = (timestamp - last_alert).total_seconds() / 60.0
                if elapsed_min >= self.cooldown_minutes:
                    can_alert = True
                elif incident["severity"] == "CRITICAL" and not incident.get("alert_dispatched", False):
                    can_alert = True  # Escalate immediately if severity is CRITICAL

            if can_alert and incident["severity"] in ["WARNING", "CRITICAL"]:
                incident["alert_dispatched"] = True
                self.last_alert_time[svc] = timestamp
                self.notifier.dispatch(incident)
                return incident

        else:
            # Metric is currently normal: if incident was active, close it
            if incident is not None:
                self.closed_incidents.append(incident)
                del self.active_incidents[svc]

        return None

    def replay_telemetry_stream(self, test_df: pd.DataFrame) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Replays historical test partition sequentially, simulating real-time operations.
        Compares intelligent alerts against naive static thresholds.
        """
        logger.info(f"Replaying {len(test_df)} telemetry events through Intelligent Alert Engine...")
        dispatched_alerts = []

        # Naive Static-Threshold Counters
        naive_alert_count = 0
        naive_false_alarms = 0

        records = test_df.to_dict(orient="records")
        for row in records:
            # 1. Intelligent Alert Processing: Only dispatch actionable incidents (WARNING & CRITICAL)
            # INFO events are logged as background telemetry without waking on-call engineers
            alert = self.process_telemetry_event(row)
            if alert and alert["severity"] in ["WARNING", "CRITICAL"]:
                dispatched_alerts.append(alert)

            # 2. Naive Static Threshold System: Typical naive static rule in legacy APM
            # (Global static latency > 180ms or HTTP 5xx without per-service baseline or cooldown)
            # This causes massive false alarms on payment-service (base 210ms) and misses auth-service anomalies (base 45ms)
            is_naive_alert = (row["response_time_ms"] > 180.0) or (row["status_code"] >= 500)
            if is_naive_alert:
                naive_alert_count += 1
                if row.get("is_anomaly", 0) == 0:
                    naive_false_alarms += 1

        # Close any lingering active incidents
        for inc in self.active_incidents.values():
            self.closed_incidents.append(inc)
        self.active_incidents.clear()

        # Compute Comparative Benchmark
        total_intelligent_alerts = len(dispatched_alerts)
        alert_reduction_pct = (
            ((naive_alert_count - total_intelligent_alerts) / naive_alert_count * 100.0)
            if naive_alert_count > 0
            else 0.0
        )

        comparison_metrics = {
            "Naive_Static_Alerts": naive_alert_count,
            "Naive_False_Alarms": naive_false_alarms,
            "Intelligent_Incidents_Dispatched": total_intelligent_alerts,
            "Alert_Noise_Reduction_Pct": round(alert_reduction_pct, 2),
            "Cooldown_Minutes": self.cooldown_minutes,
        }

        # Save alerts to CSV
        if dispatched_alerts:
            alerts_df = pd.DataFrame(dispatched_alerts)
            alerts_df.to_csv(EXPORTS_DIR / "alerts.csv", index=False)
            logger.info(f"Exported {len(alerts_df)} deduplicated incident alerts to {EXPORTS_DIR / 'alerts.csv'}")

        # Save benchmark comparison
        comp_df = pd.DataFrame([comparison_metrics])
        comp_df.to_csv(EXPORTS_DIR / "alert_benchmark_comparison.csv", index=False)

        logger.info(
            f"Alerting Benchmark: Naive={naive_alert_count} alerts vs Intelligent={total_intelligent_alerts} incidents. "
            f"Alert Fatigue Reduction = {alert_reduction_pct:.1f}%!"
        )

        return dispatched_alerts, comparison_metrics


def run_alerting_pipeline() -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """Runs the full alert engine replay pipeline."""
    pred_path = PROCESSED_DATA_DIR / "test_predictions.csv"
    if not pred_path.exists():
        raise FileNotFoundError(f"Missing test predictions at {pred_path}")

    test_df = pd.read_csv(pred_path)
    engine = IntelligentAlertEngine(cooldown_minutes=COOLDOWN_MINUTES)
    alerts, metrics = engine.replay_telemetry_stream(test_df)
    return alerts, metrics


if __name__ == "__main__":
    run_alerting_pipeline()
