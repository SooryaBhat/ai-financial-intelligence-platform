# -*- coding: utf-8 -*-
"""
Synthetic ERP Data Generator
=============================
Generates realistic, internally consistent ERP datasets for ML development.

Usage:
    python generate_synthetic_data.py

Output:
    ml/datasets/synthetic/*.csv  (17 CSV files)

Notes:
    - All foreign key relationships are preserved.
    - Date range: 2022-01-01 to 2024-12-31
    - Seasonal sales patterns: peaks in Q2 (Apr-Jun) and Q4 (Oct-Dec).
    - ~30 pct of customers are repeat buyers (same customer appears in multiple sales).
    - 3 companies, 3 branches each, 9 warehouses total.
    - Branch HQs get 2 warehouses; regular branches get 1 (total 15 warehouses).
    - Inventory covers products assigned to 1-3 warehouses per product.
"""

import os
import sys
import uuid
import random
from datetime import date, datetime, timedelta
from typing import List, Dict, Any

import pandas as pd
import numpy as np

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

random.seed(42)
np.random.seed(42)

# FIX: OUTPUT_DIR should be the synthetic/ folder itself (same dir as this script)
OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))
os.makedirs(OUTPUT_DIR, exist_ok=True)

START_DATE = date(2022, 1, 1)
END_DATE   = date(2024, 12, 31)

COMPANIES = [
    {"id": str(uuid.UUID(int=1)), "name": "Horizon Retail Ltd",   "industry": "Retail",        "country": "India",  "currency": "INR"},
    {"id": str(uuid.UUID(int=2)), "name": "Apex Manufacturing",   "industry": "Manufacturing", "country": "USA",    "currency": "USD"},
    {"id": str(uuid.UUID(int=3)), "name": "BlueStar Wholesale",   "industry": "Wholesale",     "country": "UAE",    "currency": "AED"},
]

BRANCH_CITIES = {
    COMPANIES[0]["id"]: [("Mumbai HQ",        "Mumbai",    True),
                         ("Delhi Branch",     "Delhi",     False),
                         ("Bangalore Branch", "Bangalore", False)],
    COMPANIES[1]["id"]: [("New York HQ",      "New York",  True),
                         ("Chicago Branch",   "Chicago",   False),
                         ("Houston Branch",   "Houston",   False)],
    COMPANIES[2]["id"]: [("Dubai HQ",         "Dubai",     True),
                         ("Abu Dhabi Branch", "Abu Dhabi", False),
                         ("Sharjah Branch",   "Sharjah",   False)],
}

USER_ROLES         = ["admin", "manager", "sales", "accountant"]
EXPENSE_CATEGORIES = ["Rent", "Salaries", "Utilities", "Marketing", "Logistics",
                      "Office Supplies", "IT & Software", "Travel", "Maintenance", "Insurance"]
PAYMENT_METHODS    = ["cash", "card", "bank_transfer", "cheque"]

CATEGORY_NAMES = [
    "Electronics", "Clothing", "Home Appliances", "Furniture", "Stationery",
    "Food & Beverages", "Pharmaceuticals", "Automotive Parts", "Toys & Games",
    "Sports & Fitness", "Beauty & Health", "Books", "Hardware & Tools",
    "Packaging Materials", "Raw Materials", "Chemicals", "Electrical Supplies",
    "Agricultural Inputs", "Cleaning Supplies", "Networking Equipment",
]

PRODUCT_TEMPLATES = {
    "Electronics":          [("Laptop Pro 15", 45000, 75000), ("Wireless Earbuds", 2500, 4500),
                              ("USB-C Hub 7-in-1", 1200, 2200), ("Mechanical Keyboard", 3500, 6000),
                              ("Webcam 4K", 4000, 7000)],
    "Clothing":             [("Mens Polo Shirt", 400, 850), ("Womens Kurta", 600, 1200),
                              ("Denim Jeans", 800, 1600), ("Sports Joggers", 700, 1400),
                              ("Winter Jacket", 2000, 4000)],
    "Home Appliances":      [("Microwave 20L", 5000, 9000), ("Air Purifier", 8000, 14000),
                              ("Electric Kettle", 800, 1500), ("Ceiling Fan 5-blade", 1500, 2800),
                              ("Water Purifier RO", 9000, 16000)],
    "Furniture":            [("Office Chair Ergonomic", 6000, 11000), ("Standing Desk 140cm", 12000, 22000),
                              ("Bookshelf 5-tier", 4000, 7500), ("Sofa 3-seater", 25000, 45000),
                              ("Dining Table Set", 18000, 32000)],
    "Stationery":           [("A4 Paper Ream", 200, 380), ("Whiteboard Marker Set", 120, 250),
                              ("Stapler Heavy Duty", 350, 650), ("File Cabinet A4", 900, 1700),
                              ("Notebook B5 Pack", 180, 350)],
    "Food & Beverages":     [("Green Tea 100g", 150, 280), ("Instant Coffee 200g", 220, 420),
                              ("Mixed Nuts 500g", 480, 900), ("Protein Bar Box", 600, 1100),
                              ("Mineral Water 12pk", 180, 340)],
    "Pharmaceuticals":      [("Vitamin C Tablets", 80, 160), ("Paracetamol Strip", 20, 45),
                              ("Hand Sanitizer 500ml", 90, 180), ("Digital Thermometer", 350, 680),
                              ("Blood Glucose Monitor", 1800, 3200)],
    "Automotive Parts":     [("Engine Oil 5L", 900, 1700), ("Brake Pads Set", 600, 1200),
                              ("Car Battery 65Ah", 4500, 8000), ("Wiper Blades Pair", 300, 580),
                              ("Air Filter", 250, 500)],
    "Toys & Games":         [("LEGO City Set", 1200, 2400), ("Remote Control Car", 800, 1600),
                              ("Board Game Family", 600, 1200), ("Puzzle 1000 pieces", 350, 700),
                              ("Action Figure Set", 400, 800)],
    "Sports & Fitness":     [("Yoga Mat 6mm", 500, 1000), ("Dumbbell Pair 5kg", 800, 1600),
                              ("Resistance Band Set", 300, 600), ("Jump Rope Speed", 200, 400),
                              ("Gym Gloves", 350, 700)],
    "Beauty & Health":      [("Shampoo 400ml", 200, 400), ("Face Serum 30ml", 600, 1200),
                              ("Sunscreen SPF50", 350, 700), ("Electric Toothbrush", 1200, 2400),
                              ("Perfume 50ml EDP", 1500, 3000)],
    "Books":                [("Python Data Science", 450, 900), ("Business Strategy", 380, 750),
                              ("Machine Learning A-Z", 520, 1000), ("Financial Modeling", 480, 950),
                              ("Management Accounting", 420, 830)],
    "Hardware & Tools":     [("Cordless Drill 18V", 3500, 6500), ("Angle Grinder 115mm", 2000, 3800),
                              ("Measuring Tape 10m", 200, 400), ("Socket Wrench Set", 1200, 2400),
                              ("Safety Goggles", 150, 300)],
    "Packaging Materials":  [("Bubble Wrap Roll 50m", 350, 680), ("Cardboard Box 40x30", 15, 30),
                              ("Stretch Wrap 500m", 280, 550), ("Packing Tape 12pk", 180, 360),
                              ("Foam Sheets 5mm", 80, 160)],
    "Raw Materials":        [("Steel Rod 12mm 6m", 800, 1400), ("Copper Wire 1.5mm 100m", 1200, 2100),
                              ("Aluminium Sheet 1mx2m", 1500, 2700), ("PVC Pipe 110mm 3m", 180, 340),
                              ("Epoxy Resin 1kg", 600, 1100)],
    "Chemicals":            [("Caustic Soda 25kg", 900, 1600), ("Hydrogen Peroxide 5L", 400, 750),
                              ("Acetone 5L", 550, 1000), ("Isopropanol 5L", 480, 900),
                              ("Sodium Carbonate 50kg", 700, 1300)],
    "Electrical Supplies":  [("Cable 1.5mm2 100m", 1800, 3300), ("MCB 32A", 120, 230),
                              ("Distribution Board 8way", 1500, 2800), ("LED Bulb 9W 6pk", 200, 390),
                              ("Extension Cord 5m 4way", 350, 680)],
    "Agricultural Inputs":  [("Fertilizer NPK 50kg", 1100, 2000), ("Drip Irrigation Kit", 3500, 6500),
                              ("Pesticide Spray 1L", 280, 540), ("Greenhouse Net 50m", 700, 1300),
                              ("Seed Tray 72-cell", 90, 180)],
    "Cleaning Supplies":    [("Floor Cleaner 5L", 280, 540), ("Disinfectant 5L", 320, 620),
                              ("Microfibre Cloth 10pk", 250, 480), ("Mop & Bucket Set", 600, 1150),
                              ("Industrial Vacuum", 8000, 15000)],
    "Networking Equipment": [("Router WiFi6", 4500, 8500), ("Network Switch 24port", 6000, 11000),
                              ("Cat6 Cable 305m", 2800, 5200), ("Patch Panel 24port", 1800, 3400),
                              ("Network Rack 9U", 5000, 9500)],
}

SUPPLIER_NAMES = [
    "GlobalTech Supplies", "PrimeSource Pvt Ltd", "FastTrack Traders", "Pinnacle Wholesale",
    "NexGen Distributors", "MetroTrade Co", "AlphaStock Inc", "Reliable Goods Ltd",
    "SkyHigh Imports", "Core Supply Chain", "UrbanMart Vendors", "ProLine Exports",
    "Eastern Commodities", "WestCoast Traders", "TrustWell Enterprises",
]

CUSTOMER_NAMES_FIRST = [
    "Rahul", "Priya", "Arjun", "Sneha", "Karan", "Divya", "Amit", "Pooja",
    "James", "Emily", "Michael", "Sarah", "John", "Lisa", "David", "Anna",
    "Omar", "Fatima", "Ahmed", "Aisha", "Hassan", "Layla", "Yusuf", "Noor",
    "Vikram", "Kavya", "Rohan", "Meera", "Suresh", "Anita", "Rajesh", "Sunita",
]
CUSTOMER_NAMES_LAST = [
    "Sharma", "Patel", "Singh", "Kumar", "Mehta", "Joshi", "Smith", "Brown",
    "Johnson", "Davis", "Wilson", "Taylor", "Al-Rashid", "Al-Mansoori", "Hassan",
    "Nair", "Reddy", "Gupta", "Shah", "Agarwal", "Verma", "Iyer", "Rao", "Das",
]

CITIES = {
    COMPANIES[0]["id"]: ["Mumbai", "Delhi", "Bangalore", "Chennai", "Hyderabad", "Pune", "Kolkata", "Ahmedabad"],
    COMPANIES[1]["id"]: ["New York", "Los Angeles", "Chicago", "Houston", "Phoenix", "Philadelphia", "Dallas", "Austin"],
    COMPANIES[2]["id"]: ["Dubai", "Abu Dhabi", "Sharjah", "Ajman", "Ras Al Khaimah", "Fujairah", "Al Ain", "Riyadh"],
}

# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def uid() -> str:
    """Return a new random UUID string."""
    return str(uuid.uuid4())


def rand_date(start: date = START_DATE, end: date = END_DATE) -> date:
    """Return a uniformly random date between start and end (inclusive)."""
    delta = (end - start).days
    return start + timedelta(days=random.randint(0, delta))


def seasonal_weight(d: date) -> float:
    """Return a relative weight reflecting seasonal sales patterns.

    Peaks:  Q4 (Oct-Dec) weight=1.6, Q2 (Apr-Jun) weight=1.3
    Troughs: Q3 (Jul-Sep) weight=0.85
    Also applies a 12% year-over-year growth factor.
    """
    month = d.month
    if month in (10, 11, 12):
        base = 1.6
    elif month in (4, 5, 6):
        base = 1.3
    elif month in (7, 8, 9):
        base = 0.85
    else:
        base = 1.0
    year_growth = 1.0 + (d.year - 2022) * 0.12
    return base * year_growth


def weighted_date(start: date = START_DATE, end: date = END_DATE) -> date:
    """Return a date biased toward seasonal peaks using rejection sampling."""
    for _ in range(100):
        d = rand_date(start, end)
        # max possible weight at year_growth=1.24 * 1.6 = ~1.98; use 2.0 as ceiling
        if random.random() < seasonal_weight(d) / 2.0:
            return d
    return rand_date(start, end)


def format_dt(d: date) -> str:
    """Format a date as an ISO 8601 datetime string with a random business-hours time."""
    return datetime(
        d.year, d.month, d.day,
        random.randint(8, 18), random.randint(0, 59), random.randint(0, 59),
    ).isoformat()


def save_csv(df: pd.DataFrame, name: str) -> None:
    """Write a DataFrame to CSV and print a status line."""
    path = os.path.join(OUTPUT_DIR, name)
    df.to_csv(path, index=False, encoding="utf-8")
    # FIX: use ASCII-safe checkmark to avoid cp1252 UnicodeEncodeError on Windows
    print(f"  [OK] {name:<35s} {len(df):>7,} rows  x  {len(df.columns)} cols")


# ---------------------------------------------------------------------------
# Generate companies
# ---------------------------------------------------------------------------

def gen_companies() -> pd.DataFrame:
    rows = []
    for c in COMPANIES:
        rows.append({**c, "created_at": "2021-06-01T09:00:00"})
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Generate branches
# ---------------------------------------------------------------------------

def gen_branches(companies_df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, company in companies_df.iterrows():
        for name, city, is_hq in BRANCH_CITIES[company["id"]]:
            rows.append({
                "id":              uid(),
                "company_id":      company["id"],
                "name":            name,
                "city":            city,
                "is_headquarters": is_hq,
                "created_at":      "2021-06-15T09:00:00",
            })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Generate users  (4 roles x 3 branches x 3 companies = 36 users)
# ---------------------------------------------------------------------------

def gen_users(companies_df: pd.DataFrame, branches_df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, company in companies_df.iterrows():
        company_branches = branches_df[branches_df["company_id"] == company["id"]]
        domain = company["name"].replace(" ", "").lower()
        for _, branch in company_branches.iterrows():
            for role in USER_ROLES:
                first = random.choice(CUSTOMER_NAMES_FIRST)
                last  = random.choice(CUSTOMER_NAMES_LAST)
                # FIX: sanitise last name for email (remove hyphens)
                email_last = last.replace("-", "").lower()
                rows.append({
                    "id":         uid(),
                    "company_id": company["id"],
                    "branch_id":  branch["id"],
                    "name":       f"{first} {last}",
                    "email":      f"{first.lower()}.{email_last}{random.randint(1, 99)}@{domain}.com",
                    "role":       role,
                    "created_at": "2021-07-01T09:00:00",
                })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Generate customers  (170 per company = 510 total)
# ---------------------------------------------------------------------------

def gen_customers(companies_df: pd.DataFrame, n_per_company: int = 170) -> pd.DataFrame:
    rows = []
    for _, company in companies_df.iterrows():
        cities = CITIES[company["id"]]
        for _ in range(n_per_company):
            first   = random.choice(CUSTOMER_NAMES_FIRST)
            last    = random.choice(CUSTOMER_NAMES_LAST)
            created = rand_date(date(2021, 1, 1), date(2023, 6, 30))
            rows.append({
                "id":            uid(),
                "company_id":    company["id"],
                "name":          f"{first} {last}",
                "email":         f"{first.lower()}.{last.replace('-','').lower()}{random.randint(10, 999)}@email.com",
                "phone":         f"+{random.randint(1, 99)}{random.randint(1000000000, 9999999999)}",
                "city":          random.choice(cities),
                "customer_type": random.choices(["individual", "business"], weights=[0.6, 0.4])[0],
                "credit_limit":  round(random.choice([5000, 10000, 20000, 50000, 100000])
                                       * random.uniform(0.8, 1.2), 2),
                "created_at":    format_dt(created),
            })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Generate suppliers  (17 per company = 51 total)
# ---------------------------------------------------------------------------

def gen_suppliers(companies_df: pd.DataFrame, n_per_company: int = 17) -> pd.DataFrame:
    rows = []
    for _, company in companies_df.iterrows():
        cities     = CITIES[company["id"]]
        used_names: list = []
        for _ in range(n_per_company):
            available = [n for n in SUPPLIER_NAMES if n not in used_names] or SUPPLIER_NAMES
            name      = random.choice(available)
            used_names.append(name)
            # FIX: remove spaces and special chars safely for email domain
            safe_name = name.replace(" ", "").replace("&", "and").lower()
            rows.append({
                "id":                 uid(),
                "company_id":         company["id"],
                "name":               name,
                "contact_email":      f"contact@{safe_name}{random.randint(1, 9)}.com",
                "phone":              f"+{random.randint(1, 99)}{random.randint(1000000000, 9999999999)}",
                "city":               random.choice(cities),
                "payment_terms_days": random.choice([15, 30, 45, 60, 90]),
                "created_at":         "2021-08-01T09:00:00",
            })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Generate categories  (20 per company = 60 total)
# ---------------------------------------------------------------------------

def gen_categories(companies_df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, company in companies_df.iterrows():
        for cat_name in CATEGORY_NAMES:
            rows.append({
                "id":          uid(),
                "company_id":  company["id"],
                "name":        cat_name,
                "description": f"{cat_name} products and related items",
                "created_at":  "2021-06-01T09:00:00",
            })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Generate products  (5 per category x 20 categories x 3 companies = 300 total)
# ---------------------------------------------------------------------------

def gen_products(companies_df: pd.DataFrame, categories_df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    units = ["pcs", "pcs", "pcs", "kg", "litre", "box", "roll", "set"]
    for _, company in companies_df.iterrows():
        company_cats = categories_df[categories_df["company_id"] == company["id"]]
        sku_counter  = 1
        for _, cat in company_cats.iterrows():
            templates = PRODUCT_TEMPLATES.get(cat["name"], [])
            for prod_name, cost, sell in templates:
                cost_v = round(cost * random.uniform(0.85, 1.15), 2)
                sell_v = round(sell * random.uniform(0.85, 1.15), 2)
                # Ensure selling price is always >= cost price (realistic markup)
                sell_v = max(sell_v, round(cost_v * 1.1, 2))
                rows.append({
                    "id":            uid(),
                    "company_id":    company["id"],
                    "category_id":   cat["id"],
                    "name":          prod_name,
                    "sku":           f"{cat['name'][:3].upper()}-{sku_counter:04d}",
                    "cost_price":    cost_v,
                    "selling_price": sell_v,
                    "unit":          random.choice(units),
                    "is_active":     random.choices([True, False], weights=[0.92, 0.08])[0],
                    "created_at":    "2021-09-01T09:00:00",
                })
                sku_counter += 1
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Generate warehouses  (HQ: 2 WH, branch: 1 WH → 15 total per company set)
# ---------------------------------------------------------------------------

def gen_warehouses(companies_df: pd.DataFrame, branches_df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, company in companies_df.iterrows():
        company_branches = branches_df[branches_df["company_id"] == company["id"]]
        for _, branch in company_branches.iterrows():
            n_wh = 2 if branch["is_headquarters"] else 1
            for j in range(n_wh):
                suffix = " Main" if j == 0 else " Secondary"
                rows.append({
                    "id":         uid(),
                    "company_id": company["id"],
                    "branch_id":  branch["id"],
                    "name":       f"{branch['city']}{suffix} Warehouse",
                    "location":   f"{branch['city']}, {company['country']} - Zone {chr(65 + j)}",
                    "created_at": "2021-10-01T09:00:00",
                })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Generate inventory  (each product stocked in 1-3 warehouses of its company)
# ---------------------------------------------------------------------------

def gen_inventory(products_df: pd.DataFrame, warehouses_df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, product in products_df.iterrows():
        company_whs = warehouses_df[warehouses_df["company_id"] == product["company_id"]]
        if company_whs.empty:
            continue
        k          = min(len(company_whs), random.randint(1, 3))
        sample_wh  = company_whs.sample(k, random_state=None)
        for _, wh in sample_wh.iterrows():
            qty      = random.randint(50, 500)
            reord    = random.randint(10, 50)
            reord_qty = reord * random.randint(2, 5)
            rows.append({
                "id":               uid(),
                "product_id":       product["id"],
                "warehouse_id":     wh["id"],
                "quantity_on_hand": qty,
                "reorder_level":    reord,
                "reorder_quantity": reord_qty,
                "updated_at":       "2025-01-01T00:00:00",
            })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Generate sales + sale_items
# ---------------------------------------------------------------------------

def gen_sales(
    companies_df: pd.DataFrame,
    branches_df: pd.DataFrame,
    customers_df: pd.DataFrame,
    users_df: pd.DataFrame,
    products_df: pd.DataFrame,
    n_sales: int = 8000,
):
    sales_rows: list = []
    items_rows: list = []

    # Pre-build lookup dicts keyed by company_id for O(1) access
    branch_map   = branches_df.groupby("company_id")["id"].apply(list).to_dict()
    customer_map = customers_df.groupby("company_id")["id"].apply(list).to_dict()
    user_map     = users_df.groupby("company_id")["id"].apply(list).to_dict()

    # FIX: use boolean mask properly; group as list of record dicts
    active_products = products_df[products_df["is_active"].astype(bool)]
    product_map: Dict[str, list] = {}
    for cid, grp in active_products.groupby("company_id"):
        product_map[cid] = grp.to_dict("records")

    company_ids = list(companies_df["id"])

    # Build company → country map for tax rate
    country_map = companies_df.set_index("id")["country"].to_dict()

    for _ in range(n_sales):
        cid       = random.choice(company_ids)
        prods     = product_map.get(cid, [])
        if not prods:
            continue

        branch_id = random.choice(branch_map[cid])
        cust_id   = random.choice(customer_map[cid])
        user_id   = random.choice(user_map[cid])
        sale_date = weighted_date()
        status    = random.choices(
            ["completed", "pending", "cancelled"],
            weights=[0.82, 0.13, 0.05],
        )[0]

        n_items = random.choices([1, 2, 3, 4, 5], weights=[0.30, 0.35, 0.20, 0.10, 0.05])[0]
        n_items = min(n_items, len(prods))
        chosen  = random.sample(prods, n_items)

        total_amount    = 0.0
        discount_amount = 0.0
        sale_items_temp: list = []

        for prod in chosen:
            qty        = random.randint(1, 20)
            unit_price = round(prod["selling_price"] * random.uniform(0.92, 1.08), 2)
            disc_pct   = random.choices([0.0, 0.05, 0.10, 0.15], weights=[0.50, 0.25, 0.15, 0.10])[0]
            line_total  = round(qty * unit_price * (1.0 - disc_pct), 2)
            total_amount    += line_total
            discount_amount += round(qty * unit_price * disc_pct, 2)
            sale_items_temp.append({
                "product_id":  prod["id"],
                "quantity":    qty,
                "unit_price":  unit_price,
                "discount_pct": disc_pct,
                "line_total":  line_total,
            })

        total_amount    = round(total_amount, 2)
        discount_amount = round(discount_amount, 2)
        # Tax rate: India = 18% GST, others = 10%
        tax_rate   = 0.18 if country_map.get(cid) == "India" else 0.10
        tax_amount = round(total_amount * tax_rate, 2)
        net_amount = round(total_amount + tax_amount, 2)

        # FIX: only completed sales can have paid/partial status
        if status == "completed":
            pay_status = random.choices(
                ["paid", "partial", "unpaid"],
                weights=[0.70, 0.20, 0.10],
            )[0]
        else:
            pay_status = "unpaid"

        sale_id = uid()
        sales_rows.append({
            "id":              sale_id,
            "company_id":      cid,
            "branch_id":       branch_id,
            "customer_id":     cust_id,
            "user_id":         user_id,
            "sale_date":       str(sale_date),
            "status":          status,
            "total_amount":    total_amount,
            "discount_amount": discount_amount,
            "tax_amount":      tax_amount,
            "net_amount":      net_amount,
            "payment_status":  pay_status,
            "created_at":      format_dt(sale_date),
        })

        for si in sale_items_temp:
            items_rows.append({
                "id":           uid(),
                "sale_id":      sale_id,
                "product_id":   si["product_id"],
                "quantity":     si["quantity"],
                "unit_price":   si["unit_price"],
                "discount_pct": si["discount_pct"],
                "line_total":   si["line_total"],
            })

    return pd.DataFrame(sales_rows), pd.DataFrame(items_rows)


# ---------------------------------------------------------------------------
# Generate purchases + purchase_items
# ---------------------------------------------------------------------------

def gen_purchases(
    companies_df: pd.DataFrame,
    branches_df: pd.DataFrame,
    suppliers_df: pd.DataFrame,
    users_df: pd.DataFrame,
    products_df: pd.DataFrame,
    n_purchases: int = 3000,
):
    purchases_rows: list = []
    items_rows: list     = []

    branch_map   = branches_df.groupby("company_id")["id"].apply(list).to_dict()
    # FIX: supplier_map values must be lists of UUID strings, not raw UUID strings
    supplier_map = suppliers_df.groupby("company_id")["id"].apply(list).to_dict()
    user_map     = users_df.groupby("company_id")["id"].apply(list).to_dict()
    product_map: Dict[str, list] = {}
    for cid, grp in products_df.groupby("company_id"):
        product_map[cid] = grp.to_dict("records")

    company_ids = list(companies_df["id"])

    for _ in range(n_purchases):
        cid   = random.choice(company_ids)
        prods = product_map.get(cid, [])
        if not prods:
            continue

        branch_id  = random.choice(branch_map[cid])
        # FIX: ensure we always have a valid list before random.choice
        sup_list   = supplier_map.get(cid, supplier_map.get(company_ids[0], []))
        if not sup_list:
            continue
        supplier_id = random.choice(sup_list)
        user_id     = random.choice(user_map[cid])
        purch_date  = rand_date()
        status      = random.choices(
            ["received", "pending", "cancelled"],
            weights=[0.80, 0.15, 0.05],
        )[0]

        n_items = random.choices([1, 2, 3, 4, 5], weights=[0.25, 0.35, 0.25, 0.10, 0.05])[0]
        n_items = min(n_items, len(prods))
        chosen  = random.sample(prods, n_items)

        total_amount = 0.0
        p_items_temp: list = []

        for prod in chosen:
            qty        = random.randint(5, 100)
            unit_cost  = round(prod["cost_price"] * random.uniform(0.92, 1.05), 2)
            line_total = round(qty * unit_cost, 2)
            total_amount += line_total
            p_items_temp.append({
                "product_id": prod["id"],
                "quantity":   qty,
                "unit_cost":  unit_cost,
                "line_total": line_total,
            })

        total_amount = round(total_amount, 2)
        tax_rate     = 0.05
        tax_amount   = round(total_amount * tax_rate, 2)
        net_amount   = round(total_amount + tax_amount, 2)

        if status == "cancelled":
            pay_status = "unpaid"
        else:
            pay_status = random.choices(
                ["paid", "partial", "unpaid"],
                weights=[0.70, 0.20, 0.10],
            )[0]

        purch_id = uid()
        purchases_rows.append({
            "id":             purch_id,
            "company_id":     cid,
            "branch_id":      branch_id,
            "supplier_id":    supplier_id,
            "user_id":        user_id,
            "purchase_date":  str(purch_date),
            "status":         status,
            "total_amount":   total_amount,
            "tax_amount":     tax_amount,
            "net_amount":     net_amount,
            "payment_status": pay_status,
            "created_at":     format_dt(purch_date),
        })

        for pi in p_items_temp:
            items_rows.append({
                "id":          uid(),
                "purchase_id": purch_id,
                "product_id":  pi["product_id"],
                "quantity":    pi["quantity"],
                "unit_cost":   pi["unit_cost"],
                "line_total":  pi["line_total"],
            })

    return pd.DataFrame(purchases_rows), pd.DataFrame(items_rows)


# ---------------------------------------------------------------------------
# Generate stock_movements
# FIX: replaced O(n^2) iterrows lookup with dict-based O(1) lookup
# ---------------------------------------------------------------------------

def gen_stock_movements(
    sales_df: pd.DataFrame,
    sale_items_df: pd.DataFrame,
    purchases_df: pd.DataFrame,
    purchase_items_df: pd.DataFrame,
    products_df: pd.DataFrame,
    inventory_df: pd.DataFrame,
    warehouses_df: pd.DataFrame,
    n_adjustments: int = 500,
) -> pd.DataFrame:
    rows: list = []

    # Build product -> list of warehouses dict from inventory
    inv_prod_wh: Dict[str, list] = {}
    for _, row in inventory_df.iterrows():
        inv_prod_wh.setdefault(row["product_id"], []).append(row["warehouse_id"])

    # FIX: Build O(1) lookup dicts for sales and purchases by id
    sales_by_id     = sales_df.set_index("id")[["sale_date", "company_id"]].to_dict("index")
    purchases_by_id = purchases_df.set_index("id")[["purchase_date", "company_id"]].to_dict("index")

    wh_ids_all = list(warehouses_df["id"])

    # Outbound movements from sales items
    for _, si in sale_items_df.iterrows():
        prod_whs = inv_prod_wh.get(si["product_id"])
        if not prod_whs:
            continue
        sale_rec = sales_by_id.get(si["sale_id"])
        if sale_rec is None:
            continue
        rows.append({
            "id":            uid(),
            "product_id":    si["product_id"],
            "warehouse_id":  random.choice(prod_whs),
            "movement_type": "out",
            "quantity":      int(si["quantity"]),
            "reason":        "sale",
            "reference_id":  si["sale_id"],
            "moved_at":      format_dt(date.fromisoformat(str(sale_rec["sale_date"]))),
        })

    # Inbound movements from purchase items
    for _, pi in purchase_items_df.iterrows():
        prod_whs = inv_prod_wh.get(pi["product_id"])
        if not prod_whs:
            continue
        purch_rec = purchases_by_id.get(pi["purchase_id"])
        if purch_rec is None:
            continue
        rows.append({
            "id":            uid(),
            "product_id":    pi["product_id"],
            "warehouse_id":  random.choice(prod_whs),
            "movement_type": "in",
            "quantity":      int(pi["quantity"]),
            "reason":        "purchase",
            "reference_id":  pi["purchase_id"],
            "moved_at":      format_dt(date.fromisoformat(str(purch_rec["purchase_date"]))),
        })

    # Random adjustments / returns / transfers
    prod_ids = list(products_df["id"])
    reasons  = ["adjustment", "return", "transfer", "write_off"]
    for _ in range(n_adjustments):
        pid      = random.choice(prod_ids)
        wh_list  = inv_prod_wh.get(pid) or [random.choice(wh_ids_all)]
        rows.append({
            "id":            uid(),
            "product_id":    pid,
            "warehouse_id":  random.choice(wh_list),
            "movement_type": random.choice(["in", "out"]),
            "quantity":      random.randint(1, 50),
            "reason":        random.choice(reasons),
            "reference_id":  None,
            "moved_at":      format_dt(rand_date()),
        })

    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Generate payments
# ---------------------------------------------------------------------------

def gen_payments(
    companies_df: pd.DataFrame,
    sales_df: pd.DataFrame,
    purchases_df: pd.DataFrame,
) -> pd.DataFrame:
    rows: list = []

    # Payments linked to sales
    paid_sales = sales_df[sales_df["payment_status"].isin(["paid", "partial"])].copy()
    for _, sale in paid_sales.iterrows():
        if sale["payment_status"] == "paid":
            pay_amt = sale["net_amount"]
        else:
            pay_amt = round(sale["net_amount"] * random.uniform(0.3, 0.7), 2)
        pay_date = date.fromisoformat(str(sale["sale_date"])) + timedelta(days=random.randint(0, 15))
        pay_date = min(pay_date, END_DATE)
        rows.append({
            "id":             uid(),
            "company_id":     sale["company_id"],
            "reference_type": "sale",
            "reference_id":   sale["id"],
            "amount":         pay_amt,
            "payment_method": random.choice(PAYMENT_METHODS),
            "payment_date":   str(pay_date),
            "created_at":     format_dt(pay_date),
        })

    # Payments linked to purchases
    paid_purchases = purchases_df[purchases_df["payment_status"].isin(["paid", "partial"])].copy()
    for _, purch in paid_purchases.iterrows():
        if purch["payment_status"] == "paid":
            pay_amt = purch["net_amount"]
        else:
            pay_amt = round(purch["net_amount"] * random.uniform(0.3, 0.7), 2)
        pay_date = date.fromisoformat(str(purch["purchase_date"])) + timedelta(days=random.randint(0, 30))
        pay_date = min(pay_date, END_DATE)
        rows.append({
            "id":             uid(),
            "company_id":     purch["company_id"],
            "reference_type": "purchase",
            "reference_id":   purch["id"],
            "amount":         pay_amt,
            "payment_method": random.choice(PAYMENT_METHODS),
            "payment_date":   str(pay_date),
            "created_at":     format_dt(pay_date),
        })

    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Generate expenses
# ---------------------------------------------------------------------------

def gen_expenses(
    companies_df: pd.DataFrame,
    branches_df: pd.DataFrame,
    users_df: pd.DataFrame,
    n_variable: int = 2000,
) -> pd.DataFrame:
    rows: list = []

    branch_map  = branches_df.groupby("company_id")["id"].apply(list).to_dict()
    user_map    = users_df.groupby("company_id")["id"].apply(list).to_dict()
    company_ids = list(companies_df["id"])

    # Fixed monthly expenses: Rent + Salaries + Utilities for every branch every month
    for _, company in companies_df.iterrows():
        cid      = company["id"]
        branches = branch_map[cid]
        users    = user_map[cid]
        d = START_DATE
        while d <= END_DATE:
            for branch_id in branches:
                # Rent (1st of month)
                rows.append({
                    "id":           uid(),
                    "company_id":   cid,
                    "branch_id":    branch_id,
                    "user_id":      random.choice(users),
                    "category":     "Rent",
                    "description":  f"Monthly office rent - {d.strftime('%B %Y')}",
                    "amount":       round(random.uniform(50000, 200000), 2),
                    "expense_date": str(date(d.year, d.month, 1)),
                    "status":       "approved",
                    "created_at":   format_dt(date(d.year, d.month, 1)),
                })
                # Salaries (28th of month)
                rows.append({
                    "id":           uid(),
                    "company_id":   cid,
                    "branch_id":    branch_id,
                    "user_id":      random.choice(users),
                    "category":     "Salaries",
                    "description":  f"Staff salaries - {d.strftime('%B %Y')}",
                    "amount":       round(random.uniform(200000, 800000), 2),
                    "expense_date": str(date(d.year, d.month, 28)),
                    "status":       "approved",
                    "created_at":   format_dt(date(d.year, d.month, 28)),
                })
                # Utilities (15th of month)
                rows.append({
                    "id":           uid(),
                    "company_id":   cid,
                    "branch_id":    branch_id,
                    "user_id":      random.choice(users),
                    "category":     "Utilities",
                    "description":  f"Electricity and water - {d.strftime('%B %Y')}",
                    "amount":       round(random.uniform(5000, 30000), 2),
                    "expense_date": str(date(d.year, d.month, 15)),
                    "status":       "approved",
                    "created_at":   format_dt(date(d.year, d.month, 15)),
                })
            # Advance to next month
            if d.month == 12:
                d = date(d.year + 1, 1, 1)
            else:
                d = date(d.year, d.month + 1, 1)

    # Variable expenses
    variable_cats = [c for c in EXPENSE_CATEGORIES if c not in ("Rent", "Salaries", "Utilities")]
    for _ in range(n_variable):
        cid       = random.choice(company_ids)
        exp_date  = rand_date()
        rows.append({
            "id":           uid(),
            "company_id":   cid,
            "branch_id":    random.choice(branch_map[cid]),
            "user_id":      random.choice(user_map[cid]),
            "category":     random.choice(variable_cats),
            "description":  "Operational expense",
            "amount":       round(random.uniform(500, 50000), 2),
            "expense_date": str(exp_date),
            "status":       random.choices(
                ["approved", "pending", "rejected"],
                weights=[0.75, 0.20, 0.05],
            )[0],
            "created_at":   format_dt(exp_date),
        })

    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Generate invoices  (one invoice per sale)
# FIX: replaced date.today() comparison with data-appropriate END_DATE logic
# ---------------------------------------------------------------------------

def gen_invoices(sales_df: pd.DataFrame) -> pd.DataFrame:
    rows: list = []
    inv_num    = 1

    for _, sale in sales_df.iterrows():
        sale_date = date.fromisoformat(str(sale["sale_date"]))
        due_date  = sale_date + timedelta(days=random.choice([15, 30, 45, 60]))
        due_date  = min(due_date, END_DATE)

        pay_status = sale["payment_status"]
        s_status   = sale["status"]

        if s_status == "cancelled":
            inv_status = "cancelled"
            paid_amt   = 0.0
        elif pay_status == "paid":
            inv_status = "paid"
            paid_amt   = sale["net_amount"]
        elif pay_status == "partial":
            paid_amt   = round(sale["net_amount"] * random.uniform(0.3, 0.7), 2)
            # FIX: use END_DATE (2024-12-31) as reference, not date.today()
            inv_status = "partial" if due_date >= END_DATE else "overdue"
        else:
            # unpaid
            paid_amt   = 0.0
            inv_status = "overdue" if due_date < END_DATE else "partial"

        rows.append({
            "id":             uid(),
            "company_id":     sale["company_id"],
            "sale_id":        sale["id"],
            "customer_id":    sale["customer_id"],
            "invoice_number": f"INV-{inv_num:07d}",
            "invoice_date":   str(sale_date),
            "due_date":       str(due_date),
            "total_amount":   sale["net_amount"],
            "paid_amount":    paid_amt,
            "status":         inv_status,
            "created_at":     format_dt(sale_date),
        })
        inv_num += 1

    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    print()
    print("=" * 60)
    print("  Synthetic ERP Data Generator")
    print("  AI Financial Intelligence Platform -- ML Module")
    print("=" * 60)
    print(f"  Output directory : {OUTPUT_DIR}")
    print(f"  Date range       : {START_DATE} to {END_DATE}")
    print()

    print("[1/9] Generating entity tables...")
    companies_df  = gen_companies()
    save_csv(companies_df, "companies.csv")

    branches_df   = gen_branches(companies_df)
    save_csv(branches_df, "branches.csv")

    users_df      = gen_users(companies_df, branches_df)
    save_csv(users_df, "users.csv")

    customers_df  = gen_customers(companies_df, n_per_company=170)
    save_csv(customers_df, "customers.csv")

    suppliers_df  = gen_suppliers(companies_df, n_per_company=17)
    save_csv(suppliers_df, "suppliers.csv")

    categories_df = gen_categories(companies_df)
    save_csv(categories_df, "categories.csv")

    products_df   = gen_products(companies_df, categories_df)
    save_csv(products_df, "products.csv")

    warehouses_df = gen_warehouses(companies_df, branches_df)
    save_csv(warehouses_df, "warehouses.csv")

    print()
    print("[2/9] Generating inventory...")
    inventory_df  = gen_inventory(products_df, warehouses_df)
    save_csv(inventory_df, "inventory.csv")

    print()
    print("[3/9] Generating sales and sale items...")
    sales_df, sale_items_df = gen_sales(
        companies_df, branches_df, customers_df, users_df, products_df, n_sales=8000
    )
    save_csv(sales_df, "sales.csv")
    save_csv(sale_items_df, "sale_items.csv")

    print()
    print("[4/9] Generating purchases and purchase items...")
    purchases_df, purchase_items_df = gen_purchases(
        companies_df, branches_df, suppliers_df, users_df, products_df, n_purchases=3000
    )
    save_csv(purchases_df, "purchases.csv")
    save_csv(purchase_items_df, "purchase_items.csv")

    print()
    print("[5/9] Generating payments...")
    payments_df = gen_payments(companies_df, sales_df, purchases_df)
    save_csv(payments_df, "payments.csv")

    print()
    print("[6/9] Generating expenses...")
    expenses_df = gen_expenses(companies_df, branches_df, users_df, n_variable=2000)
    save_csv(expenses_df, "expenses.csv")

    print()
    print("[7/9] Generating stock movements...")
    movements_df = gen_stock_movements(
        sales_df, sale_items_df,
        purchases_df, purchase_items_df,
        products_df, inventory_df, warehouses_df,
        n_adjustments=500,
    )
    save_csv(movements_df, "stock_movements.csv")

    print()
    print("[8/9] Generating invoices...")
    invoices_df = gen_invoices(sales_df)
    save_csv(invoices_df, "invoices.csv")

    print()
    print("=" * 60)
    print("  DATASET SUMMARY")
    print("=" * 60)
    tables = [
        ("companies.csv",       companies_df),
        ("branches.csv",        branches_df),
        ("users.csv",           users_df),
        ("customers.csv",       customers_df),
        ("suppliers.csv",       suppliers_df),
        ("categories.csv",      categories_df),
        ("products.csv",        products_df),
        ("warehouses.csv",      warehouses_df),
        ("inventory.csv",       inventory_df),
        ("stock_movements.csv", movements_df),
        ("sales.csv",           sales_df),
        ("sale_items.csv",      sale_items_df),
        ("purchases.csv",       purchases_df),
        ("purchase_items.csv",  purchase_items_df),
        ("payments.csv",        payments_df),
        ("expenses.csv",        expenses_df),
        ("invoices.csv",        invoices_df),
    ]
    total_rows = 0
    print(f"  {'File':<28} {'Rows':>8}  {'Cols':>5}")
    print(f"  {'-'*28} {'-'*8}  {'-'*5}")
    for name, df in tables:
        print(f"  {name:<28} {len(df):>8,}  {len(df.columns):>5}")
        total_rows += len(df)
    print(f"  {'-'*28} {'-'*8}  {'-'*5}")
    print(f"  {'TOTAL ROWS':<28} {total_rows:>8,}")
    print()
    print("[9/9] All done! CSV files saved to:")
    print(f"  {OUTPUT_DIR}")
    print()


if __name__ == "__main__":
    main()
