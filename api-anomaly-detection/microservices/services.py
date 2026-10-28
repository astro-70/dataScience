"""
=====================================================================
Microservices Simulator (microservices/services.py)
U23AD491 Data Science Project: API Anomaly Detection System
=====================================================================
Implements 6 production-grade demo REST microservices:
  1. Auth Service       - POST /login
  2. Payment Service    - POST /pay
  3. Order Service      - POST /orders
  4. User Service       - GET  /users
  5. Inventory Service  - GET  /inventory
  6. Notification Serv. - POST /notify

Each service exposes:
  - Business endpoints with simulated realistic latency & response payload
  - /health endpoint
  - /metrics endpoint (Prometheus exposition format)
  - Detailed request logging to data/raw/service_requests.log
"""

import time
import random
import os
import json
from datetime import datetime
from flask import Flask, request, jsonify, Response
from src.utils.config import MICROSERVICES, RAW_DATA_DIR
from src.utils.logger import get_logger

logger = get_logger("Microservices-Server")

app = Flask(__name__)

# Request Log File Destination
REQUEST_LOG_PATH = RAW_DATA_DIR / "service_requests.log"


def log_request_metric(
    service_name: str,
    endpoint: str,
    method: str,
    status_code: int,
    latency_ms: float,
    req_size: float,
    res_size: float,
    cpu_pct: float,
    mem_mb: float,
    instance_id: str,
):
    """Logs individual request metrics into structured JSONL and CSV formats."""
    record = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "service": service_name,
        "endpoint": endpoint,
        "method": method,
        "status_code": status_code,
        "response_time_ms": round(latency_ms, 2),
        "request_size": round(req_size, 2),
        "response_size": round(res_size, 2),
        "cpu_percent": round(cpu_pct, 2),
        "memory_mb": round(mem_mb, 2),
        "instance_id": instance_id,
    }

    try:
        with open(REQUEST_LOG_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")
    except Exception as e:
        logger.error(f"Failed to write request log: {e}")


def get_simulated_metrics(service_name: str, inject_anomaly: bool = False):
    """Calculates realistic latency, cpu, and memory based on service profile."""
    profile = MICROSERVICES[service_name]
    base_lat = profile["base_latency_ms"]
    std_lat = profile["latency_std_ms"]
    instance = random.choice(profile["instances"])

    if inject_anomaly:
        latency = base_lat * random.uniform(5.0, 12.0)
        cpu = min(99.5, profile["base_cpu_pct"] * random.uniform(2.5, 4.0))
        memory = profile["base_mem_mb"] * random.uniform(1.8, 3.0)
        status_code = random.choice([500, 502, 503, 504])
    else:
        # Realistic positive right-skewed latency
        latency = max(2.0, random.gauss(base_lat, std_lat))
        cpu = max(5.0, min(95.0, random.gauss(profile["base_cpu_pct"], 3.0)))
        memory = max(50.0, random.gauss(profile["base_mem_mb"], 10.0))
        status_code = 200

    return latency, cpu, memory, status_code, instance


# ---------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------
@app.route("/login", methods=["POST", "GET"])
def auth_login():
    service = "auth-service"
    inject = request.args.get("anomaly", "false").lower() == "true"
    lat, cpu, mem, code, inst = get_simulated_metrics(service, inject)
    time.sleep(lat / 1000.0 if lat < 300 else 0.05)  # slight delay for demo
    log_request_metric(service, "/login", request.method, code, lat, 1.2, 2.5, cpu, mem, inst)
    return jsonify({"service": service, "status": "authenticated", "latency_ms": lat}), code


@app.route("/pay", methods=["POST", "GET"])
def payment_pay():
    service = "payment-service"
    inject = request.args.get("anomaly", "false").lower() == "true"
    lat, cpu, mem, code, inst = get_simulated_metrics(service, inject)
    time.sleep(lat / 1000.0 if lat < 300 else 0.05)
    log_request_metric(service, "/pay", request.method, code, lat, 2.8, 3.4, cpu, mem, inst)
    return jsonify({"service": service, "status": "processed", "latency_ms": lat}), code


@app.route("/orders", methods=["POST", "GET"])
def orders():
    service = "order-service"
    inject = request.args.get("anomaly", "false").lower() == "true"
    lat, cpu, mem, code, inst = get_simulated_metrics(service, inject)
    time.sleep(lat / 1000.0 if lat < 300 else 0.05)
    log_request_metric(service, "/orders", request.method, code, lat, 3.5, 4.1, cpu, mem, inst)
    return jsonify({"service": service, "order_id": "ORD-94821", "latency_ms": lat}), code


@app.route("/users", methods=["GET"])
def users():
    service = "user-service"
    inject = request.args.get("anomaly", "false").lower() == "true"
    lat, cpu, mem, code, inst = get_simulated_metrics(service, inject)
    time.sleep(lat / 1000.0 if lat < 300 else 0.05)
    log_request_metric(service, "/users", request.method, code, lat, 0.5, 5.2, cpu, mem, inst)
    return jsonify({"service": service, "user": "student_u23ad491", "latency_ms": lat}), code


@app.route("/inventory", methods=["GET"])
def inventory():
    service = "inventory-service"
    inject = request.args.get("anomaly", "false").lower() == "true"
    lat, cpu, mem, code, inst = get_simulated_metrics(service, inject)
    time.sleep(lat / 1000.0 if lat < 300 else 0.05)
    log_request_metric(service, "/inventory", request.method, code, lat, 0.8, 6.8, cpu, mem, inst)
    return jsonify({"service": service, "in_stock": True, "latency_ms": lat}), code


@app.route("/notify", methods=["POST", "GET"])
def notify():
    service = "notification-service"
    inject = request.args.get("anomaly", "false").lower() == "true"
    lat, cpu, mem, code, inst = get_simulated_metrics(service, inject)
    time.sleep(lat / 1000.0 if lat < 300 else 0.05)
    log_request_metric(service, "/notify", request.method, code, lat, 1.5, 1.1, cpu, mem, inst)
    return jsonify({"service": service, "sent": True, "latency_ms": lat}), code


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "UP", "timestamp": datetime.now().isoformat()}), 200


@app.route("/metrics", methods=["GET"])
def prometheus_metrics():
    """Exposes Prometheus text-format metric exposition."""
    prom_data = [
        "# HELP http_requests_total Total number of HTTP requests made.",
        "# TYPE http_requests_total counter",
    ]
    for svc, meta in MICROSERVICES.items():
        base_l = meta["base_latency_ms"]
        prom_data.append(f'http_requests_total{{service="{svc}",endpoint="{meta["endpoint"]}"}} {random.randint(1200, 8500)}')
        prom_data.append(f'http_response_time_ms{{service="{svc}",endpoint="{meta["endpoint"]}"}} {base_l}')
        prom_data.append(f'service_cpu_percent{{service="{svc}"}} {meta["base_cpu_pct"]}')
        prom_data.append(f'service_memory_mb{{service="{svc}"}} {meta["base_mem_mb"]}')

    return Response("\n".join(prom_data) + "\n", mimetype="text/plain")


if __name__ == "__main__":
    logger.info("Starting Multi-tenant Microservices Gateway on port 8080...")
    app.run(host="0.0.0.0", port=8080, debug=False)
