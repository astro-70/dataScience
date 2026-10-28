"""
=====================================================================
Visualization & EDA Module (src/visualization/plots.py)
U23AD491 Data Science Project: API Anomaly Detection System
=====================================================================
Generates high-resolution academic figures (Matplotlib & Seaborn):
  1. Latency Distribution & Boxplot per Microservice
  2. Multi-Service Time-Series with Ground-Truth Anomalies Highlighted
  3. Hourly & Weekday Performance Heatmaps
  4. HTTP Status Code Distribution
  5. Pairplot of Key Telemetry Dimensions
  6. Incident Timeline & Alert Severity Distribution
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from typing import Optional

from src.utils.config import FIGURES_DIR, PROCESSED_DATA_DIR
from src.utils.logger import get_logger

logger = get_logger("Visualizations")

# Set consistent aesthetic style
sns.set_theme(style="whitegrid", font="sans-serif")
plt.rcParams.update({"font.size": 10, "axes.labelsize": 11, "axes.titlesize": 12})


def plot_latency_distributions(df: pd.DataFrame) -> Path:
    """
    Renders Latency Histogram with KDE and Boxplots across services.
    Observation: Latency displays clear right-skew with outliers corresponding to injected faults.
    """
    clean = df[(df["response_time_ms"] > 0) & (df["response_time_ms"] < 2500)].copy()

    fig, axes = plt.subplots(1, 2, figsize=(15, 5))

    # Subplot 1: Histogram + KDE
    sns.histplot(
        data=clean,
        x="response_time_ms",
        hue="service",
        kde=True,
        element="step",
        common_norm=False,
        palette="tab10",
        ax=axes[0],
    )
    axes[0].set_title("Response Time Distribution with KDE (Descriptive Analytics)", fontweight="bold")
    axes[0].set_xlabel("Latency (ms)")
    axes[0].set_ylabel("Density / Count")

    # Subplot 2: Boxplot per service
    sns.boxplot(
        data=clean,
        x="service",
        y="response_time_ms",
        palette="tab10",
        ax=axes[1],
    )
    axes[1].set_title("Latency Spread & Outliers per Microservice", fontweight="bold")
    axes[1].set_xlabel("Microservice")
    axes[1].set_ylabel("Latency (ms)")
    axes[1].tick_params(axis="x", rotation=25)

    plt.tight_layout()
    output_path = FIGURES_DIR / "eda_latency_distributions.png"
    plt.savefig(output_path, dpi=300)
    plt.close()
    logger.info(f"Saved latency distribution figure to {output_path}")
    return output_path


def plot_timeseries_with_anomalies(df: pd.DataFrame, service_name: str = "payment-service") -> Path:
    """
    Plots continuous time series with true anomaly points marked with red scatter dots.
    Observation: Spikes and gradual degradation phases are distinctly visible above baseline.
    """
    sub = df[df["service"] == service_name].copy()
    sub["datetime"] = pd.to_datetime(sub["timestamp"])
    sub = sub.sort_values(by="datetime").reset_index(drop=True)

    # Plot sample 14-day window for clear visual inspection
    sample_window = sub.iloc[: 14 * 288]

    fig, ax = plt.subplots(figsize=(14, 5))
    ax.plot(sample_window["datetime"], sample_window["response_time_ms"], color="#1f77b4", linewidth=1.2, label="Response Time (ms)")

    # Highlight Anomalies
    anomalies = sample_window[sample_window["is_anomaly"] == 1]
    ax.scatter(
        anomalies["datetime"],
        anomalies["response_time_ms"],
        color="#d62728",
        s=45,
        label="Injected Anomaly Event",
        zorder=5,
    )

    ax.set_title(f"Telemetry Time Series with Ground-Truth Anomalies: {service_name}", fontweight="bold")
    ax.set_xlabel("Timeline")
    ax.set_ylabel("Latency (ms)")
    ax.legend(loc="upper right")
    plt.xticks(rotation=20)
    plt.tight_layout()

    output_path = FIGURES_DIR / f"timeseries_anomalies_{service_name}.png"
    plt.savefig(output_path, dpi=300)
    plt.close()
    logger.info(f"Saved time-series plot to {output_path}")
    return output_path


def plot_diurnal_heatmaps(df: pd.DataFrame) -> Path:
    """
    Renders Hour vs Weekday heatmap of average latency.
    Observation: Peak working hours (11-13) and evening prime hours (19-21) exhibit higher loads.
    """
    df = df.copy()
    df["datetime"] = pd.to_datetime(df["timestamp"])
    df["hour"] = df["datetime"].dt.hour
    df["day_name"] = df["datetime"].dt.day_name()

    day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    pivot_lat = df.pivot_table(
        index="day_name",
        columns="hour",
        values="response_time_ms",
        aggfunc="mean",
    ).reindex(day_order)

    fig, ax = plt.subplots(figsize=(12, 5))
    sns.heatmap(
        pivot_lat,
        cmap="YlOrRd",
        linewidths=0.5,
        cbar_kws={"label": "Avg Latency (ms)"},
        ax=ax,
    )
    ax.set_title("Hourly vs Weekday Latency Heatmap (Seasonality Diagnostics)", fontweight="bold")
    ax.set_xlabel("Hour of Day (0 - 23)")
    ax.set_ylabel("Day of Week")
    plt.tight_layout()

    output_path = FIGURES_DIR / "eda_diurnal_heatmap.png"
    plt.savefig(output_path, dpi=300)
    plt.close()
    logger.info(f"Saved diurnal heatmap to {output_path}")
    return output_path


def plot_status_code_distribution(df: pd.DataFrame) -> Path:
    """
    Renders bar chart of HTTP status code frequency across microservices.
    Observation: HTTP 200 represents healthy traffic, while 500, 502, 503, 504 correspond to service outages.
    """
    fig, ax = plt.subplots(figsize=(9, 4.5))
    code_counts = df["status_code"].value_counts().sort_index()
    colors = ["#2ca02c" if code < 400 else "#ff7f0e" if code < 500 else "#d62728" for code in code_counts.index]

    bars = ax.bar([str(c) for c in code_counts.index], code_counts.values, color=colors, edgecolor="black", width=0.5)
    for bar in bars:
        yval = bar.get_height()
        ax.text(bar.get_x() + bar.get_width() / 2.0, yval + 100, f"{int(yval)}", ha="center", va="bottom", fontsize=9)

    ax.set_title("HTTP Status Code Frequency Distribution (Diagnostic Analytics)", fontweight="bold")
    ax.set_xlabel("HTTP Status Code")
    ax.set_ylabel("Total Requests")
    plt.tight_layout()

    output_path = FIGURES_DIR / "eda_status_code_dist.png"
    plt.savefig(output_path, dpi=300)
    plt.close()
    logger.info(f"Saved status code plot to {output_path}")
    return output_path


def plot_service_health_heatmap(df: pd.DataFrame) -> Path:
    """
    Renders 2D service health matrix across timeline showing health degradation.
    """
    df = df.copy()
    df["datetime"] = pd.to_datetime(df["timestamp"])
    df["date"] = df["datetime"].dt.date

    # Daily error rate & anomaly rate matrix
    pivot = df.pivot_table(
        index="service",
        columns="date",
        values="is_anomaly",
        aggfunc="mean",
    ) * 100.0

    fig, ax = plt.subplots(figsize=(14, 5))
    sns.heatmap(
        pivot,
        cmap="Reds",
        linewidths=0.5,
        cbar_kws={"label": "Anomaly Frequency (%)"},
        ax=ax,
    )
    ax.set_title("Microservices Operational Health Heatmap across 30 Days (Unit III)", fontweight="bold")
    ax.set_xlabel("Date")
    ax.set_ylabel("Microservice")
    plt.xticks(rotation=45)
    plt.tight_layout()

    output_path = FIGURES_DIR / "service_health_heatmap.png"
    plt.savefig(output_path, dpi=300)
    plt.close()
    logger.info(f"Saved service health heatmap to {output_path}")
    return output_path


def plot_incident_timeline_and_severity() -> Optional[Path]:
    """
    Plots incident timeline and alert severity breakdown.
    """
    from src.utils.config import EXPORTS_DIR
    alerts_path = EXPORTS_DIR / "alerts.csv"
    if not alerts_path.exists():
        return None

    alerts_df = pd.read_csv(alerts_path)
    if alerts_df.empty:
        return None

    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    # 1. Severity Distribution Donut Chart
    sev_counts = alerts_df["severity"].value_counts()
    colors = ["#d62728" if s == "CRITICAL" else "#ff7f0e" if s == "WARNING" else "#1f77b4" for s in sev_counts.index]
    axes[0].pie(
        sev_counts.values,
        labels=sev_counts.index,
        autopct="%1.1f%%",
        startangle=140,
        colors=colors,
        wedgeprops=dict(width=0.4, edgecolor="w"),
    )
    axes[0].set_title("Actionable Incidents by Severity Level", fontweight="bold")

    # 2. Alerts per Service Bar Chart
    svc_counts = alerts_df["service"].value_counts()
    axes[1].barh(svc_counts.index, svc_counts.values, color="#2ca02c", edgecolor="black")
    axes[1].set_title("Actionable Incidents per Microservice", fontweight="bold")
    axes[1].set_xlabel("Number of Incidents")
    axes[1].grid(True, linestyle=":", alpha=0.5)

    plt.tight_layout()
    output_path = FIGURES_DIR / "incident_severity_summary.png"
    plt.savefig(output_path, dpi=300)
    plt.close()
    logger.info(f"Saved incident summary plot to {output_path}")
    return output_path


def generate_all_eda_visualizations() -> None:
    """Orchestrates generation of all EDA and Dashboard figures."""
    cleaned_path = PROCESSED_DATA_DIR / "cleaned_metrics.csv"
    if not cleaned_path.exists():
        raise FileNotFoundError(f"Missing cleaned data at {cleaned_path}")

    df = pd.read_csv(cleaned_path)
    logger.info("Generating full suite of visualizations...")

    plot_latency_distributions(df)
    plot_timeseries_with_anomalies(df, "payment-service")
    plot_timeseries_with_anomalies(df, "order-service")
    plot_diurnal_heatmaps(df)
    plot_status_code_distribution(df)
    plot_service_health_heatmap(df)
    plot_incident_timeline_and_severity()

    logger.info("All visualizations successfully rendered and saved to reports/figures/!")


if __name__ == "__main__":
    generate_all_eda_visualizations()
