# Datasets — AI Financial Intelligence Platform ML Module

This directory contains all datasets used in the ML module, organized by stage in the data pipeline.

---

## Directory Structure

```
datasets/
├── raw/            # Original, unmodified source data (never edit these)
├── processed/      # Cleaned, feature-engineered data ready for training
├── synthetic/      # Synthetically generated ERP data for development
└── README.md       # This file
```

---

## Synthetic Datasets

Located in `datasets/synthetic/`. These files simulate a realistic multi-company ERP system with 3 years of business data.

All files use **UUIDs** as primary keys and preserve **foreign key relationships** across tables.

### Entity & Reference Tables

| File | Description |
|------|-------------|
| `companies.csv` | Top-level company entities (3 companies) |
| `branches.csv` | Branch offices per company (3 per company, 9 total) |
| `users.csv` | Platform users with roles assigned per company |
| `customers.csv` | Customers per company — includes repeat buyers |
| `suppliers.csv` | Suppliers per company — multiple per product category |
| `categories.csv` | Product categories (shared reference data) |
| `products.csv` | Products with cost price, selling price, and category |
| `warehouses.csv` | Warehouses linked to branches |

### Inventory Tables

| File | Description |
|------|-------------|
| `inventory.csv` | Current stock level per product per warehouse |
| `stock_movements.csv` | Every stock in/out movement with reason code |

### Transactional Tables

| File | Description |
|------|-------------|
| `sales.csv` | Sales orders — includes seasonal variation across years |
| `sale_items.csv` | Line items per sale order |
| `purchases.csv` | Purchase orders from suppliers |
| `purchase_items.csv` | Line items per purchase order |
| `payments.csv` | Payments covering sales and purchase invoices |
| `expenses.csv` | Operational expense records per branch |
| `invoices.csv` | Invoices generated per sale |

---

## Column Descriptions

### companies.csv

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID | Primary key |
| `name` | string | Company name |
| `industry` | string | Industry type (e.g., Retail, Manufacturing) |
| `country` | string | Country of registration |
| `currency` | string | Default currency (e.g., USD, INR) |
| `created_at` | datetime | Record creation timestamp |

### branches.csv

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID | Primary key |
| `company_id` | UUID | FK → companies.id |
| `name` | string | Branch name |
| `city` | string | City location |
| `is_headquarters` | boolean | True if this is the HQ |
| `created_at` | datetime | Record creation timestamp |

### users.csv

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID | Primary key |
| `company_id` | UUID | FK → companies.id |
| `branch_id` | UUID | FK → branches.id |
| `name` | string | Full name |
| `email` | string | Email address |
| `role` | string | User role (admin, manager, sales, accountant) |
| `created_at` | datetime | Record creation timestamp |

### customers.csv

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID | Primary key |
| `company_id` | UUID | FK → companies.id |
| `name` | string | Customer full name or business name |
| `email` | string | Contact email |
| `phone` | string | Contact phone |
| `city` | string | City |
| `customer_type` | string | individual / business |
| `credit_limit` | decimal | Maximum credit extended |
| `created_at` | datetime | First interaction date |

### suppliers.csv

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID | Primary key |
| `company_id` | UUID | FK → companies.id |
| `name` | string | Supplier business name |
| `contact_email` | string | Supplier contact email |
| `phone` | string | Supplier phone |
| `city` | string | Supplier city |
| `payment_terms_days` | integer | Net payment terms (e.g., 30, 60) |
| `created_at` | datetime | Record creation timestamp |

### categories.csv

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID | Primary key |
| `company_id` | UUID | FK → companies.id |
| `name` | string | Category name |
| `description` | string | Short description |
| `created_at` | datetime | Record creation timestamp |

### products.csv

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID | Primary key |
| `company_id` | UUID | FK → companies.id |
| `category_id` | UUID | FK → categories.id |
| `name` | string | Product name |
| `sku` | string | Stock Keeping Unit code |
| `cost_price` | decimal | Purchase cost per unit |
| `selling_price` | decimal | Default selling price per unit |
| `unit` | string | Unit of measure (pcs, kg, litre, box) |
| `is_active` | boolean | Whether product is currently sold |
| `created_at` | datetime | Record creation timestamp |

### warehouses.csv

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID | Primary key |
| `company_id` | UUID | FK → companies.id |
| `branch_id` | UUID | FK → branches.id |
| `name` | string | Warehouse name |
| `location` | string | Physical address or location label |
| `created_at` | datetime | Record creation timestamp |

### inventory.csv

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID | Primary key |
| `product_id` | UUID | FK → products.id |
| `warehouse_id` | UUID | FK → warehouses.id |
| `quantity_on_hand` | integer | Current stock quantity |
| `reorder_level` | integer | Minimum stock before reorder |
| `reorder_quantity` | integer | Quantity to reorder when triggered |
| `updated_at` | datetime | Last stock update timestamp |

### stock_movements.csv

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID | Primary key |
| `product_id` | UUID | FK → products.id |
| `warehouse_id` | UUID | FK → warehouses.id |
| `movement_type` | string | in / out |
| `quantity` | integer | Units moved |
| `reason` | string | purchase / sale / adjustment / return / transfer |
| `reference_id` | UUID | FK → sales.id or purchases.id (nullable) |
| `moved_at` | datetime | Timestamp of movement |

### sales.csv

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID | Primary key |
| `company_id` | UUID | FK → companies.id |
| `branch_id` | UUID | FK → branches.id |
| `customer_id` | UUID | FK → customers.id |
| `user_id` | UUID | FK → users.id (salesperson) |
| `sale_date` | date | Date of sale |
| `status` | string | completed / pending / cancelled |
| `total_amount` | decimal | Total order value |
| `discount_amount` | decimal | Discount applied |
| `tax_amount` | decimal | Tax applied |
| `net_amount` | decimal | Final payable amount |
| `payment_status` | string | paid / partial / unpaid |
| `created_at` | datetime | Record creation timestamp |

### sale_items.csv

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID | Primary key |
| `sale_id` | UUID | FK → sales.id |
| `product_id` | UUID | FK → products.id |
| `quantity` | integer | Units sold |
| `unit_price` | decimal | Actual selling price per unit |
| `discount_pct` | decimal | Discount percentage applied |
| `line_total` | decimal | quantity × unit_price × (1 - discount_pct) |

### purchases.csv

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID | Primary key |
| `company_id` | UUID | FK → companies.id |
| `branch_id` | UUID | FK → branches.id |
| `supplier_id` | UUID | FK → suppliers.id |
| `user_id` | UUID | FK → users.id (buyer) |
| `purchase_date` | date | Date of purchase |
| `status` | string | received / pending / cancelled |
| `total_amount` | decimal | Total purchase value |
| `tax_amount` | decimal | Tax on purchase |
| `net_amount` | decimal | Net payable |
| `payment_status` | string | paid / partial / unpaid |
| `created_at` | datetime | Record creation timestamp |

### purchase_items.csv

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID | Primary key |
| `purchase_id` | UUID | FK → purchases.id |
| `product_id` | UUID | FK → products.id |
| `quantity` | integer | Units purchased |
| `unit_cost` | decimal | Cost per unit at time of purchase |
| `line_total` | decimal | quantity × unit_cost |

### payments.csv

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID | Primary key |
| `company_id` | UUID | FK → companies.id |
| `reference_type` | string | sale / purchase |
| `reference_id` | UUID | FK → sales.id or purchases.id |
| `amount` | decimal | Payment amount |
| `payment_method` | string | cash / card / bank_transfer / cheque |
| `payment_date` | date | Date of payment |
| `created_at` | datetime | Record creation timestamp |

### expenses.csv

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID | Primary key |
| `company_id` | UUID | FK → companies.id |
| `branch_id` | UUID | FK → branches.id |
| `user_id` | UUID | FK → users.id (submitter) |
| `category` | string | Expense category (rent, salaries, utilities, etc.) |
| `description` | string | Short description |
| `amount` | decimal | Expense amount |
| `expense_date` | date | Date incurred |
| `status` | string | approved / pending / rejected |
| `created_at` | datetime | Record creation timestamp |

### invoices.csv

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID | Primary key |
| `company_id` | UUID | FK → companies.id |
| `sale_id` | UUID | FK → sales.id |
| `customer_id` | UUID | FK → customers.id |
| `invoice_number` | string | Human-readable invoice number |
| `invoice_date` | date | Date invoice was issued |
| `due_date` | date | Payment due date |
| `total_amount` | decimal | Invoice total |
| `paid_amount` | decimal | Amount paid so far |
| `status` | string | paid / partial / overdue / cancelled |
| `created_at` | datetime | Record creation timestamp |

---

## Data Generation Notes

- Date range: **2022-01-01 to 2024-12-31** (3 years)
- Sales include seasonal patterns: higher in **Q4 (Oct–Dec)** and **Q2 (Apr–Jun)**
- Inventory levels fluctuate in sync with sales and purchases
- ~30% of customers are **repeat customers** appearing across multiple sales
- Each company has its own isolated set of customers, suppliers, and products
- Prices include realistic **markup ratios** (1.3×–2.5× cost price)
- Expenses include fixed costs (rent, salaries) and variable costs (utilities, supplies)

---

## Usage

These datasets are for **development and prototyping only**.

Do not use synthetic data for production model training. Replace with real business data from the ERP module when available.
