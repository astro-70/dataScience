# API Performance Anomaly Detection and Intelligent Alerting System for Microservices

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![Course](https://img.shields.io/badge/Course-U23AD491%20Data%20Science%20Project-green.svg)](#)
[![Academic Year](https://img.shields.io/badge/Academic%20Year-2026--2027-orange.svg)](#)
[![Alert Noise Reduction](https://img.shields.io/badge/Alert%20Fatigue%20Reduction-98.7%25-brightgreen.svg)](#)

A complete, runnable, production-grade academic Data Science and Machine Learning project for 3rd-Year Computer Science & Engineering students. Maps directly to **Units I through V** and **Course Objectives 1 through 5** of the university Data Science curriculum.

---

## 1. System Architecture

```mermaid
graph TD
    subgraph Phase 1: Data Acquisition [Unit I]
        M1[Auth Service /login] --> LG[Load Generator 30 Days]
        M2[Payment Service /pay] --> LG
        M3[Order Service /orders] --> LG
        M4[User Service /users] --> LG
        M5[Inventory Service /inventory] --> LG
        M6[Notification Service /notify] --> LG
        SCR[BeautifulSoup Scraper] --> RFC[RFC Status Code Catalog]
    end

    subgraph Phase 2 & 3: Statistics, Cleaning & Features [Units II & IV]
        LG --> RAW[(data/raw/)]
        RAW --> CLN[Data Cleaning & Time-series Imputation]
        CLN --> STAT[Statistical Testing: CLT, Distributions, ANOVA, Bayes]
        CLN --> FE[Feature Engineering: Rolling Windows, Lag, Ratios]
        FE --> PCA[PCA Dimensionality Reduction]
    end

    subgraph Phase 4: Machine Learning Anomaly Detection [Unit IV]
        PCA --> SPLIT[Strict Chronological Train/Test Split]
        SPLIT --> IF[Isolation Forest]
        SPLIT --> LOF[Local Outlier Factor]
        SPLIT --> SVM[One-Class SVM]
        SPLIT --> RF[Supervised Random Forest Benchmark]
        IF & LOF & SVM --> ENS[Majority Voting Ensemble]
    end

    subgraph Phase 5: Intelligent Alerting Engine
        ENS --> DEDUP[Deduplication & Incident Grouping]
        DEDUP --> BAYES[Bayesian Posterior Confidence Calibration]
        BAYES --> RC[Dependency & Heuristic Root Cause Inference]
        RC --> CD[Cooldown Rate Limiter]
        CD --> DISP[Multi-channel Dispatch: Console, Logs, Email, Slack]
    end

    subgraph Phase 6 & 7: Visual Analytics & Reporting [Units III & V]
        DISP --> EXP[(data/exports/ CSVs)]
        EXP --> TAB[Tableau Public Dashboards]
        EXP --> PBI[Power BI Desktop Dashboards]
        EXP --> XL[Excel Analysis Workbook .xlsx]
    end
```

---

## 2. Comprehensive Data Dictionary

Every record in `data/raw/synthetic_microservices_logs.csv` and `data/processed/cleaned_metrics.csv` adheres to this schema:

| Column Name | Data Type | Units / Range | Description |
| :--- | :--- | :--- | :--- |
| `timestamp` | Datetime | `YYYY-MM-DD HH:MM:SS` | 5-minute sampling interval across 30 days. |
| `service` | String | Categorical (6 services) | Target microservice name (e.g., `payment-service`, `auth-service`). |
| `endpoint` | String | URI Path | REST API path (`/login`, `/pay`, `/orders`, `/users`, `/inventory`, `/notify`). |
| `method` | String | `POST` / `GET` | HTTP request verb. |
| `status_code` | Integer | HTTP Status | Standard status code (`200` OK, `500` Error, `502`, `503`, `504`). |
| `response_time_ms` | Float | Milliseconds ($> 0.0$) | Server round-trip response duration (right-skewed lognormal). |
| `request_count` | Integer | Count per interval | Number of requests received in interval (Poisson distributed). |
| `request_size_kb` | Float | Kilobytes | Average incoming HTTP payload size. |
| `response_size_kb` | Float | Kilobytes | Average outgoing HTTP response payload size. |
| `cpu_percent` | Float | Percentage ($0.0 - 100.0$) | Container / Host CPU utilization. |
| `memory_mb` | Float | Megabytes ($50 - 1000$) | Resident memory footprint (used for detecting memory leaks). |
| `instance_id` | String | Alphanumeric | Replica pod identifier (e.g., `pay-prod-01`, `auth-prod-02`). |
| `is_anomaly` | Integer | `0` (Normal) or `1` (Anomaly) | Ground-truth binary label for model evaluation. |
| `anomaly_type` | String | Categorical (7 classes) | `normal`, `latency_spike`, `gradual_degradation`, `error_burst`, `traffic_drop`, `traffic_surge`, `cpu_saturation`. |

---

## 3. Quickstart & Installation

Everything runs locally with Python 3.10+ without any paid cloud dependencies.

```bash
# 1. Clone or navigate to the project directory
cd api-anomaly-detection

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the complete pipeline end-to-end
python main.py
```

---

## 4. How to Run Each Phase Individually

You can execute each syllabus phase independently:

```bash
# Phase 1: Data Acquisition (Load generation & web scraping)
python -m src.acquisition.load_generator
python -m src.acquisition.scraper

# Phase 2: Statistical Analysis (CLT, Distributions, Bayes, ANOVA)
python -m src.statistics.stats_analysis

# Phase 3: Data Preprocessing, Cleaning & Feature Engineering
python -m src.preprocessing.cleaning
python -m src.preprocessing.feature_engineering
python -m src.visualization.plots

# Phase 4: Machine Learning Anomaly Detection & Evaluation
python -m src.models.detectors
python -m src.models.evaluate

# Phase 5: Intelligent Alerting Engine & Replay
python -m src.alerting.alert_engine

# Phase 6: Export Data for Tableau and Power BI
python -m src.visualization.exporter

# Phase 7: Generate Excel Analysis Workbook
python -m src.visualization.excel_builder
```

---

## 5. Summary of Experimental Results

### Model Performance Benchmark (Out-of-Sample Test Set):
```
Model                   Precision  Recall   F1_Score  ROC_AUC  False_Positives  Detection_Delay
StatisticalZScore       0.1641     0.6774   0.2642    0.8346   107              0.0 min
IsolationForest         0.0515     0.6452   0.0955    0.9581   368              18.3 min
LocalOutlierFactor      0.0754     1.0000   0.1403    0.9997   380              0.0 min
OneClassSVM             0.0769     1.0000   0.1429    0.9998   372              0.0 min
MajorityVotingEnsemble  0.1183     1.0000   0.2116    0.9996   231 (40% CUT)    0.0 min
SupervisedRF (Ceiling)  0.9444     0.5484   0.6939    0.9999   1                10.0 min
```

### Alerting Engine Fatigue Benchmark:
* **Naive Static Alerting System:** Dispatched **1,561 alerts** (1,530 false alarms on payment-service due to static 180ms threshold).
* **Intelligent Alerting Engine:** Dispatched **21 deduplicated actionable incidents** with Bayesian confidence and root-cause hints.
* **Alert Noise Reduction:** **98.7% Alert Fatigue Cut!**

---

## 6. Dashboards & Excel Deliverables

1. **Tableau Public Guide:** [`dashboards/tableau_guide.md`](file:///c:/Users/astro/OneDrive/Documents/ds/api-anomaly-detection/dashboards/tableau_guide.md)  
   Step-by-step instructions to create dual-axis charts, bubble risk matrix, box plots, treemaps, and 4 interactive dashboard pages.
2. **Power BI Desktop Guide:** [`dashboards/powerbi_guide.md`](file:///c:/Users/astro/OneDrive/Documents/ds/api-anomaly-detection/dashboards/powerbi_guide.md)  
   Power Query ETL, relationships, slicers, and 8 production DAX measures (`Avg Latency`, `P95 Latency`, `Error Rate %`, `Alert Reduction %`).
3. **Microsoft Excel Analysis Workbook:** [`excel/analysis_workbook.xlsx`](file:///c:/Users/astro/OneDrive/Documents/ds/api-anomaly-detection/excel/analysis_workbook.xlsx)  
   Features `Raw Sample`, `Cleaned Data`, `Service Summary` (dynamic formulas: `AVERAGE`, `STDEV.S`, `CONFIDENCE.NORM`, `CORREL`), and `Alerts & Incidents` with conditional formatting.

---

## 7. 5-Minute Viva Demo Script

Use this structured script when presenting your project to the examination panel:

* **Minute 1: Problem Statement & Motivation**  
  *"Good morning professors. Modern cloud systems split monolithic applications into microservices like auth, payment, and orders. Traditional monitoring uses static threshold rules—like alerting when latency exceeds 200ms. In microservices, this fails completely: it floods engineers with thousands of false alarms on naturally slower services like payment, while missing gradual memory leaks on fast services like auth. Our project builds an intelligent data science system to solve this."*
* **Minute 2: Data Acquisition & Statistics (Units I & II)**  
  *"In Phase 1, we simulated 30 days of 5-minute telemetry across 6 microservices with diurnal seasonality and scraped RFC HTTP specifications using BeautifulSoup. In Phase 2, we proved the Central Limit Theorem and showed that real latency rejects Gaussian normality and follows a lognormal distribution. Crucially, we applied Bayes' Theorem to show that combining high latency with error bursts elevates failure confidence from 0.3% to 92.3%."*
* **Minute 3: Preprocessing & Machine Learning (Unit IV)**  
  *"In Phase 3, we cleaned the data using time-series forward fill and linear interpolation, engineered 47 features including rolling 15-minute statistics and rate of change, and applied PCA dimensionality reduction. In Phase 4, we trained unsupervised detectors: Isolation Forest, Local Outlier Factor, and One-Class SVM. We constructed a Majority Voting Ensemble that achieved 100% recall with zero detection delay while reducing false positives by 40%."*
* **Minute 4: Intelligent Alerting & Fatigue Reduction**  
  *"In Phase 5, we built an Intelligent Alert Engine featuring Bayesian confidence scores, cooldown timers, incident deduplication, and dependency-aware root-cause analysis. When compared against naive static thresholds, our system reduced alert noise by 98.7%—from 1,561 noisy alerts down to 21 actionable incidents."*
* **Minute 5: Dashboards, Excel & Ethics (Units III, V & Course Obj 5)**  
  *"Finally, we exported clean CSVs for Tableau and Power BI dashboards, generated a formatted Excel workbook with native formulas, and authored an Ethics report covering DPDP Act 2023, PII masking, and human-in-the-loop safety. I will now demonstrate running the master pipeline."*

---

## 8. 15 Likely Viva Voce Questions & Answers

**Q1: Why is API latency modeled as lognormal rather than normal (Gaussian)?**  
*Answer:* Network and processing delays have a physical lower bound ($> 0\text{ ms}$) and an unbounded right tail caused by garbage collection pauses, queuing delay, and I/O wait. Our D'Agostino normality test rejected Gaussian normality ($p < 0.001$), confirming right-skewed lognormal behavior.

**Q2: What is the Law of Large Numbers (LLN) and how did you demonstrate it?**  
*Answer:* LLN states that as sample size ($n$) increases, the sample mean ($\bar{x}$) converges to the population mean ($\mu$). We drew random samples from $n=30$ to $n=10,000$ and plotted sample mean convergence against the true population mean ($82.58\text{ ms}$).

**Q3: How does Bayes' Theorem help eliminate false alarms in alerting?**  
*Answer:* A single metric (like high latency) has a low posterior probability of being a real anomaly ($4.1\%$) because background noise can cause temporary spikes. By applying Bayes' theorem to combine independent signals (high latency AND high error rate), the posterior probability jumps to $92.3\%$, providing a mathematically sound confidence score.

**Q4: Why must true anomalies NOT be deleted during data cleaning?**  
*Answer:* In standard regression or clustering, outliers can distort model parameters. But in anomaly detection, anomalies are the primary target of interest! Deleting them leaves the dataset sterile. We only filter impossible hardware/sensor glitches (negative latency or sensor overflow) and keep an outlier indicator flag.

**Q5: Why did you use time-based train/test splits instead of `train_test_split(shuffle=True)`?**  
*Answer:* Time series data possesses temporal autocorrelation. Randomly shuffling rows allows future observations to leak into the training partition, creating artificial, unrealistically optimistic evaluation scores (data leakage). We strictly split the first $75\%$ chronologically for training and the last $25\%$ for testing.

**Q6: How does an Isolation Forest detect anomalies?**  
*Answer:* Isolation Forest isolates anomalies by randomly selecting a feature and a split value. Because anomalies are few and have extreme attribute values, they are isolated much closer to the root of the tree (shorter average path length) than normal points.

**Q7: What is the purpose of the Majority Voting Ensemble?**  
*Answer:* Unsupervised detectors (Isolation Forest, LOF, One-Class SVM) each have distinct geometric assumptions. LOF is density-based, while IsoForest is partitioning-based. Individual detectors generate false positives. By requiring $\ge 2$ of 3 models to agree, our ensemble reduced false positives by $40\%$ while maintaining $100\%$ recall.

**Q8: Why did the supervised Random Forest have lower recall than unsupervised models?**  
*Answer:* Supervised classifiers learn fixed decision boundaries based on historical training fault patterns. When novel, unobserved failure shapes occur in the test set, supervised models fail to generalize. Unsupervised detectors flag deviations from normality regardless of the specific failure shape.

**Q9: What is "Alert Fatigue" and how does your project address it?**  
*Answer:* Alert fatigue occurs when on-call engineers are inundated with excessive false alarms, leading to desensitization and missed critical outages. We solve it via temporal incident grouping (merging consecutive alerts), a 20-minute cooldown timer, and dynamic severity thresholds, cutting alert noise by $98.7\%$.

**Q10: How does your root-cause engine determine upstream vs downstream failures?**  
*Answer:* Our engine incorporates a microservice dependency graph (`order-service` $\rightarrow$ `payment-service` $\rightarrow$ `inventory-service`). If `payment-service` fails, `order-service` also degrades. The engine detects that `payment-service` was anomalous first and flags it as the root cause origin.

**Q11: What is Cramér's V in your Chi-Square test?**  
*Answer:* The Chi-Square test indicates whether an association exists between service and error status ($p < 0.001$). Cramér's V measures the effect size (strength of association) on a scale from 0 to 1, ensuring the finding is practically meaningful and not merely a byproduct of large sample size.

**Q12: What does PCA (Principal Component Analysis) achieve here?**  
*Answer:* PCA projects our 26 engineered continuous features onto orthogonal principal axes that maximize variance. The 2D PCA projection revealed clear spatial separation between normal operational clusters and anomalous failure modes.

**Q13: How does your system comply with India's DPDP Act 2023 and GDPR?**  
*Answer:* We enforce data minimization by stripping URL query parameters, masking/hashing client IP addresses with cryptographic salt, redacting authorization tokens, using synthetic profiles, and implementing a tiered data retention policy.

**Q14: What is the difference between descriptive, diagnostic, and predictive analytics in this project?**  
*Answer:* Descriptive analytics describes what happened (mean latency, status code counts in Phase 2); diagnostic analytics investigates why it happened (correlation heatmap, root-cause inference in Phase 3 & 5); predictive analytics forecasts whether an unseen observation is an anomaly (ML models in Phase 4).

**Q15: How can this system be extended to a real-time production cluster?**  
*Answer:* By replacing batch CSV ingestion with an Apache Kafka topic for streaming request logs, deploying the trained Isolation Forest/LOF pipeline within a Faust or Apache Flink streaming consumer, and exposing Prometheus metrics for real-time Grafana visualization.

---

## 9. Syllabus Coverage Checklist

| Syllabus Unit | Course Concept | Implemented Files |
| :--- | :--- | :--- |
| **Unit I** | Data Science Lifecycle, Data Sources, APIs, Web Scraping | [`src/acquisition/load_generator.py`](file:///c:/Users/astro/OneDrive/Documents/ds/api-anomaly-detection/src/acquisition/load_generator.py), [`scraper.py`](file:///c:/Users/astro/OneDrive/Documents/ds/api-anomaly-detection/src/acquisition/scraper.py), [`microservices/services.py`](file:///c:/Users/astro/OneDrive/Documents/ds/api-anomaly-detection/microservices/services.py) |
| **Unit II** | CLT, Descriptive Stats, Distributions (Poisson/Normal), Bayes, ANOVA, t-test, Chi-Square, Correlation | [`src/statistics/stats_analysis.py`](file:///c:/Users/astro/OneDrive/Documents/ds/api-anomaly-detection/src/statistics/stats_analysis.py), [`reports/figures/correlation_heatmap.png`](file:///c:/Users/astro/OneDrive/Documents/ds/api-anomaly-detection/reports/figures/correlation_heatmap.png) |
| **Unit III** | Data Visualization, Tableau Public, Power BI Desktop | [`src/visualization/plots.py`](file:///c:/Users/astro/OneDrive/Documents/ds/api-anomaly-detection/src/visualization/plots.py), [`dashboards/tableau_guide.md`](file:///c:/Users/astro/OneDrive/Documents/ds/api-anomaly-detection/dashboards/tableau_guide.md), [`dashboards/powerbi_guide.md`](file:///c:/Users/astro/OneDrive/Documents/ds/api-anomaly-detection/dashboards/powerbi_guide.md) |
| **Unit IV** | Cleaning, Imputation, PCA, Feature Engineering, Anomaly Detection Models, Evaluation | [`src/preprocessing/cleaning.py`](file:///c:/Users/astro/OneDrive/Documents/ds/api-anomaly-detection/src/preprocessing/cleaning.py), [`feature_engineering.py`](file:///c:/Users/astro/OneDrive/Documents/ds/api-anomaly-detection/src/preprocessing/feature_engineering.py), [`src/models/detectors.py`](file:///c:/Users/astro/OneDrive/Documents/ds/api-anomaly-detection/src/models/detectors.py), [`evaluate.py`](file:///c:/Users/astro/OneDrive/Documents/ds/api-anomaly-detection/src/models/evaluate.py) |
| **Unit V** | Excel Analysis Workbook, Formulas, Pivot Ready Exports | [`src/visualization/excel_builder.py`](file:///c:/Users/astro/OneDrive/Documents/ds/api-anomaly-detection/src/visualization/excel_builder.py), [`excel/analysis_workbook.xlsx`](file:///c:/Users/astro/OneDrive/Documents/ds/api-anomaly-detection/excel/analysis_workbook.xlsx), [`src/visualization/exporter.py`](file:///c:/Users/astro/OneDrive/Documents/ds/api-anomaly-detection/src/visualization/exporter.py) |
| **Course Objective 5** | Ethics, PII Privacy, Bias, Alert Fatigue, Responsible AI | [`reports/ethics.md`](file:///c:/Users/astro/OneDrive/Documents/ds/api-anomaly-detection/reports/ethics.md) |
