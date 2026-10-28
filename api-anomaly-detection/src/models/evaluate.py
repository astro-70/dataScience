"""
=====================================================================
Model Evaluation Module (src/models/evaluate.py)
U23AD491 Data Science Project: API Anomaly Detection System
=====================================================================
Covers Unit IV Syllabus:
  1. Precision, Recall, F1-Score, ROC-AUC, and Confusion Matrix
  2. Temporal Detection Delay (Time-to-Detect in minutes)
  3. Granular Breakdown by Anomaly Type (Latency Spike, Outage, etc.)
  4. Comparative Model Benchmark Visualization (Bar Chart & Heatmaps)
  5. Scientific Justification for Model Selection
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import (
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    confusion_matrix,
)
from pathlib import Path
from typing import Dict, Any, List

from src.utils.config import PROCESSED_DATA_DIR, FIGURES_DIR, EXPORTS_DIR
from src.utils.logger import get_logger

logger = get_logger("Model-Evaluation")


def calculate_detection_delay(df: pd.DataFrame, pred_col: str) -> float:
    """
    Calculates average detection delay (in minutes) from the onset of an anomaly
    until the detector first flags it.
    """
    df_sorted = df.sort_values(by=["service", "timestamp"]).reset_index(drop=True)
    delays = []

    for _, grp in df_sorted.groupby(["service", "anomaly_type"]):
        if grp["anomaly_type"].iloc[0] == "normal":
            continue

        anomaly_indices = grp.index[grp["is_anomaly"] == 1].tolist()
        if not anomaly_indices:
            continue

        first_onset_idx = anomaly_indices[0]
        # Find first positive prediction after or at onset
        flagged = grp.loc[anomaly_indices][grp.loc[anomaly_indices, pred_col] == 1]
        if not flagged.empty:
            first_detected_idx = flagged.index[0]
            # Each interval is 5 minutes
            delay_minutes = (first_detected_idx - first_onset_idx) * 5.0
            delays.append(max(0.0, delay_minutes))
        else:
            # Missed entirely: assign max penalty delay
            delays.append(len(anomaly_indices) * 5.0)

    return round(float(np.mean(delays)) if delays else 0.0, 1)


def evaluate_all_models() -> pd.DataFrame:
    """
    Computes comparative benchmarks across all detector architectures.
    """
    pred_path = PROCESSED_DATA_DIR / "test_predictions.csv"
    if not pred_path.exists():
        raise FileNotFoundError(f"Missing test predictions at {pred_path}")

    df = pd.read_csv(pred_path)
    y_true = df["is_anomaly"].values

    models = [
        ("StatisticalZScore", "pred_StatisticalZScore", None),
        ("IsolationForest", "pred_IsolationForest", "score_IsolationForest"),
        ("LocalOutlierFactor", "pred_LocalOutlierFactor", "score_LocalOutlierFactor"),
        ("OneClassSVM", "pred_OneClassSVM", "score_OneClassSVM"),
        ("MajorityVotingEnsemble", "pred_MajorityVotingEnsemble", "ensemble_score"),
        ("SupervisedRF", "pred_SupervisedRF", "score_SupervisedRF"),
    ]

    benchmark_records = []
    confusion_matrices = {}

    for name, pred_col, score_col in models:
        y_pred = df[pred_col].values
        prec = precision_score(y_true, y_pred, zero_division=0)
        rec = recall_score(y_true, y_pred, zero_division=0)
        f1 = f1_score(y_true, y_pred, zero_division=0)

        # ROC-AUC (using continuous score if available, else binary prediction)
        if score_col and score_col in df.columns:
            auc = roc_auc_score(y_true, df[score_col].values)
        else:
            auc = roc_auc_score(y_true, y_pred)

        delay = calculate_detection_delay(df, pred_col)
        cm = confusion_matrix(y_true, y_pred)
        confusion_matrices[name] = cm

        tn, fp, fn, tp = cm.ravel()
        specificity = tn / (tn + fp) if (tn + fp) > 0 else 0.0

        benchmark_records.append({
            "Model": name,
            "Precision": round(prec, 4),
            "Recall": round(rec, 4),
            "F1_Score": round(f1, 4),
            "ROC_AUC": round(auc, 4),
            "Specificity": round(specificity, 4),
            "False_Positives": int(fp),
            "Detection_Delay_Min": delay,
        })

    benchmark_df = pd.DataFrame(benchmark_records)
    benchmark_csv_path = EXPORTS_DIR / "model_evaluation_benchmark.csv"
    benchmark_df.to_csv(benchmark_csv_path, index=False)
    logger.info(f"Model benchmark saved to {benchmark_csv_path}")

    # -----------------------------------------------------------------
    # Per-Anomaly-Type Recall Breakdown
    # -----------------------------------------------------------------
    anomaly_types = [
        "latency_spike",
        "gradual_degradation",
        "error_burst",
        "traffic_drop",
        "traffic_surge",
        "cpu_saturation",
    ]
    type_breakdown = []
    for atype in anomaly_types:
        sub = df[df["anomaly_type"] == atype]
        if len(sub) == 0:
            continue
        row = {"Anomaly_Type": atype, "True_Instances": len(sub)}
        for name, pred_col, _ in models:
            rec = (sub[pred_col] == 1).mean()
            row[f"{name}_Recall"] = round(rec, 3)
        type_breakdown.append(row)

    type_df = pd.DataFrame(type_breakdown)
    type_csv_path = EXPORTS_DIR / "per_anomaly_type_recall.csv"
    type_df.to_csv(type_csv_path, index=False)
    logger.info(f"Per-anomaly-type recall exported to {type_csv_path}")

    # -----------------------------------------------------------------
    # Render Comparison Figures
    # -----------------------------------------------------------------
    # 1. Bar Chart Comparison
    fig, axes = plt.subplots(1, 2, figsize=(15, 5))
    metrics_to_plot = ["Precision", "Recall", "F1_Score"]
    benchmark_df.set_index("Model")[metrics_to_plot].plot(
        kind="bar",
        ax=axes[0],
        colormap="viridis",
        width=0.75,
        edgecolor="black",
    )
    axes[0].set_title("Model Performance Comparison (Unit IV)", fontweight="bold")
    axes[0].set_ylabel("Score (0.0 - 1.0)")
    axes[0].set_ylim(0, 1.1)
    axes[0].tick_params(axis="x", rotation=30)
    axes[0].grid(True, linestyle=":", alpha=0.5)

    # 2. False Positives vs Detection Delay
    axes[1].scatter(
        benchmark_df["False_Positives"],
        benchmark_df["Detection_Delay_Min"],
        s=120,
        c="#d62728",
        edgecolor="black",
        zorder=4,
    )
    for _, r in benchmark_df.iterrows():
        axes[1].annotate(
            r["Model"],
            (r["False_Positives"] + 8, r["Detection_Delay_Min"] + 0.3),
            fontsize=9,
            fontweight="bold",
        )
    axes[1].set_title("Operational Trade-off: False Positives vs Detection Delay", fontweight="bold")
    axes[1].set_xlabel("Number of False Positives (Alert Fatigue Risk)")
    axes[1].set_ylabel("Mean Detection Delay (Minutes)")
    axes[1].grid(True, linestyle=":", alpha=0.5)

    plt.tight_layout()
    comp_plot_path = FIGURES_DIR / "model_comparison.png"
    plt.savefig(comp_plot_path, dpi=300)
    plt.close()

    # 3. Confusion Matrices Heatmaps
    fig, axes = plt.subplots(2, 3, figsize=(14, 8))
    axes = axes.flatten()
    for idx, (name, _, _) in enumerate(models):
        cm = confusion_matrices[name]
        sns.heatmap(
            cm,
            annot=True,
            fmt="d",
            cmap="Blues",
            cbar=False,
            ax=axes[idx],
            xticklabels=["Normal", "Anomaly"],
            yticklabels=["Normal", "Anomaly"],
        )
        axes[idx].set_title(f"{name}", fontweight="bold", fontsize=11)
        axes[idx].set_xlabel("Predicted Label")
        axes[idx].set_ylabel("True Label")

    plt.suptitle("Confusion Matrices across Evaluated Models", fontsize=13, fontweight="bold")
    plt.tight_layout()
    cm_plot_path = FIGURES_DIR / "confusion_matrices.png"
    plt.savefig(cm_plot_path, dpi=300)
    plt.close()

    logger.info(f"Evaluation completed! Charts saved to {comp_plot_path} and {cm_plot_path}")
    return benchmark_df


if __name__ == "__main__":
    evaluate_all_models()
