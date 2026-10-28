"""
=====================================================================
Central Configuration Module (src/utils/config.py)
U23AD491 Data Science Project: API Anomaly Detection System
=====================================================================
Provides centralized directory paths, baseline service definitions,
thresholds, hyperparameters, and environment settings.
"""

import os
from pathlib import Path

# ---------------------------------------------------------------------
# Path Resolution (Auto-detecting Project Root)
# ---------------------------------------------------------------------
# File is located at: <PROJECT_ROOT>/src/utils/config.py
CURRENT_FILE = Path(__file__).resolve()
PROJECT_ROOT = CURRENT_FILE.parent.parent.parent

# Core Directories
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
EXPORTS_DIR = DATA_DIR / "exports"
MICROSERVICES_DIR = PROJECT_ROOT / "microservices"
REPORTS_DIR = PROJECT_ROOT / "reports"
FIGURES_DIR = REPORTS_DIR / "figures"
EXCEL_DIR = PROJECT_ROOT / "excel"
MODELS_DIR = PROJECT_ROOT / "models"
DASHBOARDS_DIR = PROJECT_ROOT / "dashboards"
NOTEBOOKS_DIR = PROJECT_ROOT / "notebooks"

# Ensure all directories exist
for directory in [
    RAW_DATA_DIR,
    PROCESSED_DATA_DIR,
    EXPORTS_DIR,
    FIGURES_DIR,
    EXCEL_DIR,
    MODELS_DIR,
    MICROSERVICES_DIR,
    DASHBOARDS_DIR,
    NOTEBOOKS_DIR,
]:
    directory.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------
# Reproducibility Seed
# ---------------------------------------------------------------------
RANDOM_SEED = 42

# ---------------------------------------------------------------------
# Microservice Topology & Baseline Performance Catalog
# ---------------------------------------------------------------------
# 6 core production microservices with distinct baseline metrics
MICROSERVICES = {
    "auth-service": {
        "port": 5001,
        "endpoint": "/login",
        "method": "POST",
        "base_latency_ms": 45.0,
        "latency_std_ms": 8.0,
        "base_cpu_pct": 22.0,
        "base_mem_mb": 180.0,
        "avg_req_kb": 1.2,
        "avg_res_kb": 2.5,
        "instances": ["auth-prod-01", "auth-prod-02"],
    },
    "payment-service": {
        "port": 5002,
        "endpoint": "/pay",
        "method": "POST",
        "base_latency_ms": 210.0,
        "latency_std_ms": 25.0,
        "base_cpu_pct": 38.0,
        "base_mem_mb": 320.0,
        "avg_req_kb": 2.8,
        "avg_res_kb": 3.4,
        "instances": ["pay-prod-01", "pay-prod-02", "pay-prod-03"],
    },
    "order-service": {
        "port": 5003,
        "endpoint": "/orders",
        "method": "POST",
        "base_latency_ms": 115.0,
        "latency_std_ms": 18.0,
        "base_cpu_pct": 32.0,
        "base_mem_mb": 260.0,
        "avg_req_kb": 3.5,
        "avg_res_kb": 4.1,
        "instances": ["order-prod-01", "order-prod-02"],
    },
    "user-service": {
        "port": 5004,
        "endpoint": "/users",
        "method": "GET",
        "base_latency_ms": 32.0,
        "latency_std_ms": 5.0,
        "base_cpu_pct": 16.0,
        "base_mem_mb": 150.0,
        "avg_req_kb": 0.5,
        "avg_res_kb": 5.2,
        "instances": ["user-prod-01", "user-prod-02"],
    },
    "inventory-service": {
        "port": 5005,
        "endpoint": "/inventory",
        "method": "GET",
        "base_latency_ms": 58.0,
        "latency_std_ms": 10.0,
        "base_cpu_pct": 25.0,
        "base_mem_mb": 210.0,
        "avg_req_kb": 0.8,
        "avg_res_kb": 6.8,
        "instances": ["inv-prod-01", "inv-prod-02"],
    },
    "notification-service": {
        "port": 5006,
        "endpoint": "/notify",
        "method": "POST",
        "base_latency_ms": 28.0,
        "latency_std_ms": 4.0,
        "base_cpu_pct": 14.0,
        "base_mem_mb": 130.0,
        "avg_req_kb": 1.5,
        "avg_res_kb": 1.1,
        "instances": ["notif-prod-01", "notif-prod-02"],
    },
}

# Dependency Topology for Root-Cause Analysis
# key: service, value: list of downstream dependencies
SERVICE_DEPENDENCIES = {
    "order-service": ["payment-service", "inventory-service", "notification-service"],
    "payment-service": ["inventory-service"],
    "auth-service": ["user-service"],
    "user-service": [],
    "inventory-service": [],
    "notification-service": [],
}

# ---------------------------------------------------------------------
# Anomaly Ingestion & Types Catalog
# ---------------------------------------------------------------------
ANOMALY_TYPES = [
    "normal",
    "latency_spike",
    "gradual_degradation",
    "error_burst",
    "traffic_drop",
    "traffic_surge",
    "cpu_saturation",
]

# ---------------------------------------------------------------------
# Alerting Engine Configurations
# ---------------------------------------------------------------------
SEVERITY_LEVELS = ["INFO", "WARNING", "CRITICAL"]

# Thresholds for Alert Scoring and Naive Comparison
NAIVE_LATENCY_THRESHOLD_MS = 500.0
NAIVE_ERROR_RATE_THRESHOLD = 0.05
NAIVE_CPU_THRESHOLD_PCT = 85.0

# Alert Engine Tuning
COOLDOWN_MINUTES = 20  # Minimum cooldown before re-alerting same service
INCIDENT_GROUPING_WINDOW_MINUTES = 15

# Notification Channel Settings (Read from env or fallback to defaults)
ALERT_EMAIL_RECIPIENT = os.getenv("ALERT_EMAIL_RECIPIENT", "admin@microservices.local")
SMTP_SERVER = os.getenv("SMTP_SERVER", "localhost")
SMTP_PORT = int(os.getenv("SMTP_PORT", 25))
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL", "")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
