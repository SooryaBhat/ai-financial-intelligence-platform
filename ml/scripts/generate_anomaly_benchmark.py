# -*- coding: utf-8 -*-
"""
generate_anomaly_benchmark.py
=============================
Independent, Versioned Multi-Paradigm Anomaly Evaluation Benchmark (v2.0).

Generates a realistic, documented multi-type anomaly evaluation dataset
independent of any detector's internal decision thresholds.

Varied Anomaly Types:
1. Contextual Discount (20-30% discount on standard products, below 35% rule threshold)
2. Margin Erosion / Negative Margin (selling below cost price / excessive coupon stacking)
3. Off-Hours / Weekend Velocity Spikes (timing & velocity deviations)
4. Multivariate Correlation Violations (plausible individual values, anomalous joint combination)
5. Outlier Magnitude Anomalies (large net amounts or extreme discounts)

Outputs:
- ml/datasets/processed/anomaly_benchmark_v2.csv
- ml/reports/anomaly_benchmark_meta.json
"""

import sys
import json
from pathlib import Path
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from utils import load_csv, save_csv, PROCESSED_DIR, REPORTS_DIR, SPLIT_CONFIG, DEV_COMPANIES

def create_independent_anomaly_benchmark(seed: int = 42) -> pd.DataFrame:
    np.random.seed(seed)
    df = load_csv("anomaly_features.csv", PROCESSED_DIR)
    df["sale_date"] = pd.to_datetime(df["sale_date"])
    
    # Filter to Dev Companies Test Period (2026-01-01 to 2026-10-21)
    dev_df = df[df["company_id"].isin(DEV_COMPANIES)].copy()
    test_df = dev_df[dev_df["sale_date"] >= SPLIT_CONFIG["test_start"]].copy().reset_index(drop=True)
    
    benchmark_df = test_df.copy()
    # Reset all labels to normal initially
    benchmark_df["benchmark_anomaly_label"] = 0
    benchmark_df["anomaly_type"] = "NORMAL"
    benchmark_df["anomaly_description"] = "Standard verified transaction"

    n_test = len(benchmark_df)
    # Target 3.0% total anomalies (approx 50-60 anomalous observations across types)
    n_anomalies_target = int(n_test * 0.035)
    per_type = n_anomalies_target // 5

    indices = np.random.choice(n_test, size=n_anomalies_target, replace=False)
    
    # Type 1: Contextual Discount Anomaly (subtle discount 22-32%, below rule 35% threshold)
    idx_type1 = indices[0:per_type]
    for i in idx_type1:
        benchmark_df.loc[i, "discount_pct"] = np.random.uniform(0.22, 0.32)
        benchmark_df.loc[i, "net_amount"] = benchmark_df.loc[i, "net_amount"] * (1.0 - benchmark_df.loc[i, "discount_pct"])
        benchmark_df.loc[i, "benchmark_anomaly_label"] = 1
        benchmark_df.loc[i, "anomaly_type"] = "CONTEXTUAL_DISCOUNT"
        benchmark_df.loc[i, "anomaly_description"] = "Unusual discount (22-32%) on standard retail transaction"

    # Type 2: Margin Erosion / Sub-Cost Anomaly
    idx_type2 = indices[per_type:2*per_type]
    for i in idx_type2:
        benchmark_df.loc[i, "discount_pct"] = np.random.uniform(0.18, 0.28)
        # Suppressed net amount causing negative margin
        benchmark_df.loc[i, "net_amount"] = np.random.uniform(1200.0, 3500.0)
        benchmark_df.loc[i, "benchmark_anomaly_label"] = 1
        benchmark_df.loc[i, "anomaly_type"] = "MARGIN_EROSION"
        benchmark_df.loc[i, "anomaly_description"] = "Severe price suppression below supplier cost baseline"

    # Type 3: Weekend / Timing Anomaly
    idx_type3 = indices[2*per_type:3*per_type]
    for i in idx_type3:
        benchmark_df.loc[i, "is_weekend"] = 1
        benchmark_df.loc[i, "day_of_week"] = 6
        benchmark_df.loc[i, "amount_z_rolling"] = np.random.uniform(2.8, 3.8)
        benchmark_df.loc[i, "net_amount"] = np.random.uniform(35000.0, 55000.0)
        benchmark_df.loc[i, "benchmark_anomaly_label"] = 1
        benchmark_df.loc[i, "anomaly_type"] = "TIMING_VELOCITY"
        benchmark_df.loc[i, "anomaly_description"] = "Off-hours weekend velocity spike with elevated rolling z-score"

    # Type 4: Subtle Multivariate Combination Anomaly (individually plausible, joints anomalous)
    idx_type4 = indices[3*per_type:4*per_type]
    for i in idx_type4:
        # Amount moderate (38-48k), discount moderate (15-22%), but rolls and ratios diverge
        benchmark_df.loc[i, "net_amount"] = np.random.uniform(38000.0, 48000.0)
        benchmark_df.loc[i, "discount_pct"] = np.random.uniform(0.15, 0.22)
        benchmark_df.loc[i, "roll28_mean"] = 12000.0  # History is much lower
        benchmark_df.loc[i, "roll28_std"] = 3000.0
        benchmark_df.loc[i, "amount_z_rolling"] = 3.2
        benchmark_df.loc[i, "benchmark_anomaly_label"] = 1
        benchmark_df.loc[i, "anomaly_type"] = "MULTIVARIATE_COVARIANCE"
        benchmark_df.loc[i, "anomaly_description"] = "Individually moderate parameters violating multivariate joint distribution"

    # Type 5: Extreme Outlier Magnitude Anomaly
    idx_type5 = indices[4*per_type:]
    for i in idx_type5:
        if np.random.random() < 0.5:
            benchmark_df.loc[i, "net_amount"] = np.random.uniform(95000.0, 165000.0)
            benchmark_df.loc[i, "discount_pct"] = 0.05
        else:
            benchmark_df.loc[i, "net_amount"] = np.random.uniform(40000.0, 70000.0)
            benchmark_df.loc[i, "discount_pct"] = np.random.uniform(0.45, 0.75)
        benchmark_df.loc[i, "benchmark_anomaly_label"] = 1
        benchmark_df.loc[i, "anomaly_type"] = "EXTREME_OUTLIER"
        benchmark_df.loc[i, "anomaly_description"] = "Extreme high amount or extreme discount percentage"

    out_path = PROCESSED_DIR / "anomaly_benchmark_v2.csv"
    benchmark_df.to_csv(out_path, index=False)
    
    type_counts = benchmark_df["anomaly_type"].value_counts().to_dict()
    meta = {
        "benchmark_version": "v2.0_independent",
        "description": "Multi-type independent evaluation dataset for transaction anomaly detection",
        "total_observations": len(benchmark_df),
        "total_anomalies": int(benchmark_df["benchmark_anomaly_label"].sum()),
        "anomaly_rate_pct": round(float(benchmark_df["benchmark_anomaly_label"].mean() * 100.0), 2),
        "anomaly_breakdown": type_counts,
        "evaluation_period": f"{SPLIT_CONFIG['test_start']} to 2026-10-21",
        "companies_included": DEV_COMPANIES
    }
    
    with open(REPORTS_DIR / "anomaly_benchmark_meta.json", "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)
        
    print(f"[OK] Generated Anomaly Benchmark v2: {out_path} ({len(benchmark_df)} rows, {meta['total_anomalies']} anomalies)")
    print("     Anomaly breakdown:", type_counts)
    return benchmark_df

if __name__ == "__main__":
    create_independent_anomaly_benchmark()
