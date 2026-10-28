"""
=====================================================================
Dashboard Data Exporter (src/visualization/exporter.py)
U23AD491 Data Science Project: API Anomaly Detection System
=====================================================================
Generates standardized CSV exports for Tableau Public and Power BI Desktop:
  1. data/exports/metrics_clean.csv
  2. data/exports/anomalies.csv
  3. data/exports/alerts.csv
  4. data/exports/service_summary.csv
"""

import pandas as pd
import numpy as np
from pathlib import Path

from src.utils.config import PROCESSED_DATA_DIR, EXPORTS_DIR
from src.utils.logger import get_logger

logger = get_logger("Dashboard-Exporter")


def generate_dashboard_exports() -> None:
    """Creates pivot-ready, clean CSVs for Tableau and Power BI ingestion."""
    logger.info("Generating clean CSV exports for Tableau and Power BI...")

    cleaned_path = PROCESSED_DATA_DIR / "cleaned_metrics.csv"
    featured_path = PROCESSED_DATA_DIR / "featured_metrics.csv"
    test_pred_path = PROCESSED_DATA_DIR / "test_predictions.csv"
    alerts_path = EXPORTS_DIR / "alerts.csv"

    if not cleaned_path.exists():
        raise FileNotFoundError(f"Missing {cleaned_path}")

    df_clean = pd.read_csv(cleaned_path)

    # 1. metrics_clean.csv
    # Core operational metrics with parsed dates
    export_metrics_path = EXPORTS_DIR / "metrics_clean.csv"
    core_cols = [
        "timestamp",
        "service",
        "endpoint",
        "method",
        "status_code",
        "response_time_ms",
        "request_count",
        "request_size_kb",
        "response_size_kb",
        "cpu_percent",
        "memory_mb",
        "instance_id",
        "is_anomaly",
        "anomaly_type",
    ]
    df_clean[core_cols].to_csv(export_metrics_path, index=False)
    logger.info(f"1. Exported metrics_clean.csv ({len(df_clean)} rows)")

    # 2. anomalies.csv
    # Detailed anomaly records including model scores
    if test_pred_path.exists():
        df_pred = pd.read_csv(test_pred_path)
        anomalies_df = df_pred[(df_pred["is_anomaly"] == 1) | (df_pred["pred_MajorityVotingEnsemble"] == 1)].copy()
        export_anom_path = EXPORTS_DIR / "anomalies.csv"
        anom_cols = [
            "timestamp",
            "service",
            "endpoint",
            "status_code",
            "response_time_ms",
            "cpu_percent",
            "memory_mb",
            "is_anomaly",
            "anomaly_type",
            "pred_MajorityVotingEnsemble",
            "ensemble_score",
            "pca_1",
            "pca_2",
        ]
        available_anom_cols = [c for c in anom_cols if c in anomalies_df.columns]
        anomalies_df[available_anom_cols].to_csv(export_anom_path, index=False)
        logger.info(f"2. Exported anomalies.csv ({len(anomalies_df)} rows)")

    # 3. service_summary.csv
    # High-level executive KPI roll-up
    alerts_count_map = {}
    if alerts_path.exists():
        try:
            alerts_df = pd.read_csv(alerts_path)
            alerts_count_map = alerts_df["service"].value_counts().to_dict()
        except Exception:
            alerts_count_map = {}

    summary_records = []
    for svc, grp in df_clean.groupby("service"):
        total_reqs = grp["request_count"].sum()
        lat = grp["response_time_ms"]
        errs = (grp["status_code"] >= 500).sum()
        total_anom = (grp["is_anomaly"] == 1).sum()

        summary_records.append({
            "service": svc,
            "total_intervals": len(grp),
            "total_requests": int(total_reqs),
            "avg_latency_ms": round(lat.mean(), 2),
            "median_latency_ms": round(lat.median(), 2),
            "p95_latency_ms": round(lat.quantile(0.95), 2),
            "max_latency_ms": round(lat.max(), 2),
            "avg_cpu_percent": round(grp["cpu_percent"].mean(), 2),
            "max_cpu_percent": round(grp["cpu_percent"].max(), 2),
            "avg_memory_mb": round(grp["memory_mb"].mean(), 2),
            "total_errors_5xx": int(errs),
            "error_rate_pct": round((errs / len(grp)) * 100.0, 3),
            "ground_truth_anomalies": int(total_anom),
            "actionable_alerts_count": int(alerts_count_map.get(svc, 0)),
        })

    summary_df = pd.DataFrame(summary_records)
    summary_path = EXPORTS_DIR / "service_summary.csv"
    summary_df.to_csv(summary_path, index=False)
    logger.info(f"3. Exported service_summary.csv ({len(summary_df)} services)")

    logger.info("All dashboard CSV exports successfully created!")


if __name__ == "__main__":
    generate_dashboard_exports()
