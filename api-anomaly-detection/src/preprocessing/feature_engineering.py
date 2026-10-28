"""
=====================================================================
Feature Engineering Module (src/preprocessing/feature_engineering.py)
U23AD491 Data Science Project: API Anomaly Detection System
=====================================================================
Covers Unit IV Syllabus:
  1. Temporal Calendar Features (Hour, DayOfWeek, IsWeekend, IsPeakHour)
  2. Windowed Rolling Aggregations (Rolling Mean, Std, Max over 15m, 60m)
  3. Lag Features & First-Order Differencing (Rates of change)
  4. Operational Derived Ratios (Latency/KB, CPU/Request, Rolling Error Rate)
  5. Deviation from Diurnal Historical Baselines (Hourly Z-score)
  6. Categorical Encoding (One-Hot & Label Encoding)
  7. Feature Scaling (StandardScaler)
  8. Dimensionality Reduction via PCA (Explained Variance & 2D Projection)
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.decomposition import PCA
import joblib
from pathlib import Path
from typing import Tuple, List

from src.utils.config import (
    PROCESSED_DATA_DIR,
    MODELS_DIR,
    FIGURES_DIR,
    RANDOM_SEED,
)
from src.utils.logger import get_logger

logger = get_logger("Feature-Engineering")


def extract_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Constructs rich domain features for microservice performance telemetry.
    """
    logger.info("Extracting time, rolling, lag, and ratio features...")
    df = df.copy()
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df = df.sort_values(by=["service", "timestamp"]).reset_index(drop=True)

    # 1. Temporal Calendar Features
    df["hour"] = df["timestamp"].dt.hour
    df["day_of_week"] = df["timestamp"].dt.dayofweek
    df["is_weekend"] = (df["day_of_week"] >= 5).astype(int)
    # Peak hours: 10:00-14:00 and 19:00-22:00
    df["is_peak_hour"] = df["hour"].apply(lambda h: 1 if (10 <= h <= 14) or (19 <= h <= 22) else 0)

    # 2. Windowed Rolling & Lag Features (Grouped by service to prevent leakage)
    processed_groups = []
    for svc, group in df.groupby("service"):
        g = group.copy()

        # Rolling windows (with 5-min intervals: 3 intervals = 15m, 12 intervals = 60m)
        g["latency_roll_mean_15m"] = g["response_time_ms"].rolling(3, min_periods=1).mean()
        g["latency_roll_std_15m"] = g["response_time_ms"].rolling(3, min_periods=1).std().fillna(0.0)
        g["latency_roll_max_15m"] = g["response_time_ms"].rolling(3, min_periods=1).max()

        g["latency_roll_mean_60m"] = g["response_time_ms"].rolling(12, min_periods=1).mean()
        g["latency_roll_std_60m"] = g["response_time_ms"].rolling(12, min_periods=1).std().fillna(0.0)

        g["cpu_roll_mean_15m"] = g["cpu_percent"].rolling(3, min_periods=1).mean()
        g["cpu_roll_max_15m"] = g["cpu_percent"].rolling(3, min_periods=1).max()
        g["mem_roll_mean_15m"] = g["memory_mb"].rolling(3, min_periods=1).mean()

        # Lag features (previous interval)
        g["latency_lag_1"] = g["response_time_ms"].shift(1).bfill()
        g["cpu_lag_1"] = g["cpu_percent"].shift(1).bfill()

        # Rate of change (First difference)
        g["latency_diff_1"] = g["response_time_ms"] - g["latency_lag_1"]
        g["cpu_diff_1"] = g["cpu_percent"] - g["cpu_lag_1"]
        g["memory_diff_1"] = g["memory_mb"] - g["memory_mb"].shift(1).bfill()

        # Windowed Error Rate (5xx count / total requests)
        is_5xx = (g["status_code"] >= 500).astype(float)
        g["rolling_error_rate"] = is_5xx.rolling(6, min_periods=1).mean()

        processed_groups.append(g)

    df_featured = pd.concat(processed_groups, ignore_index=True)

    # 3. Derived Operational Ratios
    df_featured["requests_per_minute"] = df_featured["request_count"] / 5.0
    df_featured["latency_per_kb"] = df_featured["response_time_ms"] / (df_featured["response_size_kb"] + 0.01)
    df_featured["cpu_per_request"] = df_featured["cpu_percent"] / (df_featured["request_count"] + 0.1)

    # 4. Hourly Baseline Z-score Deviation
    # Computes how much current latency deviates from the average historical latency for that specific hour & service
    hourly_baselines = (
        df_featured.groupby(["service", "hour"])["response_time_ms"]
        .agg(["mean", "std"])
        .reset_index()
        .rename(columns={"mean": "hourly_base_mean", "std": "hourly_base_std"})
    )
    df_featured = df_featured.merge(hourly_baselines, on=["service", "hour"], how="left")
    df_featured["hourly_base_std"] = df_featured["hourly_base_std"].replace(0, 1.0).fillna(1.0)
    df_featured["hourly_z_deviation"] = (
        (df_featured["response_time_ms"] - df_featured["hourly_base_mean"]) / df_featured["hourly_base_std"]
    ).fillna(0.0)

    # 5. Label Encoding for Categoricals
    le_endpoint = LabelEncoder()
    df_featured["endpoint_code"] = le_endpoint.fit_transform(df_featured["endpoint"])

    le_anomaly = LabelEncoder()
    df_featured["anomaly_type_code"] = le_anomaly.fit_transform(df_featured["anomaly_type"])

    # One-Hot Encoding for Service and Method (retaining original categorical columns for routing)
    for svc in df_featured["service"].unique():
        df_featured[f"service_{svc}"] = (df_featured["service"] == svc).astype(int)
    for m in df_featured["method"].unique():
        df_featured[f"method_{m}"] = (df_featured["method"] == m).astype(int)
    df_encoded = df_featured

    logger.info(f"Feature engineering completed: Shape is {df_encoded.shape}")
    return df_encoded


def apply_pca_reduction(
    df: pd.DataFrame, feature_cols: List[str], n_components: int = 2
) -> Tuple[pd.DataFrame, PCA]:
    """
    Applies Principal Component Analysis (PCA) for dimensionality reduction
    and renders 2D projection scatter plot colored by ground-truth anomaly status.
    """
    logger.info(f"Applying PCA on {len(feature_cols)} features...")
    X = df[feature_cols].copy()

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    pca = PCA(n_components=n_components, random_state=RANDOM_SEED)
    X_pca = pca.fit_transform(X_scaled)

    df["pca_1"] = X_pca[:, 0]
    df["pca_2"] = X_pca[:, 1]

    exp_var = pca.explained_variance_ratio_
    logger.info(
        f"PCA Explained Variance: PC1={exp_var[0]*100:.2f}%, PC2={exp_var[1]*100:.2f}% "
        f"(Total 2D Variance={sum(exp_var)*100:.2f}%)"
    )

    # Plot PCA 2D Projection
    plt.figure(figsize=(9, 6))
    scatter = plt.scatter(
        df["pca_1"],
        df["pca_2"],
        c=df["is_anomaly"],
        cmap="coolwarm",
        alpha=0.6,
        edgecolors="none",
        s=25,
    )
    plt.title(
        f"PCA 2D Projection: Normal vs Anomaly (Unit IV: Dimensionality Reduction)\n"
        f"Explained Variance: PC1 ({exp_var[0]*100:.1f}%), PC2 ({exp_var[1]*100:.1f}%)",
        fontsize=12,
        fontweight="bold",
    )
    plt.xlabel(f"Principal Component 1 ({exp_var[0]*100:.1f}% Variance)")
    plt.ylabel(f"Principal Component 2 ({exp_var[1]*100:.1f}% Variance)")
    cbar = plt.colorbar(scatter, ticks=[0, 1])
    cbar.ax.set_yticklabels(["Normal", "Anomaly"])
    plt.grid(True, linestyle=":", alpha=0.5)
    plt.tight_layout()

    pca_plot_path = FIGURES_DIR / "pca_anomaly_projection.png"
    plt.savefig(pca_plot_path, dpi=300)
    plt.close()
    logger.info(f"PCA projection visualization saved to {pca_plot_path}")

    return df, pca


def build_feature_dataset() -> pd.DataFrame:
    """End-to-end pipeline to generate featured dataset for machine learning models."""
    cleaned_path = PROCESSED_DATA_DIR / "cleaned_metrics.csv"
    if not cleaned_path.exists():
        raise FileNotFoundError(f"Missing cleaned data at {cleaned_path}. Run cleaning.py first.")

    df_cleaned = pd.read_csv(cleaned_path)
    df_featured = extract_features(df_cleaned)

    # Define model feature subset (excluding target labels, text identifiers, and PCA outputs)
    numeric_features = [
        "response_time_ms",
        "request_count",
        "cpu_percent",
        "memory_mb",
        "requests_per_minute",
        "latency_roll_mean_15m",
        "latency_roll_std_15m",
        "latency_roll_max_15m",
        "latency_roll_mean_60m",
        "latency_roll_std_60m",
        "cpu_roll_mean_15m",
        "cpu_roll_max_15m",
        "mem_roll_mean_15m",
        "latency_diff_1",
        "cpu_diff_1",
        "memory_diff_1",
        "rolling_error_rate",
        "latency_per_kb",
        "cpu_per_request",
        "hourly_z_deviation",
    ]

    service_cols = [c for c in df_featured.columns if c.startswith("service_")]
    all_model_features = numeric_features + service_cols

    # Apply PCA
    df_final, pca_model = apply_pca_reduction(df_featured, all_model_features, n_components=2)

    # Save fitted PCA model
    joblib.dump(pca_model, MODELS_DIR / "pca_transformer.joblib")

    # Export final model-ready CSV
    featured_csv_path = PROCESSED_DATA_DIR / "featured_metrics.csv"
    df_final.to_csv(featured_csv_path, index=False)
    logger.info(f"Final model-ready dataset saved to {featured_csv_path} with {df_final.shape[1]} columns.")

    return df_final


if __name__ == "__main__":
    build_feature_dataset()
