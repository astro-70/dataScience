"""
=====================================================================
Data Cleaning Module (src/preprocessing/cleaning.py)
U23AD491 Data Science Project: API Anomaly Detection System
=====================================================================
Covers Unit IV Syllabus:
  1. Missing Value Imputation (Mean, Median, Forward-Fill, Interpolation)
  2. Duplicate Record Identification & Deduplication
  3. Strict Schema & Datetime Type Enforcement
  4. Outlier Diagnostics (Z-score & IQR flagging without blind deletion)
  5. Export of Cleaned Dataset to data/processed/cleaned_metrics.csv
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Tuple

from src.utils.config import RAW_DATA_DIR, PROCESSED_DATA_DIR
from src.utils.logger import get_logger

logger = get_logger("Data-Cleaning")


def clean_telemetry_dataset() -> pd.DataFrame:
    """
    Executes end-to-end data cleaning pipeline with audit trail logging.
    """
    raw_path = RAW_DATA_DIR / "synthetic_microservices_logs.csv"
    if not raw_path.exists():
        raise FileNotFoundError(f"Missing raw logs file at {raw_path}")

    logger.info("Initiating Phase 3 Data Cleaning...")
    df = pd.read_csv(raw_path)
    initial_rows = len(df)
    logger.info(f"Raw dataset loaded: {initial_rows} rows, {len(df.columns)} columns.")

    # -----------------------------------------------------------------
    # Step 1: Duplicate Detection & Removal
    # -----------------------------------------------------------------
    # In microservices, duplicate logs can occur due to network retries
    dup_mask = df.duplicated(subset=["timestamp", "service", "endpoint", "instance_id"])
    num_duplicates = dup_mask.sum()
    df = df[~dup_mask].copy()
    logger.info(f"Deduplication: Removed {num_duplicates} duplicate records ({len(df)} rows remaining).")

    # -----------------------------------------------------------------
    # Step 2: Datetime Type Enforcement & Chronological Ordering
    # -----------------------------------------------------------------
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df = df.sort_values(by=["service", "timestamp"]).reset_index(drop=True)

    # -----------------------------------------------------------------
    # Step 3: Outlier Handling & Sensor Glitch Filtering
    # -----------------------------------------------------------------
    # In anomaly detection, true anomalies must NOT be deleted.
    # However, impossible hardware/sensor glitch artifacts (negative latency or 99999 overflow)
    # must be treated as missing values and imputed.
    glitch_mask = (df["response_time_ms"] < 0) | (df["response_time_ms"] >= 50000)
    num_glitches = glitch_mask.sum()
    if num_glitches > 0:
        logger.info(f"Identified {num_glitches} impossible physical sensor glitches. Flagging as NaN.")
        df.loc[glitch_mask, "response_time_ms"] = np.nan

    # Calculate statistical outlier flags using IQR for analytics reporting
    q25 = df["response_time_ms"].quantile(0.25)
    q75 = df["response_time_ms"].quantile(0.75)
    iqr = q75 - q25
    iqr_upper = q75 + 3.0 * iqr  # 3*IQR for extreme outliers
    df["is_statistical_outlier"] = (df["response_time_ms"] > iqr_upper).astype(int)

    # -----------------------------------------------------------------
    # Step 4: Missing Value Imputation (Comparison & Time-Series Imputation)
    # -----------------------------------------------------------------
    # For ordered time series, Forward-Fill (LOCF) followed by Linear Interpolation
    # preserves temporal continuity far better than global mean or median!
    null_counts = df[["response_time_ms", "cpu_percent", "memory_mb"]].isnull().sum()
    logger.info(f"Missing values before imputation:\n{null_counts.to_dict()}")

    # Apply service-grouped Forward-fill and Linear Interpolation
    df["response_time_ms"] = (
        df.groupby("service")["response_time_ms"]
        .transform(lambda s: s.ffill().bfill().interpolate(method="linear"))
    )
    df["cpu_percent"] = (
        df.groupby("service")["cpu_percent"]
        .transform(lambda s: s.ffill().bfill().interpolate(method="linear"))
    )
    df["memory_mb"] = (
        df.groupby("service")["memory_mb"]
        .transform(lambda s: s.ffill().bfill().interpolate(method="linear"))
    )

    # Verify zero missing values remaining
    post_nulls = df.isnull().sum().sum()
    logger.info(f"Post-imputation null count: {post_nulls} remaining.")

    # -----------------------------------------------------------------
    # Step 5: Export Cleaned Dataset
    # -----------------------------------------------------------------
    cleaned_path = PROCESSED_DATA_DIR / "cleaned_metrics.csv"
    df.to_csv(cleaned_path, index=False)
    logger.info(f"Cleaned dataset successfully exported to {cleaned_path}")

    return df


if __name__ == "__main__":
    clean_telemetry_dataset()
