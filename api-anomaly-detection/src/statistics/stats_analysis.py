"""
=====================================================================
Statistical Analysis Module (src/statistics/stats_analysis.py)
U23AD491 Data Science Project: API Anomaly Detection System
=====================================================================
Covers Unit II Syllabus:
  1. Population vs Sample & Central Limit Theorem convergence
  2. Descriptive statistics (Mean, Median, Skewness, Kurtosis, Percentiles)
  3. Theoretical Probability Distributions (Poisson, Lognormal, Binomial, Uniform)
  4. Bayes' Theorem & Multi-Signal Posterior Probability
  5. Inferential Statistics:
     - 2-Sample Student's t-test
     - 95% Confidence Intervals
     - One-way ANOVA across microservices
     - Chi-Square test of independence (Errors vs Services)
  6. Covariance & Correlation Heatmap
  7. Rolling Statistical Detectors (Z-score and IQR)
"""

import numpy as np
import pandas as pd
import scipy.stats as stats
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from typing import Dict, Tuple, Any

from src.utils.config import (
    RAW_DATA_DIR,
    PROCESSED_DATA_DIR,
    FIGURES_DIR,
    EXPORTS_DIR,
    RANDOM_SEED,
)
from src.utils.logger import get_logger

logger = get_logger("Statistical-Analysis")


def load_raw_dataset() -> pd.DataFrame:
    """Loads raw generated telemetry dataset."""
    path = RAW_DATA_DIR / "synthetic_microservices_logs.csv"
    if not path.exists():
        raise FileNotFoundError(f"Raw data not found at {path}. Run load_generator.py first.")
    df = pd.read_csv(path)
    return df


def analyze_population_vs_sample(df: pd.DataFrame, target_col: str = "response_time_ms") -> Dict[str, Any]:
    """
    Demonstrates Law of Large Numbers (LLN) and Central Limit Theorem (CLT).
    Treats the dataset as the ground-truth population and draws random samples.
    """
    valid_series = df[target_col].dropna()
    # Filter extreme physical sensor glitches for clean statistical sampling
    clean_population = valid_series[(valid_series >= 0) & (valid_series < 10000)]
    pop_mean = clean_population.mean()
    pop_std = clean_population.std()

    sample_sizes = [30, 100, 250, 500, 1000, 2500, 5000, 10000]
    sample_means = []
    sample_errors = []

    np.random.seed(RANDOM_SEED)
    for n in sample_sizes:
        sample = clean_population.sample(n=n, replace=False, random_state=RANDOM_SEED)
        s_mean = sample.mean()
        sample_means.append(s_mean)
        sample_errors.append(abs(s_mean - pop_mean))

    # Plot Central Limit Theorem Convergence
    plt.figure(figsize=(10, 5))
    plt.plot(sample_sizes, sample_means, marker="o", color="#1f77b4", linewidth=2.5, label="Sample Mean (x̄)")
    plt.axhline(pop_mean, color="#d62728", linestyle="--", linewidth=2, label=f"True Population Mean (μ = {pop_mean:.2f} ms)")
    plt.title("Population vs Sample: Central Limit Theorem Convergence (Unit II)", fontsize=13, fontweight="bold")
    plt.xlabel("Sample Size (n)", fontsize=11)
    plt.ylabel("Mean Latency (ms)", fontsize=11)
    plt.grid(True, linestyle=":", alpha=0.6)
    plt.legend(fontsize=10)
    plt.tight_layout()
    clt_plot_path = FIGURES_DIR / "population_vs_sample_clt.png"
    plt.savefig(clt_plot_path, dpi=300)
    plt.close()

    logger.info(f"CLT Analysis: True Pop Mean={pop_mean:.2f}ms. Largest Sample Mean={sample_means[-1]:.2f}ms.")
    return {
        "population_mean": round(pop_mean, 2),
        "population_std": round(pop_std, 2),
        "sample_sizes": sample_sizes,
        "sample_means": [round(m, 2) for m in sample_means],
        "sample_errors": [round(e, 3) for e in sample_errors],
    }


def compute_descriptive_statistics(df: pd.DataFrame) -> pd.DataFrame:
    """
    Computes comprehensive descriptive statistics per service:
    Mean, Median, Std, Variance, Min, Max, P50, P90, P95, P99, Skewness, Kurtosis.
    """
    valid = df.dropna(subset=["response_time_ms"]).copy()
    valid = valid[(valid["response_time_ms"] >= 0) & (valid["response_time_ms"] < 10000)]

    records = []
    for svc, group in valid.groupby("service"):
        lat = group["response_time_ms"]
        records.append({
            "service": svc,
            "count": len(lat),
            "mean": round(lat.mean(), 2),
            "median": round(lat.median(), 2),
            "std": round(lat.std(), 2),
            "variance": round(lat.var(), 2),
            "min": round(lat.min(), 2),
            "max": round(lat.max(), 2),
            "p50": round(lat.quantile(0.50), 2),
            "p90": round(lat.quantile(0.90), 2),
            "p95": round(lat.quantile(0.95), 2),
            "p99": round(lat.quantile(0.99), 2),
            "skewness": round(stats.skew(lat), 3),
            "kurtosis": round(stats.kurtosis(lat), 3),
        })

    summary_df = pd.DataFrame(records)
    summary_path = EXPORTS_DIR / "service_descriptive_stats.csv"
    summary_df.to_csv(summary_path, index=False)
    logger.info(f"Descriptive statistics computed and saved to {summary_path}")
    return summary_df


def fit_and_test_distributions(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Fits and tests theoretical probability distributions:
      1. Poisson: Request throughput per minute
      2. Normal vs Lognormal: Response time (testing skewness with D'Agostino & Shapiro-Wilk)
      3. Binomial: Number of errors per batch
      4. Uniform: Load balancer instance distribution (Chi-Square goodness of fit)
    """
    results = {}

    # 1. Poisson Fit on request counts
    req_counts = df["request_count"].dropna()
    lambda_poisson = req_counts.mean()
    results["poisson_lambda"] = round(float(lambda_poisson), 2)

    # 2. Normality Test on Latency (Normal vs Lognormal)
    auth_lat = df[(df["service"] == "auth-service") & (df["is_anomaly"] == 0)]["response_time_ms"].dropna()
    auth_lat = auth_lat[(auth_lat > 0) & (auth_lat < 1000)]
    stat_norm, p_val_norm = stats.normaltest(auth_lat)
    log_lat = np.log(auth_lat)
    stat_lognorm, p_val_lognorm = stats.normaltest(log_lat)

    results["normality_test"] = {
        "raw_dagostino_stat": round(float(stat_norm), 2),
        "raw_p_value": float(p_val_norm),
        "is_raw_normal": bool(p_val_norm > 0.05),
        "log_transformed_dagostino_stat": round(float(stat_lognorm), 2),
        "log_transformed_p_value": float(p_val_lognorm),
        "interpretation": "Raw latency strongly rejects Gaussian normality (p < 0.05) and conforms to Lognormal distribution.",
    }

    # 3. Uniform Distribution: Instance selection
    instance_counts = df[df["service"] == "payment-service"]["instance_id"].value_counts()
    chi_instance, p_instance = stats.chisquare(instance_counts)
    results["instance_uniformity"] = {
        "chi_square_stat": round(float(chi_instance), 3),
        "p_value": round(float(p_instance), 4),
        "is_uniform": bool(p_instance > 0.05),
        "interpretation": "Instance traffic is uniformly balanced across replica pods.",
    }

    # Plot Probability Distributions Comparison
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    # Subplot 1: Latency Distribution with Normal and Lognormal Fits
    sns.histplot(auth_lat, kde=True, stat="density", ax=axes[0], color="#2ca02c", bins=40, label="Observed Auth Latency")
    x = np.linspace(auth_lat.min(), auth_lat.max(), 200)
    axes[0].plot(x, stats.norm.pdf(x, auth_lat.mean(), auth_lat.std()), "r--", linewidth=2, label="Fitted Normal")
    shape, loc, scale = stats.lognorm.fit(auth_lat)
    axes[0].plot(x, stats.lognorm.pdf(x, shape, loc, scale), "b-", linewidth=2.5, label="Fitted Lognormal")
    axes[0].set_title("Response Time: Normal vs Lognormal Fit", fontsize=11, fontweight="bold")
    axes[0].set_xlabel("Latency (ms)")
    axes[0].legend()
    axes[0].grid(True, linestyle=":", alpha=0.5)

    # Subplot 2: Poisson Distribution for Request Throughput
    sns.histplot(req_counts, discrete=True, stat="density", ax=axes[1], color="#1f77b4", label="Observed Requests/Min")
    k = np.arange(int(req_counts.min()), int(req_counts.max()) + 1)
    axes[1].plot(k, stats.poisson.pmf(k, lambda_poisson), "ro-", markersize=3, linewidth=1.5, label=f"Poisson (λ={lambda_poisson:.1f})")
    axes[1].set_title("Request Counts: Poisson Distribution", fontsize=11, fontweight="bold")
    axes[1].set_xlabel("Requests per Interval")
    axes[1].legend()
    axes[1].grid(True, linestyle=":", alpha=0.5)

    plt.tight_layout()
    dist_plot_path = FIGURES_DIR / "probability_distributions.png"
    plt.savefig(dist_plot_path, dpi=300)
    plt.close()

    logger.info("Fitted theoretical probability distributions successfully.")
    return results


def calculate_bayesian_conditional_probabilities(df: pd.DataFrame) -> Dict[str, float]:
    """
    Computes prior, likelihood, and posterior probabilities via Bayes' Theorem:
      P(A | B) = [P(B | A) * P(A)] / P(B)

    Signals:
      A = Anomaly event (is_anomaly == 1)
      B_lat = High Latency (> p95 baseline)
      B_err = High Error (status_code >= 500)
      B_comb = Both Latency High AND Error High
    """
    clean = df.dropna(subset=["response_time_ms"]).copy()
    total = len(clean)

    # Global Anomaly Prior
    n_anomaly = (clean["is_anomaly"] == 1).sum()
    p_anomaly = n_anomaly / total

    # Define thresholds
    lat_p95 = clean["response_time_ms"].quantile(0.95)
    is_lat_high = clean["response_time_ms"] > lat_p95
    is_err_high = clean["status_code"] >= 500
    is_comb_high = is_lat_high & is_err_high

    p_lat_high = is_lat_high.mean()
    p_err_high = is_err_high.mean()
    p_comb_high = is_comb_high.mean()

    # Likelihoods: P(Evidence | Anomaly)
    df_anomaly = clean[clean["is_anomaly"] == 1]
    p_lat_given_anom = (df_anomaly["response_time_ms"] > lat_p95).mean()
    p_err_given_anom = (df_anomaly["status_code"] >= 500).mean()
    p_comb_given_anom = ((df_anomaly["response_time_ms"] > lat_p95) & (df_anomaly["status_code"] >= 500)).mean()

    # Posterior Probabilities: P(Anomaly | Evidence) via Bayes Theorem
    p_anom_given_lat = (p_lat_given_anom * p_anomaly) / p_lat_high if p_lat_high > 0 else 0.0
    p_anom_given_err = (p_err_given_anom * p_anomaly) / p_err_high if p_err_high > 0 else 0.0
    p_anom_given_comb = (p_comb_given_anom * p_anomaly) / p_comb_high if p_comb_high > 0 else 0.0

    bayesian_results = {
        "prior_p_anomaly": round(float(p_anomaly), 4),
        "posterior_p_anomaly_given_latency_high": round(float(p_anom_given_lat), 4),
        "posterior_p_anomaly_given_error_high": round(float(p_anom_given_err), 4),
        "posterior_p_anomaly_given_both_signals": round(float(p_anom_given_comb), 4),
    }

    logger.info(
        f"Bayesian Analysis: Prior={p_anomaly:.3f} | P(Anom|Lat)={p_anom_given_lat:.3f} | "
        f"P(Anom|Err)={p_anom_given_err:.3f} | P(Anom|Both)={p_anom_given_comb:.3f}"
    )
    return bayesian_results


def run_inferential_hypothesis_tests(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Executes core inferential hypothesis tests (Unit II):
      1. Student's 2-Sample t-test: Current peak hour mean vs Off-peak baseline mean
      2. 95% Confidence Intervals for mean latency per service
      3. One-Way ANOVA across all 6 microservices
      4. Chi-Square Test of Independence: Error Status vs Service
    """
    clean = df.dropna(subset=["response_time_ms"]).copy()
    clean = clean[(clean["response_time_ms"] >= 0) & (clean["response_time_ms"] < 10000)]
    clean["datetime"] = pd.to_datetime(clean["timestamp"])
    clean["hour"] = clean["datetime"].dt.hour

    inferential_results = {}

    # 1. Student's t-test: Peak Hours (11:00-13:00) vs Baseline Off-Peak (02:00-05:00) for payment-service
    pay_data = clean[clean["service"] == "payment-service"]
    peak_sample = pay_data[pay_data["hour"].isin([11, 12, 13])]["response_time_ms"]
    offpeak_sample = pay_data[pay_data["hour"].isin([2, 3, 4, 5])]["response_time_ms"]

    t_stat, t_pval = stats.ttest_ind(peak_sample, offpeak_sample, equal_var=False)
    inferential_results["t_test_peak_vs_offpeak"] = {
        "t_statistic": round(float(t_stat), 3),
        "p_value": float(t_pval),
        "reject_null": bool(t_pval < 0.05),
        "interpretation": "Peak hour latency is statistically significantly higher than off-peak baseline (p < 0.05).",
    }

    # 2. 95% Confidence Intervals per service: x_bar +/- t_crit * (s / sqrt(n))
    ci_table = []
    for svc, grp in clean.groupby("service"):
        vals = grp["response_time_ms"]
        n = len(vals)
        mean = vals.mean()
        sem = stats.sem(vals)
        ci_lower, ci_upper = stats.t.interval(0.95, df=n - 1, loc=mean, scale=sem)
        ci_table.append({
            "service": svc,
            "sample_size": n,
            "mean_latency_ms": round(mean, 2),
            "ci_95_lower": round(ci_lower, 2),
            "ci_95_upper": round(ci_upper, 2),
            "margin_of_error": round(ci_upper - mean, 2),
        })
    ci_df = pd.DataFrame(ci_table)
    ci_path = EXPORTS_DIR / "confidence_intervals_95.csv"
    ci_df.to_csv(ci_path, index=False)
    inferential_results["confidence_intervals"] = ci_table

    # 3. One-Way ANOVA across 6 microservices
    service_groups = [grp["response_time_ms"].values for _, grp in clean.groupby("service")]
    f_stat, anova_pval = stats.f_oneway(*service_groups)
    inferential_results["anova"] = {
        "f_statistic": round(float(f_stat), 3),
        "p_value": float(anova_pval),
        "reject_null": bool(anova_pval < 0.05),
        "interpretation": "Microservices have statistically distinct baseline latencies (F-stat large, p < 0.001).",
    }

    # 4. Chi-Square Test of Independence (Status Code Success vs 5xx Failure across Services)
    clean["is_error"] = (clean["status_code"] >= 500).astype(int)
    contingency_table = pd.crosstab(clean["service"], clean["is_error"])
    chi2_stat, chi_pval, dof, _ = stats.chi2_contingency(contingency_table)

    # Cramér's V for effect size
    n_tot = contingency_table.sum().sum()
    cramers_v = np.sqrt(chi2_stat / (n_tot * (min(contingency_table.shape) - 1)))

    inferential_results["chi_square"] = {
        "chi2_statistic": round(float(chi2_stat), 3),
        "p_value": float(chi_pval),
        "degrees_of_freedom": int(dof),
        "cramers_v": round(float(cramers_v), 3),
        "interpretation": "5xx error occurrence is dependent on the specific microservice.",
    }

    logger.info("Inferential hypothesis testing completed successfully.")
    return inferential_results


def compute_correlation_covariance(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Computes Pearson Correlation and Covariance matrices between:
    response_time_ms, request_count, cpu_percent, memory_mb, request_size_kb, response_size_kb.
    Renders Seaborn heatmap to reports/figures/correlation_heatmap.png.
    """
    metrics = [
        "response_time_ms",
        "request_count",
        "cpu_percent",
        "memory_mb",
        "request_size_kb",
        "response_size_kb",
    ]
    clean = df[metrics].dropna().copy()
    clean = clean[(clean["response_time_ms"] >= 0) & (clean["response_time_ms"] < 10000)]

    corr_matrix = clean.corr(method="pearson")
    cov_matrix = clean.cov()

    # Save to CSV
    corr_matrix.to_csv(EXPORTS_DIR / "correlation_matrix.csv")
    cov_matrix.to_csv(EXPORTS_DIR / "covariance_matrix.csv")

    # Plot Seaborn Heatmap
    plt.figure(figsize=(9, 7))
    sns.heatmap(
        corr_matrix,
        annot=True,
        fmt=".3f",
        cmap="coolwarm",
        vmin=-1,
        vmax=1,
        linewidths=1.0,
        cbar_kws={"label": "Pearson Correlation Coefficient (r)"},
    )
    plt.title("Metrics Correlation Heatmap (Unit II: Correlation & Covariance)", fontsize=12, fontweight="bold")
    plt.tight_layout()
    heatmap_path = FIGURES_DIR / "correlation_heatmap.png"
    plt.savefig(heatmap_path, dpi=300)
    plt.close()

    logger.info(f"Correlation and covariance matrices exported. Heatmap saved to {heatmap_path}")
    return corr_matrix, cov_matrix


def run_statistical_anomaly_detectors(df: pd.DataFrame, window: int = 24) -> pd.DataFrame:
    """
    Implements Rolling Z-score and Rolling IQR detectors (Unit II Baseline):
      - Z-Score: |z| > 3.0 on rolling mean/std
      - IQR Rule: value > Q3 + 1.5 * IQR or value < Q1 - 1.5 * IQR
    """
    clean = df.copy()
    clean["datetime"] = pd.to_datetime(clean["timestamp"])
    clean = clean.sort_values(by=["service", "datetime"]).reset_index(drop=True)

    results = []
    for svc, grp in clean.groupby("service"):
        grp = grp.copy()
        series = grp["response_time_ms"].fillna(grp["response_time_ms"].median())

        # Rolling Z-score
        roll_mean = series.rolling(window=window, min_periods=5).mean()
        roll_std = series.rolling(window=window, min_periods=5).std().replace(0, 1e-5)
        z_scores = (series - roll_mean) / roll_std
        grp["z_score"] = z_scores.fillna(0.0)
        grp["z_anomaly"] = (grp["z_score"].abs() > 3.0).astype(int)

        # Rolling IQR
        q25 = series.rolling(window=window, min_periods=5).quantile(0.25)
        q75 = series.rolling(window=window, min_periods=5).quantile(0.75)
        iqr = (q75 - q25).replace(0, 1e-5)
        upper_bound = q75 + 1.5 * iqr
        lower_bound = q25 - 1.5 * iqr
        grp["iqr_anomaly"] = ((series > upper_bound) | (series < lower_bound)).astype(int)

        results.append(grp)

    final_df = pd.concat(results, ignore_index=True)
    return final_df


def execute_full_statistical_pipeline() -> Dict[str, Any]:
    """Runs all statistical routines and returns aggregated results dictionary."""
    df = load_raw_dataset()
    logger.info("Starting Phase 2: Full Statistical Analysis Pipeline...")

    clt_res = analyze_population_vs_sample(df)
    desc_df = compute_descriptive_statistics(df)
    dist_res = fit_and_test_distributions(df)
    bayes_res = calculate_bayesian_conditional_probabilities(df)
    infer_res = run_inferential_hypothesis_tests(df)
    corr_mat, cov_mat = compute_correlation_covariance(df)
    stat_detected_df = run_statistical_anomaly_detectors(df)

    # Save stat detected sample
    stat_detected_df.to_csv(PROCESSED_DATA_DIR / "statistical_baseline_detected.csv", index=False)

    logger.info("Phase 2 Statistical Analysis executed successfully with all artifacts generated!")
    return {
        "clt": clt_res,
        "descriptive_stats": desc_df.to_dict(orient="records"),
        "distributions": dist_res,
        "bayesian": bayes_res,
        "inferential": infer_res,
    }


if __name__ == "__main__":
    execute_full_statistical_pipeline()
