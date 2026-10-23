# -*- coding: utf-8 -*-
"""
generate_synthetic_data.py
==========================
Generates realistic, internally consistent synthetic ERP and retail datasets
for the ALLADIN AI Financial Intelligence Platform (ML Module - Approach C).

Simulates multiple heterogeneous retail businesses in India operating in INR:
  1. FreshMart Hypermarket Ltd (Large-format retail / hypermarket chain)
  2. GreenRoots Gourmet & Organics (Specialty premium organic & gourmet store)
  3. Apna Kirana QuickRetail (High-velocity neighborhood discount staples chain)

Covers approximately 36 consecutive months of daily retail history (2022-01-01 to 2024-12-31 = 1,096 days).

Features:
  - 100% deterministic & reproducible with fixed random seed (default: 42)
  - Consecutive daily calendar coverage across all 1,096 days
  - Rich Indian retail dynamics: weekly patterns, month-beginning salary cycle,
    major Indian festive peaks (Diwali, Dussehra, Holi, Eid, Independence Day, Republic Day)
  - Realistic stock-out modeling with unconstrained demand vs realized sales tracking
  - Injected, labeled synthetic anomalies for unsupervised and supervised detection
  - Fully reconciled financial ledger: COGS, net sales, taxes (GST), operating expenses,
    invoices, payments, and stock movements
  - Generates 17 core entity & transactional CSVs + 1 daily KPI summary CSV
"""

import os
import sys
import uuid
import random
import argparse
from datetime import date, datetime, timedelta
from typing import List, Dict, Any, Tuple, Optional

import pandas as pd
import numpy as np

# ---------------------------------------------------------------------------
# CLI & Configuration
# ---------------------------------------------------------------------------

DEFAULT_SEED = 42
DEFAULT_START = date(2022, 1, 1)
DEFAULT_END = date.today()

OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))


class DeterministicUUID:
    """Generates reproducible RFC 4122 compliant UUID strings from a seeded RNG."""
    def __init__(self, seed: int = DEFAULT_SEED):
        self.rng = random.Random(seed)

    def __call__(self) -> str:
        return str(uuid.UUID(int=self.rng.getrandbits(128), version=4))


# ---------------------------------------------------------------------------
# Indian Retail Entities & Profiles
# ---------------------------------------------------------------------------

COMPANIES = [
    {
        "id": str(uuid.UUID(int=1)),
        "name": "FreshMart Hypermarket Ltd",
        "industry": "Supermarket",
        "country": "India",
        "currency": "INR",
        "business_model": "Large format hypermarket chain, broad catalog, moderate 18% margins, weekend promotions",
        "annual_growth_rate": 0.10,
        "base_daily_orders": 2.1,
        "default_margin": 0.22,
    },
    {
        "id": str(uuid.UUID(int=2)),
        "name": "GreenRoots Gourmet & Organics",
        "industry": "Specialty Retail",
        "country": "India",
        "currency": "INR",
        "business_model": "Premium organic & wellness foods, higher ticket size, premium 35% margins, low discounting",
        "annual_growth_rate": 0.05,
        "base_daily_orders": 1.3,
        "default_margin": 0.38,
    },
    {
        "id": str(uuid.UUID(int=3)),
        "name": "Apna Kirana QuickRetail",
        "industry": "Grocery",
        "country": "India",
        "currency": "INR",
        "business_model": "High-velocity discount neighborhood kirana, fast staples turnover, slim 12% margins",
        "annual_growth_rate": 0.18,
        "base_daily_orders": 2.2,
        "default_margin": 0.14,
    },
]

BRANCH_LOCATIONS = {
    COMPANIES[0]["id"]: [
        ("Mumbai HQ", "Mumbai", "Andheri West, Mumbai", True),
        ("Pune Branch", "Pune", "Kothrud, Pune", False),
        ("Ahmedabad Branch", "Ahmedabad", "SG Highway, Ahmedabad", False),
    ],
    COMPANIES[1]["id"]: [
        ("Bengaluru HQ", "Bengaluru", "Indiranagar, Bengaluru", True),
        ("Hyderabad Branch", "Hyderabad", "Banjara Hills, Hyderabad", False),
        ("Chennai Branch", "Chennai", "Adyar, Chennai", False),
    ],
    COMPANIES[2]["id"]: [
        ("Delhi NCR HQ", "Delhi", "Noida Sector 18, Delhi NCR", True),
        ("Jaipur Branch", "Jaipur", "Malviya Nagar, Jaipur", False),
        ("Lucknow Branch", "Lucknow", "Gomti Nagar, Lucknow", False),
    ],
}

USER_ROLES = ["admin", "manager", "sales", "accountant"]

INDIAN_FIRST_NAMES = [
    "Aarav", "Aditi", "Amit", "Ananya", "Arjun", "Bhavna", "Chetan", "Deepak",
    "Divya", "Gaurav", "Harsh", "Isha", "Karan", "Kavya", "Manish", "Meera",
    "Nikhil", "Neha", "Pooja", "Pranav", "Priya", "Rahul", "Rakesh", "Ritu",
    "Rohan", "Sanjay", "Shreya", "Siddharth", "Sneha", "Suresh", "Tanvi", "Vikram"
]

INDIAN_LAST_NAMES = [
    "Agarwal", "Bhatia", "Chauhan", "Deshmukh", "Gupta", "Iyer", "Jain", "Joshi",
    "Kapur", "Kumar", "Mehta", "Mishra", "Nair", "Patel", "Reddy", "Rao",
    "Sharma", "Singh", "Shah", "Trivedi", "Varma", "Verma", "Yadav"
]

EXPENSE_CATEGORIES = [
    "Rent", "Salaries", "Utilities", "Marketing", "Logistics",
    "Packaging Materials", "Maintenance", "Office Supplies", "IT & Software", "Insurance"
]

PAYMENT_METHODS = ["cash", "card", "bank_transfer", "cheque"]

# 20 realistic Indian retail product categories per company
CATEGORY_CATALOG = [
    ("Staples & Grains", "Rice, wheat flour, lentils, sugar, salt and pulses"),
    ("Edible Oils & Ghee", "Cooking oils, mustard oil, sunflower oil, and pure cow ghee"),
    ("Dairy & Chilled", "Fresh milk, paneer, butter, curd, and farm eggs"),
    ("Bakery & Breakfast", "Fresh whole wheat breads, toasts, oats, cereals, and jams"),
    ("Snacks & Namkeen", "Traditional Indian namkeen, bhujia, roasted nuts, and makhana"),
    ("Biscuits & Cookies", "Digestive biscuits, cream cookies, rusk, and tea snacks"),
    ("Tea & Beverages", "Assam CTC tea, South Indian filter coffee, green tea, juices"),
    ("Spices & Masalas", "Whole and ground spices, turmeric, chilli, garam masala"),
    ("Packaged Foods", "Instant noodles, pasta, sauces, tomato ketchup, and ready-to-cook"),
    ("Fresh Produce", "Daily fresh vegetables, onions, potatoes, tomatoes, and seasonal fruits"),
    ("Personal Care", "Bathing soaps, herbal shampoos, toothpastes, and hair oils"),
    ("Skincare & Hygiene", "Moisturizers, sunscreen lotions, face washes, and hand sanitizers"),
    ("Household Cleaners", "Detergent powders, dishwash gels, floor and toilet cleaners"),
    ("Pooja & Festive Needs", "Pure camphor, agarbatti, brass diyas, and cotton wicks"),
    ("Kitchenware & Utensils", "Stainless steel cookware, tawas, bottles, and storage containers"),
    ("Stationery & Books", "Notebooks, pens, markers, scissors, and office supplies"),
    ("Baby Care", "Diapers, baby wipes, gentle baby shampoos, and baby powders"),
    ("Pet Care Essentials", "Dry dog food, cat food, pet biscuits, and grooming supplies"),
    ("Small Home Appliances", "Electric kettles, sandwich makers, dry irons, and hand blenders"),
    ("Cleaning Accessories", "Mops, brooms, garbage bags, aluminum foils, and scrub sponges"),
]

# Product catalog templates: (Product Name, Cost Price INR, Selling Price INR, Unit)
PRODUCT_CATALOG = {
    "Staples & Grains": [
        ("Premium Basmati Rice 5kg", 380, 520, "bag"),
        ("Sharbati Whole Wheat Atta 10kg", 320, 420, "bag"),
        ("Organic Toor Dal 1kg", 110, 155, "kg"),
        ("Moong Dal Washed 1kg", 95, 135, "kg"),
        ("Thick Poha 1kg", 45, 65, "kg"),
    ],
    "Edible Oils & Ghee": [
        ("Cold Pressed Mustard Oil 1L", 130, 180, "litre"),
        ("Refined Sunflower Oil 1L", 115, 155, "litre"),
        ("Pure Desi Cow Ghee 500ml", 310, 440, "box"),
        ("Groundnut Oil Filtered 1L", 160, 220, "litre"),
        ("Extra Virgin Olive Oil 500ml", 420, 599, "box"),
    ],
    "Dairy & Chilled": [
        ("Toned Fresh Milk 1L", 42, 54, "litre"),
        ("Malai Fresh Paneer 200g", 65, 88, "pcs"),
        ("Traditional Curd Dahi 400g", 30, 42, "pcs"),
        ("Pasteurized Salted Butter 100g", 40, 56, "pcs"),
        ("Farm Fresh Eggs Tray of 12", 68, 92, "box"),
    ],
    "Bakery & Breakfast": [
        ("100% Whole Wheat Bread 400g", 28, 45, "pcs"),
        ("Suji Rusk Toast 200g", 35, 50, "pcs"),
        ("Rolled Oats 1kg Pouch", 140, 195, "bag"),
        ("Almond Corn Flakes 500g", 130, 185, "box"),
        ("Mixed Fruit Jam 500g", 110, 160, "pcs"),
    ],
    "Snacks & Namkeen": [
        ("Bikaneri Aloo Bhujia 400g", 80, 115, "pcs"),
        ("Masala Roasted Cashews 200g", 180, 260, "box"),
        ("California Almonds 200g", 160, 230, "box"),
        ("Organic Roasted Makhana 100g", 90, 140, "box"),
        ("Traditional Chakli Murukku 200g", 50, 75, "pcs"),
    ],
    "Biscuits & Cookies": [
        ("Digestive High Fiber Biscuits", 55, 80, "pcs"),
        ("Rich Butter Cookies 250g", 70, 105, "pcs"),
        ("Dark Choco Cream Biscuits 300g", 65, 95, "pcs"),
        ("Classic Marie Gold 300g", 30, 42, "pcs"),
        ("Herb Salt Crackers 200g", 38, 55, "pcs"),
    ],
    "Tea & Beverages": [
        ("Premium Assam CTC Tea 500g", 190, 275, "bag"),
        ("South Indian Filter Coffee 200g", 110, 165, "pcs"),
        ("Pure Green Tea Bags 100pk", 220, 320, "box"),
        ("Pure Alphonso Mango Drink 1L", 70, 110, "litre"),
        ("Natural Tender Coconut Water 200ml", 35, 50, "pcs"),
    ],
    "Spices & Masalas": [
        ("Royal Garam Masala 100g", 60, 90, "pcs"),
        ("Salem Turmeric Powder 200g", 45, 68, "pcs"),
        ("Kashmiri Red Chilli Powder 200g", 85, 125, "pcs"),
        ("Coriander Powder Dhaniya 200g", 42, 65, "pcs"),
        ("Unpolished Cumin Seeds Jeera 200g", 95, 145, "pcs"),
    ],
    "Packaged Foods": [
        ("Masala Instant Noodles 8pk", 75, 105, "pcs"),
        ("Durum Wheat Pasta Fusilli 500g", 65, 99, "pcs"),
        ("Classic Tomato Ketchup 1kg", 85, 130, "pcs"),
        ("70% Dark Chocolate Bar 100g", 75, 120, "pcs"),
        ("Sweet Golden Corn Can 400g", 55, 85, "pcs"),
    ],
    "Fresh Produce": [
        ("Fresh Red Onions 1kg", 25, 40, "kg"),
        ("Fresh Jyoti Potatoes 1kg", 20, 32, "kg"),
        ("Hybrid Vine Tomatoes 1kg", 28, 45, "kg"),
        ("Hydroponic Baby Spinach 250g", 25, 45, "pcs"),
        ("Shimla Royal Apple 1kg", 110, 160, "kg"),
    ],
    "Personal Care": [
        ("Neem & Tulsi Soap 125g 3pk", 70, 110, "box"),
        ("Herbal Anti-Dandruff Shampoo 400ml", 175, 260, "pcs"),
        ("Ayurvedic Toothpaste 150g", 65, 95, "pcs"),
        ("Pure Coconut Hair Oil 200ml", 60, 88, "pcs"),
        ("Anti-Bacterial Handwash Refill 750ml", 85, 135, "pcs"),
    ],
    "Skincare & Hygiene": [
        ("Light Moisturizing Cold Cream 100ml", 110, 175, "pcs"),
        ("Pure Aloe Vera Gel 200g", 80, 130, "pcs"),
        ("Mineral Sunscreen SPF50 100ml", 210, 340, "pcs"),
        ("Natural Rose Water Toner 250ml", 60, 95, "pcs"),
        ("Moisturizing Shea Lip Balm 10g", 50, 85, "pcs"),
    ],
    "Household Cleaners": [
        ("Advanced Detergent Powder 2kg", 180, 260, "bag"),
        ("Lemon Dishwash Gel 750ml", 100, 150, "pcs"),
        ("Citrus Floor Disinfectant Cleaner 1L", 90, 140, "litre"),
        ("Power Toilet Cleaner Liquid 750ml", 85, 130, "pcs"),
        ("Glass & Mirror Cleaner Spray 500ml", 65, 99, "pcs"),
    ],
    "Pooja & Festive Needs": [
        ("Pure Refined Camphor 50g", 45, 70, "box"),
        ("Handcrafted Agarbatti 100 sticks", 60, 95, "box"),
        ("Brass Akhand Diya Single", 160, 250, "pcs"),
        ("Long Cotton Wicks Pack of 200", 30, 48, "box"),
        ("Sandalwood Dhoop Cups 12pk", 55, 85, "box"),
    ],
    "Kitchenware & Utensils": [
        ("Tri-Ply Stainless Steel Kadhai 22cm", 650, 990, "pcs"),
        ("Granite Non-Stick Tawa 28cm", 480, 750, "pcs"),
        ("Insulated Stainless Steel Bottle 1L", 280, 450, "pcs"),
        ("Precision Chef Knife 8-inch", 180, 320, "pcs"),
        ("BPA-Free Airtight Food Containers 4pc", 240, 380, "set"),
    ],
    "Stationery & Books": [
        ("Classmate A4 Spiral Notebook 6pk", 210, 320, "set"),
        ("Smooth Ballpoint Pens Pack of 10", 60, 90, "set"),
        ("Pastel Color Highlighters 4pk", 75, 120, "set"),
        ("Mathematical Geometry Box Set", 85, 130, "set"),
        ("Non-Toxic Craft Glue 100g", 25, 40, "pcs"),
    ],
    "Baby Care": [
        ("Gentle Baby Diapers Medium 48pk", 480, 699, "pack"),
        ("Aloe Vera Baby Wet Wipes 72pk", 95, 149, "pack"),
        ("Baby Nourishing Lotion 200ml", 120, 185, "pcs"),
        ("Dusting Baby Powder 200g", 90, 135, "pcs"),
        ("Ayurvedic Gripe Water 150ml", 45, 68, "pcs"),
    ],
    "Pet Care Essentials": [
        ("Complete Adult Dog Food 3kg", 520, 780, "bag"),
        ("Ocean Fish Dry Cat Food 1.2kg", 320, 490, "bag"),
        ("Calcium Milk Dog Biscuits 500g", 110, 170, "box"),
        ("Herbal Pet Grooming Shampoo 250ml", 140, 220, "pcs"),
        ("Pressed Rawhide Dog Chews 4pk", 90, 145, "pack"),
    ],
    "Small Home Appliances": [
        ("Stainless Steel Electric Kettle 1.5L", 520, 850, "pcs"),
        ("Non-Stick Sandwich Toaster 750W", 680, 1150, "pcs"),
        ("Heavyweight Dry Iron 1000W", 450, 750, "pcs"),
        ("Stainless Steel Hand Blender 300W", 720, 1200, "pcs"),
        ("Rechargeable LED Study Desk Lamp", 340, 580, "pcs"),
    ],
    "Cleaning Accessories": [
        ("360 Spin Mop & Bucket System", 480, 790, "set"),
        ("Heavy Duty Kitchen Garbage Bags 30pk", 85, 135, "roll"),
        ("Food Grade Aluminum Foil 18m", 80, 125, "roll"),
        ("Absorbent Kitchen Paper Towel 2pk", 70, 110, "pack"),
        ("Multipurpose Scrub Sponge 4pk", 35, 55, "pack"),
    ],
}

INDIAN_SUPPLIERS = [
    ("Godrej Consumer Distributors", 30),
    ("Dabur India Supply Hub", 30),
    ("Tata Consumer Products Logistics", 45),
    ("ITC Agro & FMCG Wholesale", 30),
    ("Amul Dairy Federation Depot", 15),
    ("Fortune Adani Wilmar Distributors", 30),
    ("Hindustan Unilever Wholesale", 45),
    ("Britannia Foods Agency", 30),
    ("Parle Products Distribution", 30),
    ("Nestle India Regional Supply", 45),
    ("Patanjali Ayurved Wholesale", 30),
    ("Marico Consumer Supply Hub", 30),
    ("Mother Dairy Fruits & Veg", 15),
    ("MDH Spices Trade Agency", 30),
    ("Everest Food Products Depot", 30),
    ("Haldiram Snacks Wholesale", 30),
    ("Bikaji Foods Distribution", 30),
]


# ---------------------------------------------------------------------------
# Calendar & Seasonality Model
# ---------------------------------------------------------------------------

def get_indian_festival_multiplier(d: date) -> float:
    """Returns demand surge multiplier for Indian festival dates (2022-2026)."""
    year = d.year
    month = d.month
    day = d.day

    # Republic Day Great Sale (Jan 22-26)
    if month == 1 and 22 <= day <= 26:
        return 1.45

    # Holi Festive Surges
    if (year == 2022 and month == 3 and 15 <= day <= 19) or \
       (year == 2023 and month == 3 and 5 <= day <= 9) or \
       (year == 2024 and month == 3 and 22 <= day <= 26) or \
       (year == 2025 and month == 3 and 12 <= day <= 16) or \
       (year == 2026 and month == 3 and 2 <= day <= 6):
        return 1.55

    # Eid-ul-Fitr
    if (year == 2022 and month == 5 and 1 <= day <= 4) or \
       (year == 2023 and month == 4 and 20 <= day <= 23) or \
       (year == 2024 and month == 4 and 9 <= day <= 12) or \
       (year == 2025 and month == 3 and 30 <= day <= 31 or (year == 2025 and month == 4 and 1 <= day <= 2)) or \
       (year == 2026 and month == 3 and 19 <= day <= 23):
        return 1.40

    # Independence Day Freedom Sale (Aug 10-15)
    if month == 8 and 10 <= day <= 15:
        return 1.50

    # Navratri & Dussehra Festive Period
    if (year == 2022 and month in (9, 10) and ((month == 9 and day >= 26) or (month == 10 and day <= 5))) or \
       (year == 2023 and month == 10 and 15 <= day <= 24) or \
       (year == 2024 and month == 10 and 3 <= day <= 12) or \
       (year == 2025 and month in (9, 10) and ((month == 9 and day >= 22) or (month == 10 and day <= 2))) or \
       (year == 2026 and month == 10 and 10 <= day <= 20):
        return 1.65

    # Diwali & Dhanteras Super Festive Peak (Highest Indian retail shopping period)
    if (year == 2022 and month == 10 and 19 <= day <= 26) or \
       (year == 2023 and month == 11 and 7 <= day <= 14) or \
       (year == 2024 and month in (10, 11) and ((month == 10 and day >= 27) or (month == 11 and day <= 2))) or \
       (year == 2025 and month == 10 and 18 <= day <= 25) or \
       (year == 2026 and month in (10, 11) and ((month == 10 and day >= 25) or (month == 11 and day <= 10))):
        return 2.50

    # Year-End Clearance / New Year (Dec 25-31)
    if month == 12 and day >= 25:
        return 1.45

    return 1.0


def get_calendar_multiplier(d: date) -> float:
    """Returns combined weekly, monthly salary cycle, and general quarterly baseline."""
    dow = d.weekday()  # 0=Monday, 6=Sunday
    # Retail stores see heaviest traffic on weekends in India
    if dow == 6:       # Sunday
        dow_mult = 1.45
    elif dow == 5:     # Saturday
        dow_mult = 1.35
    elif dow == 4:     # Friday
        dow_mult = 1.10
    elif dow in (1, 2, 3):  # Tue, Wed, Thu
        dow_mult = 0.90
    else:              # Monday
        dow_mult = 0.85

    # Salary cycle: Indian household grocery replenishment in 1st week of the month
    if 1 <= d.day <= 7:
        salary_mult = 1.20
    elif 8 <= d.day <= 20:
        salary_mult = 1.00
    else:
        salary_mult = 0.92

    # Quarter seasonal trend (Q4 festive > Q2 summer > Q1 spring > Q3 monsoon)
    q = (d.month - 1) // 3 + 1
    q_mult = {1: 0.95, 2: 1.15, 3: 0.90, 4: 1.40}[q]

    fest_mult = get_indian_festival_multiplier(d)

    return dow_mult * salary_mult * (0.4 * q_mult + 0.6 * fest_mult)


# ---------------------------------------------------------------------------
# Data Generator Engine
# ---------------------------------------------------------------------------

class RetailDataGenerator:
    def __init__(self, seed: int = DEFAULT_SEED, start_date: date = DEFAULT_START, end_date: date = DEFAULT_END):
        self.seed = seed
        self.start_date = start_date
        self.end_date = end_date
        self.rng = random.Random(seed)
        self.np_rng = np.random.RandomState(seed)
        self.uid_gen = DeterministicUUID(seed)

    def uid(self) -> str:
        return self.uid_gen()

    def format_dt(self, d: date, hour_override: int = None) -> str:
        h = hour_override if hour_override is not None else self.rng.randint(9, 21)
        m = self.rng.randint(0, 59)
        s = self.rng.randint(0, 59)
        return datetime(d.year, d.month, d.day, h, m, s).isoformat()

    def build_companies(self) -> pd.DataFrame:
        rows = []
        for c in COMPANIES:
            rows.append({
                "id": c["id"],
                "name": c["name"],
                "industry": c["industry"],
                "country": c["country"],
                "currency": c["currency"],
                "created_at": "2021-06-01T09:00:00",
            })
        return pd.DataFrame(rows)

    def build_branches(self, companies_df: pd.DataFrame) -> pd.DataFrame:
        rows = []
        for _, co in companies_df.iterrows():
            locs = BRANCH_LOCATIONS[co["id"]]
            for name, city, addr, is_hq in locs:
                rows.append({
                    "id": self.uid(),
                    "company_id": co["id"],
                    "name": name,
                    "city": city,
                    "is_headquarters": is_hq,
                    "created_at": "2021-06-15T09:00:00",
                })
        return pd.DataFrame(rows)

    def build_users(self, companies_df: pd.DataFrame, branches_df: pd.DataFrame) -> pd.DataFrame:
        rows = []
        for _, co in companies_df.iterrows():
            cid = co["id"]
            co_branches = branches_df[branches_df["company_id"] == cid]
            domain = co["name"].split()[0].lower() + "retail.in"
            for _, br in co_branches.iterrows():
                for role in USER_ROLES:
                    first = self.rng.choice(INDIAN_FIRST_NAMES)
                    last = self.rng.choice(INDIAN_LAST_NAMES)
                    email = f"{first.lower()}.{last.lower()}{self.rng.randint(1, 99)}@{domain}"
                    rows.append({
                        "id": self.uid(),
                        "company_id": cid,
                        "branch_id": br["id"],
                        "name": f"{first} {last}",
                        "email": email,
                        "role": role,
                        "created_at": "2021-07-01T09:00:00",
                    })
        return pd.DataFrame(rows)

    def build_customers(self, companies_df: pd.DataFrame, n_per_company: int = 170) -> pd.DataFrame:
        rows = []
        for _, co in companies_df.iterrows():
            cid = co["id"]
            cities = [b[1] for b in BRANCH_LOCATIONS[cid]]
            for _ in range(n_per_company):
                first = self.rng.choice(INDIAN_FIRST_NAMES)
                last = self.rng.choice(INDIAN_LAST_NAMES)
                c_type = self.rng.choices(["individual", "business"], weights=[0.75, 0.25])[0]
                name = f"{first} {last}" if c_type == "individual" else f"{last} Enterprises ({first})"
                email = f"{first.lower()}.{last.lower()}{self.rng.randint(10, 999)}@gmail.com"
                phone = f"+91{self.rng.randint(7000000000, 9999999999)}"
                credit = 25000.0 if c_type == "individual" else 150000.0
                rows.append({
                    "id": self.uid(),
                    "company_id": cid,
                    "name": name,
                    "email": email,
                    "phone": phone,
                    "city": self.rng.choice(cities),
                    "customer_type": c_type,
                    "credit_limit": credit,
                    "created_at": "2021-08-01T09:00:00",
                })
        return pd.DataFrame(rows)

    def build_suppliers(self, companies_df: pd.DataFrame, n_per_company: int = 17) -> pd.DataFrame:
        rows = []
        for _, co in companies_df.iterrows():
            cid = co["id"]
            cities = [b[1] for b in BRANCH_LOCATIONS[cid]]
            used_suppliers = self.rng.sample(INDIAN_SUPPLIERS, min(n_per_company, len(INDIAN_SUPPLIERS)))
            for sup_name, terms in used_suppliers:
                clean_name = sup_name.lower().replace(" ", "").replace("&", "")
                rows.append({
                    "id": self.uid(),
                    "company_id": cid,
                    "name": sup_name,
                    "contact_email": f"orders@{clean_name}.com",
                    "phone": f"+91{self.rng.randint(7000000000, 9999999999)}",
                    "city": self.rng.choice(cities),
                    "payment_terms_days": terms,
                    "created_at": "2021-08-01T09:00:00",
                })
        return pd.DataFrame(rows)

    def build_categories(self, companies_df: pd.DataFrame) -> pd.DataFrame:
        rows = []
        for _, co in companies_df.iterrows():
            cid = co["id"]
            for cat_name, desc in CATEGORY_CATALOG:
                rows.append({
                    "id": self.uid(),
                    "company_id": cid,
                    "name": cat_name,
                    "type": "product",
                    "description": desc,
                    "created_at": "2021-06-01T09:00:00",
                })
            for exp_cat in EXPENSE_CATEGORIES:
                rows.append({
                    "id": self.uid(),
                    "company_id": cid,
                    "name": exp_cat,
                    "type": "expense",
                    "description": f"Operational expense category: {exp_cat}",
                    "created_at": "2021-06-01T09:00:00",
                })
        return pd.DataFrame(rows)

    def build_products(self, companies_df: pd.DataFrame, categories_df: pd.DataFrame) -> pd.DataFrame:
        rows = []
        sku_counters = {co["id"]: 1 for co in COMPANIES}

        for _, co in companies_df.iterrows():
            cid = co["id"]
            co_cats = categories_df[(categories_df["company_id"] == cid) & (categories_df["name"].isin(PRODUCT_CATALOG.keys()))]
            # Company specific pricing adjustments
            cost_factor = 1.15 if "Gourmet" in co["name"] else (0.90 if "Kirana" in co["name"] else 1.0)
            markup_factor = 1.38 if "Gourmet" in co["name"] else (1.14 if "Kirana" in co["name"] else 1.22)

            for _, cat in co_cats.iterrows():
                cat_name = cat["name"]
                templates = PRODUCT_CATALOG.get(cat_name, [])
                for prod_name, base_cost, base_sell, unit in templates:
                    cost = round(base_cost * cost_factor * self.rng.uniform(0.96, 1.04), 2)
                    sell = round(cost * markup_factor * self.rng.uniform(0.98, 1.05), 2)
                    sell = max(sell, round(cost * 1.05, 2))  # Ensure selling >= cost

                    sku = f"{cat_name[:3].upper()}-{sku_counters[cid]:04d}"
                    sku_counters[cid] += 1

                    rows.append({
                        "id": self.uid(),
                        "company_id": cid,
                        "category_id": cat["id"],
                        "name": prod_name,
                        "sku": sku,
                        "cost_price": cost,
                        "selling_price": sell,
                        "unit": unit,
                        "is_active": True,
                        "created_at": "2021-09-01T09:00:00",
                    })
        return pd.DataFrame(rows)

    def build_warehouses(self, companies_df: pd.DataFrame, branches_df: pd.DataFrame) -> pd.DataFrame:
        rows = []
        for _, co in companies_df.iterrows():
            cid = co["id"]
            co_branches = branches_df[branches_df["company_id"] == cid]
            for _, br in co_branches.iterrows():
                # HQ gets 2 warehouses; branches get 1
                n_wh = 2 if br["is_headquarters"] else 1
                for j in range(n_wh):
                    suffix = "Central Warehouse" if j == 0 else "Reserve Depot"
                    rows.append({
                        "id": self.uid(),
                        "company_id": cid,
                        "branch_id": br["id"],
                        "name": f"{br['city']} {suffix}",
                        "location": f"{br['name']}, {br['city']} - Sector {j + 1}",
                        "created_at": "2021-10-01T09:00:00",
                    })
        return pd.DataFrame(rows)

    def build_inventory_initial(self, products_df: pd.DataFrame, warehouses_df: pd.DataFrame) -> pd.DataFrame:
        rows = []
        wh_by_co = warehouses_df.groupby("company_id")["id"].apply(list).to_dict()

        for _, prod in products_df.iterrows():
            cid = prod["company_id"]
            whs = wh_by_co.get(cid, [])
            if not whs:
                continue
            # Stock each product in 1 to 3 warehouses of its company
            k = min(len(whs), self.rng.randint(1, 3))
            assigned_whs = self.rng.sample(whs, k)
            for wh_id in assigned_whs:
                qty = self.rng.randint(60, 450)
                reorder_lvl = self.rng.randint(15, 40)
                reorder_qty = reorder_lvl * self.rng.randint(3, 6)
                rows.append({
                    "id": self.uid(),
                    "product_id": prod["id"],
                    "warehouse_id": wh_id,
                    "quantity_on_hand": qty,
                    "reorder_level": reorder_lvl,
                    "reorder_quantity": reorder_qty,
                    "updated_at": "2022-01-01T00:00:00",
                })
        return pd.DataFrame(rows)

    def simulate_operations(
        self,
        companies_df: pd.DataFrame,
        branches_df: pd.DataFrame,
        users_df: pd.DataFrame,
        customers_df: pd.DataFrame,
        suppliers_df: pd.DataFrame,
        products_df: pd.DataFrame,
        warehouses_df: pd.DataFrame,
        inventory_initial_df: pd.DataFrame,
        categories_df: Optional[pd.DataFrame] = None,
    ) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """
        Runs the daily calendar simulation across consecutive days from start_date to end_date.
        Tracks dynamic inventory levels, stock-outs, sales, purchases, payments, expenses, and KPI aggregates.
        """
        # Lookup maps
        branch_map = branches_df.groupby("company_id")["id"].apply(list).to_dict()
        user_map = users_df.groupby("company_id")["id"].apply(list).to_dict()
        customer_map = customers_df.groupby("company_id")["id"].apply(list).to_dict()
        supplier_map = suppliers_df.groupby("company_id")["id"].apply(list).to_dict()

        exp_cat_map = {}
        if categories_df is not None and "type" in categories_df.columns:
            for _, r in categories_df[categories_df["type"] == "expense"].iterrows():
                exp_cat_map[(r["company_id"], r["name"])] = r["id"]

        prods_by_co = {}
        for cid, grp in products_df.groupby("company_id"):
            prods_by_co[cid] = grp.to_dict("records")

        # Dynamic stock tracking: (product_id, warehouse_id) -> quantity_on_hand
        stock_tracker: Dict[Tuple[str, str], int] = {}
        reorder_info: Dict[Tuple[str, str], Dict[str, int]] = {}
        prod_wh_list: Dict[str, List[str]] = {}

        for _, row in inventory_initial_df.iterrows():
            key = (row["product_id"], row["warehouse_id"])
            stock_tracker[key] = int(row["quantity_on_hand"])
            reorder_info[key] = {
                "reorder_level": int(row["reorder_level"]),
                "reorder_quantity": int(row["reorder_quantity"]),
            }
            prod_wh_list.setdefault(row["product_id"], []).append(row["warehouse_id"])

        # Pre-index warehouse to company mapping and company stock keys for O(1) lookup
        wh_to_co = warehouses_df.set_index("id")["company_id"].to_dict()
        co_stock_keys = {cid: [] for cid in companies_df["id"]}
        for k in stock_tracker.keys():
            cid_k = wh_to_co.get(k[1])
            if cid_k:
                co_stock_keys[cid_k].append(k)

        # Collectors
        sales_records = []
        sale_items_records = []
        purchases_records = []
        purchase_items_records = []
        stock_movements = []
        invoices_records = []
        payments_records = []
        expenses_records = []
        daily_kpi_records = []

        # Track pending purchase deliveries: list of dicts {arrival_date, purchase_id, items: [(prod_id, wh_id, qty)]}
        pending_deliveries = []

        # Iterate every single day from START_DATE to END_DATE
        curr_date = self.start_date
        invoice_counter = 1

        # Fixed expense calendar tracking
        processed_months_rent = set()
        processed_months_salaries = set()
        processed_months_utilities = set()

        company_config = {c["id"]: c for c in COMPANIES}
        total_days = (self.end_date - self.start_date).days + 1

        for day_idx in range(total_days):
            current_date = self.start_date + timedelta(days=day_idx)
            cal_multiplier = get_calendar_multiplier(current_date)
            years_elapsed = (current_date - self.start_date).days / 365.25
            today_approved_expenses = {cid: 0.0 for cid in company_config.keys()}

            # Process inbound purchase deliveries that arrive today
            today_deliveries = [d for d in pending_deliveries if d["arrival_date"] == current_date]
            pending_deliveries = [d for d in pending_deliveries if d["arrival_date"] > current_date]

            for deliv in today_deliveries:
                for p_id, wh_id, p_qty in deliv["items"]:
                    key = (p_id, wh_id)
                    stock_tracker[key] = stock_tracker.get(key, 0) + p_qty
                    stock_movements.append({
                        "id": self.uid(),
                        "product_id": p_id,
                        "warehouse_id": wh_id,
                        "movement_type": "in",
                        "quantity": p_qty,
                        "reason": "purchase",
                        "reference_id": deliv["purchase_id"],
                        "moved_at": self.format_dt(current_date, hour_override=10),
                    })

            # Process fixed monthly expenses on specific days of the month
            # Rent: 1st of every month
            if current_date.day == 1 and (current_date.year, current_date.month) not in processed_months_rent:
                processed_months_rent.add((current_date.year, current_date.month))
                for _, co in companies_df.iterrows():
                    cid = co["id"]
                    for br_id in branch_map[cid]:
                        rent_amt = round(self.rng.uniform(65000, 160000), 2)
                        today_approved_expenses[cid] += rent_amt
                        expenses_records.append({
                            "id": self.uid(),
                            "company_id": cid,
                            "branch_id": br_id,
                            "user_id": self.rng.choice(user_map[cid]),
                            "category_id": exp_cat_map.get((cid, "Rent")),
                            "category": "Rent",
                            "description": f"Monthly retail facility rent - {current_date.strftime('%B %Y')}",
                            "amount": rent_amt,
                            "expense_date": str(current_date),
                            "status": "approved",
                            "is_anomaly": False,
                            "created_at": self.format_dt(current_date, 9),
                        })

            # Utilities: 15th of every month
            if current_date.day == 15 and (current_date.year, current_date.month) not in processed_months_utilities:
                processed_months_utilities.add((current_date.year, current_date.month))
                for _, co in companies_df.iterrows():
                    cid = co["id"]
                    for br_id in branch_map[cid]:
                        util_amt = round(self.rng.uniform(12000, 38000), 2)
                        today_approved_expenses[cid] += util_amt
                        expenses_records.append({
                            "id": self.uid(),
                            "company_id": cid,
                            "branch_id": br_id,
                            "user_id": self.rng.choice(user_map[cid]),
                            "category_id": exp_cat_map.get((cid, "Utilities")),
                            "category": "Utilities",
                            "description": f"Electricity, water, and cooling - {current_date.strftime('%B %Y')}",
                            "amount": util_amt,
                            "expense_date": str(current_date),
                            "status": "approved",
                            "is_anomaly": False,
                            "created_at": self.format_dt(current_date, 11),
                        })

            # Salaries: 28th of every month
            if current_date.day == 28 and (current_date.year, current_date.month) not in processed_months_salaries:
                processed_months_salaries.add((current_date.year, current_date.month))
                for _, co in companies_df.iterrows():
                    cid = co["id"]
                    for br_id in branch_map[cid]:
                        sal_amt = round(self.rng.uniform(180000, 480000), 2)
                        today_approved_expenses[cid] += sal_amt
                        expenses_records.append({
                            "id": self.uid(),
                            "company_id": cid,
                            "branch_id": br_id,
                            "user_id": self.rng.choice(user_map[cid]),
                            "category_id": exp_cat_map.get((cid, "Salaries")),
                            "category": "Salaries",
                            "description": f"Staff payroll & store operations compensation - {current_date.strftime('%B %Y')}",
                            "amount": sal_amt,
                            "expense_date": str(current_date),
                            "status": "approved",
                            "is_anomaly": False,
                            "created_at": self.format_dt(current_date, 17),
                        })

            # Variable operational expenses across branches (~1.8 per day platform-wide)
            n_var_exp = self.rng.choices([1, 2, 3], weights=[0.35, 0.50, 0.15])[0]
            for _ in range(n_var_exp):
                exp_cid = self.rng.choice(list(companies_df["id"]))
                exp_cat = self.rng.choice([c for c in EXPENSE_CATEGORIES if c not in ("Rent", "Salaries", "Utilities")])
                exp_anom = self.rng.random() < 0.015  # 1.5% labeled anomaly
                base_exp = self.rng.uniform(1200, 24000)
                exp_amount = round(base_exp * (8.5 if exp_anom else 1.0), 2)

                if not exp_anom:
                    today_approved_expenses[exp_cid] += exp_amount

                expenses_records.append({
                    "id": self.uid(),
                    "company_id": exp_cid,
                    "branch_id": self.rng.choice(branch_map[exp_cid]),
                    "user_id": self.rng.choice(user_map[exp_cid]),
                    "category_id": exp_cat_map.get((exp_cid, exp_cat)),
                    "category": exp_cat,
                    "description": f"Store operational expense ({exp_cat})" + (" [SURGE_ANOMALY]" if exp_anom else ""),
                    "amount": exp_amount,
                    "expense_date": str(current_date),
                    "status": "approved" if not exp_anom else "pending",
                    "is_anomaly": exp_anom,
                    "created_at": self.format_dt(current_date),
                })

            # --- Company Daily Operations (Sales, Purchases, Inventory Checks) ---
            company_config = {c["id"]: c for c in COMPANIES}
            for _, co in companies_df.iterrows():
                cid = co["id"]
                c_meta = company_config[cid]
                growth_mult = 1.0 + c_meta["annual_growth_rate"] * years_elapsed
                prods = prods_by_co[cid]

                # Determine daily sales count for this company
                expected_sales = c_meta["base_daily_orders"] * cal_multiplier * growth_mult
                # Poisson-like sampling with floor of 1 to ensure consecutive daily presence
                daily_sales_count = max(1, int(round(expected_sales + self.rng.uniform(-0.6, 0.6))))

                co_day_revenue = 0.0
                co_day_cogs = 0.0
                co_day_units = 0
                co_day_unconstrained = 0
                co_day_stockouts = 0
                co_day_anomalies = False

                for _ in range(daily_sales_count):
                    sale_id = self.uid()
                    branch_id = self.rng.choice(branch_map[cid])
                    cust_id = self.rng.choice(customer_map[cid])
                    sales_user_id = self.rng.choice(user_map[cid])

                    is_sale_anom = self.rng.random() < 0.012  # 1.2% labeled anomaly
                    if is_sale_anom:
                        co_day_anomalies = True

                    sale_status = self.rng.choices(
                        ["completed", "pending", "cancelled"],
                        weights=[0.85, 0.11, 0.04]
                    )[0]

                    n_items = self.rng.choices([1, 2, 3, 4, 5], weights=[0.30, 0.35, 0.20, 0.10, 0.05])[0]
                    chosen_prods = self.rng.sample(prods, min(n_items, len(prods)))

                    sale_total = 0.0
                    sale_discount = 0.0
                    has_stockout_flag = False
                    sale_items_batch = []

                    for prod in chosen_prods:
                        pid = prod["id"]
                        wh_candidates = prod_wh_list.get(pid, [])
                        chosen_wh = self.rng.choice(wh_candidates) if wh_candidates else None

                        # Unconstrained demand (customer intent)
                        unconstrained_qty = self.rng.randint(1, 14) if not is_sale_anom else self.rng.randint(35, 75)

                        # Check available stock
                        current_avail = stock_tracker.get((pid, chosen_wh), 0) if chosen_wh else 999
                        if current_avail >= unconstrained_qty:
                            realized_qty = unconstrained_qty
                            is_stockout = False
                        else:
                            # Stock suppressed demand
                            realized_qty = max(1, current_avail) if sale_status == "completed" and current_avail > 0 else (1 if current_avail == 0 else current_avail)
                            is_stockout = True
                            has_stockout_flag = True
                            co_day_stockouts += 1

                        unit_price = round(prod["selling_price"] * self.rng.uniform(0.96, 1.04), 2)
                        disc_pct = 0.75 if (is_sale_anom and self.rng.random() < 0.5) else self.rng.choices([0.0, 0.05, 0.10, 0.15], weights=[0.55, 0.22, 0.15, 0.08])[0]

                        line_total = round(realized_qty * unit_price * (1.0 - disc_pct), 2)
                        line_disc = round(realized_qty * unit_price * disc_pct, 2)

                        sale_total += line_total
                        sale_discount += line_disc
                        co_day_units += realized_qty
                        co_day_unconstrained += unconstrained_qty

                        if sale_status == "completed":
                            co_day_cogs += round(realized_qty * prod["cost_price"], 2)
                            # Deduct from stock tracker
                            if chosen_wh:
                                key = (pid, chosen_wh)
                                stock_tracker[key] = max(0, stock_tracker.get(key, 0) - realized_qty)
                                stock_movements.append({
                                    "id": self.uid(),
                                    "product_id": pid,
                                    "warehouse_id": chosen_wh,
                                    "movement_type": "out",
                                    "quantity": realized_qty,
                                    "reason": "sale",
                                    "reference_id": sale_id,
                                    "moved_at": self.format_dt(current_date),
                                })

                        sale_items_batch.append({
                            "id": self.uid(),
                            "sale_id": sale_id,
                            "product_id": pid,
                            "quantity": realized_qty,
                            "unit_price": unit_price,
                            "discount_pct": disc_pct,
                            "line_total": line_total,
                            "unconstrained_demand": unconstrained_qty,
                            "stockout_flag": is_stockout,
                        })

                    sale_total = round(sale_total, 2)
                    sale_discount = round(sale_discount, 2)
                    # Indian GST tax rate: 18% standard retail GST
                    tax_rate = 0.18
                    tax_amount = round(sale_total * tax_rate, 2)
                    net_amount = round(sale_total + tax_amount, 2)

                    if sale_status == "completed":
                        pay_status = self.rng.choices(["paid", "partial", "unpaid"], weights=[0.78, 0.16, 0.06])[0]
                        co_day_revenue += net_amount
                    else:
                        pay_status = "unpaid"

                    sales_records.append({
                        "id": sale_id,
                        "company_id": cid,
                        "branch_id": branch_id,
                        "customer_id": cust_id,
                        "user_id": sales_user_id,
                        "sale_date": str(current_date),
                        "status": sale_status,
                        "total_amount": sale_total,
                        "discount_amount": sale_discount,
                        "tax_amount": tax_amount,
                        "net_amount": net_amount,
                        "payment_status": pay_status,
                        "is_anomaly": is_sale_anom,
                        "has_stockout": has_stockout_flag,
                        "created_at": self.format_dt(current_date),
                    })

                    sale_items_records.extend(sale_items_batch)

                    # Generate 1:1 matching Invoice
                    due_days = self.rng.choice([15, 30, 45, 60])
                    due_date = min(current_date + timedelta(days=due_days), self.end_date)
                    inv_status = "cancelled" if sale_status == "cancelled" else (
                        "paid" if pay_status == "paid" else ("partial" if pay_status == "partial" else "overdue")
                    )
                    paid_amt = net_amount if pay_status == "paid" else (
                        round(net_amount * self.rng.uniform(0.35, 0.70), 2) if pay_status == "partial" else 0.0
                    )

                    invoices_records.append({
                        "id": self.uid(),
                        "company_id": cid,
                        "invoice_type": "receivable",
                        "sale_id": sale_id,
                        "customer_id": cust_id,
                        "invoice_number": f"INV-{invoice_counter:07d}",
                        "invoice_date": str(current_date),
                        "due_date": str(due_date),
                        "total_amount": net_amount,
                        "paid_amount": paid_amt,
                        "status": inv_status,
                        "created_at": self.format_dt(current_date),
                    })
                    invoice_counter += 1

                    # Payments for paid/partial sales
                    if pay_status in ("paid", "partial"):
                        p_method = self.rng.choice(PAYMENT_METHODS)
                        pay_delay = self.rng.randint(0, 10)
                        pay_date = min(current_date + timedelta(days=pay_delay), self.end_date)
                        payments_records.append({
                            "id": self.uid(),
                            "company_id": cid,
                            "reference_type": "sale",
                            "reference_id": sale_id,
                            "amount": paid_amt,
                            "payment_method": p_method,
                            "payment_date": str(pay_date),
                            "created_at": self.format_dt(pay_date),
                        })

                # Check low-stock replenishment & trigger purchase orders (O(1) in-memory)
                low_stock_skus = sum(
                    1 for k in co_stock_keys[cid]
                    if stock_tracker[k] <= reorder_info[k]["reorder_level"]
                )

                # Daily KPI compilation
                day_expenses = round(today_approved_expenses[cid], 2)
                gross_profit = round(co_day_revenue - co_day_cogs, 2)
                net_profit = round(gross_profit - day_expenses, 2)

                daily_kpi_records.append({
                    "company_id": cid,
                    "date": str(current_date),
                    "revenue": round(co_day_revenue, 2),
                    "cogs": round(co_day_cogs, 2),
                    "gross_profit": gross_profit,
                    "operating_expenses": round(day_expenses, 2),
                    "net_profit": net_profit,
                    "order_count": daily_sales_count,
                    "units_sold": co_day_units,
                    "unconstrained_demand_units": co_day_unconstrained,
                    "stockout_count": co_day_stockouts,
                    "low_stock_skus": low_stock_skus,
                    "is_anomaly": co_day_anomalies,
                })

            # --- Periodic Supplier Restocking Purchases (~2.6 purchases per day platform-wide) ---
            n_purchases_today = self.rng.choices([2, 3, 4], weights=[0.45, 0.45, 0.10])[0]
            for _ in range(n_purchases_today):
                p_cid = self.rng.choice(list(companies_df["id"]))
                p_branch = self.rng.choice(branch_map[p_cid])
                p_sup = self.rng.choice(supplier_map[p_cid])
                p_user = self.rng.choice(user_map[p_cid])
                p_status = self.rng.choices(["received", "pending", "cancelled"], weights=[0.82, 0.14, 0.04])[0]
                p_id = self.uid()

                p_prods = prods_by_co[p_cid]
                n_p_items = self.rng.choices([1, 2, 3, 4], weights=[0.30, 0.35, 0.25, 0.10])[0]
                chosen_p_prods = self.rng.sample(p_prods, min(n_p_items, len(p_prods)))

                p_total = 0.0
                delivery_items = []
                p_items_batch = []

                for prod in chosen_p_prods:
                    p_qty = self.rng.randint(25, 120)
                    u_cost = round(prod["cost_price"] * self.rng.uniform(0.94, 1.02), 2)
                    p_line = round(p_qty * u_cost, 2)
                    p_total += p_line

                    p_items_batch.append({
                        "id": self.uid(),
                        "purchase_id": p_id,
                        "product_id": prod["id"],
                        "quantity": p_qty,
                        "unit_cost": u_cost,
                        "line_total": p_line,
                    })

                    if p_status == "received":
                        wh_candidates = prod_wh_list.get(prod["id"], [])
                        dest_wh = self.rng.choice(wh_candidates) if wh_candidates else None
                        if dest_wh:
                            delivery_items.append((prod["id"], dest_wh, p_qty))

                p_total = round(p_total, 2)
                p_tax = round(p_total * 0.05, 2)  # 5% purchase input tax
                p_net = round(p_total + p_tax, 2)
                p_pay_status = "unpaid" if p_status == "cancelled" else self.rng.choices(["paid", "partial", "unpaid"], weights=[0.72, 0.20, 0.08])[0]

                purchases_records.append({
                    "id": p_id,
                    "company_id": p_cid,
                    "branch_id": p_branch,
                    "supplier_id": p_sup,
                    "user_id": p_user,
                    "purchase_date": str(current_date),
                    "status": p_status,
                    "total_amount": p_total,
                    "tax_amount": p_tax,
                    "net_amount": p_net,
                    "payment_status": p_pay_status,
                    "created_at": self.format_dt(current_date),
                })
                purchase_items_records.extend(p_items_batch)

                # Schedule delivery with lead time of 1-3 days
                if p_status == "received" and delivery_items:
                    lead_time = self.rng.randint(1, 3)
                    arrival = min(current_date + timedelta(days=lead_time), self.end_date)
                    pending_deliveries.append({
                        "arrival_date": arrival,
                        "purchase_id": p_id,
                        "items": delivery_items,
                    })

                # Purchase payment
                if p_pay_status in ("paid", "partial"):
                    pay_amt = p_net if p_pay_status == "paid" else round(p_net * self.rng.uniform(0.35, 0.65), 2)
                    p_pay_delay = self.rng.randint(5, 30)
                    p_pay_date = min(current_date + timedelta(days=p_pay_delay), self.end_date)
                    payments_records.append({
                        "id": self.uid(),
                        "company_id": p_cid,
                        "reference_type": "purchase",
                        "reference_id": p_id,
                        "amount": pay_amt,
                        "payment_method": self.rng.choice(PAYMENT_METHODS),
                        "payment_date": str(p_pay_date),
                        "created_at": self.format_dt(p_pay_date),
                    })

        # Occasional stock adjustments / damaged goods / inventory audits
        all_wh_ids = list(warehouses_df["id"])
        all_prod_ids = list(products_df["id"])
        adj_reasons = ["adjustment", "return", "transfer", "write_off"]
        for _ in range(500):
            pid = self.rng.choice(all_prod_ids)
            wh_list = prod_wh_list.get(pid) or [self.rng.choice(all_wh_ids)]
            m_date = self.start_date + timedelta(days=self.rng.randint(0, total_days - 1))
            stock_movements.append({
                "id": self.uid(),
                "product_id": pid,
                "warehouse_id": self.rng.choice(wh_list),
                "movement_type": self.rng.choice(["in", "out"]),
                "quantity": self.rng.randint(1, 40),
                "reason": self.rng.choice(adj_reasons),
                "reference_id": None,
                "moved_at": self.format_dt(m_date),
            })

        # Final updated inventory snapshot at 2024-12-31
        inventory_final_rows = []
        for _, init_row in inventory_initial_df.iterrows():
            key = (init_row["product_id"], init_row["warehouse_id"])
            current_q = max(0, stock_tracker.get(key, int(init_row["quantity_on_hand"])))
            inventory_final_rows.append({
                "id": init_row["id"],
                "product_id": init_row["product_id"],
                "warehouse_id": init_row["warehouse_id"],
                "quantity_on_hand": current_q,
                "reorder_level": init_row["reorder_level"],
                "reorder_quantity": init_row["reorder_quantity"],
                "updated_at": f"{self.end_date}T23:59:59",
            })

        return (
            pd.DataFrame(sales_records),
            pd.DataFrame(sale_items_records),
            pd.DataFrame(purchases_records),
            pd.DataFrame(purchase_items_records),
            pd.DataFrame(stock_movements),
            pd.DataFrame(invoices_records),
            pd.DataFrame(payments_records),
            pd.DataFrame(expenses_records),
            pd.DataFrame(inventory_final_rows),
            pd.DataFrame(daily_kpi_records),
        )


# ---------------------------------------------------------------------------
# Main Routine
# ---------------------------------------------------------------------------

def save_csv(df: pd.DataFrame, filename: str) -> None:
    path = os.path.join(OUTPUT_DIR, filename)
    df.to_csv(path, index=False, encoding="utf-8")
    print(f"  [OK] {filename:<32s} {len(df):>8,} rows  x  {len(df.columns):>2} cols")


def main():
    parser = argparse.ArgumentParser(description="ALLADIN Synthetic Retail Dataset Generator")
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED, help="Random seed for reproducibility")
    parser.add_argument("--start-date", type=str, default="2022-01-01", help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end-date", type=str, default=DEFAULT_END.isoformat(), help="End date (YYYY-MM-DD)")
    args = parser.parse_args()

    start_d = date.fromisoformat(args.start_date)
    end_d = date.fromisoformat(args.end_date)

    print()
    print("=" * 68)
    print("  ALLADIN Synthetic Retail Dataset Generator (Approach C)")
    print(f"  Indian Supermarket & Retail Environment -- Continuous to {end_d}")
    print("=" * 68)
    print(f"  Random Seed : {args.seed}")
    print(f"  Date Range  : {start_d} to {end_d} ({(end_d - start_d).days + 1} days)")
    print(f"  Output Dir  : {OUTPUT_DIR}")
    print()

    gen = RetailDataGenerator(seed=args.seed, start_date=start_d, end_date=end_d)

    print("[1/4] Generating business profiles, locations, users, and catalog...")
    companies_df = gen.build_companies()
    save_csv(companies_df, "companies.csv")

    branches_df = gen.build_branches(companies_df)
    save_csv(branches_df, "branches.csv")

    users_df = gen.build_users(companies_df, branches_df)
    save_csv(users_df, "users.csv")

    customers_df = gen.build_customers(companies_df, n_per_company=170)
    save_csv(customers_df, "customers.csv")

    suppliers_df = gen.build_suppliers(companies_df, n_per_company=17)
    save_csv(suppliers_df, "suppliers.csv")

    categories_df = gen.build_categories(companies_df)
    save_csv(categories_df, "categories.csv")

    products_df = gen.build_products(companies_df, categories_df)
    save_csv(products_df, "products.csv")

    warehouses_df = gen.build_warehouses(companies_df, branches_df)
    save_csv(warehouses_df, "warehouses.csv")

    inventory_initial_df = gen.build_inventory_initial(products_df, warehouses_df)

    print()
    print(f"[2/4] Simulating {(end_d - start_d).days + 1} consecutive days of retail transactions...")
    (
        sales_df,
        sale_items_df,
        purchases_df,
        purchase_items_df,
        stock_movements_df,
        invoices_df,
        payments_df,
        expenses_df,
        inventory_final_df,
        daily_kpi_df,
    ) = gen.simulate_operations(
        companies_df,
        branches_df,
        users_df,
        customers_df,
        suppliers_df,
        products_df,
        warehouses_df,
        inventory_initial_df,
        categories_df=categories_df,
    )

    print()
    print("[3/4] Writing transactional, ledger, and KPI summary CSV files...")
    save_csv(sales_df, "sales.csv")
    save_csv(sale_items_df, "sale_items.csv")
    save_csv(purchases_df, "purchases.csv")
    save_csv(purchase_items_df, "purchase_items.csv")
    save_csv(stock_movements_df, "stock_movements.csv")
    save_csv(invoices_df, "invoices.csv")
    save_csv(payments_df, "payments.csv")
    save_csv(expenses_df, "expenses.csv")
    save_csv(inventory_final_df, "inventory.csv")
    save_csv(daily_kpi_df, "daily_kpi_summary.csv")

    print()
    print("[4/4] Dataset generation complete.")
    total_records = (
        len(companies_df) + len(branches_df) + len(users_df) + len(customers_df) +
        len(suppliers_df) + len(categories_df) + len(products_df) + len(warehouses_df) +
        len(sales_df) + len(sale_items_df) + len(purchases_df) + len(purchase_items_df) +
        len(stock_movements_df) + len(invoices_df) + len(payments_df) + len(expenses_df) +
        len(inventory_final_df) + len(daily_kpi_df)
    )
    print(f"  Total records generated across 18 files: {total_records:,}")
    print()


if __name__ == "__main__":
    main()
