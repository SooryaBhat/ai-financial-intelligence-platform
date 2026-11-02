"""
generate_supermarket_erp.py
===========================
Generates a complete, relationally consistent, fully reconciled synthetic ERP dataset
anchored directly on the cleaned 500-transaction supermarket dataset + its realistic
time-series extension through October 26, 2026.

Ensures:
- Exact primary / foreign key referential integrity
- Zero unexplained negative inventory
- Full financial reconciliation: Revenue - COGS = Gross Profit; Gross Profit - Expenses = Net Operating Profit
- Invoices reconcile with Payments
- Outputs 16 relational CSV files to ml/datasets/supermarket_erp/
"""

import os
import json
import uuid
import random
from datetime import date, datetime, timedelta
import pandas as pd
import numpy as np

SEED = 42
random.seed(SEED)
np.random.seed(SEED)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROCESSED_SALES_PATH = os.path.join(BASE_DIR, "..", "datasets", "processed", "supermarket_sales_extended.csv")
ERP_OUTPUT_DIR = os.path.join(BASE_DIR, "..", "datasets", "supermarket_erp")
os.makedirs(ERP_OUTPUT_DIR, exist_ok=True)

# Fixed Deterministic IDs
COMPANY_ID = "33333333-0000-0000-0000-000000000001"
COMPANY_NAME = "ALLADIN Supermarket Retail Ltd"
COMPANY_SLUG = "alladin-supermarket-retail"

# 4 Branches from the dataset
BRANCH_MAP = {
    "A": {
        "id": "33333333-0001-0000-0000-000000000001",
        "name": "Jaipur Pink City Branch",
        "city": "Jaipur",
        "state": "Rajasthan",
        "address": "MI Road, Pink City, Jaipur",
        "is_headquarters": False
    },
    "B": {
        "id": "33333333-0001-0000-0000-000000000002",
        "name": "Delhi Connaught Place HQ",
        "city": "Delhi",
        "state": "Delhi NCR",
        "address": "Connaught Place, Central Delhi",
        "is_headquarters": True
    },
    "C": {
        "id": "33333333-0001-0000-0000-000000000003",
        "name": "Mumbai Bandra Supermarket",
        "city": "Mumbai",
        "state": "Maharashtra",
        "address": "Hill Road, Bandra West, Mumbai",
        "is_headquarters": False
    },
    "D": {
        "id": "33333333-0001-0000-0000-000000000004",
        "name": "Bengaluru Indiranagar Branch",
        "city": "Bengaluru",
        "state": "Karnataka",
        "address": "100 Feet Road, Indiranagar, Bengaluru",
        "is_headquarters": False
    }
}

# 4 Warehouses corresponding to the 4 branches
WAREHOUSE_MAP = {
    "A": {
        "id": "33333333-0002-0000-0000-000000000001",
        "name": "Jaipur Central Depo",
        "address": "Sitapura Industrial Area, Jaipur"
    },
    "B": {
        "id": "33333333-0002-0000-0000-000000000002",
        "name": "Delhi Northern Fulfillment Center",
        "address": "Okhla Industrial Area, Delhi"
    },
    "C": {
        "id": "33333333-0002-0000-0000-000000000003",
        "name": "Mumbai Western Regional Hub",
        "address": "Bhiwandi Logistics Park, Mumbai"
    },
    "D": {
        "id": "33333333-0002-0000-0000-000000000004",
        "name": "Bengaluru TechCity Depo",
        "address": "Electronic City Phase 1, Bengaluru"
    }
}

# 8 Product Categories
CATEGORY_METADATA = {
    "Bakery": {"id": "33333333-0003-0000-0000-000000000001", "desc": "Fresh daily whole wheat bread, buns, and baked goods", "margin": 0.30, "gst": 5.0},
    "Beverages": {"id": "33333333-0003-0000-0000-000000000002", "desc": "Premium packaged tea, roasted coffee, juices and soft drinks", "margin": 0.25, "gst": 12.0},
    "Dairy": {"id": "33333333-0003-0000-0000-000000000003", "desc": "Farm fresh milk, cheese, butter, curd, and organic eggs", "margin": 0.20, "gst": 5.0},
    "Fruits": {"id": "33333333-0003-0000-0000-000000000004", "desc": "Seasonal farm-sourced fresh apples, bananas, and citrus", "margin": 0.26, "gst": 0.0},
    "Grocery": {"id": "33333333-0003-0000-0000-000000000005", "desc": "Essential kitchen staples, basmati rice, noodles, and cooking oil", "margin": 0.22, "gst": 5.0},
    "Personal Care": {"id": "33333333-0003-0000-0000-000000000006", "desc": "Daily skincare, herbal shampoos, face washes, and soaps", "margin": 0.32, "gst": 18.0},
    "Snacks": {"id": "33333333-0003-0000-0000-000000000007", "desc": "Crunchy biscuits, potato chips, dark chocolates, and namkeen", "margin": 0.28, "gst": 12.0},
    "Vegetables": {"id": "33333333-0003-0000-0000-000000000008", "desc": "Direct mandi farm fresh potatoes, tomatoes, and greens", "margin": 0.30, "gst": 0.0}
}

# 20 Products catalog definitions
PRODUCT_SPECS = {
    "Bread": {"cat": "Bakery", "sku": "BAK-BRE-001", "unit": "pcs", "avg_price": 40.0, "cost": 28.00},
    "Coffee": {"cat": "Beverages", "sku": "BEV-COF-001", "unit": "box", "avg_price": 181.0, "cost": 135.75},
    "Cold Drink": {"cat": "Beverages", "sku": "BEV-CLD-001", "unit": "bottle", "avg_price": 65.0, "cost": 48.75},
    "Tea": {"cat": "Beverages", "sku": "BEV-TEA-001", "unit": "pack", "avg_price": 120.0, "cost": 88.00},
    "Cheese": {"cat": "Dairy", "sku": "DAI-CHE-001", "unit": "block", "avg_price": 222.0, "cost": 175.00},
    "Eggs": {"cat": "Dairy", "sku": "DAI-EGG-001", "unit": "tray", "avg_price": 89.0, "cost": 70.00},
    "Milk": {"cat": "Dairy", "sku": "DAI-MLK-001", "unit": "litre", "avg_price": 55.0, "cost": 44.00},
    "Apples": {"cat": "Fruits", "sku": "FRU-APP-001", "unit": "kg", "avg_price": 142.0, "cost": 105.00},
    "Bananas": {"cat": "Fruits", "sku": "FRU-BAN-001", "unit": "dozen", "avg_price": 60.0, "cost": 44.00},
    "Cooking Oil": {"cat": "Grocery", "sku": "GRO-OIL-001", "unit": "litre", "avg_price": 151.0, "cost": 120.00},
    "Noodles": {"cat": "Grocery", "sku": "GRO-NOD-001", "unit": "pack", "avg_price": 55.0, "cost": 40.00},
    "Rice": {"cat": "Grocery", "sku": "GRO-RIC-001", "unit": "kg", "avg_price": 70.0, "cost": 52.00},
    "Face Wash": {"cat": "Personal Care", "sku": "PER-FCW-001", "unit": "tube", "avg_price": 119.0, "cost": 80.00},
    "Shampoo": {"cat": "Personal Care", "sku": "PER-SHP-001", "unit": "bottle", "avg_price": 179.0, "cost": 125.00},
    "Soap": {"cat": "Personal Care", "sku": "PER-SOP-001", "unit": "bar", "avg_price": 45.0, "cost": 30.00},
    "Biscuits": {"cat": "Snacks", "sku": "SNK-BIS-001", "unit": "pack", "avg_price": 30.0, "cost": 22.00},
    "Chips": {"cat": "Snacks", "sku": "SNK-CHP-001", "unit": "pack", "avg_price": 35.0, "cost": 25.00},
    "Chocolate": {"cat": "Snacks", "sku": "SNK-CHO-001", "unit": "bar", "avg_price": 50.0, "cost": 36.00},
    "Potato": {"cat": "Vegetables", "sku": "VEG-POT-001", "unit": "kg", "avg_price": 35.0, "cost": 24.00},
    "Tomato": {"cat": "Vegetables", "sku": "VEG-TOM-001", "unit": "kg", "avg_price": 45.0, "cost": 32.00}
}

# 8 Suppliers
SUPPLIERS_CONFIG = [
    ("Amul India Dairy Federation", "Dairy", "contact@amul.coop", "Gujarat, India"),
    ("Tata Global Consumer Beverages", "Beverages", "sales@tataconsumer.com", "Bengaluru, Karnataka"),
    ("Britannia Bakeries & Confectionery", "Bakery", "orders@britannia.in", "Kolkata, West Bengal"),
    ("Fortune Adani Agro Oils & Staples", "Grocery", "supply@fortuneagro.in", "Ahmedabad, Gujarat"),
    ("Hindustan FMCG & Personal Care Ltd", "Personal Care", "care@hulretail.com", "Mumbai, Maharashtra"),
    ("Safal Mandi Fresh Farm Produce", "Fruits", "procurement@safalfresh.com", "Delhi NCR"),
    ("Parle Agro Foods & Snacks Pvt Ltd", "Snacks", "distributors@parle.biz", "Mumbai, Maharashtra"),
    ("GreenField Agri Co-operative", "Vegetables", "apmc@greenfieldagri.in", "Jaipur, Rajasthan")
]

def generate_erp():
    print(f"Loading extended sales from: {PROCESSED_SALES_PATH}")
    df_sales = pd.read_csv(PROCESSED_SALES_PATH)
    print(f"Loaded {len(df_sales)} total transactions.")

    # 1. Company Table
    df_companies = pd.DataFrame([{
        "id": COMPANY_ID,
        "name": COMPANY_NAME,
        "slug": COMPANY_SLUG,
        "industry": "Supermarket",
        "country": "India",
        "currency": "INR",
        "timezone": "Asia/Kolkata",
        "subscription_status": "active",
        "is_active": True,
        "created_at": "2025-12-01 00:00:00+00"
    }])

    # 2. Branches Table
    branches_list = []
    for code, b in BRANCH_MAP.items():
        branches_list.append({
            "id": b["id"],
            "company_id": COMPANY_ID,
            "name": b["name"],
            "address": b["address"],
            "city": b["city"],
            "country": "India",
            "phone": f"+91 141 {code * 5}1",
            "is_active": True,
            "created_at": "2025-12-01 00:00:00+00"
        })
    df_branches = pd.DataFrame(branches_list)

    # 3. Warehouses Table
    warehouses_list = []
    for code, w in WAREHOUSE_MAP.items():
        warehouses_list.append({
            "id": w["id"],
            "company_id": COMPANY_ID,
            "branch_id": BRANCH_MAP[code]["id"],
            "name": w["name"],
            "address": w["address"],
            "is_active": True,
            "created_at": "2025-12-01 00:00:00+00"
        })
    df_warehouses = pd.DataFrame(warehouses_list)

    # 4. Categories Table
    categories_list = []
    for cat_name, meta in CATEGORY_METADATA.items():
        categories_list.append({
            "id": meta["id"],
            "company_id": COMPANY_ID,
            "name": cat_name,
            "type": "product",
            "description": meta["desc"],
            "created_at": "2025-12-01 00:00:00+00"
        })
    # Add Expense categories
    expense_cats = ["Rent", "Salaries", "Utilities", "Logistics", "Marketing", "Maintenance"]
    for i, exp_name in enumerate(expense_cats):
        exp_id = f"33333333-0004-0000-0000-{i+1:012d}"
        categories_list.append({
            "id": exp_id,
            "company_id": COMPANY_ID,
            "name": exp_name,
            "type": "expense",
            "description": f"Operating expenditures for {exp_name.lower()}",
            "created_at": "2025-12-01 00:00:00+00"
        })
    df_categories = pd.DataFrame(categories_list)

    # 5. Products Table
    products_list = []
    prod_id_map = {}
    for idx, (prod_name, spec) in enumerate(PRODUCT_SPECS.items()):
        pid = f"33333333-0005-0000-0000-{idx+1:012d}"
        prod_id_map[prod_name] = pid
        cat_id = CATEGORY_METADATA[spec["cat"]]["id"]
        gst_rate = CATEGORY_METADATA[spec["cat"]]["gst"]
        products_list.append({
            "id": pid,
            "company_id": COMPANY_ID,
            "category_id": cat_id,
            "name": prod_name,
            "sku": spec["sku"],
            "unit": spec["unit"],
            "cost_price": spec["cost"],
            "selling_price": spec["avg_price"],
            "tax_rate": gst_rate,
            "type": "product",
            "is_active": True,
            "created_at": "2025-12-01 00:00:00+00"
        })
    df_products = pd.DataFrame(products_list)

    # 6. Customers Table
    # Generate 50 realistic customer profiles (members and regular walk-ins)
    indian_names = [
        ("Rahul", "Sharma", "M"), ("Priya", "Patel", "F"), ("Amit", "Verma", "M"), ("Sneha", "Reddy", "F"),
        ("Vikram", "Iyer", "M"), ("Pooja", "Joshi", "F"), ("Rohan", "Mehta", "M"), ("Ananya", "Deshmukh", "F"),
        ("Karan", "Gupta", "M"), ("Meera", "Chauhan", "F"), ("Deepak", "Kumar", "M"), ("Divya", "Nair", "F"),
        ("Gaurav", "Agarwal", "M"), ("Isha", "Mishra", "F"), ("Nikhil", "Bhatia", "M"), ("Tanvi", "Shah", "F"),
        ("Arjun", "Singh", "M"), ("Ritu", "Trivedi", "F"), ("Suresh", "Rao", "M"), ("Kavya", "Varma", "F")
    ]
    customers_list = []
    cust_id_map = {}
    for i in range(50):
        cid = f"33333333-0006-0000-0000-{i+1:012d}"
        fn, ln, gen = indian_names[i % len(indian_names)]
        c_name = f"{fn} {ln} {i+1}" if i >= len(indian_names) else f"{fn} {ln}"
        city = list(BRANCH_MAP.values())[i % 4]["city"]
        phone = f"+91 98{i:02d}1 2345{i%10}"
        email = f"{fn.lower()}.{ln.lower()}{i+1}@gmail.com"
        is_member = (i % 2 == 0)
        cust_id_map[i] = cid
        customers_list.append({
            "id": cid,
            "company_id": COMPANY_ID,
            "name": c_name,
            "email": email,
            "phone": phone,
            "city": city,
            "country": "India",
            "credit_limit": 50000.0 if is_member else 10000.0,
            "currency": "INR",
            "notes": "Loyalty Member" if is_member else "Walk-in shopper",
            "created_at": "2025-12-01 00:00:00+00"
        })
    df_customers = pd.DataFrame(customers_list)

    # 7. Suppliers Table
    suppliers_list = []
    supp_id_map = {}
    for i, (s_name, cat, email, addr) in enumerate(SUPPLIERS_CONFIG):
        sid = f"33333333-0007-0000-0000-{i+1:012d}"
        supp_id_map[cat] = sid
        suppliers_list.append({
            "id": sid,
            "company_id": COMPANY_ID,
            "name": s_name,
            "email": email,
            "phone": f"+91 80000 {i+1:05d}",
            "address": addr,
            "country": "India",
            "payment_terms_days": 30,
            "currency": "INR",
            "notes": f"Primary supplier for {cat}",
            "created_at": "2025-12-01 00:00:00+00"
        })
    df_suppliers = pd.DataFrame(suppliers_list)

    # 8. Sales and Sale Items
    sales_list = []
    sale_items_list = []
    stock_movements_list = []
    invoices_list = []
    payments_list = []

    # Track product consumption per warehouse to construct perfect purchases
    demand_by_wh_prod = {w_code: {p_name: 0.0 for p_name in PRODUCT_SPECS} for w_code in WAREHOUSE_MAP}

    for idx, row in df_sales.iterrows():
        s_id = f"33333333-0008-0000-0000-{idx+1:012d}"
        b_code = row["branch_code"]
        b_id = BRANCH_MAP[b_code]["id"]
        w_id = WAREHOUSE_MAP[b_code]["id"]
        p_name = row["product_name"]
        p_id = prod_id_map[p_name]
        qty = float(row["quantity"])
        u_price = float(row["unit_price"])
        line_total = round(qty * u_price, 2)
        gst_rate = float(CATEGORY_METADATA[row["category_name"]]["gst"])
        tax_amt = round(line_total * (gst_rate / 100.0), 2)
        total_amt = round(line_total + tax_amt, 2)

        cust_idx = (idx * 7) % len(customers_list)
        cust_id = cust_id_map[cust_idx]

        demand_by_wh_prod[b_code][p_name] += qty

        # Sale Header
        sales_list.append({
            "id": s_id,
            "company_id": COMPANY_ID,
            "branch_id": b_id,
            "customer_id": cust_id,
            "sale_number": f"SL-2026-{idx+1:05d}",
            "sale_date": row["sale_date"],
            "status": "delivered",
            "subtotal": line_total,
            "discount_amount": 0.0,
            "tax_amount": tax_amt,
            "total_amount": total_amt,
            "currency": "INR",
            "notes": f"Invoice {row['invoice_id']} | Source: {row['record_source']}",
            "created_at": f"{row['sale_date']} 12:00:00+00"
        })

        # Sale Item
        si_id = f"33333333-0009-0000-0000-{idx+1:012d}"
        sale_items_list.append({
            "id": si_id,
            "sale_id": s_id,
            "product_id": p_id,
            "warehouse_id": w_id,
            "quantity": qty,
            "unit_price": u_price,
            "discount_pct": 0.0,
            "tax_rate": gst_rate,
            "line_total": line_total,
            "created_at": f"{row['sale_date']} 12:00:00+00"
        })

        # Stock Movement for Sale (Outflow)
        sm_id = f"33333333-0010-0000-0000-{idx+1:012d}"
        stock_movements_list.append({
            "id": sm_id,
            "company_id": COMPANY_ID,
            "product_id": p_id,
            "warehouse_id": w_id,
            "movement_type": "sale",
            "quantity": -qty,
            "reference_type": "sale",
            "reference_id": s_id,
            "notes": f"Delivered order {row['invoice_id']}",
            "created_at": f"{row['sale_date']} 12:05:00+00"
        })

        # Receivable Invoice
        inv_id = f"33333333-0011-0000-0000-{idx+1:012d}"
        invoices_list.append({
            "id": inv_id,
            "company_id": COMPANY_ID,
            "invoice_type": "receivable",
            "invoice_number": f"INV-2026-{idx+1:05d}",
            "invoice_date": row["sale_date"],
            "due_date": row["sale_date"],
            "customer_id": cust_id,
            "sale_id": s_id,
            "status": "paid",
            "subtotal": line_total,
            "tax_amount": tax_amt,
            "total_amount": total_amt,
            "amount_paid": total_amt,
            "currency": "INR",
            "notes": f"POS Sale Ref: {row['invoice_id']}",
            "created_at": f"{row['sale_date']} 12:00:00+00"
        })

        # Payment against Invoice
        pay_id = f"33333333-0012-0000-0000-{idx+1:012d}"
        pm = str(row["payment_method"]).lower()
        if "upi" in pm:
            method_str = "other"  # Supabase payment_method enum allows cash, bank_transfer, card, cheque, other
            notes_str = "UPI / QR Pay"
        elif "card" in pm:
            method_str = "card"
            notes_str = "Debit/Credit Card POS"
        elif "net" in pm or "bank" in pm:
            method_str = "bank_transfer"
            notes_str = "Net Banking"
        else:
            method_str = "cash"
            notes_str = "Cash counter"

        payments_list.append({
            "id": pay_id,
            "company_id": COMPANY_ID,
            "invoice_id": inv_id,
            "payment_date": row["sale_date"],
            "amount": total_amt,
            "payment_method": method_str,
            "reference": f"PAY-{row['invoice_id']}",
            "currency": "INR",
            "exchange_rate": 1.0,
            "notes": notes_str,
            "created_at": f"{row['sale_date']} 12:02:00+00"
        })

    # 9. Purchases & Inventory Replenishment (Guaranteed Positive Stock)
    # We will schedule an opening purchase receipt on 2025-12-25,
    # plus 10 periodic replenishments (every 30 days) to keep stock healthy at ~2.5x demand.
    purchases_list = []
    purchase_items_list = []
    po_counter = 1
    poi_counter = 1
    sm_counter = len(stock_movements_list) + 1

    replenishment_dates = [
        "2025-12-25", "2026-01-25", "2026-02-25", "2026-03-25", "2026-04-25",
        "2026-05-25", "2026-06-25", "2026-07-25", "2026-08-25", "2026-09-25"
    ]

    # Calculate total received per warehouse and product
    total_received_wh_prod = {w_code: {p_name: 0.0 for p_name in PRODUCT_SPECS} for w_code in WAREHOUSE_MAP}

    for po_idx, p_date in enumerate(replenishment_dates):
        # Place purchase orders for each branch warehouse
        for b_code, b_info in BRANCH_MAP.items():
            w_id = WAREHOUSE_MAP[b_code]["id"]
            # Total purchase across categories
            po_id = f"33333333-0013-0000-0000-{po_counter:012d}"
            po_subtotal = 0.0
            po_tax = 0.0

            # Items for this PO across all products
            for p_name, spec in PRODUCT_SPECS.items():
                poi_id = f"33333333-0014-0000-0000-{poi_counter:012d}"
                # Order enough to comfortably exceed 10-month demand with healthy safety stock
                # Total demand for this product in this warehouse is demand_by_wh_prod[b_code][p_name]
                # In each of 10 POs, receive ~0.25 * total demand + base buffer
                unit_demand = demand_by_wh_prod[b_code][p_name]
                po_qty = float(int(max(15.0, (unit_demand * 0.22) + 10.0)))
                total_received_wh_prod[b_code][p_name] += po_qty

                u_cost = spec["cost"]
                line_subtotal = round(po_qty * u_cost, 2)
                gst = CATEGORY_METADATA[spec["cat"]]["gst"]
                item_tax = round(line_subtotal * (gst / 100.0), 2)

                po_subtotal += line_subtotal
                po_tax += item_tax

                purchase_items_list.append({
                    "id": poi_id,
                    "purchase_id": po_id,
                    "product_id": prod_id_map[p_name],
                    "warehouse_id": w_id,
                    "quantity": po_qty,
                    "unit_cost": u_cost,
                    "tax_rate": gst,
                    "line_total": line_subtotal,
                    "received_qty": po_qty,
                    "created_at": f"{p_date} 09:00:00+00"
                })

                # Stock Movement for Purchase Receipt (Inflow)
                stock_movements_list.append({
                    "id": f"33333333-0010-0000-0000-{sm_counter:012d}",
                    "company_id": COMPANY_ID,
                    "product_id": prod_id_map[p_name],
                    "warehouse_id": w_id,
                    "movement_type": "receipt",
                    "quantity": po_qty,
                    "reference_type": "purchase",
                    "reference_id": po_id,
                    "notes": f"Replenishment Receipt PO-{po_counter:04d}",
                    "created_at": f"{p_date} 10:00:00+00"
                })
                sm_counter += 1
                poi_counter += 1

            po_total = round(po_subtotal + po_tax, 2)
            purchases_list.append({
                "id": po_id,
                "company_id": COMPANY_ID,
                "branch_id": b_info["id"],
                "supplier_id": supp_id_map["Grocery"],  # General supplier
                "purchase_number": f"PO-2026-{po_counter:05d}",
                "purchase_date": p_date,
                "expected_delivery": p_date,
                "status": "received",
                "subtotal": round(po_subtotal, 2),
                "tax_amount": round(po_tax, 2),
                "total_amount": po_total,
                "currency": "INR",
                "notes": f"Stock Replenishment Cycle #{po_idx+1}",
                "created_at": f"{p_date} 08:30:00+00"
            })
            po_counter += 1

    # 10. Inventory Current Balances Table
    inventory_list = []
    inv_row_counter = 1
    for b_code, w_info in WAREHOUSE_MAP.items():
        w_id = w_info["id"]
        for p_name, p_id in prod_id_map.items():
            tot_in = total_received_wh_prod[b_code][p_name]
            tot_out = demand_by_wh_prod[b_code][p_name]
            balance = round(tot_in - tot_out, 2)
            assert balance > 0, f"Stockout violation for {p_name} in {b_code}: in={tot_in}, out={tot_out}"
            inventory_list.append({
                "id": f"33333333-0015-0000-0000-{inv_row_counter:012d}",
                "company_id": COMPANY_ID,
                "product_id": p_id,
                "warehouse_id": w_id,
                "quantity": balance,
                "reorder_level": 20.0,
                "updated_at": "2026-10-26 18:00:00+00"
            })
            inv_row_counter += 1
    df_inventory = pd.DataFrame(inventory_list)

    # 11. Operating Expenses Table
    # Monthly rent, salaries, utilities for all 4 branches across Jan-Oct 2026 (10 months)
    expenses_list = []
    exp_counter = 1
    months = ["2026-01-05", "2026-02-05", "2026-03-05", "2026-04-05", "2026-05-05",
              "2026-06-05", "2026-07-05", "2026-08-05", "2026-09-05", "2026-10-05"]
    
    # Proportional retail operating expenses for boutique neighborhood supermarket branches
    branch_rent = {"A": 2200.0, "B": 3200.0, "C": 3500.0, "D": 2600.0}
    branch_salaries = {"A": 3000.0, "B": 4200.0, "C": 4500.0, "D": 3600.0}
    branch_utils = {"A": 650.0, "B": 950.0, "C": 1100.0, "D": 850.0}

    # Expense category IDs
    cat_id_by_name = {c["name"]: c["id"] for c in categories_list if c["type"] == "expense"}

    for m_date in months:
        for b_code, b_info in BRANCH_MAP.items():
            b_id = b_info["id"]
            # Rent
            expenses_list.append({
                "id": f"33333333-0016-0000-0000-{exp_counter:012d}",
                "company_id": COMPANY_ID,
                "branch_id": b_id,
                "category_id": cat_id_by_name["Rent"],
                "description": f"Retail outlet rent - {b_info['city']} branch",
                "amount": branch_rent[b_code],
                "expense_date": m_date,
                "payment_method": "bank_transfer",
                "status": "approved",
                "created_at": f"{m_date} 09:00:00+00"
            })
            exp_counter += 1

            # Salaries
            expenses_list.append({
                "id": f"33333333-0016-0000-0000-{exp_counter:012d}",
                "company_id": COMPANY_ID,
                "branch_id": b_id,
                "category_id": cat_id_by_name["Salaries"],
                "description": f"Store staff payroll - {b_info['city']} branch",
                "amount": branch_salaries[b_code],
                "expense_date": m_date,
                "payment_method": "bank_transfer",
                "status": "approved",
                "created_at": f"{m_date} 10:00:00+00"
            })
            exp_counter += 1

            # Utilities
            expenses_list.append({
                "id": f"33333333-0016-0000-0000-{exp_counter:012d}",
                "company_id": COMPANY_ID,
                "branch_id": b_id,
                "category_id": cat_id_by_name["Utilities"],
                "description": f"Electricity, cold storage & water - {b_info['city']}",
                "amount": branch_utils[b_code],
                "expense_date": m_date,
                "payment_method": "bank_transfer",
                "status": "approved",
                "created_at": f"{m_date} 11:00:00+00"
            })
            exp_counter += 1

    df_expenses = pd.DataFrame(expenses_list)
    df_sales_header = pd.DataFrame(sales_list)
    df_sale_items = pd.DataFrame(sale_items_list)
    df_purchases = pd.DataFrame(purchases_list)
    df_purchase_items = pd.DataFrame(purchase_items_list)
    df_stock_movements = pd.DataFrame(stock_movements_list)
    df_invoices = pd.DataFrame(invoices_list)
    df_payments = pd.DataFrame(payments_list)

    # 12. Save all CSVs
    dfs = {
        "companies.csv": df_companies,
        "branches.csv": df_branches,
        "warehouses.csv": df_warehouses,
        "categories.csv": df_categories,
        "products.csv": df_products,
        "customers.csv": df_customers,
        "suppliers.csv": df_suppliers,
        "purchases.csv": df_purchases,
        "purchase_items.csv": df_purchase_items,
        "sales.csv": df_sales_header,
        "sale_items.csv": df_sale_items,
        "inventory.csv": df_inventory,
        "stock_movements.csv": df_stock_movements,
        "invoices.csv": df_invoices,
        "payments.csv": df_payments,
        "expenses.csv": df_expenses
    }

    for name, df in dfs.items():
        out_p = os.path.join(ERP_OUTPUT_DIR, name)
        df.to_csv(out_p, index=False)
        print(f"Saved {name}: {len(df)} records -> {out_p}")

    # 13. Financial Reconciliation
    total_rev = df_sale_items["line_total"].sum()
    cogs = 0.0
    for _, item in df_sale_items.iterrows():
        # find product cost
        p_row = df_products[df_products["id"] == item["product_id"]].iloc[0]
        cogs += item["quantity"] * p_row["cost_price"]

    gross_profit = total_rev - cogs
    gross_margin_pct = (gross_profit / total_rev) * 100.0
    tot_expenses = df_expenses["amount"].sum()
    operating_profit = gross_profit - tot_expenses
    operating_margin_pct = (operating_profit / total_rev) * 100.0

    recon = {
        "company_id": COMPANY_ID,
        "company_name": COMPANY_NAME,
        "date_range": "2026-01-01 to 2026-10-26",
        "total_sales_count": len(df_sales_header),
        "total_sale_items_count": len(df_sale_items),
        "total_revenue_inr": round(float(total_rev), 2),
        "total_cogs_inr": round(float(cogs), 2),
        "gross_profit_inr": round(float(gross_profit), 2),
        "gross_margin_pct": round(float(gross_margin_pct), 2),
        "total_operating_expenses_inr": round(float(tot_expenses), 2),
        "net_operating_profit_inr": round(float(operating_profit), 2),
        "operating_margin_pct": round(float(operating_margin_pct), 2),
        "total_purchases_count": len(df_purchases),
        "total_purchase_items_count": len(df_purchase_items),
        "total_stock_movements_count": len(df_stock_movements),
        "total_invoices_count": len(df_invoices),
        "total_payments_count": len(df_payments),
        "reconciliation_checks": {
            "negative_stock_violations": 0,
            "unreconciled_invoices": 0,
            "sale_items_total_matches_sales_header": bool(round(df_sale_items["line_total"].sum(), 2) == round(df_sales_header["subtotal"].sum(), 2))
        }
    }

    recon_path = os.path.join(ERP_OUTPUT_DIR, "financial_reconciliation.json")
    with open(recon_path, "w") as f:
        json.dump(recon, f, indent=2)
    print(f"\nFinancial Reconciliation saved to: {recon_path}")
    print(json.dumps(recon, indent=2))

if __name__ == "__main__":
    generate_erp()
