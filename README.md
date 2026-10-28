# API Performance Anomaly Detection and Intelligent Alerting System for Microservices

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![Course](https://img.shields.io/badge/Course-U23AD491%20Data%20Science%20Project-green.svg)](#)
[![Academic Year](https://img.shields.io/badge/Academic%20Year-2026--2027-orange.svg)](#)
[![Alert Noise Reduction](https://img.shields.io/badge/Alert%20Fatigue%20Reduction-98.7%25-brightgreen.svg)](#)
[![Web Dashboard](https://img.shields.io/badge/Web%20Dashboard-Live%20on%20Port%205000-purple.svg)](#)

A comprehensive, end-to-end, production-grade academic Data Science and Machine Learning project for 3rd-Year Computer Science & Engineering students. Maps directly to **Units I through V** and **Course Objectives 1 through 5** of the university Data Science curriculum.

---

## 1. Quick Links & Execution Commands

### Run End-to-End Master Pipeline (Phases 1 to 7)
Runs data generation, scraping, statistical tests, data cleaning, feature engineering, model training, evaluation, alerting replay, dashboard exports, and Excel generation in ~40 seconds:
```bash
python main.py
```

### Launch Interactive Web Dashboard & APM Control Center
Starts the Flask-powered glassmorphic APM control center on `http://localhost:5000`:
```bash
python run_web.py
```

### Key Deliverables & Documentation:
- **Interactive Web App:** Open `http://localhost:5000` in your browser.
- **Academic Research Final Report:** [`api-anomaly-detection/reports/final_report.md`](file:///c:/Users/astro/OneDrive/Documents/ds/api-anomaly-detection/reports/final_report.md)
- **Ethics & Privacy Report (DPDP 2023 / GDPR):** [`api-anomaly-detection/reports/ethics.md`](file:///c:/Users/astro/OneDrive/Documents/ds/api-anomaly-detection/reports/ethics.md)
- **Tableau Public Guide:** [`api-anomaly-detection/dashboards/tableau_guide.md`](file:///c:/Users/astro/OneDrive/Documents/ds/api-anomaly-detection/dashboards/tableau_guide.md)
- **Power BI Desktop Guide:** [`api-anomaly-detection/dashboards/powerbi_guide.md`](file:///c:/Users/astro/OneDrive/Documents/ds/api-anomaly-detection/dashboards/powerbi_guide.md)
- **Excel Analysis Workbook:** [`api-anomaly-detection/excel/analysis_workbook.xlsx`](file:///c:/Users/astro/OneDrive/Documents/ds/api-anomaly-detection/excel/analysis_workbook.xlsx)
- **Curriculum Jupyter Notebooks:** [`api-anomaly-detection/notebooks/`](file:///c:/Users/astro/OneDrive/Documents/ds/api-anomaly-detection/notebooks) (`01_` through `05_`)

---

## 2. Problem Statement & Motivation

Modern software is divided into dozens of loosely coupled REST microservices (`auth-service`, `payment-service`, `order-service`, `user-service`, `inventory-service`, `notification-service`). Traditional monitoring systems rely on static threshold alerting (e.g., *“Alert if latency > 200ms”*), which suffers from two critical flaws:
1. **High False Alarms (Alert Fatigue):** Naturally slower services (such as a database-heavy payment gateway taking ~210ms) trigger thousands of spurious alerts during normal peak load.
2. **Missed Incidents (False Negatives):** Naturally fast services (such as an in-memory auth cache taking ~45ms) can suffer severe 200% degradation (reaching 140ms) without ever crossing a static 200ms threshold.

### Project Objective:
Build an intelligent, data-driven APM system that:
1. Collects high-cardinality multi-service telemetry (latency, CPU, memory, error rates, throughput).
2. Cleans, imputes, and engineers time-series features.
3. Applies probability theory and unsupervised machine learning ensembles to detect complex anomalies.
4. Uses Bayesian inference, deduplication, and cooldown rate-limiting to cut alert fatigue by **98.7%**.
5. Delivers interactive web dashboards, Tableau/Power BI exports, and Excel workbooks.

---

## 3. High-Level System Architecture

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
        EXP --> WEB[Interactive Web Dashboard localhost:5000]
        EXP --> TAB[Tableau Public Dashboards]
        EXP --> PBI[Power BI Desktop Dashboards]
        EXP --> XL[Excel Analysis Workbook .xlsx]
    end
```

---

## 4. Complete Data Dictionary

Every record in [`data/raw/synthetic_microservices_logs.csv`](file:///c:/Users/astro/OneDrive/Documents/ds/api-anomaly-detection/data/raw/synthetic_microservices_logs.csv) and [`data/processed/cleaned_metrics.csv`](file:///c:/Users/astro/OneDrive/Documents/ds/api-anomaly-detection/data/processed/cleaned_metrics.csv) adheres to the following specification:

| Column Name | Data Type | Units / Range | Description |
| :--- | :--- | :--- | :--- |
| `timestamp` | Datetime | `YYYY-MM-DD HH:MM:SS` | 5-minute sampling interval across 30 continuous days. |
| `service` | String | Categorical (6 services) | Target microservice (`auth`, `payment`, `order`, `user`, `inventory`, `notification`). |
| `endpoint` | String | URI Path | REST endpoint path (`/login`, `/pay`, `/orders`, `/users`, `/inventory`, `/notify`). |
| `method` | String | `POST` / `GET` | HTTP request verb. |
| `status_code` | Integer | HTTP Status | Status code (`200` OK, `500` Internal Error, `502`, `503`, `504`). |
| `response_time_ms` | Float | Milliseconds ($> 0.0$) | Server response round-trip time (modeled as right-skewed lognormal). |
| `request_count` | Integer | Count per interval | Request volume received in interval (Poisson distributed with diurnal curves). |
| `request_size_kb` | Float | Kilobytes | Average incoming HTTP payload size. |
| `response_size_kb` | Float | Kilobytes | Average outgoing HTTP payload size. |
| `cpu_percent` | Float | Percentage ($0.0 - 100.0$) | Container / Host CPU utilization. |
| `memory_mb` | Float | Megabytes ($50 - 1000$) | Resident memory footprint (used for detecting gradual memory leaks). |
| `instance_id` | String | Alphanumeric | Replica pod identifier (e.g., `pay-prod-01`, `auth-prod-02`). |
| `is_anomaly` | Integer | `0` (Normal) or `1` (Anomaly) | Ground-truth binary label for model evaluation. |
| `anomaly_type` | String | Categorical (7 classes) | `normal`, `latency_spike`, `gradual_degradation`, `error_burst`, `traffic_drop`, `traffic_surge`, `cpu_saturation`. |

---

## 5. Summary of Experimental Results

### 5.1 Machine Learning Benchmark Comparison (Out-of-Sample Test Set)
Tested on chronological out-of-sample data (first 75% train, last 25% test = 12,960 intervals; zero temporal data leakage):

```text
Model                   Precision  Recall   F1_Score  ROC_AUC  Specificity  False_Positives  Detection_Delay
StatisticalZScore       0.1641     0.6774   0.2642    0.8346   0.9917       107              0.0 min
IsolationForest         0.0515     0.6452   0.0955    0.9581   0.9715       368              18.3 min
LocalOutlierFactor      0.0754     1.0000   0.1403    0.9997   0.9706       380              0.0 min
OneClassSVM             0.0769     1.0000   0.1429    0.9998   0.9712       372              0.0 min
MajorityVotingEnsemble  0.1183     1.0000   0.2116    0.9996   0.9821       231 (40% CUT)    0.0 min
SupervisedRF (Ceiling)  0.9444     0.5484   0.6939    0.9999   0.9999       1                10.0 min
```

* **Best Unsupervised Detector:** **Majority Voting Ensemble** achieved **100.0% Recall** with **0.0 minutes detection delay**, slashing false positives by **~40%** compared to standalone models.

### 5.2 Alert Fatigue Benchmark
* **Naive Static System ($> 180\text{ ms}$ or $5xx$):** Generated **1,561 alerts** (including 1,530 false alarms on payment-service).
* **Intelligent Alert Engine:** Dispatched **21 actionable, deduplicated incidents** with Bayesian confidence and root-cause hints.
* **Alert Noise Reduction:** **98.7% Alert Fatigue Cut!**

---

## 6. Project Structure Overview

```text
c:\Users\astro\OneDrive\Documents\ds\
├── README.md                           # Master Project Overview (This File)
├── requirements.txt                    # Project dependencies
├── main.py                             # Root launcher forwarding to api-anomaly-detection/main.py
├── run_web.py                          # Root launcher starting Web Dashboard on port 5000
└── api-anomaly-detection/
    ├── README.md                       # Comprehensive Technical README & Viva Guide
    ├── requirements.txt
    ├── main.py                         # Master Pipeline Orchestrator (Phases 1-7)
    ├── run_web.py                      # Flask APM Web Server
    ├── microservices/
    │   └── services.py                 # 6 REST microservices (/login, /pay, /orders, etc.) & /metrics
    ├── data/
    │   ├── raw/                        # 30-day raw logs & scraped RFC status specifications
    │   ├── processed/                  # Cleaned & 51-feature engineered datasets
    │   └── exports/                    # CSVs for Tableau, Power BI, and benchmarking
    ├── src/
    │   ├── acquisition/                # load_generator.py, collector.py, scraper.py
    │   ├── statistics/                 # stats_analysis.py (CLT, Bayes, ANOVA, distributions)
    │   ├── preprocessing/              # cleaning.py, feature_engineering.py
    │   ├── models/                     # detectors.py, evaluate.py
    │   ├── alerting/                   # alert_engine.py, notifier.py
    │   ├── visualization/              # plots.py, exporter.py, excel_builder.py
    │   └── utils/                      # config.py, logger.py
    ├── web/
    │   ├── app.py                      # Flask REST backend + live inference engine
    │   ├── templates/index.html        # Glassmorphic SPA Dashboard with 6 interactive tabs
    │   └── static/                     # CSS design system & Chart.js client logic
    ├── notebooks/                      # 5 curriculum Jupyter notebooks (01_ to 05_)
    ├── dashboards/                     # Step-by-step Tableau & Power BI implementation guides
    ├── excel/                          # analysis_workbook.xlsx (4 sheets with live formulas)
    └── reports/
        ├── final_report.md             # Formal academic research report
        ├── ethics.md                   # DPDP Act 2023, PII masking, alert fatigue, XAI
        └── figures/                    # 11 publication-grade PNG charts
```

---

## 7. Syllabus Coverage Checklist

| Syllabus Unit | Core Theoretical Concept | Implemented Project Files |
| :--- | :--- | :--- |
| **Unit I** | Data Science Lifecycle, Data Sources, REST API Ingestion, Ethical Web Scraping | [`src/acquisition/load_generator.py`](file:///c:/Users/astro/OneDrive/Documents/ds/api-anomaly-detection/src/acquisition/load_generator.py), [`scraper.py`](file:///c:/Users/astro/OneDrive/Documents/ds/api-anomaly-detection/src/acquisition/scraper.py), [`collector.py`](file:///c:/Users/astro/OneDrive/Documents/ds/api-anomaly-detection/src/acquisition/collector.py), [`microservices/services.py`](file:///c:/Users/astro/OneDrive/Documents/ds/api-anomaly-detection/microservices/services.py), [`notebooks/01_data_acquisition.ipynb`](file:///c:/Users/astro/OneDrive/Documents/ds/api-anomaly-detection/notebooks/01_data_acquisition.ipynb) |
| **Unit II** | Central Limit Theorem, Descriptive Stats, Probability Distributions (Poisson, Lognormal, Uniform), Bayes' Theorem, ANOVA, Student's $t$-test, Chi-Square, Correlation Heatmap | [`src/statistics/stats_analysis.py`](file:///c:/Users/astro/OneDrive/Documents/ds/api-anomaly-detection/src/statistics/stats_analysis.py), [`reports/figures/correlation_heatmap.png`](file:///c:/Users/astro/OneDrive/Documents/ds/api-anomaly-detection/reports/figures/correlation_heatmap.png), [`population_vs_sample_clt.png`](file:///c:/Users/astro/OneDrive/Documents/ds/api-anomaly-detection/reports/figures/population_vs_sample_clt.png), [`notebooks/02_statistical_analysis.ipynb`](file:///c:/Users/astro/OneDrive/Documents/ds/api-anomaly-detection/notebooks/02_statistical_analysis.ipynb) |
| **Unit III** | Data Visualization, Interactive Web Dashboard, Tableau Public Guide, Power BI Desktop, DAX Measures | [`web/app.py`](file:///c:/Users/astro/OneDrive/Documents/ds/api-anomaly-detection/web/app.py), [`src/visualization/plots.py`](file:///c:/Users/astro/OneDrive/Documents/ds/api-anomaly-detection/src/visualization/plots.py), [`src/visualization/exporter.py`](file:///c:/Users/astro/OneDrive/Documents/ds/api-anomaly-detection/src/visualization/exporter.py), [`dashboards/tableau_guide.md`](file:///c:/Users/astro/OneDrive/Documents/ds/api-anomaly-detection/dashboards/tableau_guide.md), [`dashboards/powerbi_guide.md`](file:///c:/Users/astro/OneDrive/Documents/ds/api-anomaly-detection/dashboards/powerbi_guide.md) |
| **Unit IV** | Data Preprocessing, Time-series Imputation, PCA Dimensionality Reduction, Unsupervised ML Detectors (Isolation Forest, LOF, OCSVM), Ensemble, Supervised RF Ceiling | [`src/preprocessing/cleaning.py`](file:///c:/Users/astro/OneDrive/Documents/ds/api-anomaly-detection/src/preprocessing/cleaning.py), [`feature_engineering.py`](file:///c:/Users/astro/OneDrive/Documents/ds/api-anomaly-detection/src/preprocessing/feature_engineering.py), [`src/models/detectors.py`](file:///c:/Users/astro/OneDrive/Documents/ds/api-anomaly-detection/src/models/detectors.py), [`evaluate.py`](file:///c:/Users/astro/OneDrive/Documents/ds/api-anomaly-detection/src/models/evaluate.py), [`notebooks/03_eda_feature_engineering.ipynb`](file:///c:/Users/astro/OneDrive/Documents/ds/api-anomaly-detection/notebooks/03_eda_feature_engineering.ipynb), [`notebooks/04_anomaly_detection.ipynb`](file:///c:/Users/astro/OneDrive/Documents/ds/api-anomaly-detection/notebooks/04_anomaly_detection.ipynb) |
| **Unit V** | Excel Analysis Workbook, Dynamic Formulas (AVERAGE, STDEV.S, CONFIDENCE.NORM, CORREL), Pivot Ready Tables | [`src/visualization/excel_builder.py`](file:///c:/Users/astro/OneDrive/Documents/ds/api-anomaly-detection/src/visualization/excel_builder.py), [`excel/analysis_workbook.xlsx`](file:///c:/Users/astro/OneDrive/Documents/ds/api-anomaly-detection/excel/analysis_workbook.xlsx), [`notebooks/05_alerting_and_evaluation.ipynb`](file:///c:/Users/astro/OneDrive/Documents/ds/api-anomaly-detection/notebooks/05_alerting_and_evaluation.ipynb) |
| **Course Objective 5** | Ethics & Societal Impact, PII & Token Masking, DPDP Act 2023 / GDPR, Alert Fatigue Mitigation, Human-in-the-Loop SRE | [`reports/ethics.md`](file:///c:/Users/astro/OneDrive/Documents/ds/api-anomaly-detection/reports/ethics.md) |

---

## 8. 5-Minute Viva Demo Script

Use this structured script when presenting your project to the examination panel:

* **Minute 1: Problem Statement & Motivation**  
  *"Good morning professors. Modern cloud systems split monolithic applications into microservices like auth, payment, and orders. Traditional monitoring uses static threshold rules—like alerting when latency exceeds 200ms. In microservices, this fails completely: it floods engineers with thousands of false alarms on naturally slower services like payment, while missing gradual memory leaks on fast services like auth. Our project builds an intelligent data science system to solve this."*
* **Minute 2: Data Acquisition & Statistics (Units I & II)**  
  *"In Phase 1, we simulated 30 days of 5-minute telemetry across 6 microservices with diurnal seasonality and scraped RFC HTTP specifications using BeautifulSoup. In Phase 2, we proved the Central Limit Theorem and showed that real latency rejects Gaussian normality and follows a lognormal distribution. Crucially, we applied Bayes' Theorem to show that combining high latency with error bursts elevates failure confidence from 0.3% to 92.3%."*
* **Minute 3: Preprocessing & Machine Learning (Unit IV)**  
  *"In Phase 3, we cleaned the data using time-series forward fill and linear interpolation, engineered 47 features including rolling 15-minute statistics and rate of change, and applied PCA dimensionality reduction. In Phase 4, we trained unsupervised detectors: Isolation Forest, Local Outlier Factor, and One-Class SVM. We constructed a Majority Voting Ensemble that achieved 100% recall with zero detection delay while reducing false positives by 40%."*
* **Minute 4: Intelligent Alerting & Fatigue Reduction**  
  *"In Phase 5, we built an Intelligent Alert Engine featuring Bayesian confidence scores, cooldown timers, incident deduplication, and dependency-aware root-cause analysis. When compared against naive static thresholds, our system reduced alert noise by 98.7%—from 1,561 noisy alerts down to 21 actionable incidents."*
* **Minute 5: Interactive Web App, Excel & Ethics (Units III, V & Course Obj 5)**  
  *"Finally, we deployed a live web dashboard running on port 5000 with real-time anomaly simulation, exported clean CSVs for Tableau and Power BI, generated an Excel workbook with native formulas, and authored an Ethics report covering DPDP Act 2023 and PII masking. I will now demonstrate running the master pipeline and web application."*

---

## 9. 15 Likely Viva Voce Questions & Answers

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
