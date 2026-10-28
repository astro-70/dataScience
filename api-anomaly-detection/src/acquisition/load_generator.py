"""
=====================================================================
Load Generator Module (src/acquisition/load_generator.py)
U23AD491 Data Science Project: API Anomaly Detection System
=====================================================================
Simulates realistic multi-microservice production traffic across 30 days
at 1-minute granularity with:
  1. Daily and weekly seasonality (diurnal peaks, weekend variance)
  2. Baseline right-skewed latency (lognormal)
  3. Labeled injected anomalies (6 distinct failure modes)
  4. Synthetic data impurities (missing values, duplicates, outliers)
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import random
from pathlib import Path
from src.utils.config import (
    MICROSERVICES,
    RAW_DATA_DIR,
    RANDOM_SEED,
)
from src.utils.logger import get_logger

logger = get_logger("Load-Generator")


def generate_seasonality_factor(timestamp: datetime) -> float:
    """Calculates diurnal (hour-of-day) and weekly traffic multiplier."""
    hour = timestamp.hour + timestamp.minute / 60.0
    day_of_week = timestamp.weekday()  # 0=Monday, 6=Sunday

    # Diurnal twin-peak curve (11:00-13:00 and 19:00-22:00 peaks)
    # Using smooth sinusoidal mixture
    diurnal = (
        0.35
        + 0.40 * np.exp(-((hour - 12.0) ** 2) / (2 * 2.5**2))
        + 0.55 * np.exp(-((hour - 20.5) ** 2) / (2 * 2.2**2))
        + 0.15 * np.sin(np.pi * hour / 12.0)
    )
    diurnal = max(0.15, diurnal)

    # Weekend effect: slightly elevated evening traffic, lower work hours
    is_weekend = day_of_week >= 5
    weekend_multiplier = 0.85 if is_weekend and (9 <= hour <= 17) else 1.10 if is_weekend else 1.0

    return float(diurnal * weekend_multiplier)


def generate_microservice_traffic(
    days: int = 30,
    interval_minutes: int = 5,
    insert_impurities: bool = True,
    seed: int = RANDOM_SEED,
) -> pd.DataFrame:
    """
    Generates synthetic time series metrics dataset across all microservices.

    Parameters:
      days: Number of days to simulate (default 30)
      interval_minutes: Granularity in minutes (default 5 for fast yet detailed analysis)
      insert_impurities: Whether to inject missing values, duplicates and outliers
      seed: Random seed for reproducibility

    Returns:
      pd.DataFrame with full microservices API performance logs
    """
    np.random.seed(seed)
    random.seed(seed)

    start_date = datetime(2026, 9, 1, 0, 0, 0)
    total_intervals = (days * 24 * 60) // interval_minutes
    timestamps = [start_date + timedelta(minutes=i * interval_minutes) for i in range(total_intervals)]

    records = []
    logger.info(f"Generating synthetic traffic for {len(MICROSERVICES)} services across {days} days ({total_intervals} time intervals)...")

    # Pre-plan anomaly schedule across the timeline to ensure balanced representation
    # We will inject 6 types of anomalies across different services and dates
    anomaly_schedule = [
        # (day_idx, start_hour, duration_minutes, service, anomaly_type)
        (2, 14, 15, "auth-service", "latency_spike"),
        (4, 10, 180, "payment-service", "gradual_degradation"),  # memory leak
        (6, 19, 25, "order-service", "error_burst"),
        (8, 3, 40, "inventory-service", "traffic_drop"),  # outage
        (11, 20, 30, "user-service", "traffic_surge"),  # flash sale / DDoS
        (13, 11, 45, "payment-service", "cpu_saturation"),
        (16, 15, 20, "order-service", "latency_spike"),
        (18, 9, 210, "auth-service", "gradual_degradation"),
        (21, 21, 35, "payment-service", "error_burst"),
        (23, 2, 50, "notification-service", "traffic_drop"),
        (25, 18, 40, "order-service", "traffic_surge"),
        (28, 16, 50, "inventory-service", "cpu_saturation"),
    ]

    for t in timestamps:
        seasonality = generate_seasonality_factor(t)

        for svc_name, meta in MICROSERVICES.items():
            endpoint = meta["endpoint"]
            method = meta["method"]
            base_lat = meta["base_latency_ms"]
            base_cpu = meta["base_cpu_pct"]
            base_mem = meta["base_mem_mb"]
            instance_id = random.choice(meta["instances"])

            # Check if current timestamp falls within an injected anomaly window
            current_day = (t - start_date).days
            active_anomaly = "normal"
            is_anomaly = 0
            anomaly_progress = 0.0  # 0 to 1 progress for gradual anomalies

            for a_day, a_hour, a_dur, a_svc, a_type in anomaly_schedule:
                if current_day == a_day and a_svc == svc_name:
                    a_start_dt = start_date + timedelta(days=a_day, hours=a_hour)
                    a_end_dt = a_start_dt + timedelta(minutes=a_dur)
                    if a_start_dt <= t <= a_end_dt:
                        active_anomaly = a_type
                        is_anomaly = 1
                        total_secs = (a_end_dt - a_start_dt).total_seconds()
                        elapsed_secs = (t - a_start_dt).total_seconds()
                        anomaly_progress = elapsed_secs / total_secs if total_secs > 0 else 1.0
                        break

            # Requests count based on Poisson distribution modulated by seasonality
            base_lambda = 120.0 * seasonality
            req_count = max(5, int(np.random.poisson(base_lambda)))

            # Normal baseline metrics with lognormal latency to mirror production right-skew
            # Lognormal parameters: mean and sigma in log space
            sigma_log = 0.28
            mu_log = np.log(base_lat) - (sigma_log**2) / 2
            response_time = np.random.lognormal(mu_log, sigma_log)

            cpu_percent = max(4.0, min(92.0, np.random.normal(base_cpu * seasonality, 3.5)))
            memory_mb = max(50.0, np.random.normal(base_mem, 12.0))
            status_code = 200

            # -------------------------------------------------------------
            # Apply Anomaly Signatures
            # -------------------------------------------------------------
            if active_anomaly == "latency_spike":
                # Sudden dramatic 5x-12x latency surge
                response_time = base_lat * np.random.uniform(5.5, 12.0)
                cpu_percent = min(96.0, cpu_percent * 1.5)

            elif active_anomaly == "gradual_degradation":
                # Memory leak: memory climbs to ~850MB, latency climbs with it
                mem_growth = (base_mem * 2.8) * anomaly_progress
                memory_mb = base_mem + mem_growth + np.random.normal(0, 5)
                lat_multiplier = 1.0 + (7.0 * anomaly_progress)
                response_time = base_lat * lat_multiplier * np.random.uniform(0.9, 1.2)
                cpu_percent = min(95.0, cpu_percent + 20.0 * anomaly_progress)

            elif active_anomaly == "error_burst":
                # HTTP 500/502/503 wave
                status_code = np.random.choice([500, 502, 503, 504], p=[0.45, 0.25, 0.20, 0.10])
                response_time = base_lat * np.random.uniform(2.0, 4.5)
                cpu_percent = min(90.0, cpu_percent * 1.3)

            elif active_anomaly == "traffic_drop":
                # Service outage / network blackhole: requests drop by ~95%
                req_count = max(0, int(np.random.poisson(2.0)))
                status_code = 503 if random.random() < 0.6 else 200

            elif active_anomaly == "traffic_surge":
                # DDoS / flash sale: 6x-10x request surge causing queue latency
                req_count = int(req_count * np.random.uniform(6.0, 10.0))
                cpu_percent = min(99.0, np.random.uniform(88.0, 98.5))
                response_time = base_lat * np.random.uniform(3.5, 7.0)

            elif active_anomaly == "cpu_saturation":
                # Infinite loop / thread lock: CPU pins at 97-100%
                cpu_percent = np.random.uniform(96.0, 99.8)
                response_time = base_lat * np.random.uniform(4.0, 9.0)
                if random.random() < 0.35:
                    status_code = 504

            # Standard background noise error (<0.4% chance under normal conditions)
            if active_anomaly == "normal" and random.random() < 0.003:
                status_code = random.choice([400, 401, 404, 500])

            request_size = max(0.1, np.random.normal(meta["avg_req_kb"], 0.2))
            response_size = max(0.1, np.random.normal(meta["avg_res_kb"], 0.4))

            records.append({
                "timestamp": t.strftime("%Y-%m-%d %H:%M:%S"),
                "service": svc_name,
                "endpoint": endpoint,
                "method": method,
                "status_code": int(status_code),
                "response_time_ms": round(float(response_time), 2),
                "request_count": int(req_count),
                "request_size_kb": round(float(request_size), 2),
                "response_size_kb": round(float(response_size), 2),
                "cpu_percent": round(float(cpu_percent), 2),
                "memory_mb": round(float(memory_mb), 2),
                "instance_id": instance_id,
                "is_anomaly": int(is_anomaly),
                "anomaly_type": active_anomaly,
            })

    df = pd.DataFrame(records)

    # -----------------------------------------------------------------
    # Synthetic Data Impurities (For Phase 3 Data Cleaning Syllabus Demo)
    # -----------------------------------------------------------------
    if insert_impurities:
        logger.info("Injecting realistic data impurities (missing values, duplicates, outliers)...")
        n_rows = len(df)

        # 1. Missing Values (NaN) in ~1.5% of numeric columns
        nan_indices_lat = np.random.choice(n_rows, size=int(n_rows * 0.015), replace=False)
        nan_indices_cpu = np.random.choice(n_rows, size=int(n_rows * 0.012), replace=False)
        nan_indices_mem = np.random.choice(n_rows, size=int(n_rows * 0.010), replace=False)

        df.loc[nan_indices_lat, "response_time_ms"] = np.nan
        df.loc[nan_indices_cpu, "cpu_percent"] = np.nan
        df.loc[nan_indices_mem, "memory_mb"] = np.nan

        # 2. Measurement Glitch Outliers (e.g. sensor recording error 99999.0 or negative)
        glitch_indices = np.random.choice(n_rows, size=15, replace=False)
        for idx in glitch_indices:
            if random.random() < 0.5:
                df.loc[idx, "response_time_ms"] = 99999.0  # Sensor max overflow
            else:
                df.loc[idx, "response_time_ms"] = -50.0   # Impossible negative clock drift

        # 3. Duplicate Rows (~0.8% duplicated log entries)
        dup_indices = np.random.choice(n_rows, size=int(n_rows * 0.008), replace=False)
        duplicates = df.iloc[dup_indices].copy()
        df = pd.concat([df, duplicates], ignore_index=True)
        # Randomly shuffle slightly to interleave duplicates
        df = df.sample(frac=1.0, random_state=seed).reset_index(drop=True)

    output_path = RAW_DATA_DIR / "synthetic_microservices_logs.csv"
    df.to_csv(output_path, index=False)
    logger.info(f"Dataset generation complete! Saved {len(df)} records to {output_path}")

    return df


if __name__ == "__main__":
    generate_microservice_traffic(days=30, interval_minutes=5)
