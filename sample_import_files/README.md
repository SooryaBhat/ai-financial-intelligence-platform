# ALLADIN Import Center — Sample Business Test Files

This directory contains a complete set of realistic Indian retail business sample datasets formatted for testing the **ALLADIN AI-Powered Financial Intelligence Platform** Import Center (`/imports`).

All monetary figures are in Indian Rupees (**INR ₹**), entities feature authentic Karnataka retail goods (Mangaluru, Bengaluru, Mysuru), realistic addresses, GSTIN tax identifiers, and dates across the year **2026**.

---

## 📂 File Directory & Overview

| File Name | Format | Record Count | Expected Import Entity | Compatibility Status |
| :--- | :--- | :--- | :--- | :--- |
| [`products.csv`](./products.csv) | CSV | 25 products | `products` (Products & SKUs) | ✅ Fully Compatible |
| [`products.xlsx`](./products.xlsx) | Excel (.xlsx) | 25 products | `products` (Products & SKUs) | ✅ Fully Compatible |
| [`sales.csv`](./sales.csv) | CSV | 50 line items (18 orders) | `sales` (Sales Orders & Items) | ✅ Fully Compatible* |
| [`expenses.csv`](./expenses.csv) | CSV | 20 records | `expenses` (Operating Expenses) | ✅ Fully Compatible |
| [`inventory.csv`](./inventory.csv) | CSV | 20 adjustments | `inventory` (Stock Adjustments) | ✅ Fully Compatible* |
| [`expenses.pdf`](./expenses.pdf) | PDF (Text-based) | 1 voucher (2 line items) | PDF Document Extraction | ✅ Fully Compatible |
| [`customers.csv`](./customers.csv) | CSV | 20 accounts | Reference / Customers Table | ⚠️ Reference File only |
| [`suppliers.csv`](./suppliers.csv) | CSV | 5 vendors | Reference / Suppliers Table | ⚠️ Reference File only |
| [`validation_test.csv`](./validation_test.csv) | CSV | 8 test cases | `products` (Validation Test) | 🧪 Intentional Errors |

> * **Note on Referential Integrity:** `sales.csv` and `inventory.csv` referentially link to product SKUs defined in `products.csv`. Ensure you import `products.csv` into your company catalog first before importing sales or inventory adjustments.

---

## 📋 File Details & Column Mappings

### 1. `products.csv` & `products.xlsx`
* **Target Import Entity:** `products`
* **Source Headers & Destination Mappings:**
  * `name` → **Product Name** (`name`, *Required*)
  * `sku` → **SKU / Code** (`sku`, *Unique per company*)
  * `category` → **Category Name** (`category`)
  * `unit_price` → **Selling Price** (`selling_price`, *Required, auto-mapped via alias*)
  * `cost_price` → **Cost Price** (`cost_price`, *Auto-mapped via alias*)
  * `tax_rate` → **Tax Rate %** (`tax_rate`, *Auto-mapped via alias*)
  * `unit` → **Unit of Measurement** (`unit`, e.g. pack, bottle, kg, bag)
  * `stock_quantity` → Reference column (tracked live in `inventory` table)
  * `description` → **Description** (`description`)
* **Retail Catalog Highlights:** Premium Mangalore Cashews (W240), Mysore Filter Coffee, Coorg Cardamom, Karnataka Sona Masoori Rice, Nandini Cow Ghee, Udupi Turmeric, Byadgi Chillies, and consulting services.

---

### 2. `sales.csv`
* **Target Import Entity:** `sales`
* **Source Headers & Destination Mappings:**
  * `sale_number` → **Sale / Order Number** (`sale_number`, *Required*)
  * `sale_date` → **Sale Date** (`sale_date`, YYYY-MM-DD)
  * `customer_name` → **Customer Name** (`customer_name`)
  * `product_sku` → **Product SKU / Code** (`product_sku`, *Required, must exist in catalog*)
  * `quantity` → **Quantity** (`quantity`, *Required, > 0*)
  * `unit_price` → **Unit Price** (`unit_price`, *Required, >= 0*)
  * `discount_pct` → **Discount %** (`discount_pct`, 0–100%)
  * `tax_rate` → **Tax Rate %** (`tax_rate`, 0–100%)
  * `total` → Calculated line total `round((qty * price * (1 - disc/100)) * (1 + tax/100), 2)`
  * `notes` → **Notes / Memo** (`notes`)
* **Order Structure:** Multi-item orders (e.g. `SO-2026-001` to `SO-2026-018`) demonstrating multi-line transaction grouping during import confirmation.

---

### 3. `expenses.csv`
* **Target Import Entity:** `expenses`
* **Source Headers & Destination Mappings:**
  * `expense_date` → **Expense Date** (`expense_date`, YYYY-MM-DD)
  * `category` → **Expense Category** (`category`, e.g. Utilities, Rent & Leases, Logistics & Freight)
  * `description` → **Expense Description** (`description`, *Required*)
  * `amount` → **Amount** (`amount`, *Required, > 0*)
  * `payment_method` → **Payment Method** (`payment_method`, enum: `cash`, `bank_transfer`, `card`, `cheque`, `other`)
  * `reference` → **Notes / Receipt Ref** (`notes`, auto-mapped via alias `reference`)
* **Highlights:** Real Indian operational costs including MESCOM & BESCOM power bills, DTDC & VRL freight, store godown rentals in Mangaluru & Bengaluru, CA retainers, and packaging supplies.

---

### 4. `inventory.csv`
* **Target Import Entity:** `inventory`
* **Source Headers & Destination Mappings:**
  * `product_sku` → **Product SKU / Code** (`product_sku`, *Required, must match catalog*)
  * `warehouse_name` → **Warehouse** (`warehouse_name`, e.g. 'Main Warehouse Mangaluru', 'Bengaluru Central Godown', 'Mysuru Retail Hub')
  * `quantity_delta` → **Quantity Delta (+ / -)** (`quantity_delta`, *Required, positive for restock, negative for deduction*)
  * `reorder_level` → **Reorder Level** (`reorder_level`, safety threshold)
  * `notes` → **Reason / Notes** (`notes`, audit log explanation)

---

### 5. `expenses.pdf`
* **Target Import Workflow:** `PDF Document Extraction` (Modal extraction & review)
* **Design & Characteristics:**
  * 100% digital, text-based PDF created using ReportLab (no scanned images or unselectable raster bitmaps).
  * Automatically parsed by `pypdf.PdfReader` and analyzed by `PDFExtractorService`.
  * Classified as `receipt` (defaults directly to the Expense review modal).
  * Extracted candidate metadata:
    * **Document Number:** `REC-2026-0842` (High confidence)
    * **Issue Date:** `2026-08-15` (High confidence)
    * **Counterparty Vendor:** `Karnataka Office Supplies & Tech Hub`
    * **Currency:** `INR` (₹)
    * **Subtotal:** `₹21,600.00`
    * **GST Tax:** `₹3,888.00` (18%)
    * **Grand Total:** `₹25,488.00`
    * **Line Items:** 2 line items with arithmetic check `is_consistent: True`.

---

### 6. `customers.csv` & `suppliers.csv` (Reference Files)
* **Compatibility Status:** ⚠️ **Reference Files Only**
* **Important System Finding:** The existing ALLADIN Import Center (`/imports`) currently exposes 5 import schemas: `products`, `sales`, `inventory`, `expenses`, and `invoices`. Direct batch CSV ingestion for `customers` and `suppliers` is not supported in the existing Import Center interface.
* **Intended Use:** These files match the exact relational database schemas of the `customers` and `suppliers` tables in PostgreSQL/Supabase and can be created via the direct CRUD API (`/api/v1/customers` and `/api/v1/suppliers`) or future customer import modules.

---

### 7. `validation_test.csv` (Intentional Error Cases)
This file is deliberately structured to test and verify the validation engine (`/api/v1/imports/validate`) and the UI's error display badges:

| Row # | Item Name | SKU | Test Condition | Expected Validation Behavior |
| :---: | :--- | :--- | :--- | :--- |
| **1** | Valid Baseline Basmati Rice | `VAL-OK-101` | Clean baseline record | `status: "valid"` |
| **2** | *(Empty Name)* | `VAL-ERR-102` | Missing required product name | `status: "invalid"` \| *Product name is required.* |
| **3** | Negative Selling Price Item | `VAL-ERR-103` | `selling_price = -150.00` | `status: "invalid"` \| *Selling price: Value must be at least 0.0* |
| **4** | Empty Selling Price Item | `VAL-ERR-104` | `selling_price = ""` | `status: "invalid"` \| *Selling price is required.* |
| **5** | Duplicate SKU In File Item | `VAL-OK-101` | Duplicate of Row 1 | `status: "invalid"` \| *Duplicate SKU 'VAL-OK-101' found multiple times in upload file* |
| **6** | Excessive Tax Rate Item | `VAL-ERR-106` | `tax_rate = 180.0` | `status: "invalid"` \| *Tax rate: Value must be at most 100.0* |
| **7** | Missing SKU Auto-Recommend | *(Empty)* | SKU omitted | `status: "warning"` \| *No SKU provided; automatic SKU will be recommended.* |
| **8** | Unrecognized Enum Type Item | `VAL-WRN-108` | `type = "equipment_rental"` | `status: "warning"` \| *Type: Invalid option 'equipment_rental'. Defaulted to 'product'* |

---

## 🔄 Regeneration Command

To regenerate all sample files at any time, execute the following command from the project root:

```powershell
& ".\backend\venv\Scripts\python.exe" scripts/generate_sample_import_files.py
```
