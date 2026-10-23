# Datasets — ALLADIN AI Financial Intelligence Platform

This directory contains datasets used by the Machine Learning module of the **ALLADIN — AI-Powered Financial Intelligence Platform**.

All datasets in this directory are **strictly synthetic** simulations designed for offline ML model training, benchmarking, evaluation, and pipeline development. They do **not** represent real business records or private individual data.

---

## Directory Structure

```text
ml/datasets/
├── raw/            # Source / reference data
├── processed/      # Cleaned, feature-engineered artifacts ready for pipeline training
├── synthetic/      # Synthetically generated retail ERP datasets (18 CSV files)
│   ├── generate_synthetic_data.py   # Deterministic dataset generator
│   ├── validate_synthetic_data.py   # Comprehensive validation suite
│   └── *.csv                        # Generated dataset tables
└── README.md       # Dataset documentation and pipeline mapping (this file)
```

---

## ML Approach: Approach C (Global Shared Models)

ALLADIN uses **Approach C** for its retail intelligence engine:
- Shared/global ML models trained across compatible historical data from multiple simulated Indian retail businesses operating in **INR**.
- Enables training robust global models (gradient boosting, time-series, isolation forests) that generalize across different business operating dynamics.
- Supports holding out an entire company during evaluation (Leave-One-Group-Out cross-validation) to test generalization to new companies.
- Supports evaluating future unseen time periods (chronological backtesting).
- Accommodates cold-start companies with little historical data via global models, with optional per-company calibration when sufficient history exists.

### Simulated Business Profiles (Heterogeneous Profiles)

The dataset simulates three distinct retail business operating models across major Indian metropolitan hubs:

| Company ID | Business Name | Format / Operating Model | Locations & HQ | Pricing & Margin Profile | Annual Growth Trend |
|---|---|---|---|---|---|
| `00000000-0000-0000-0000-000000000001` | **FreshMart Hypermarket Ltd** | Large-format supermarket & hypermarket chain; broad FMCG, grocery & household merchandise assortment. | Mumbai (HQ), Pune, Ahmedabad | Moderate price points, ~26% gross margin, active weekend promotional discounts. | +10% YoY CAGR |
| `00000000-0000-0000-0000-000000000002` | **GreenRoots Gourmet & Organics** | Premium organic & wellness specialty grocery; health foods, imported goods, artisanal staples. | Bengaluru (HQ), Hyderabad, Chennai | High ticket size, ~35% gross margin, minimal promotional discounting. | +5% YoY CAGR |
| `00000000-0000-0000-0000-000000000003` | **Apna Kirana QuickRetail** | Modern neighborhood discount kirana & value mini-mart; fast-moving staple foods and daily essentials. | Delhi NCR (HQ), Jaipur, Lucknow | Price-sensitive low ticket size, ~22% gross margin, rapid stock turns. | +18% YoY CAGR |

---

## Dataset Schema Reference (18 CSV Files)

The dataset consists of **17 core ERP entities & transaction tables** plus **1 daily KPI summary table**. All primary and foreign keys use deterministic, valid UUIDs.

### 1. Entity & Master Data Tables

#### `companies.csv`
- `id` (UUID): Primary key (`00000000-0000-0000-0000-000000000001` to `...0003`).
- `name` (string): Business entity name.
- `industry` (string): Retail industry classification (Supermarket, Specialty Retail, Grocery).
- `country` (string): Always `"India"`.
- `currency` (string): Always `"INR"`.
- `created_at` (ISO datetime): Organization registration timestamp.

#### `branches.csv`
- `id` (UUID): Primary key.
- `company_id` (UUID): FK → `companies.id`.
- `name` (string): Branch office / retail outlet name.
- `city` (string): Indian metropolitan city (Mumbai, Pune, Ahmedabad, Bengaluru, Hyderabad, Chennai, Delhi, Jaipur, Lucknow).
- `is_headquarters` (boolean): Exactly one HQ per company.
- `created_at` (ISO datetime): Branch opening timestamp.

#### `users.csv`
- `id` (UUID): Primary key.
- `company_id` (UUID): FK → `companies.id`.
- `branch_id` (UUID): FK → `branches.id`.
- `name` (string): User full name (realistic Indian naming).
- `email` (string): Corporate email address.
- `role` (enum): `"admin"`, `"manager"`, `"sales"`, `"accountant"`.
- `created_at` (ISO datetime): Account creation timestamp.

#### `customers.csv`
- `id` (UUID): Primary key.
- `company_id` (UUID): FK → `companies.id`.
- `name` (string): Customer full name or enterprise client label.
- `email` (string): Contact email.
- `phone` (string): Indian telephone format (`+91 9xxxxxxxxx`).
- `city` (string): Customer location city.
- `customer_type` (enum): `"individual"` (75%), `"business"` (25%).
- `credit_limit` (decimal): Maximum extended store credit in INR.
- `created_at` (ISO datetime): Customer profile timestamp.

#### `suppliers.csv`
- `id` (UUID): Primary key.
- `company_id` (UUID): FK → `companies.id`.
- `name` (string): Indian FMCG, dairy, produce, or staples supplier name.
- `contact_email` (string): Supplier contact email.
- `phone` (string): Contact telephone number.
- `city` (string): Supply depot city.
- `payment_terms_days` (integer): Credit terms in days (`15`, `30`, `45`, `60`, `90`).
- `created_at` (ISO datetime): Vendor onboarding timestamp.

#### `categories.csv`
- `id` (UUID): Primary key.
- `company_id` (UUID): FK → `companies.id`.
- `name` (string): Category name (e.g., Staples & Grains, Dairy & Chilled, Spices & Masalas, Household Cleaners).
- `description` (string): Category merchandise description.
- `created_at` (ISO datetime): Creation timestamp.

#### `products.csv`
- `id` (UUID): Primary key.
- `company_id` (UUID): FK → `companies.id`.
- `category_id` (UUID): FK → `categories.id`.
- `name` (string): Product catalog title (e.g., Premium Basmati Rice 5kg, Pure Desi Cow Ghee 500ml).
- `sku` (string): Unique Stock Keeping Unit code per company (`CAT-0001`).
- `cost_price` (decimal): Wholesale procurement cost in INR.
- `selling_price` (decimal): Base retail selling price in INR (`selling_price >= cost_price`).
- `unit` (string): Unit of measure (`pcs`, `kg`, `litre`, `box`, `bag`, `set`, `pack`, `roll`).
- `is_active` (boolean): Active catalog status.
- `created_at` (ISO datetime): Product registration timestamp.

#### `warehouses.csv`
- `id` (UUID): Primary key.
- `company_id` (UUID): FK → `companies.id`.
- `branch_id` (UUID): FK → `branches.id`.
- `name` (string): Warehouse facility name (Central Warehouse, Reserve Depot).
- `location` (string): Facility physical location address.
- `created_at` (ISO datetime): Commissioning timestamp.

---

### 2. Transactional & Ledger Tables

#### `sales.csv`
- `id` (UUID): Primary key.
- `company_id` (UUID): FK → `companies.id`.
- `branch_id` (UUID): FK → `branches.id`.
- `customer_id` (UUID): FK → `customers.id`.
- `user_id` (UUID): FK → `users.id` (salesperson).
- `sale_date` (date): Date of transaction (`YYYY-MM-DD`). Spans all 1,096 consecutive days.
- `status` (enum): `"completed"`, `"pending"`, `"cancelled"`.
- `total_amount` (decimal): Order gross value after discount, before tax. Reconciles with `sum(sale_items.line_total)`.
- `discount_amount` (decimal): Total discount value applied.
- `tax_amount` (decimal): 18% standard Indian GST (`round(total_amount * 0.18, 2)`).
- `net_amount` (decimal): Final invoice payable amount (`total_amount + tax_amount`).
- `payment_status` (enum): `"paid"`, `"partial"`, `"unpaid"`. Cancelled sales are always `"unpaid"`.
- `is_anomaly` (boolean): Labeled indicator of injected transactional anomaly.
- `has_stockout` (boolean): Flag indicating one or more line items experienced constrained stock.
- `created_at` (ISO datetime): Transaction timestamp with realistic business hours.

#### `sale_items.csv`
- `id` (UUID): Primary key.
- `sale_id` (UUID): FK → `sales.id`.
- `product_id` (UUID): FK → `products.id`.
- `quantity` (integer): Actual realized sold quantity (`quantity >= 0`).
- `unit_price` (decimal): Unit selling price in INR.
- `discount_pct` (decimal): Line discount rate (`0.0`, `0.05`, `0.10`, `0.15`, or `0.75` for anomalies).
- `line_total` (decimal): Calculated value: `round(quantity * unit_price * (1 - discount_pct), 2)`.
- `unconstrained_demand` (integer): Latent customer demand before stockout suppression (`unconstrained_demand >= quantity`).
- `stockout_flag` (boolean): True when available inventory was lower than unconstrained customer demand.

#### `purchases.csv`
- `id` (UUID): Primary key.
- `company_id` (UUID): FK → `companies.id`.
- `branch_id` (UUID): FK → `branches.id`.
- `supplier_id` (UUID): FK → `suppliers.id`.
- `user_id` (UUID): FK → `users.id` (procurement officer).
- `purchase_date` (date): Order placement date.
- `status` (enum): `"received"`, `"pending"`, `"cancelled"`.
- `total_amount` (decimal): Order procurement value. Reconciles with `sum(purchase_items.line_total)`.
- `tax_amount` (decimal): 5% input tax (`round(total_amount * 0.05, 2)`).
- `net_amount` (decimal): Total payable (`total_amount + tax_amount`).
- `payment_status` (enum): `"paid"`, `"partial"`, `"unpaid"`.
- `created_at` (ISO datetime): Order timestamp.

#### `purchase_items.csv`
- `id` (UUID): Primary key.
- `purchase_id` (UUID): FK → `purchases.id`.
- `product_id` (UUID): FK → `products.id`.
- `quantity` (integer): Restock units purchased.
- `unit_cost` (decimal): Procurement unit cost in INR.
- `line_total` (decimal): Reconciled total: `round(quantity * unit_cost, 2)`.

#### `invoices.csv`
- `id` (UUID): Primary key.
- `company_id` (UUID): FK → `companies.id`.
- `sale_id` (UUID): FK → `sales.id` (1:1 mapping with sales).
- `customer_id` (UUID): FK → `customers.id`.
- `invoice_number` (string): Sequential alphanumeric invoice number (`INV-0000001`).
- `invoice_date` (date): Issue date, matching `sales.sale_date`.
- `due_date` (date): Due date (`invoice_date + 15..60 days`).
- `total_amount` (decimal): Exactly equals `sales.net_amount`.
- `paid_amount` (decimal): Amount settled so far (`paid_amount <= total_amount`).
- `status` (enum): `"paid"`, `"partial"`, `"overdue"`, `"cancelled"`.
- `created_at` (ISO datetime): Invoice timestamp.

#### `payments.csv`
- `id` (UUID): Primary key.
- `company_id` (UUID): FK → `companies.id`.
- `reference_type` (enum): `"sale"`, `"purchase"`.
- `reference_id` (UUID): FK → `sales.id` or `purchases.id`.
- `amount` (decimal): Payment installment amount in INR.
- `payment_method` (enum): `"cash"`, `"card"`, `"bank_transfer"`, `"cheque"`.
- `payment_date` (date): Settlement date (`payment_date >= reference_date`).
- `created_at` (ISO datetime): Payment receipt timestamp.

#### `expenses.csv`
- `id` (UUID): Primary key.
- `company_id` (UUID): FK → `companies.id`.
- `branch_id` (UUID): FK → `branches.id`.
- `user_id` (UUID): FK → `users.id`.
- `category` (enum): Fixed (`Rent`, `Salaries`, `Utilities`) + Variable (`Marketing`, `Logistics`, `Packaging Materials`, `Maintenance`, `Office Supplies`, `IT & Software`, `Insurance`).
- `description` (string): Expense operational description.
- `amount` (decimal): Expense value in INR.
- `expense_date` (date): Date incurred.
- `status` (enum): `"approved"`, `"pending"`, `"rejected"`.
- `is_anomaly` (boolean): Labeled anomaly indicator for cost surges or duplicate billing.
- `created_at` (ISO datetime): Expense timestamp.

---

### 3. Inventory & Daily Summary Tables

#### `inventory.csv`
- `id` (UUID): Primary key.
- `product_id` (UUID): FK → `products.id`.
- `warehouse_id` (UUID): FK → `warehouses.id`.
- `quantity_on_hand` (integer): Realized closing physical stock at end of 2024.
- `reorder_level` (integer): Minimum stock quantity triggering restock alert.
- `reorder_quantity` (integer): Batch procurement quantity (`reorder_quantity >= reorder_level`).
- `updated_at` (ISO datetime): Last inventory snapshot timestamp.

#### `stock_movements.csv`
- `id` (UUID): Primary key.
- `product_id` (UUID): FK → `products.id`.
- `warehouse_id` (UUID): FK → `warehouses.id`.
- `movement_type` (enum): `"in"` (inbound shipments), `"out"` (outbound customer sales / write-offs).
- `quantity` (integer): Units transferred.
- `reason` (enum): `"sale"`, `"purchase"`, `"adjustment"`, `"return"`, `"transfer"`, `"write_off"`.
- `reference_id` (UUID, nullable): FK → `sales.id` for sales, `purchases.id` for purchases; null for audit adjustments.
- `moved_at` (ISO datetime): Timestamp of physical movement.

#### `daily_kpi_summary.csv`
Contains **3,288 rows** covering every consecutive day across the 36-month period for all 3 simulated companies (1,096 days × 3 companies):
- `company_id` (UUID): FK → `companies.id`.
- `date` (date): Consecutive daily calendar date from `2022-01-01` to `2024-12-31`.
- `revenue` (decimal): Daily completed sales net amount in INR.
- `cogs` (decimal): Daily Cost of Goods Sold derived from item quantities × procurement cost prices.
- `gross_profit` (decimal): Reconciled: `revenue - cogs`.
- `operating_expenses` (decimal): Daily approved operating expenses incurred for that company.
- `net_profit` (decimal): Reconciled: `gross_profit - operating_expenses`.
- `order_count` (integer): Total daily completed transactions.
- `units_sold` (integer): Total physical units sold across transactions.
- `unconstrained_demand_units` (integer): Latent customer demand before stockout suppression.
- `stockout_count` (integer): Number of line items impacted by inventory shortages.
- `low_stock_skus` (integer): Count of product SKUs with quantity on hand at or below reorder level.
- `is_anomaly` (boolean): Flag indicating if any transactional or expense anomaly occurred on this day.

---

## Time-Series & Behavioral Modeling Dynamics

The synthetic data generation incorporates realistic Indian retail behavioral patterns:

1. **Weekly Retail Cycle**:
   - Weekends (Saturday & Sunday) experience the highest retail footfall and sales volume (1.35× to 1.45× baseline).
   - Friday experiences a moderate uplift (1.10×).
   - Weekdays (Monday through Thursday) exhibit baseline regular retail replenishment.

2. **Month-Beginning Salary Cycle**:
   - Household grocery replenishment surges during the 1st through 7th of every month (1.20× multiplier) following monthly salary disbursements in India.

3. **Indian Festive & Holiday Calendar**:
   - Explicit surges modeled for all major Indian festival windows across 2022, 2023, and 2024:
     - **Diwali & Dhanteras** (Oct/Nov): Retail peak surge (2.50× volume).
     - **Navratri & Dussehra** (Sept/Oct): Pre-festive surge (1.65×).
     - **Holi** (March): Spring festival surge (1.55×).
     - **Independence Day Great Freedom Sale** (August 10–15): Retail clearance surge (1.50×).
     - **Republic Day Sale** (January 22–26): Republic Day promotion surge (1.45×).
     - **Year-End & New Year Clearance** (December 25–31): Holiday surge (1.45×).
     - **Eid-ul-Fitr** (April/May): Festive dining & staples surge (1.40×).

4. **Stock-Outs vs. Unconstrained Demand**:
   - As customer orders deplete warehouse inventory, products with stock below customer request experience partial fulfillment or out-of-stock events (`stockout_flag = True`).
   - `unconstrained_demand` tracks true latent customer demand, while `quantity` reflects realized physical sales.
   - Restocking orders are periodically dispatched to suppliers, replenishing stock after realistic lead times (1–3 days).

5. **Injected Synthetic Anomalies**:
   - **Sales Anomalies (~1.2%)**:
     - Extreme bulk orders (8× to 12× quantity spikes).
     - Excessive promotional discounts (75% unauthorized discounting).
   - **Expense Anomalies (~1.5%)**:
     - Operational expense cost surges (8.5× base value).
     - Duplicate submissions with pending review status.
   - All anomalies are explicitly tagged with `is_anomaly = True` to provide ground truth for anomaly detection pipelines.

---

## Mapping to the Seven ML Pipelines

The dataset directly provides the training inputs, engineered features, and target labels for the seven ALLADIN ML pipelines:

| Pipeline | Target Variable | Primary Input Tables | Key Features & Lags | Synthetic Limitations & Assumptions |
|---|---|---|---|---|
| **1. Revenue Forecasting** | `daily_kpi_summary.revenue` or monthly aggregated revenue | `daily_kpi_summary.csv`, `sales.csv` | Calendar features (day of week, month, day of month, quarter), Indian holiday flags, `revenue_lag1`, `revenue_lag7`, `revenue_lag30`, 7-day & 30-day rolling revenue means, `company_id` for global training. | Multipliers follow modeled distributions; does not model exogenous macro shocks (e.g. demonetization, inflation spikes). |
| **2. Product-Level Sales Forecasting** | `sale_items.quantity` | `sale_items.csv`, `sales.csv`, `products.csv`, `categories.csv` | `product_id`, `category_id`, `unit_price`, `discount_pct`, day of week, month, festival flags, historical demand lags. | Customer price elasticity is modeled parametrically; cross-product cannibalization is simplified. |
| **3. Inventory Demand & Reorder** | `reorder_trigger` (binary: `quantity <= reorder_level`) and `recommended_order_qty` | `inventory.csv`, `stock_movements.csv`, `sale_items.csv`, `purchases.csv` | `quantity_on_hand`, `reorder_level`, `daily_consumption_rate` (from outbound stock movements), supplier lead time days, `stockout_count`. | Supplier lead times are modeled uniformly between 1–3 days; supplier stock-outs are not modeled. |
| **4. Profit Prediction** | `daily_kpi_summary.net_profit` / `gross_profit` | `daily_kpi_summary.csv`, `sales.csv`, `expenses.csv`, `products.csv` | `revenue`, `cogs`, `gross_margin_pct`, `operating_expenses`, `expense_ratio`, `revenue_growth_yoy`, monthly profit lags. | Overhead allocations across branches are modeled uniformly based on branch size. |
| **5. Operating Expense Forecasting** | `expenses.amount` by category | `expenses.csv`, `branches.csv` | `category`, `expense_date` (month, day), `branch_id`, `is_month_start` (Rent), `is_month_end` (Salaries), trailing category averages. | Rent and salaries are fixed monthly steps with minor annual adjustments; emergency capital expenditures are limited to surge anomalies. |
| **6. Business Health Scoring** | Composite financial health score (0–100) & rating label | `daily_kpi_summary.csv`, `invoices.csv`, `expenses.csv`, `inventory.csv` | `revenue_growth`, `profit_margin`, `expense_ratio`, `collection_rate` (`paid_amount / total_amount`), `inventory_turnover` (`cogs / inventory_value`). | Health scores are derived from foundational financial ratios; actual corporate credit ratings would use bank statements and GST filings. |
| **7. Anomaly Detection** | `sales.is_anomaly` / `expenses.is_anomaly` | `sales.csv`, `sale_items.csv`, `expenses.csv` | `net_amount`, `discount_amount`, `discount_pct`, `hour_of_day`, `day_of_week`, `roll28_mean`, `roll28_std`, `amount_z_rolling`. | Anomalies are synthetically injected with parametric rules; real-world fraud exhibits evolving, adversarial evasion techniques. |

---

## How to Regenerate and Validate the Dataset

All scripts run out-of-the-box using the project's standard Python virtual environment.

### 1. Regenerate Dataset (Deterministic & Reproducible)

```bash
# From repository root or ai-financial-intelligence-platform directory:
python ml/datasets/synthetic/generate_synthetic_data.py --seed 42 --start-date 2022-01-01 --end-date 2024-12-31
```

Options:
- `--seed`: Integer random seed (default: `42`). Running with `--seed 42` guarantees byte-for-byte identical output files.
- `--start-date`: Beginning date in `YYYY-MM-DD` format (default: `2022-01-01`).
- `--end-date`: Ending date in `YYYY-MM-DD` format (default: `2024-12-31`).

### 2. Run Comprehensive Validation

```bash
python ml/datasets/synthetic/validate_synthetic_data.py
```

The validation suite executes over 270 individual checks across:
- Presence of all 18 files.
- Foreign-key integrity and primary key uniqueness (zero duplicate IDs).
- Date coverage: continuous 1,096 calendar days with zero missing dates.
- Mathematical reconciliation across order line totals, taxes, invoices, payments, and daily business KPIs.
- Stock movements vs. inventory logic.
- Presence and verification of stockouts, latent unconstrained demand, and labeled anomalies.
- Heterogeneity verification across the simulated Indian business profiles.
