"""
clean_and_extend_supermarket.py
================================
1. Cleans and validates the genuine 500-row supermarket dataset (2026-01-01 to 2026-07-01).
2. Generates a realistic, statistically grounded time-series extension through October 26, 2026.
3. Produces:
   - ml/datasets/processed/supermarket_sales_500_cleaned.csv
   - ml/datasets/processed/supermarket_sales_extended.csv
"""

import os
import random
import numpy as np
import pandas as pd
from datetime import date, datetime, timedelta

SEED = 42
random.seed(SEED)
np.random.seed(SEED)

RAW_PATH = os.path.join(os.path.dirname(__file__), "..", "datasets", "raw", "supermarket_sales_500_rows.csv")
PROCESSED_DIR = os.path.join(os.path.dirname(__file__), "..", "datasets", "processed")
os.makedirs(PROCESSED_DIR, exist_ok=True)

CLEANED_500_PATH = os.path.join(PROCESSED_DIR, "supermarket_sales_500_cleaned.csv")
EXTENDED_PATH = os.path.join(PROCESSED_DIR, "supermarket_sales_extended.csv")

def clean_original():
    print(f"Loading raw dataset from: {RAW_PATH}")
    df = pd.read_csv(RAW_PATH)
    assert len(df) == 500, f"Expected 500 rows, got {len(df)}"

    # Normalize column names
    col_mapping = {
        "Invoice ID": "invoice_id",
        "Date": "sale_date",
        "Branch": "branch_code",
        "City": "city",
        "Customer Type": "customer_type",
        "Gender": "gender",
        "Product": "product_name",
        "Category": "category_name",
        "Quantity": "quantity",
        "Unit Price": "unit_price",
        "Payment": "payment_method",
        "Rating": "customer_rating",
        "Sales": "sales_amount"
    }
    df = df.rename(columns=col_mapping)

    # Date normalization
    df["sale_date"] = pd.to_datetime(df["sale_date"]).dt.strftime("%Y-%m-%d")

    # Validate math: quantity * unit_price == sales_amount
    expected = (df["quantity"] * df["unit_price"]).round(2)
    diff = (df["sales_amount"] - expected).abs()
    assert diff.max() < 0.05, f"Sales formula mismatch: max diff {diff.max()}"

    # Tag provenance
    df["record_source"] = "historical_source"

    # Save cleaned
    df.to_csv(CLEANED_500_PATH, index=False)
    print(f"Cleaned 500-row dataset saved to: {CLEANED_500_PATH}")
    print(f"Historical date range: {df['sale_date'].min()} to {df['sale_date'].max()}")
    return df

def extend_sales(df_hist):
    min_date = datetime.strptime(df_hist["sale_date"].min(), "%Y-%m-%d").date()
    max_date = datetime.strptime(df_hist["sale_date"].max(), "%Y-%m-%d").date()
    
    start_ext = max_date + timedelta(days=1)
    end_ext = date(2026, 10, 26)
    num_ext_days = (end_ext - start_ext).days + 1
    print(f"Generating realistic extension from {start_ext} to {end_ext} ({num_ext_days} calendar days)...")

    # Empirical distributions from historical 500 rows
    prod_counts = df_hist["product_name"].value_counts()
    products = prod_counts.index.tolist()
    prod_weights = (prod_counts / prod_counts.sum()).values

    # Category map
    prod_cat_map = df_hist.set_index("product_name")["category_name"].to_dict()

    # Price distributions per product
    price_stats = df_hist.groupby("product_name")["unit_price"].agg(["min", "max", "mean", "std"]).to_dict("index")

    # Quantity distributions per product
    qty_dist = df_hist.groupby("product_name")["quantity"].apply(list).to_dict()

    # Branch and city pairs and probabilities
    branch_city_counts = df_hist.groupby(["branch_code", "city"]).size()
    branch_pairs = branch_city_counts.index.tolist()
    branch_weights = (branch_city_counts / branch_city_counts.sum()).values

    # Customer types and weights
    cust_counts = df_hist["customer_type"].value_counts()
    cust_types = cust_counts.index.tolist()
    cust_weights = (cust_counts / cust_counts.sum()).values

    # Gender weights
    gender_counts = df_hist["gender"].value_counts()
    genders = gender_counts.index.tolist()
    gender_weights = (gender_counts / gender_counts.sum()).values

    # Payment methods and weights
    pay_counts = df_hist["payment_method"].value_counts()
    pay_methods = pay_counts.index.tolist()
    pay_weights = (pay_counts / pay_counts.sum()).values

    # Historical average daily transactions: 500 / 182 ≈ 2.75
    base_lambda = 3.2  # Modest organic growth from ~2.75 to ~3.2

    ext_rows = []
    inv_counter = 501
    curr_date = start_ext

    while curr_date <= end_ext:
        dow = curr_date.weekday()  # 0=Monday, 6=Sunday
        dom = curr_date.day

        # Day of week factor
        if dow in [5, 6]:  # Weekend
            dow_factor = 1.35
        elif dow == 4:  # Friday
            dow_factor = 1.10
        elif dow in [1, 2]:  # Tue/Wed
            dow_factor = 0.88
        else:
            dow_factor = 0.95

        # Salary beginning-of-month factor
        if dom <= 5:
            salary_factor = 1.20
        elif dom >= 25:
            salary_factor = 0.95
        else:
            salary_factor = 1.0

        # Festive / seasonal trend in India (October Navratri / Dussehra / Pre-Diwali shopping)
        if curr_date.month == 10 and dom >= 10:
            festive_factor = 1.30
        elif curr_date.month == 8 and dom in [14, 15, 16]:  # Independence Day long weekend
            festive_factor = 1.25
        else:
            festive_factor = 1.0

        # Organic growth trend (subtle ~4% annualized)
        days_from_start = (curr_date - min_date).days
        trend_factor = 1.0 + 0.04 * (days_from_start / 365.25)

        daily_rate = base_lambda * dow_factor * salary_factor * festive_factor * trend_factor
        num_txns = np.random.poisson(daily_rate)
        # Ensure at least 1 transaction per day in active supermarket branches
        num_txns = max(1, num_txns)

        for _ in range(num_txns):
            inv_id = f"INV{inv_counter:04d}"
            inv_counter += 1

            # Sample branch & city
            b_idx = np.random.choice(len(branch_pairs), p=branch_weights)
            b_code, city = branch_pairs[b_idx]

            # Sample customer & gender
            c_type = np.random.choice(cust_types, p=cust_weights)
            gen = np.random.choice(genders, p=gender_weights)
            pm = np.random.choice(pay_methods, p=pay_weights)

            # Sample product
            prod = np.random.choice(products, p=prod_weights)
            cat = prod_cat_map[prod]

            # Sample quantity with occasional basket surges
            if random.random() < 0.04:  # Occasional bulk purchase
                qty = random.randint(7, 10)
            else:
                qty = random.choice(qty_dist[prod])

            # Sample unit price with stability around empirical product mean
            p_stat = price_stats[prod]
            std_dev = p_stat["std"] if pd.notnull(p_stat["std"]) and p_stat["std"] > 0 else p_stat["mean"] * 0.03
            price = np.random.normal(p_stat["mean"], std_dev * 0.5)
            # Clip within historical bounds plus minor 2% inflation corridor
            price = np.clip(price, p_stat["min"] * 0.98, p_stat["max"] * 1.03)
            price = round(float(price), 2)

            sales = round(qty * price, 2)

            # Rating centered at 4.0
            rating = round(float(np.clip(np.random.normal(4.0, 0.45), 3.0, 5.0)), 1)

            ext_rows.append({
                "invoice_id": inv_id,
                "sale_date": curr_date.strftime("%Y-%m-%d"),
                "branch_code": b_code,
                "city": city,
                "customer_type": c_type,
                "gender": gen,
                "product_name": prod,
                "category_name": cat,
                "quantity": qty,
                "unit_price": price,
                "payment_method": pm,
                "customer_rating": rating,
                "sales_amount": sales,
                "record_source": "synthetic"
            })

        curr_date += timedelta(days=1)

    df_ext = pd.DataFrame(ext_rows)
    print(f"Generated {len(df_ext)} synthetic transactions over {num_ext_days} days.")
    
    # Combine historical and extension
    df_combined = pd.concat([df_hist, df_ext], ignore_index=True)
    df_combined.to_csv(EXTENDED_PATH, index=False)
    print(f"Combined dataset saved to: {EXTENDED_PATH}")
    print(f"Total transactions: {len(df_combined)} (500 historical + {len(df_ext)} synthetic)")
    print(f"Full date range: {df_combined['sale_date'].min()} to {df_combined['sale_date'].max()}")

    # Monthly revenue verification
    df_combined["month"] = pd.to_datetime(df_combined["sale_date"]).dt.to_period("M")
    monthly = df_combined.groupby(["month", "record_source"]).agg(
        txns=("invoice_id", "count"),
        revenue=("sales_amount", "sum"),
        avg_basket=("sales_amount", "mean")
    )
    print("\n=== Monthly Breakdown ===")
    print(monthly.to_string())
    return df_combined

if __name__ == "__main__":
    df_cleaned = clean_original()
    extend_sales(df_cleaned)
