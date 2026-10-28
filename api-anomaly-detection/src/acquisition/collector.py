"""
=====================================================================
Metrics Collector Module (src/acquisition/collector.py)
U23AD491 Data Science Project: API Anomaly Detection System
=====================================================================
Collects microservice telemetry through multiple sources:
  1. Direct REST API polling (via requests library)
  2. Prometheus-style /metrics text format parsing
  3. File-based log ingestion (JSONL request logs and CSV datasets)
"""

import re
import requests
import pandas as pd
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from src.utils.config import RAW_DATA_DIR, MICROSERVICES
from src.utils.logger import get_logger

logger = get_logger("Metrics-Collector")


class MetricsCollector:
    """Multi-source metrics collector for microservice architectures."""

    def __init__(self, base_url: str = "http://localhost:8080"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "Antigravity-MetricsCollector/1.0"})

    def poll_service_rest_api(self, endpoint: str, timeout: float = 3.0) -> Optional[Dict]:
        """
        Polls a microservice REST endpoint and records network round-trip time.

        Parameters:
          endpoint: API URI path, e.g. '/orders'
          timeout: Maximum seconds to wait

        Returns:
          Dict containing response metrics or None if unreachable
        """
        url = f"{self.base_url}{endpoint}"
        t_start = datetime.now()
        try:
            resp = self.session.get(url, timeout=timeout)
            duration_ms = (datetime.now() - t_start).total_seconds() * 1000.0
            return {
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "url": url,
                "status_code": resp.status_code,
                "response_time_ms": round(duration_ms, 2),
                "content_length_bytes": len(resp.content),
                "is_reachable": True,
            }
        except requests.RequestException as e:
            logger.warning(f"REST API polling error for {url}: {e}")
            return {
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "url": url,
                "status_code": 0,
                "response_time_ms": 0.0,
                "content_length_bytes": 0,
                "is_reachable": False,
            }

    def scrape_prometheus_metrics(self, endpoint: str = "/metrics") -> List[Dict]:
        """
        Scrapes and parses Prometheus text exposition format.
        Example line: http_response_time_ms{service="auth-service",endpoint="/login"} 45.0
        """
        url = f"{self.base_url}{endpoint}"
        parsed_records = []
        try:
            resp = self.session.get(url, timeout=3.0)
            if resp.status_code == 200:
                pattern = re.compile(
                    r'^([a-zA-Z_:][a-zA-Z0-9_:]*)\{([^}]+)\}\s+([0-9eE\.\+\-]+)$'
                )
                for line in resp.text.splitlines():
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    match = pattern.match(line)
                    if match:
                        metric_name, label_str, val_str = match.groups()
                        # Parse labels: service="auth-service",endpoint="/login"
                        labels = {}
                        for kv in re.findall(r'([a-zA-Z_][a-zA-Z0-9_]*)="([^"]*)"', label_str):
                            labels[kv[0]] = kv[1]
                        parsed_records.append({
                            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "metric_name": metric_name,
                            "value": float(val_str),
                            "labels": labels,
                        })
        except Exception as e:
            logger.warning(f"Failed to scrape Prometheus metrics from {url}: {e}")
        return parsed_records

    def ingest_from_file(self, filename: str = "synthetic_microservices_logs.csv") -> pd.DataFrame:
        """
        Ingests metrics from a stored raw CSV file.
        """
        file_path = RAW_DATA_DIR / filename
        if not file_path.exists():
            logger.error(f"Target log file not found: {file_path}")
            raise FileNotFoundError(f"Missing {file_path}. Run load_generator.py first.")

        logger.info(f"Ingesting raw telemetry records from {file_path}...")
        df = pd.read_csv(file_path)
        logger.info(f"Successfully ingested {len(df)} telemetry records.")
        return df


if __name__ == "__main__":
    collector = MetricsCollector()
    logger.info("Testing file ingestion capability...")
    try:
        data = collector.ingest_from_file()
        print(data.head())
    except Exception as err:
        logger.error(f"Execution test note: {err}")
