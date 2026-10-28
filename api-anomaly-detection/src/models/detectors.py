"""
=====================================================================
Anomaly Detection Models Module (src/models/detectors.py)
U23AD491 Data Science Project: API Anomaly Detection System
=====================================================================
Implements unsupervised, semi-supervised, and supervised detectors:
  1. Statistical Rolling Z-score / IQR Baseline
  2. Isolation Forest (Tree-based path-length isolation)
  3. Local Outlier Factor (Density-based novelty detection)
  4. One-Class SVM (Support Vector boundary estimation)
  5. Supervised Random Forest Classifier
  6. Majority Voting Ensemble (Suppresses false positives)
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest, RandomForestClassifier
from sklearn.neighbors import LocalOutlierFactor
from sklearn.svm import OneClassSVM
from sklearn.preprocessing import StandardScaler
import joblib
from pathlib import Path
from typing import Dict, Any, Tuple, List

from src.utils.config import MODELS_DIR, PROCESSED_DATA_DIR, RANDOM_SEED
from src.utils.logger import get_logger

logger = get_logger("Anomaly-Detectors")


class AnomalyDetectorPipeline:
    """Manages training, inference, and persistence of anomaly detection models."""

    def __init__(self, contamination: float = 0.03):
        self.contamination = contamination
        self.scaler = StandardScaler()
        self.models: Dict[str, Any] = {}
        self.feature_columns: List[str] = []

    def prepare_train_test_split(
        self, df: pd.DataFrame, train_ratio: float = 0.75
    ) -> Tuple[pd.DataFrame, pd.DataFrame, np.ndarray, np.ndarray]:
        """
        Executes strict time-based train/test split (no random shuffling)
        to prevent future-to-past temporal data leakage.
        """
        df = df.sort_values(by="timestamp").reset_index(drop=True)
        split_idx = int(len(df) * train_ratio)

        train_df = df.iloc[:split_idx].copy()
        test_df = df.iloc[split_idx:].copy()

        # Identify numeric feature set
        exclude_cols = [
            "timestamp",
            "service",
            "endpoint",
            "method",
            "instance_id",
            "is_anomaly",
            "anomaly_type",
            "anomaly_type_code",
            "is_statistical_outlier",
            "pca_1",
            "pca_2",
            "hourly_base_mean",
            "hourly_base_std",
        ]
        self.feature_columns = [
            c for c in df.columns if c not in exclude_cols and np.issubdtype(df[c].dtype, np.number)
        ]

        logger.info(
            f"Chronological split: Train={len(train_df)} rows, Test={len(test_df)} rows. "
            f"Features count={len(self.feature_columns)}"
        )

        # Scale features using training set parameters only
        X_train = self.scaler.fit_transform(train_df[self.feature_columns])
        X_test = self.scaler.transform(test_df[self.feature_columns])

        return train_df, test_df, X_train, X_test

    def train_models(self, X_train: np.ndarray, y_train_supervised: np.ndarray) -> None:
        """Trains unsupervised detectors and the supervised benchmark."""
        logger.info("Training 1. Isolation Forest...")
        iso_forest = IsolationForest(
            n_estimators=150,
            contamination=self.contamination,
            random_state=RANDOM_SEED,
            n_jobs=-1,
        )
        iso_forest.fit(X_train)
        self.models["IsolationForest"] = iso_forest

        logger.info("Training 2. Local Outlier Factor (Novelty Mode)...")
        # Novelty mode allows predicting on out-of-sample test data
        lof = LocalOutlierFactor(
            n_neighbors=25,
            contamination=self.contamination,
            novelty=True,
            n_jobs=-1,
        )
        lof.fit(X_train)
        self.models["LocalOutlierFactor"] = lof

        logger.info("Training 3. One-Class SVM...")
        ocsvm = OneClassSVM(
            kernel="rbf",
            gamma="scale",
            nu=self.contamination,
        )
        # Train on a representative subsample for faster convergence
        sub_idx = np.random.RandomState(RANDOM_SEED).choice(len(X_train), size=min(10000, len(X_train)), replace=False)
        ocsvm.fit(X_train[sub_idx])
        self.models["OneClassSVM"] = ocsvm

        logger.info("Training 4. Supervised Random Forest Classifier Benchmark...")
        rf_clf = RandomForestClassifier(
            n_estimators=100,
            max_depth=12,
            random_state=RANDOM_SEED,
            class_weight="balanced",
            n_jobs=-1,
        )
        rf_clf.fit(X_train, y_train_supervised)
        self.models["SupervisedRandomForest"] = rf_clf

        logger.info("All model architectures trained successfully.")

    def predict_all(self, X_test: np.ndarray, test_df: pd.DataFrame) -> pd.DataFrame:
        """
        Runs inference across all models and computes Majority Voting Ensemble.
        sklearn anomaly detectors return -1 for anomaly and 1 for inlier.
        We standardize: 1 = Anomaly, 0 = Normal.
        """
        predictions_df = test_df.copy()

        # 1. Isolation Forest
        raw_iso = self.models["IsolationForest"].predict(X_test)
        predictions_df["pred_IsolationForest"] = np.where(raw_iso == -1, 1, 0)
        # Decision function: lower values mean more anomalous; invert and normalize to 0-1
        scores_iso = -self.models["IsolationForest"].decision_function(X_test)
        predictions_df["score_IsolationForest"] = (scores_iso - scores_iso.min()) / (scores_iso.max() - scores_iso.min() + 1e-6)

        # 2. Local Outlier Factor
        raw_lof = self.models["LocalOutlierFactor"].predict(X_test)
        predictions_df["pred_LocalOutlierFactor"] = np.where(raw_lof == -1, 1, 0)
        scores_lof = -self.models["LocalOutlierFactor"].decision_function(X_test)
        predictions_df["score_LocalOutlierFactor"] = (scores_lof - scores_lof.min()) / (scores_lof.max() - scores_lof.min() + 1e-6)

        # 3. One-Class SVM
        raw_ocsvm = self.models["OneClassSVM"].predict(X_test)
        predictions_df["pred_OneClassSVM"] = np.where(raw_ocsvm == -1, 1, 0)
        scores_ocsvm = -self.models["OneClassSVM"].decision_function(X_test)
        predictions_df["score_OneClassSVM"] = (scores_ocsvm - scores_ocsvm.min()) / (scores_ocsvm.max() - scores_ocsvm.min() + 1e-6)

        # 4. Supervised Benchmark
        predictions_df["pred_SupervisedRF"] = self.models["SupervisedRandomForest"].predict(X_test)
        predictions_df["score_SupervisedRF"] = self.models["SupervisedRandomForest"].predict_proba(X_test)[:, 1]

        # 5. Statistical Baseline (Z-Score Rule: |hourly_z_deviation| > 3.0)
        predictions_df["pred_StatisticalZScore"] = (predictions_df["hourly_z_deviation"].abs() > 3.0).astype(int)

        # 6. Majority Voting Ensemble
        # Flags anomaly if >= 2 out of 3 unsupervised detectors (IsoForest, LOF, OCSVM) agree
        ensemble_votes = (
            predictions_df["pred_IsolationForest"]
            + predictions_df["pred_LocalOutlierFactor"]
            + predictions_df["pred_OneClassSVM"]
        )
        predictions_df["pred_MajorityVotingEnsemble"] = (ensemble_votes >= 2).astype(int)
        predictions_df["ensemble_score"] = (
            predictions_df["score_IsolationForest"] * 0.4
            + predictions_df["score_LocalOutlierFactor"] * 0.3
            + predictions_df["score_OneClassSVM"] * 0.3
        ) * 100.0  # Normalized 0 - 100

        return predictions_df

    def save_artifacts(self) -> None:
        """Persists trained models and scaler."""
        joblib.dump(self.models, MODELS_DIR / "trained_detectors.joblib")
        joblib.dump(self.scaler, MODELS_DIR / "feature_scaler.joblib")
        joblib.dump(self.feature_columns, MODELS_DIR / "feature_columns.joblib")
        logger.info(f"Model artifacts persisted to {MODELS_DIR}")


def run_detector_training_pipeline() -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Orchestrates full model training and evaluation dataset preparation."""
    featured_path = PROCESSED_DATA_DIR / "featured_metrics.csv"
    if not featured_path.exists():
        raise FileNotFoundError(f"Missing featured metrics at {featured_path}")

    df = pd.read_csv(featured_path)
    pipeline = AnomalyDetectorPipeline(contamination=0.03)

    train_df, test_df, X_train, X_test = pipeline.prepare_train_test_split(df, train_ratio=0.75)
    pipeline.train_models(X_train, train_df["is_anomaly"].values)

    test_predictions = pipeline.predict_all(X_test, test_df)
    pipeline.save_artifacts()

    # Save test predictions for evaluation and alerting engine
    test_pred_path = PROCESSED_DATA_DIR / "test_predictions.csv"
    test_predictions.to_csv(test_pred_path, index=False)
    logger.info(f"Predictions exported to {test_pred_path}")

    return train_df, test_predictions


if __name__ == "__main__":
    run_detector_training_pipeline()
