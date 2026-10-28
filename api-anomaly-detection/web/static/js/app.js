/**
 * =====================================================================
 * Microservices APM & Anomaly Detection Dashboard Client (app.js)
 * U23AD491 Data Science Project: Interactive Web Dashboard
 * =====================================================================
 */

// Global Chart Instances
let latencyThroughputChart = null;
let serviceComparisonChart = null;
let modelComparisonChart = null;
let pcaScatterChart = null;
let severityDonutChart = null;

document.addEventListener("DOMContentLoaded", () => {
    initTabNavigation();
    initServiceSelector();
    initSimulatorForm();
    initVivaSearch();
    loadDashboardData();
});

// ---------------------------------------------------------------------
// Tab Navigation Routing
// ---------------------------------------------------------------------
function initTabNavigation() {
    const tabButtons = document.querySelectorAll(".tab-btn");
    const tabContents = document.querySelectorAll(".tab-content");

    tabButtons.forEach(btn => {
        btn.addEventListener("click", () => {
            const target = btn.getAttribute("data-tab");

            tabButtons.forEach(b => b.classList.remove("active"));
            tabContents.forEach(c => c.classList.remove("active"));

            btn.classList.add("active");
            const targetContent = document.getElementById(target);
            if (targetContent) {
                targetContent.classList.add("active");
            }

            // Trigger chart resize when tabs become visible
            if (target === "tab-overview" && latencyThroughputChart) latencyThroughputChart.resize();
            if (target === "tab-models" && modelComparisonChart) modelComparisonChart.resize();
        });
    });
}

// ---------------------------------------------------------------------
// Service Selector in Overview Tab
// ---------------------------------------------------------------------
function initServiceSelector() {
    const selector = document.getElementById("overview-service-select");
    if (selector) {
        selector.addEventListener("change", (e) => {
            loadTimeseriesChart(e.target.value);
        });
    }
}

// ---------------------------------------------------------------------
// Core Data Loader
// ---------------------------------------------------------------------
async function loadDashboardData() {
    try {
        await Promise.all([
            loadOverviewKPIs(),
            loadMicroservicesFleet(),
            loadTimeseriesChart("payment-service"),
            loadModelBenchmarks(),
            loadAlertsList(),
            loadPcaScatterChart()
        ]);
    } catch (err) {
        console.error("Dashboard initial data loading error:", err);
    }
}

// ---------------------------------------------------------------------
// 1. Overview KPIs
// ---------------------------------------------------------------------
async function loadOverviewKPIs() {
    const res = await fetch("/api/overview");
    const data = await res.json();

    document.getElementById("kpi-total-requests").innerText = Number(data.total_requests).toLocaleString();
    document.getElementById("kpi-avg-latency").innerText = `${data.avg_latency_ms} ms`;
    document.getElementById("kpi-error-rate").innerText = `${data.error_rate_pct}%`;
    document.getElementById("kpi-total-errors").innerText = Number(data.total_errors).toLocaleString();
    document.getElementById("kpi-actionable-alerts").innerText = data.actionable_alerts;
    document.getElementById("kpi-fatigue-cut").innerText = `${data.alert_reduction_pct}%`;
    document.getElementById("kpi-naive-alerts").innerText = `Saved ${data.naive_alerts - data.actionable_alerts} false alerts`;
}

// ---------------------------------------------------------------------
// 2. Timeseries Chart (Dual-Axis Latency + Throughput)
// ---------------------------------------------------------------------
async function loadTimeseriesChart(serviceName) {
    const res = await fetch(`/api/timeseries?service=${serviceName}`);
    const resData = await res.json();
    const items = resData.data;

    const labels = items.map(d => d.timestamp);
    const latencyValues = items.map(d => d.latency_ms);
    const requestValues = items.map(d => d.requests);

    const ctx = document.getElementById("chart-timeseries").getContext("2d");

    if (latencyThroughputChart) {
        latencyThroughputChart.destroy();
    }

    latencyThroughputChart = new Chart(ctx, {
        type: "line",
        data: {
            labels: labels,
            datasets: [
                {
                    label: "Avg Response Time (ms)",
                    data: latencyValues,
                    borderColor: "#6366f1",
                    backgroundColor: "rgba(99, 102, 241, 0.1)",
                    borderWidth: 2,
                    tension: 0.3,
                    yAxisID: "yLatency",
                    fill: true,
                    pointRadius: 1,
                    pointHoverRadius: 5
                },
                {
                    label: "Requests / Interval",
                    data: requestValues,
                    type: "bar",
                    backgroundColor: "rgba(148, 163, 184, 0.25)",
                    borderWidth: 0,
                    yAxisID: "yRequests",
                    barPercentage: 0.6
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: { mode: "index", intersect: false },
            scales: {
                x: {
                    grid: { color: "rgba(255, 255, 255, 0.05)" },
                    ticks: { color: "#94a3b8", maxTicksLimit: 12 }
                },
                yLatency: {
                    type: "linear",
                    position: "left",
                    title: { display: true, text: "Latency (ms)", color: "#818cf8" },
                    grid: { color: "rgba(255, 255, 255, 0.05)" },
                    ticks: { color: "#94a3b8" }
                },
                yRequests: {
                    type: "linear",
                    position: "right",
                    title: { display: true, text: "Requests Volume", color: "#94a3b8" },
                    grid: { drawOnChartArea: false },
                    ticks: { color: "#94a3b8" }
                }
            },
            plugins: {
                legend: { labels: { color: "#f8fafc" } },
                tooltip: { backgroundColor: "rgba(15, 23, 42, 0.9)" }
            }
        }
    });
}

// ---------------------------------------------------------------------
// 3. Microservices Fleet View
// ---------------------------------------------------------------------
async function loadMicroservicesFleet() {
    const res = await fetch("/api/services");
    const services = await res.json();

    const container = document.getElementById("services-grid-container");
    container.innerHTML = "";

    const labels = [];
    const avgLatencies = [];
    const p95Latencies = [];

    services.forEach(s => {
        labels.push(s.service);
        avgLatencies.push(s.avg_latency_ms);
        p95Latencies.push(s.p95_latency_ms);

        const card = document.createElement("div");
        card.className = "card service-card";
        const statusBadge = s.status === "HEALTHY" 
            ? '<span class="badge badge-healthy">HEALTHY</span>'
            : s.status === "WARNING"
            ? '<span class="badge badge-warning">WARNING</span>'
            : '<span class="badge badge-critical">CRITICAL</span>';

        card.innerHTML = `
            <div class="card-header">
                <div>
                    <h3 class="card-title">${s.service}</h3>
                    <span class="card-subtitle">${s.method} ${s.endpoint} (Port ${s.port})</span>
                </div>
                ${statusBadge}
            </div>
            <div class="service-meta-row">
                <span class="service-meta-label">Avg Latency / P95:</span>
                <span class="service-meta-value">${s.avg_latency_ms} ms / ${s.p95_latency_ms} ms</span>
            </div>
            <div class="service-meta-row">
                <span class="service-meta-label">Avg CPU / Memory:</span>
                <span class="service-meta-value">${s.avg_cpu_pct}% / ${s.avg_mem_mb} MB</span>
            </div>
            <div class="service-meta-row">
                <span class="service-meta-label">5xx Error Count:</span>
                <span class="service-meta-value" style="color:${s.total_errors > 0 ? '#f43f5e' : '#10b981'}">${s.total_errors}</span>
            </div>
            <div class="service-meta-row">
                <span class="service-meta-label">Dependencies:</span>
                <span class="service-meta-value" style="font-size:0.75rem">${s.dependencies.length > 0 ? s.dependencies.join(', ') : 'None (Root Node)'}</span>
            </div>
        `;
        container.appendChild(card);
    });

    // Render Service Comparison Bar Chart in Fleet Tab
    const ctx = document.getElementById("chart-service-comparison").getContext("2d");
    if (serviceComparisonChart) serviceComparisonChart.destroy();
    serviceComparisonChart = new Chart(ctx, {
        type: "bar",
        data: {
            labels: labels,
            datasets: [
                {
                    label: "Mean Latency (ms)",
                    data: avgLatencies,
                    backgroundColor: "rgba(99, 102, 241, 0.7)",
                    borderRadius: 4
                },
                {
                    label: "P95 Latency SLA (ms)",
                    data: p95Latencies,
                    backgroundColor: "rgba(244, 63, 94, 0.6)",
                    borderRadius: 4
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: { ticks: { color: "#94a3b8" }, grid: { color: "rgba(255,255,255,0.05)" } },
                y: { ticks: { color: "#94a3b8" }, grid: { color: "rgba(255,255,255,0.05)" } }
            },
            plugins: { legend: { labels: { color: "#f8fafc" } } }
        }
    });
}

// ---------------------------------------------------------------------
// 4. ML Models Benchmark
// ---------------------------------------------------------------------
async function loadModelBenchmarks() {
    const res = await fetch("/api/models");
    const data = await res.json();
    const bench = data.benchmark;

    const tbody = document.getElementById("table-models-body");
    tbody.innerHTML = "";

    const labels = [];
    const precisions = [];
    const recalls = [];
    const f1s = [];

    bench.forEach(m => {
        labels.push(m.Model);
        precisions.push(m.Precision);
        recalls.push(m.Recall);
        f1s.push(m.F1_Score);

        const tr = document.createElement("tr");
        tr.innerHTML = `
            <td><strong>${m.Model}</strong></td>
            <td>${(m.Precision * 100).toFixed(1)}%</td>
            <td><strong style="color:${m.Recall >= 0.99 ? '#10b981' : '#f8fafc'}">${(m.Recall * 100).toFixed(1)}%</strong></td>
            <td>${m.F1_Score.toFixed(3)}</td>
            <td>${m.ROC_AUC.toFixed(4)}</td>
            <td>${m.False_Positives}</td>
            <td>${m.Detection_Delay_Min} min</td>
        `;
        tbody.appendChild(tr);
    });

    const ctx = document.getElementById("chart-model-benchmark").getContext("2d");
    if (modelComparisonChart) modelComparisonChart.destroy();
    modelComparisonChart = new Chart(ctx, {
        type: "bar",
        data: {
            labels: labels,
            datasets: [
                { label: "Precision", data: precisions, backgroundColor: "rgba(6, 182, 212, 0.7)", borderRadius: 4 },
                { label: "Recall", data: recalls, backgroundColor: "rgba(16, 185, 129, 0.7)", borderRadius: 4 },
                { label: "F1 Score", data: f1s, backgroundColor: "rgba(99, 102, 241, 0.7)", borderRadius: 4 }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: { ticks: { color: "#94a3b8", font: { size: 10 } }, grid: { color: "rgba(255,255,255,0.05)" } },
                y: { max: 1.05, ticks: { color: "#94a3b8" }, grid: { color: "rgba(255,255,255,0.05)" } }
            },
            plugins: { legend: { labels: { color: "#f8fafc" } } }
        }
    });
}

// ---------------------------------------------------------------------
// 5. 2D PCA Anomaly Projection Scatter Visual
// ---------------------------------------------------------------------
async function loadPcaScatterChart() {
    const res = await fetch("/api/pca");
    const points = await res.json();

    const normalPoints = points.filter(p => p.is_anomaly === 0).map(p => ({ x: p.pca_1, y: p.pca_2 }));
    const anomalyPoints = points.filter(p => p.is_anomaly === 1).map(p => ({ x: p.pca_1, y: p.pca_2 }));

    const ctx = document.getElementById("chart-pca").getContext("2d");
    if (pcaScatterChart) pcaScatterChart.destroy();
    pcaScatterChart = new Chart(ctx, {
        type: "scatter",
        data: {
            datasets: [
                {
                    label: "Normal Cluster",
                    data: normalPoints,
                    backgroundColor: "rgba(6, 182, 212, 0.6)",
                    pointRadius: 4
                },
                {
                    label: "Injected Anomalies",
                    data: anomalyPoints,
                    backgroundColor: "rgba(244, 63, 94, 0.8)",
                    pointRadius: 6
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: { title: { display: true, text: "Principal Component 1 (39.1% Variance)", color: "#94a3b8" }, grid: { color: "rgba(255,255,255,0.05)" } },
                y: { title: { display: true, text: "Principal Component 2 (10.1% Variance)", color: "#94a3b8" }, grid: { color: "rgba(255,255,255,0.05)" } }
            },
            plugins: { legend: { labels: { color: "#f8fafc" } } }
        }
    });
}

// ---------------------------------------------------------------------
// 6. Actionable Alerts Table & Donut
// ---------------------------------------------------------------------
async function loadAlertsList(severity = "ALL") {
    const url = severity === "ALL" ? "/api/alerts" : `/api/alerts?severity=${severity}`;
    const res = await fetch(url);
    const alerts = await res.json();

    const tbody = document.getElementById("table-alerts-body");
    tbody.innerHTML = "";

    let criticalCount = 0;
    let warningCount = 0;

    alerts.forEach(a => {
        if (a.severity === "CRITICAL") criticalCount++;
        if (a.severity === "WARNING") warningCount++;

        const tr = document.createElement("tr");
        const sevBadge = a.severity === "CRITICAL"
            ? '<span class="badge badge-critical">CRITICAL</span>'
            : '<span class="badge badge-warning">WARNING</span>';

        tr.innerHTML = `
            <td><code>${a.incident_id}</code></td>
            <td>${sevBadge}</td>
            <td><strong>${a.service}</strong></td>
            <td>${a.root_cause_service}</td>
            <td>${a.start_time}</td>
            <td>${a.peak_latency_ms} ms</td>
            <td><strong style="color:#818cf8">${a.confidence_pct}%</strong></td>
            <td>${a.probable_cause}</td>
        `;
        tbody.appendChild(tr);
    });

    // Render Severity Donut in Alerts Tab
    const ctx = document.getElementById("chart-severity-donut").getContext("2d");
    if (severityDonutChart) severityDonutChart.destroy();
    severityDonutChart = new Chart(ctx, {
        type: "doughnut",
        data: {
            labels: ["CRITICAL", "WARNING"],
            datasets: [{
                data: [criticalCount, warningCount],
                backgroundColor: ["#f43f5e", "#f59e0b"],
                borderWidth: 0
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { labels: { color: "#f8fafc" } } }
        }
    });
}

// Filter alerts by button
function filterAlerts(sev) {
    document.querySelectorAll(".alert-filter-btn").forEach(b => b.classList.remove("active"));
    const activeBtn = document.getElementById(`filter-alert-${sev.toLowerCase()}`);
    if (activeBtn) activeBtn.classList.add("active");
    loadAlertsList(sev);
}

// ---------------------------------------------------------------------
// 7. Live Interactive Anomaly Injector Simulator
// ---------------------------------------------------------------------
function initSimulatorForm() {
    const form = document.getElementById("simulator-form");
    if (!form) return;

    form.addEventListener("submit", async (e) => {
        e.preventDefault();
        const service = document.getElementById("sim-service").value;
        const anomalyType = document.getElementById("sim-type").value;
        const btn = document.getElementById("sim-submit-btn");

        btn.innerText = "Analyzing Telemetry...";
        btn.disabled = true;

        try {
            const res = await fetch("/api/simulate", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ service: service, anomaly_type: anomalyType })
            });
            const result = await res.json();

            displaySimulationResult(result);
        } catch (err) {
            console.error("Simulation error:", err);
        } finally {
            btn.innerText = "Simulate & Detect Anomaly";
            btn.disabled = false;
        }
    });
}

function displaySimulationResult(result) {
    const container = document.getElementById("sim-result-container");
    container.style.display = "block";

    const badgeClass = result.severity === "CRITICAL" ? "badge-critical" : result.severity === "WARNING" ? "badge-warning" : "badge-healthy";

    container.innerHTML = `
        <div class="simulation-result">
            <div class="sim-header">
                <div>
                    <h4 style="font-family:var(--font-heading); font-size:1.15rem">${result.incident_id}: ${result.service}</h4>
                    <span style="font-size:0.8rem; color:var(--text-dim)">Detected at ${result.timestamp}</span>
                </div>
                <span class="badge ${badgeClass}">${result.severity}</span>
            </div>
            
            <div style="display:grid; grid-template-columns: repeat(auto-fit, minmax(130px, 1fr)); gap:0.75rem; margin:1rem 0;">
                <div style="background:rgba(255,255,255,0.03); padding:0.6rem; border-radius:6px;">
                    <div style="font-size:0.75rem; color:var(--text-dim)">Latency</div>
                    <div style="font-weight:700; color:#f8fafc; font-family:var(--font-mono)">${result.metrics.response_time_ms} ms</div>
                </div>
                <div style="background:rgba(255,255,255,0.03); padding:0.6rem; border-radius:6px;">
                    <div style="font-size:0.75rem; color:var(--text-dim)">CPU Usage</div>
                    <div style="font-weight:700; color:#f8fafc; font-family:var(--font-mono)">${result.metrics.cpu_percent}%</div>
                </div>
                <div style="background:rgba(255,255,255,0.03); padding:0.6rem; border-radius:6px;">
                    <div style="font-size:0.75rem; color:var(--text-dim)">Memory</div>
                    <div style="font-weight:700; color:#f8fafc; font-family:var(--font-mono)">${result.metrics.memory_mb} MB</div>
                </div>
                <div style="background:rgba(255,255,255,0.03); padding:0.6rem; border-radius:6px;">
                    <div style="font-size:0.75rem; color:var(--text-dim)">Bayesian Confidence</div>
                    <div style="font-weight:700; color:#818cf8; font-family:var(--font-mono)">${result.bayesian_confidence_pct}%</div>
                </div>
            </div>

            <div style="margin-bottom:0.75rem;">
                <strong style="color:#f8fafc; font-size:0.88rem">Probable Root Cause:</strong>
                <p style="color:var(--text-muted); font-size:0.88rem">${result.probable_cause}</p>
            </div>
            <div style="margin-bottom:0.75rem;">
                <strong style="color:#f8fafc; font-size:0.88rem">Recommended Remediation:</strong>
                <p style="color:var(--text-muted); font-size:0.88rem">${result.recommended_remediation}</p>
            </div>
            <div style="font-size:0.78rem; color:var(--text-dim); border-top:1px solid rgba(255,255,255,0.05); padding-top:0.5rem">
                Model Consensus: ${result.model_agreement.EnsembleVotes} (Isolation Forest + LOF + OCSVM)
            </div>
        </div>
    `;
}

// ---------------------------------------------------------------------
// 8. Viva Q&A Accordion Search
// ---------------------------------------------------------------------
function initVivaSearch() {
    const input = document.getElementById("viva-search-input");
    if (!input) return;

    input.addEventListener("input", (e) => {
        const query = e.target.value.toLowerCase();
        const items = document.querySelectorAll(".accordion-item");

        items.forEach(item => {
            const text = item.innerText.toLowerCase();
            if (text.includes(query)) {
                item.style.display = "block";
            } else {
                item.style.display = "none";
            }
        });
    });
}

function toggleAccordion(element) {
    const item = element.parentElement;
    item.classList.toggle("open");
}
