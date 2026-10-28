# Tableau Public Dashboard Construction Guide
**Project:** API Performance Anomaly Detection and Intelligent Alerting System for Microservices  
**Course Code:** U23AD491 Data Science Project (Unit III: Data Visualization)

---

## 1. Overview & Data Sources
This guide provides click-by-click instructions to build an enterprise-grade, interactive 4-page APM (Application Performance Monitoring) dashboard using **Tableau Public** or **Tableau Desktop**.

### Target Export Files (Located in `data/exports/`):
1. `metrics_clean.csv`: 51,840 records of 5-minute interval telemetry across 6 microservices.
2. `anomalies.csv`: Granular anomaly events with machine learning scores and PCA coordinates.
3. `alerts.csv`: Deduplicated actionable incidents with Bayesian confidence and root-cause hints.
4. `service_summary.csv`: Aggregated executive roll-up by microservice.

---

## 2. Connecting to Data in Tableau
1. Open **Tableau Public / Desktop**.
2. Under **Connect** > **To a File**, select **Text file**.
3. Navigate to `data/exports/metrics_clean.csv` and click **Open**.
4. In the Data Source pane, click **Add** next to Connections, select **Text file**, and add:
   - `alerts.csv`
   - `service_summary.csv`
5. **Relationship Setup:**
   - Drag `service_summary.csv` to the canvas. Join with `metrics_clean.csv` on `[service] = [service]`.
   - Keep `alerts.csv` as an independent or related table linked on `[service] = [service]`.
6. Verify Data Types:
   - `timestamp`: Date & Time
   - `response_time_ms`, `cpu_percent`, `memory_mb`: Number (decimal)
   - `status_code`, `request_count`, `is_anomaly`: Number (whole)
   - `service`, `endpoint`, `method`, `anomaly_type`: String (nominal)

---

## 3. Creating Visualizations (Step-by-Step)

### Visual 1: Dual-Axis Combination Chart (Traffic & Latency Timeline)
* **Goal:** Correlate request throughput spikes with latency degradation.
* **Columns:** Drag `timestamp` (Right-click > select continuous `Minute/Hour`).
* **Rows:** 
  - Drag `AVG(response_time_ms)` to Rows.
  - Drag `SUM(request_count)` to Rows right next to it.
* **Dual Axis:** Right-click the second pill `SUM(request_count)` > select **Dual Axis**. Right-click the right axis > select **Synchronize Axis** (or keep independent scales for ms vs count).
* **Marks Card:**
  - For `AVG(response_time_ms)`: Select **Line** chart, set color to Navy Blue (`#1f77b4`).
  - For `SUM(request_count)`: Select **Bar** chart, set color to Light Gray (`#b0bec5`) with 40% opacity.
* **Tooltip:** Add `service`, `AVG(cpu_percent)`, and `is_anomaly`.

### Visual 2: Box Plot (Latency Spread & Outlier Profiling)
* **Goal:** Visualize variance, skewness, and extreme latency outliers per microservice.
* **Columns:** Drag `service` (Dimension).
* **Rows:** Drag `response_time_ms` (Continuous Measure).
* **Detail:** Drag `timestamp` to **Detail** on the Marks card.
* **Analytics Tab:** Drag **Box Plot** from the Analytics pane onto the view.
* **Formatting:** Set whiskers to 1.5 IQR (Standard Outlier boundary). Color marks by `service`.

### Visual 3: Treemap (Alert Distribution by Service & Root Cause)
* **Goal:** Hierarchical view of which services generate the most severe incidents.
* **Data Source:** Switch to `alerts.csv`.
* **Marks Card:** Select **Treemap** in the Show Me panel.
* **Hierarchy:** Drag `service` and `probable_cause` to **Label**.
* **Size:** Drag `Number of Records` (or count of `incident_id`) to **Size**.
* **Color:** Drag `severity` to **Color** (Red for `CRITICAL`, Orange for `WARNING`).

### Visual 4: Bubble Chart (Latency vs Error Rate Sized by Throughput)
* **Goal:** Multi-dimensional diagnostic chart.
* **Columns:** Drag `AVG(response_time_ms)` to Columns.
* **Rows:** Drag `error_rate_pct` (from `service_summary.csv`) to Rows.
* **Marks:** Select **Circle**.
* **Detail:** Drag `service` to **Detail** and **Label**.
* **Size:** Drag `total_requests` to **Size**.
* **Color:** Drag `actionable_alerts_count` to **Color** (Palette: Red-Yellow-Green diverging).

### Visual 5: Heatmap (Hourly vs Weekday Performance Matrix)
* **Goal:** Diagnose diurnal traffic patterns and off-peak anomalies.
* **Columns:** Drag `timestamp` (set to Discrete **Hour** `0 - 23`).
* **Rows:** Drag `timestamp` (set to Discrete **Weekday** `Monday - Sunday`).
* **Color:** Drag `AVG(response_time_ms)` to **Color**.
* **Marks:** Set mark type to **Square**. Select Palette **Orange-Blue Diverging** or **YlOrRd**.

---

## 4. Parameters and Calculated Fields

### Calculated Field 1: SLA Compliance Indicator
```tableau
IF [response_time_ms] > 500.0 THEN "SLA Breached (>500ms)"
ELSEIF [response_time_ms] > 200.0 THEN "Warning (200-500ms)"
ELSE "Healthy (<200ms)"
END
```

### Calculated Field 2: Error Status Group
```tableau
IF [status_code] >= 500 THEN "5xx Server Error"
ELSEIF [status_code] >= 400 THEN "4xx Client Error"
ELSE "2xx Success"
END
```

### Parameter: Dynamic Anomaly Threshold Slider
1. Create Parameter > Name: `p_AnomalyScoreCutoff`.
2. Data Type: **Float**, Allowable Values: **Range** (Min: 50, Max: 100, Step: 5, Current: 70).
3. Filter Calculation: `[ensemble_score] >= [p_AnomalyScoreCutoff]`.

---

## 5. Dashboard Assembly (4 Pages)

### Page 1: Executive Overview KPIs
* **Top Ribbon (Cards):** Total Requests, Average System Latency, Overall 5xx Error Rate, Total Actionable Incidents.
* **Main Area (Left):** Dual-Axis Traffic & Response Time Trend.
* **Main Area (Right):** Treemap of Incidents by Service.
* **Bottom:** Summary Health Table with conditional color badges.

### Page 2: Service Performance Drill-Down
* **Interactive Slicer:** `service` dropdown filter (Apply to all worksheets using this data source).
* **Visuals:** Box Plot of Latency, CPU & Memory Correlation Scatter, HTTP Status Code breakdown.

### Page 3: Anomaly Explorer
* **Visuals:** 2D PCA Projection scatter plot (`pca_1` vs `pca_2`), Hourly Heatmap matrix, Anomaly Type distribution bar chart.
* **Slider:** `p_AnomalyScoreCutoff` parameter control.

### Page 4: Alerts and Incidents Timeline
* **Visuals:** Incident Timeline Gantt/Scatter, Severity Distribution Donut, Detailed Incident List Table (Incident ID, Timestamp, Service, Cause, Confidence %, Remediation).

---

## 6. Interactive Filter Actions
1. Navigate to **Dashboard** > **Actions...** > **Add Action** > **Filter**.
2. **Name:** `FilterByService`.
3. **Source Sheets:** Select Treemap visual.
4. **Run Action on:** **Select**.
5. **Target Sheets:** All other worksheets on the dashboard.
6. **Clearing selection will:** **Show all values**.
*Now, clicking any service box in the Treemap automatically filters the time series and scatter plots to that specific service!*
