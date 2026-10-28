# Power BI Desktop Dashboard Construction Guide
**Project:** API Performance Anomaly Detection and Intelligent Alerting System for Microservices  
**Course Code:** U23AD491 Data Science Project (Unit III: Data Visualization)

---

## 1. Overview & Data Import
This guide outlines the step-by-step process for building an executive-ready APM report in **Power BI Desktop** using clean CSV exports from the pipeline.

### Prerequisites:
* Power BI Desktop installed (free version).
* Clean export CSVs generated in `data/exports/`:
  - `metrics_clean.csv`
  - `anomalies.csv`
  - `alerts.csv`
  - `service_summary.csv`

---

## 2. Power Query ETL & Data Modeling
1. Open **Power BI Desktop** > Select **Get Data** > **Text/CSV**.
2. Import `metrics_clean.csv` > Click **Transform Data** to open Power Query Editor.
3. In Power Query:
   - Ensure `timestamp` column is typed as `Date/Time`.
   - Ensure `response_time_ms`, `cpu_percent`, `memory_mb` are typed as `Decimal Number`.
   - Add a custom column for Calendar Hour: `Time.Hour([timestamp])` as `Hour`.
4. Click **New Source** > **Text/CSV** and repeat for:
   - `alerts.csv`
   - `service_summary.csv`
5. Click **Close & Apply**.
6. **Model View Relationships:**
   - Create a 1-to-Many relationship from `service_summary[service]` (1) to `metrics_clean[service]` (*).
   - Create a 1-to-Many relationship from `service_summary[service]` (1) to `alerts[service]` (*).
   - Cross-filter direction: **Both**.

---

## 3. Production DAX Measures
Create a dedicated measure table called `_TelemetryMeasures` and insert the following industry-standard APM DAX formulas:

### Measure 1: Average Latency
```dax
Avg Latency = 
AVERAGE('metrics_clean'[response_time_ms])
```

### Measure 2: 95th Percentile Latency (P95 SLA)
```dax
P95 Latency = 
PERCENTILE.INC('metrics_clean'[response_time_ms], 0.95)
```

### Measure 3: Total Requests Count
```dax
Total Requests = 
SUM('metrics_clean'[request_count])
```

### Measure 4: Total 5xx Server Errors
```dax
Total 5xx Errors = 
CALCULATE(
    COUNTROWS('metrics_clean'),
    'metrics_clean'[status_code] >= 500
)
```

### Measure 5: Error Rate Percentage
```dax
Error Rate % = 
DIVIDE(
    [Total 5xx Errors],
    COUNTROWS('metrics_clean'),
    0
) * 100
```

### Measure 6: Total Actionable Alerts
```dax
Total Actionable Alerts = 
COUNTROWS('alerts')
```

### Measure 7: Critical Severity Incidents
```dax
Critical Incidents = 
CALCULATE(
    COUNTROWS('alerts'),
    'alerts'[severity] = "CRITICAL"
)
```

### Measure 8: Alert Fatigue Reduction Percentage
```dax
Alert Fatigue Reduction % = 
VAR NaiveAlerts = 1561
VAR IntelligentAlerts = COUNTROWS('alerts')
RETURN
DIVIDE(NaiveAlerts - IntelligentAlerts, NaiveAlerts, 0) * 100
```

---

## 4. Visual Construction Guide

### Visual 1: Line and Clustered Column Chart (Dual-Axis)
* **Visual Type:** **Line and Clustered Column Chart**.
* **X-axis:** `metrics_clean[timestamp]` (Continuous).
* **Column y-axis:** `[Total Requests]`.
* **Line y-axis:** `[Avg Latency]`.
* **Line Style:** Smooth, Stroke width 2.5, Color Navy `#1155cc`.
* **Column Color:** Light Slate `#cfd8dc`.

### Visual 2: Treemap (Incident Blast Radius by Service)
* **Visual Type:** **Treemap**.
* **Category:** `alerts[service]`.
* **Details:** `alerts[probable_cause]`.
* **Values:** `[Total Actionable Alerts]`.
* **Color Saturation:** `alerts[peak_latency_ms]`.

### Visual 3: Scatter / Bubble Chart (Operational Risk Matrix)
* **Visual Type:** **Scatter Chart**.
* **X-axis:** `[Avg Latency]`.
* **Y-axis:** `[Error Rate %]`.
* **Size:** `[Total Requests]`.
* **Legend:** `service_summary[service]`.
* **Reference Lines:** Add constant X line at `500 ms` (SLA Breach) and constant Y line at `5.0%` (Error SLA).

### Visual 4: Matrix / Heatmap (Hourly Diurnal Health)
* **Visual Type:** **Matrix**.
* **Rows:** `metrics_clean[day_name]` (or Day of Week).
* **Columns:** `metrics_clean[Hour]`.
* **Values:** `[Avg Latency]`.
* **Conditional Formatting:** Background color > Rules > Low (Green `#66bb6a`) -> Mid (Yellow `#ffee58`) -> High (Red `#ef5350`).

### Visual 5: Donut Chart (Severity Breakdown)
* **Visual Type:** **Donut Chart**.
* **Legend:** `alerts[severity]`.
* **Values:** `COUNT(alerts[incident_id])`.
* **Colors:** Red for `CRITICAL`, Orange for `WARNING`.

---

## 5. Report Layout & Suggested 4 Pages

### Page 1: Executive KPI Command Center
* **Header:** Title, Refresh Timestamp, Environment ("Production - US-East-1").
* **Top KPIs (Card Visuals):**
  - Card 1: `[Avg Latency]` (Formatted as `0.0 ms`).
  - Card 2: `[P95 Latency]` (Formatted as `0.0 ms`).
  - Card 3: `[Error Rate %]` (Formatted as `0.00%`).
  - Card 4: `[Critical Incidents]`.
  - Card 5: `[Alert Fatigue Reduction %]` (Shows `98.7%`).
* **Visuals:** Dual-Axis Line & Column chart, Treemap of Alerts, and Service Summary table.

### Page 2: Microservice Deep-Dive Analysis
* **Slicers:** Dropdown slicer for `service`, Date Range slicer.
* **Visuals:** Latency Spread Box Plot / Violin, CPU vs Latency Scatter, Status Code breakdown clustered bar.

### Page 3: Anomaly & PCA Explorer
* **Visuals:**
  - PCA 2D Scatter Chart (`pca_1` on X, `pca_2` on Y, colored by `is_anomaly`).
  - Anomaly Type breakdown horizontal bar.
  - Diurnal Hour Heatmap.

### Page 4: Incident Timeline & Remediation Playbook
* **Visuals:**
  - Gantt/Timeline of active and resolved incidents.
  - Table: `Incident ID`, `Timestamp`, `Service`, `Origin`, `Probable Cause`, `Bayesian Confidence %`, `Remediation`.

---

## 6. Slicers and Cross-Filtering
1. Add a **Horizontal Button Slicer** at the top for `metrics_clean[service]`.
2. Format > Slicer settings > Style: **Tile**.
3. In Format > **Edit Interactions**:
   - Ensure clicking a microservice tile filters all cards, charts, and tables simultaneously.
