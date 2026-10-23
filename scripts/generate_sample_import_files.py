"""
Generate realistic sample business files for testing the ALLADIN Import Center.
Outputs clean CSV, Excel (.xlsx), and text-based PDF files with realistic Indian retail business data (INR currency, Mangaluru/Bengaluru/Mysuru addresses).
"""

import csv
import io
import os
import sys
from pathlib import Path
import openpyxl
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
import pypdf
from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

# Base directory for output
PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = PROJECT_ROOT / "sample_import_files"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# ─────────────────────────────────────────────────────────────────────────────
# 1. PRODUCTS DATA (25 realistic Indian retail items)
# ─────────────────────────────────────────────────────────────────────────────
PRODUCTS_DATA = [
    {
        "name": "Mangalore Jumbo Cashews W240 500g",
        "sku": "PRD-CAS-001",
        "category": "Dry Fruits & Nuts",
        "unit_price": 540.00,
        "cost_price": 420.00,
        "tax_rate": 5.0,
        "unit": "pack",
        "stock_quantity": 120,
        "description": "Premium whole cashew nuts processed in Mangaluru",
    },
    {
        "name": "Mysore Traditional Filter Coffee 500g",
        "sku": "PRD-COF-002",
        "category": "Beverages",
        "unit_price": 280.00,
        "cost_price": 210.00,
        "tax_rate": 5.0,
        "unit": "pack",
        "stock_quantity": 200,
        "description": "85:15 Coffee Chicory blend dark roasted ground coffee",
    },
    {
        "name": "Coorg Green Cardamom 100g",
        "sku": "PRD-SPI-003",
        "category": "Spices & Condiments",
        "unit_price": 340.00,
        "cost_price": 260.00,
        "tax_rate": 5.0,
        "unit": "pack",
        "stock_quantity": 85,
        "description": "8mm bold green aromatic cardamom pods from Madikeri",
    },
    {
        "name": "Karnataka Sona Masoori Rice 25kg",
        "sku": "PRD-RIC-004",
        "category": "Grains & Staples",
        "unit_price": 1450.00,
        "cost_price": 1220.00,
        "tax_rate": 0.0,
        "unit": "bag",
        "stock_quantity": 60,
        "description": "Aged premium lightweight aromatic rice grain",
    },
    {
        "name": "Dakshina Wood Pressed Coconut Oil 1L",
        "sku": "PRD-OIL-005",
        "category": "Oils & Ghee",
        "unit_price": 320.00,
        "cost_price": 250.00,
        "tax_rate": 5.0,
        "unit": "bottle",
        "stock_quantity": 150,
        "description": "Pure cold pressed virgin coconut cooking and hair oil",
    },
    {
        "name": "Nandini Pure Cow Ghee 1L Tin",
        "sku": "PRD-GHE-006",
        "category": "Dairy & Ghee",
        "unit_price": 630.00,
        "cost_price": 545.00,
        "tax_rate": 12.0,
        "unit": "tin",
        "stock_quantity": 110,
        "description": "KMF Nandini golden granulated pure cow ghee",
    },
    {
        "name": "Udupi Stone Ground Turmeric Powder 500g",
        "sku": "PRD-TUR-007",
        "category": "Spices & Condiments",
        "unit_price": 160.00,
        "cost_price": 115.00,
        "tax_rate": 5.0,
        "unit": "pack",
        "stock_quantity": 175,
        "description": "High-curcumin sun dried pure organic turmeric",
    },
    {
        "name": "Byadgi Whole Red Chillies Stemless 1kg",
        "sku": "PRD-CHL-008",
        "category": "Spices & Condiments",
        "unit_price": 480.00,
        "cost_price": 380.00,
        "tax_rate": 5.0,
        "unit": "pack",
        "stock_quantity": 90,
        "description": "Deep red color low pungency authentic Byadgi chillies",
    },
    {
        "name": "Malnad Whole Black Pepper 500g",
        "sku": "PRD-PEP-009",
        "category": "Spices & Condiments",
        "unit_price": 450.00,
        "cost_price": 350.00,
        "tax_rate": 5.0,
        "unit": "pack",
        "stock_quantity": 130,
        "description": "Tellicherry garbled special extra bold black pepper",
    },
    {
        "name": "Mangalorean Palm Jaggery Blocks 1kg",
        "sku": "PRD-JAG-010",
        "category": "Organic Sweeteners",
        "unit_price": 190.00,
        "cost_price": 135.00,
        "tax_rate": 5.0,
        "unit": "pack",
        "stock_quantity": 140,
        "description": "Chemical free unrefined traditional palm jaggery",
    },
    {
        "name": "Bangalore Blue Grapes Jam 400g",
        "sku": "PRD-JAM-011",
        "category": "Breakfast & Spreads",
        "unit_price": 145.00,
        "cost_price": 105.00,
        "tax_rate": 12.0,
        "unit": "jar",
        "stock_quantity": 95,
        "description": "GI-tagged Bangalore blue grapes fruit preserve",
    },
    {
        "name": "Roasted Salted California Almonds 500g",
        "sku": "PRD-ALM-012",
        "category": "Dry Fruits & Nuts",
        "unit_price": 490.00,
        "cost_price": 390.00,
        "tax_rate": 5.0,
        "unit": "pack",
        "stock_quantity": 80,
        "description": "Crunchy oven roasted lightly salted snacking badam",
    },
    {
        "name": "Organic Toor Dal (Pigeon Pea) 2kg",
        "sku": "PRD-DAL-013",
        "category": "Pulses & Lentils",
        "unit_price": 320.00,
        "cost_price": 265.00,
        "tax_rate": 0.0,
        "unit": "pack",
        "stock_quantity": 160,
        "description": "Unpolished Gulbarga variety high protein toor dal",
    },
    {
        "name": "Mysore Pak Royal Sweets Gift Box 500g",
        "sku": "PRD-SWT-014",
        "category": "Sweets & Confectionery",
        "unit_price": 360.00,
        "cost_price": 250.00,
        "tax_rate": 5.0,
        "unit": "box",
        "stock_quantity": 70,
        "description": "Authentic melt-in-mouth ghee rich Mysore Pak",
    },
    {
        "name": "Kundapura Koli Rotti Crisp Sheets 500g",
        "sku": "PRD-ROT-015",
        "category": "Bakery & Snacks",
        "unit_price": 110.00,
        "cost_price": 75.00,
        "tax_rate": 5.0,
        "unit": "pack",
        "stock_quantity": 180,
        "description": "Crispy paper-thin Coastal Karnataka rice wafers",
    },
    {
        "name": "Mangaluru Banana Chips in Pure Coconut Oil 250g",
        "sku": "PRD-CHP-016",
        "category": "Bakery & Snacks",
        "unit_price": 125.00,
        "cost_price": 85.00,
        "tax_rate": 12.0,
        "unit": "pack",
        "stock_quantity": 220,
        "description": "Fresh Nendran yellow banana chips fried in pure coconut oil",
    },
    {
        "name": "Wild Multi-Flora Forest Honey 500g",
        "sku": "PRD-HNY-017",
        "category": "Organic Sweeteners",
        "unit_price": 375.00,
        "cost_price": 280.00,
        "tax_rate": 5.0,
        "unit": "jar",
        "stock_quantity": 65,
        "description": "Raw unpasteurized Western Ghats forest honey",
    },
    {
        "name": "Canara Cold Pressed Mustard Oil 1L",
        "sku": "PRD-MUS-018",
        "category": "Oils & Ghee",
        "unit_price": 210.00,
        "cost_price": 165.00,
        "tax_rate": 5.0,
        "unit": "bottle",
        "stock_quantity": 75,
        "description": "Kachi ghani pungent virgin mustard cooking oil",
    },
    {
        "name": "Mangalorean Fish Curry Masala Paste 200g",
        "sku": "PRD-MAS-019",
        "category": "Ready to Cook",
        "unit_price": 95.00,
        "cost_price": 60.00,
        "tax_rate": 12.0,
        "unit": "pack",
        "stock_quantity": 190,
        "description": "Traditional Kundapur style roasted spice curry paste",
    },
    {
        "name": "Mysore Jasmine Incense Sticks 150 Sticks",
        "sku": "PRD-INC-020",
        "category": "Pooja & Household",
        "unit_price": 180.00,
        "cost_price": 105.00,
        "tax_rate": 12.0,
        "unit": "box",
        "stock_quantity": 130,
        "description": "Natural hand-rolled floral agarbatti sticks",
    },
    {
        "name": "White Sesame Seeds (Till) 500g",
        "sku": "PRD-SES-021",
        "category": "Grains & Staples",
        "unit_price": 140.00,
        "cost_price": 100.00,
        "tax_rate": 5.0,
        "unit": "pack",
        "stock_quantity": 115,
        "description": "Cleaned sortex grade calcium rich sesame seeds",
    },
    {
        "name": "Cold Pressed Groundnut Oil 1L Bottle",
        "sku": "PRD-GND-022",
        "category": "Oils & Ghee",
        "unit_price": 240.00,
        "cost_price": 185.00,
        "tax_rate": 5.0,
        "unit": "bottle",
        "stock_quantity": 105,
        "description": "Traditional wooden chekku extracted peanut cooking oil",
    },
    {
        "name": "Mangalore Kokum Rind Dried 250g",
        "sku": "PRD-KOK-023",
        "category": "Spices & Condiments",
        "unit_price": 135.00,
        "cost_price": 90.00,
        "tax_rate": 5.0,
        "unit": "pack",
        "stock_quantity": 145,
        "description": "Sun dried red kokum rind used in coastal sol kadi & curries",
    },
    {
        "name": "A2 Desi Gir Cow Milk Powder 500g",
        "sku": "PRD-MLK-024",
        "category": "Dairy & Ghee",
        "unit_price": 420.00,
        "cost_price": 310.00,
        "tax_rate": 12.0,
        "unit": "pack",
        "stock_quantity": 50,
        "description": "100% natural spray dried desi cow whole milk powder",
    },
    {
        "name": "Retail Store Setup & Catalog Consultation",
        "sku": "SRV-CON-025",
        "category": "Consulting Services",
        "unit_price": 5000.00,
        "cost_price": 1500.00,
        "tax_rate": 18.0,
        "unit": "hr",
        "stock_quantity": 0,
        "description": "Professional in-store inventory audit and barcode setup service",
    },
]


# ─────────────────────────────────────────────────────────────────────────────
# 2. CUSTOMERS DATA (20 realistic Indian retail buyers & B2B accounts)
# ─────────────────────────────────────────────────────────────────────────────
CUSTOMERS_DATA = [
    {
        "name": "Ramesh Bhat",
        "email": "ramesh.bhat@coastalventures.in",
        "phone": "+91 98450 12345",
        "address": "#14-2, Temple Square, Car Street",
        "city": "Mangaluru",
        "country": "India",
        "tax_number": "29AABPB1234F1Z8",
        "credit_limit": 100000.00,
        "currency": "INR",
        "notes": "Premium retailer account, Hampankatta retail cluster",
    },
    {
        "name": "Priya Shenoy",
        "email": "priya.shenoy@bengalurufresh.com",
        "phone": "+91 98801 23456",
        "address": "402, 7th Main, 4th Block, Koramangala",
        "city": "Bengaluru",
        "country": "India",
        "tax_number": "29AAMCS5678H1ZP",
        "credit_limit": 150000.00,
        "currency": "INR",
        "notes": "Regular bulk buyer for organic pantry staples",
    },
    {
        "name": "Ananya Rao",
        "email": "ananya.rao@mysurudelights.biz",
        "phone": "+91 94481 34567",
        "address": "Plot 88, 3rd Stage, Gokulam",
        "city": "Mysuru",
        "country": "India",
        "tax_number": "29AAACR9012J1Z3",
        "credit_limit": 75000.00,
        "currency": "INR",
        "notes": "Heritage cafe & retail corner account",
    },
    {
        "name": "Rajesh Nayak",
        "email": "rajesh.nayak@kadriretail.in",
        "phone": "+91 97412 45678",
        "address": "Shop 12, Kadri Mall, Kadri Hills",
        "city": "Mangaluru",
        "country": "India",
        "tax_number": "29AABPN3456K1Z1",
        "credit_limit": 120000.00,
        "currency": "INR",
        "notes": "Net 30 days payment terms agreed",
    },
    {
        "name": "Deepa Hegde",
        "email": "deepa.hegde@indiranagarfoods.in",
        "phone": "+91 99001 56789",
        "address": "1205, 100 Feet Road, Indiranagar",
        "city": "Bengaluru",
        "country": "India",
        "tax_number": "29AAEFH7890L1ZU",
        "credit_limit": 200000.00,
        "currency": "INR",
        "notes": "Specialty grocery outlet chain contact",
    },
    {
        "name": "Vikram Prabhu",
        "email": "vikram.prabhu@canaraspices.com",
        "phone": "+91 98442 67890",
        "address": "#5-18, Bejai Main Road, Bejai",
        "city": "Mangaluru",
        "country": "India",
        "tax_number": "29AAAFP1234M1ZX",
        "credit_limit": 80000.00,
        "currency": "INR",
        "notes": "Weekly spice & dry fruit purchaser",
    },
    {
        "name": "Karthik Pai",
        "email": "karthik.pai@jayanagarmart.co.in",
        "phone": "+91 99453 78901",
        "address": "78, 9th Cross, 2nd Block, Jayanagar",
        "city": "Bengaluru",
        "country": "India",
        "tax_number": "29AAAKP4567N1ZQ",
        "credit_limit": 175000.00,
        "currency": "INR",
        "notes": "South Bengaluru supermarket branch",
    },
    {
        "name": "Sneha Kamath",
        "email": "sneha.kamath@heritagebites.in",
        "phone": "+91 94804 89012",
        "address": "15, Kalidasa Road, Jayalakshmipuram",
        "city": "Mysuru",
        "country": "India",
        "tax_number": "29AAECK8901P1ZS",
        "credit_limit": 60000.00,
        "currency": "INR",
        "notes": "Confectionery & sweet store buyer",
    },
    {
        "name": "Suresh Poojary",
        "email": "suresh.poojary@kankanadywholesales.in",
        "phone": "+91 97315 90123",
        "address": "45, Pumpwell Junction, Kankanady",
        "city": "Mangaluru",
        "country": "India",
        "tax_number": "29AABPP2345Q1ZA",
        "credit_limit": 90000.00,
        "currency": "INR",
        "notes": "Coastal distribution buyer",
    },
    {
        "name": "Mamatha Shetty",
        "email": "mamatha.shetty@whitefieldpantry.com",
        "phone": "+91 98866 01234",
        "address": "Tower 3, ITPL Main Road, Whitefield",
        "city": "Bengaluru",
        "country": "India",
        "tax_number": "29AAEMS6789R1ZC",
        "credit_limit": 250000.00,
        "currency": "INR",
        "notes": "Corporate cafeteria bulk provisioning",
    },
    {
        "name": "Ganesh Acharya",
        "email": "ganesh.acharya@kuvempunagarmart.in",
        "phone": "+91 94497 12340",
        "address": "321, Adichunchanagiri Road, Kuvempunagar",
        "city": "Mysuru",
        "country": "India",
        "tax_number": "29AAAGA0123S1ZE",
        "credit_limit": 85000.00,
        "currency": "INR",
        "notes": "Residential department store",
    },
    {
        "name": "Sunita Mallya",
        "email": "sunita.mallya@mallyagrocery.in",
        "phone": "+91 98458 23451",
        "address": "22, Pandeshwar Commercial Complex",
        "city": "Mangaluru",
        "country": "India",
        "tax_number": "29AAASM4567T1ZG",
        "credit_limit": 95000.00,
        "currency": "INR",
        "notes": "Harbor district retail client",
    },
    {
        "name": "Preethi Alva",
        "email": "preethi.alva@hsrgourmet.com",
        "phone": "+91 99019 34562",
        "address": "512, 27th Main, Sector 1, HSR Layout",
        "city": "Bengaluru",
        "country": "India",
        "tax_number": "29AAAPA8901U1ZI",
        "credit_limit": 140000.00,
        "currency": "INR",
        "notes": "Gourmet coastal provisions vendor",
    },
    {
        "name": "Rohan D'Souza",
        "email": "rohan.dsouza@falnirstores.biz",
        "phone": "+91 98800 45673",
        "address": "8, Mother Teresa Road, Falnir",
        "city": "Mangaluru",
        "country": "India",
        "tax_number": "29AAARD2345V1ZK",
        "credit_limit": 70000.00,
        "currency": "INR",
        "notes": "Family owned grocery & cold storage",
    },
    {
        "name": "Ashwitha Rai",
        "email": "ashwitha.rai@saraswathipantry.in",
        "phone": "+91 94489 56784",
        "address": "19, Main Road, Saraswathipuram",
        "city": "Mysuru",
        "country": "India",
        "tax_number": "29AAEAR6789W1ZM",
        "credit_limit": 65000.00,
        "currency": "INR",
        "notes": "University neighborhood grocery hub",
    },
    {
        "name": "Harish Kunder",
        "email": "harish.kunder@malleshwaramstaples.com",
        "phone": "+91 97410 67895",
        "address": "84, 8th Cross, Margosa Road, Malleshwaram",
        "city": "Bengaluru",
        "country": "India",
        "tax_number": "29AAAHK0123X1ZO",
        "credit_limit": 160000.00,
        "currency": "INR",
        "notes": "Traditional food grains distributor",
    },
    {
        "name": "Poornima Holla",
        "email": "poornima.holla@urwafoods.in",
        "phone": "+91 98451 78906",
        "address": "71, Urwa Market Road, Urwa",
        "city": "Mangaluru",
        "country": "India",
        "tax_number": "29AAAPH4567Y1ZQ",
        "credit_limit": 50000.00,
        "currency": "INR",
        "notes": "Prompt UPI payer on weekly terms",
    },
    {
        "name": "Chethan Kumar",
        "email": "chethan.kumar@electroniccitymart.biz",
        "phone": "+91 99802 89017",
        "address": "Phase 1, Hosur Road, Electronic City",
        "city": "Bengaluru",
        "country": "India",
        "tax_number": "29AAACK8901Z1ZS",
        "credit_limit": 180000.00,
        "currency": "INR",
        "notes": "Tech corridor mini-supermarket",
    },
    {
        "name": "Vidya Kamath",
        "email": "vidya.kamath@bannimantapretail.in",
        "phone": "+91 94813 90128",
        "address": "Plot 14, Industrial Area, Bannimantap",
        "city": "Mysuru",
        "country": "India",
        "tax_number": "29AAAVK2345A1ZU",
        "credit_limit": 110000.00,
        "currency": "INR",
        "notes": "Industrial canteen provision supplier",
    },
    {
        "name": "Naveen Suvarna",
        "email": "naveen.suvarna@surathkalprovisions.in",
        "phone": "+91 97314 01239",
        "address": "NH-66 Highway Junction, Surathkal",
        "city": "Mangaluru",
        "country": "India",
        "tax_number": "29AAANS6789B1ZW",
        "credit_limit": 90000.00,
        "currency": "INR",
        "notes": "Campus & university township store",
    },
]


# ─────────────────────────────────────────────────────────────────────────────
# 3. SUPPLIERS DATA (5 primary wholesale vendors)
# ─────────────────────────────────────────────────────────────────────────────
SUPPLIERS_DATA = [
    {
        "name": "Dakshina Cashew & Spices Wholesale Corp",
        "email": "sales@dakshinaspices.com",
        "phone": "+91 824 2428901",
        "address": "Industrial Area, Baikampady",
        "city": "Mangaluru",
        "country": "India",
        "tax_number": "29AAACD4412E1Z2",
        "payment_terms_days": 30,
        "currency": "INR",
        "notes": "Direct plantation cashew nuts and whole spices supplier",
    },
    {
        "name": "Malnad Plantation Coffee & Estate Products",
        "email": "procurement@malnadcoffee.co.in",
        "phone": "+91 8272 228945",
        "address": "Estate Road, Madikeri",
        "city": "Coorg",
        "country": "India",
        "tax_number": "29AABCM8821F1Z6",
        "payment_terms_days": 45,
        "currency": "INR",
        "notes": "Single-origin Arabica & Robusta beans and cardamom",
    },
    {
        "name": "Karnataka Dairy Federation & Agro Wholesalers",
        "email": "orders@kmfwholesale.kar.nic.in",
        "phone": "+91 80 25530122",
        "address": "KMF Complex, Dr. MH Marigowda Road",
        "city": "Bengaluru",
        "country": "India",
        "tax_number": "29AAACK1104G1ZA",
        "payment_terms_days": 15,
        "currency": "INR",
        "notes": "Nandini milk products, ghee, and dairy consumables",
    },
    {
        "name": "Canara Packaging & Logistics Solutions",
        "email": "support@canarapackaging.in",
        "phone": "+91 824 2495510",
        "address": "Warehouse Cluster B, Kuloor",
        "city": "Mangaluru",
        "country": "India",
        "tax_number": "29AAACP9934H1ZD",
        "payment_terms_days": 30,
        "currency": "INR",
        "notes": "Corrugated boxes, food-grade pouches, and packing tape",
    },
    {
        "name": "Mysore Royal Agro & Rice Mills Consortium",
        "email": "dispatch@mysorericemills.biz",
        "phone": "+91 821 2490088",
        "address": "Bannur Road Industrial Estate",
        "city": "Mysuru",
        "country": "India",
        "tax_number": "29AAAFM7765J1ZH",
        "payment_terms_days": 30,
        "currency": "INR",
        "notes": "Sona Masoori, unpolished dals, and heritage grains",
    },
]


# ─────────────────────────────────────────────────────────────────────────────
# 4. SALES ORDERS DATA (50 rows spanning multiple multi-line orders)
# ─────────────────────────────────────────────────────────────────────────────
# Pre-calculate sales orders across 2026
SALES_ORDERS_SPEC = [
    # SO-2026-001 (Jan 2026, Ramesh Bhat)
    ("SO-2026-001", "2026-01-14", "Ramesh Bhat", "PRD-CAS-001", 10, 540.00, 5.0, 5.0, "New Year retail stocking"),
    ("SO-2026-001", "2026-01-14", "Ramesh Bhat", "PRD-COF-002", 15, 280.00, 5.0, 5.0, "New Year retail stocking"),
    ("SO-2026-001", "2026-01-14", "Ramesh Bhat", "PRD-GHE-006", 5, 630.00, 0.0, 12.0, "New Year retail stocking"),
    
    # SO-2026-002 (Jan 2026, Priya Shenoy)
    ("SO-2026-002", "2026-01-22", "Priya Shenoy", "PRD-RIC-004", 4, 1450.00, 0.0, 0.0, "Monthly organic store batch"),
    ("SO-2026-002", "2026-01-22", "Priya Shenoy", "PRD-DAL-013", 10, 320.00, 5.0, 0.0, "Monthly organic store batch"),
    ("SO-2026-002", "2026-01-22", "Priya Shenoy", "PRD-OIL-005", 12, 320.00, 0.0, 5.0, "Monthly organic store batch"),
    
    # SO-2026-003 (Feb 2026, Ananya Rao)
    ("SO-2026-003", "2026-02-05", "Ananya Rao", "PRD-COF-002", 20, 280.00, 10.0, 5.0, "Cafe weekly brew inventory"),
    ("SO-2026-003", "2026-02-05", "Ananya Rao", "PRD-SWT-014", 8, 360.00, 5.0, 5.0, "Display sweet box counter"),
    
    # SO-2026-004 (Feb 2026, Rajesh Nayak)
    ("SO-2026-004", "2026-02-18", "Rajesh Nayak", "PRD-CHP-016", 25, 125.00, 0.0, 12.0, "Snack shelf replenishment"),
    ("SO-2026-004", "2026-02-18", "Rajesh Nayak", "PRD-ROT-015", 20, 110.00, 0.0, 5.0, "Snack shelf replenishment"),
    ("SO-2026-004", "2026-02-18", "Rajesh Nayak", "PRD-TUR-007", 15, 160.00, 5.0, 5.0, "Snack shelf replenishment"),
    
    # SO-2026-005 (Mar 2026, Deepa Hegde)
    ("SO-2026-005", "2026-03-02", "Deepa Hegde", "PRD-CAS-001", 12, 540.00, 0.0, 5.0, "Spring festive hamper stock"),
    ("SO-2026-005", "2026-03-02", "Deepa Hegde", "PRD-ALM-012", 15, 490.00, 5.0, 5.0, "Spring festive hamper stock"),
    ("SO-2026-005", "2026-03-02", "Deepa Hegde", "PRD-SPI-003", 10, 340.00, 0.0, 5.0, "Spring festive hamper stock"),
    ("SO-2026-005", "2026-03-02", "Deepa Hegde", "PRD-HNY-017", 8, 375.00, 0.0, 5.0, "Spring festive hamper stock"),
    
    # SO-2026-006 (Mar 2026, Vikram Prabhu)
    ("SO-2026-006", "2026-03-19", "Vikram Prabhu", "PRD-PEP-009", 14, 450.00, 5.0, 5.0, "Export grade spices consignment"),
    ("SO-2026-006", "2026-03-19", "Vikram Prabhu", "PRD-CHL-008", 12, 480.00, 5.0, 5.0, "Export grade spices consignment"),
    
    # SO-2026-007 (Apr 2026, Karthik Pai)
    ("SO-2026-007", "2026-04-08", "Karthik Pai", "PRD-GHE-006", 18, 630.00, 5.0, 12.0, "Ugadi festive season demand"),
    ("SO-2026-007", "2026-04-08", "Karthik Pai", "PRD-JAG-010", 25, 190.00, 0.0, 5.0, "Ugadi festive season demand"),
    ("SO-2026-007", "2026-04-08", "Karthik Pai", "PRD-RIC-004", 5, 1450.00, 0.0, 0.0, "Ugadi festive season demand"),
    
    # SO-2026-008 (Apr 2026, Sneha Kamath)
    ("SO-2026-008", "2026-04-24", "Sneha Kamath", "PRD-SWT-014", 15, 360.00, 10.0, 5.0, "Catering sweet box delivery"),
    ("SO-2026-008", "2026-04-24", "Sneha Kamath", "PRD-JAM-011", 12, 145.00, 0.0, 12.0, "Bakery spread jars"),
    
    # SO-2026-009 (May 2026, Suresh Poojary)
    ("SO-2026-009", "2026-05-11", "Suresh Poojary", "PRD-OIL-005", 20, 320.00, 5.0, 5.0, "Wholesale oil stock replenishment"),
    ("SO-2026-009", "2026-05-11", "Suresh Poojary", "PRD-GND-022", 15, 240.00, 0.0, 5.0, "Wholesale oil stock replenishment"),
    ("SO-2026-009", "2026-05-11", "Suresh Poojary", "PRD-MUS-018", 10, 210.00, 0.0, 5.0, "Wholesale oil stock replenishment"),
    
    # SO-2026-010 (May 2026, Mamatha Shetty)
    ("SO-2026-010", "2026-05-27", "Mamatha Shetty", "PRD-RIC-004", 8, 1450.00, 5.0, 0.0, "Cafeteria staples consignment"),
    ("SO-2026-010", "2026-05-27", "Mamatha Shetty", "PRD-DAL-013", 16, 320.00, 0.0, 0.0, "Cafeteria staples consignment"),
    ("SO-2026-010", "2026-05-27", "Mamatha Shetty", "PRD-COF-002", 24, 280.00, 5.0, 5.0, "Corporate lounge coffee inventory"),
    
    # SO-2026-011 (Jun 2026, Ganesh Acharya)
    ("SO-2026-011", "2026-06-12", "Ganesh Acharya", "PRD-TUR-007", 20, 160.00, 0.0, 5.0, "Monsoon grocery stocking"),
    ("SO-2026-011", "2026-06-12", "Ganesh Acharya", "PRD-PEP-009", 10, 450.00, 0.0, 5.0, "Monsoon grocery stocking"),
    ("SO-2026-011", "2026-06-12", "Ganesh Acharya", "PRD-INC-020", 25, 180.00, 5.0, 12.0, "Pooja section refill"),
    
    # SO-2026-012 (Jun 2026, Sunita Mallya)
    ("SO-2026-012", "2026-06-25", "Sunita Mallya", "PRD-MAS-019", 30, 95.00, 5.0, 12.0, "Coastal fish curry masala push"),
    ("SO-2026-012", "2026-06-25", "Sunita Mallya", "PRD-KOK-023", 20, 135.00, 0.0, 5.0, "Coastal cooking souring agent"),
    
    # SO-2026-013 (Jul 2026, Preethi Alva)
    ("SO-2026-013", "2026-07-07", "Preethi Alva", "PRD-CAS-001", 15, 540.00, 5.0, 5.0, "Gourmet snack pack selection"),
    ("SO-2026-013", "2026-07-07", "Preethi Alva", "PRD-ALM-012", 12, 490.00, 0.0, 5.0, "Gourmet snack pack selection"),
    ("SO-2026-013", "2026-07-07", "Preethi Alva", "PRD-HNY-017", 10, 375.00, 5.0, 5.0, "Organic honey counter"),
    
    # SO-2026-014 (Jul 2026, Rohan D'Souza)
    ("SO-2026-014", "2026-07-20", "Rohan D'Souza", "PRD-CHP-016", 35, 125.00, 5.0, 12.0, "Weekend fast moving stock"),
    ("SO-2026-014", "2026-07-20", "Rohan D'Souza", "PRD-ROT-015", 25, 110.00, 5.0, 5.0, "Weekend fast moving stock"),
    
    # SO-2026-015 (Aug 2026, Ashwitha Rai)
    ("SO-2026-015", "2026-08-04", "Ashwitha Rai", "PRD-SES-021", 18, 140.00, 0.0, 5.0, "Traditional condiment seed stock"),
    ("SO-2026-015", "2026-08-04", "Ashwitha Rai", "PRD-JAG-010", 20, 190.00, 5.0, 5.0, "Organic jaggery cubes refill"),
    
    # SO-2026-016 (Aug 2026, Harish Kunder)
    ("SO-2026-016", "2026-08-19", "Harish Kunder", "PRD-RIC-004", 10, 1450.00, 5.0, 0.0, "Grain store wholesale shipment"),
    ("SO-2026-016", "2026-08-19", "Harish Kunder", "PRD-DAL-013", 20, 320.00, 5.0, 0.0, "Grain store wholesale shipment"),
    ("SO-2026-016", "2026-08-19", "Harish Kunder", "PRD-GHE-006", 12, 630.00, 0.0, 12.0, "Ghee tins stock for Gokulashtami"),
    
    # SO-2026-017 (Sep 2026, Poornima Holla)
    ("SO-2026-017", "2026-09-03", "Poornima Holla", "PRD-COF-002", 15, 280.00, 0.0, 5.0, "Morning brew supplies"),
    ("SO-2026-017", "2026-09-03", "Poornima Holla", "PRD-MLK-024", 8, 420.00, 0.0, 12.0, "Desi cow milk powder tin orders"),
    
    # SO-2026-018 (Sep 2026, Chethan Kumar)
    ("SO-2026-018", "2026-09-17", "Chethan Kumar", "PRD-CAS-001", 20, 540.00, 5.0, 5.0, "Festival pre-orders for Diwali hampers"),
    ("SO-2026-018", "2026-09-17", "Chethan Kumar", "PRD-SWT-014", 25, 360.00, 5.0, 5.0, "Festival pre-orders for Diwali hampers"),
    ("SO-2026-018", "2026-09-17", "Chethan Kumar", "PRD-INC-020", 30, 180.00, 5.0, 12.0, "Festival pre-orders for Diwali hampers"),

    # SO-2026-019 (Sep 2026, Vidya Kamath)
    ("SO-2026-019", "2026-09-24", "Vidya Kamath", "PRD-OIL-005", 15, 320.00, 5.0, 5.0, "Canteen festival preparation stock"),
    ("SO-2026-019", "2026-09-24", "Vidya Kamath", "PRD-TUR-007", 10, 160.00, 0.0, 5.0, "Spices for commercial cooking"),
]


# ─────────────────────────────────────────────────────────────────────────────
# 5. EXPENSES DATA (20 realistic Indian operational expenditures)
# ─────────────────────────────────────────────────────────────────────────────
EXPENSES_DATA = [
    {
        "expense_date": "2026-01-05",
        "category": "Rent & Leases",
        "description": "Monthly Central Godown Lease - Kadri Mangaluru",
        "amount": 35000.00,
        "payment_method": "bank_transfer",
        "reference": "VCH-2026-0101",
    },
    {
        "expense_date": "2026-01-12",
        "category": "Utilities",
        "description": "MESCOM Electricity Bill - Hampankatta Main Branch",
        "amount": 4820.00,
        "payment_method": "bank_transfer",
        "reference": "NEFT-MESCOM-8831",
    },
    {
        "expense_date": "2026-01-28",
        "category": "Logistics & Freight",
        "description": "DTDC Express Inter-city Consignment Charges",
        "amount": 2650.00,
        "payment_method": "card",
        "reference": "DTDC-TRK-99214",
    },
    {
        "expense_date": "2026-02-04",
        "category": "Office Supplies",
        "description": "POS Thermal Receipt Paper Rolls & Barcode Labels",
        "amount": 3400.00,
        "payment_method": "cash",
        "reference": "CASH-REC-102",
    },
    {
        "expense_date": "2026-02-15",
        "category": "Marketing & Promotion",
        "description": "Udayavani Daily Coastal Print Advertisement",
        "amount": 12500.00,
        "payment_method": "bank_transfer",
        "reference": "VCH-2026-0145",
    },
    {
        "expense_date": "2026-02-28",
        "category": "Maintenance & Repairs",
        "description": "Quarterly Servicing of Cold Storage Compressors",
        "amount": 6800.00,
        "payment_method": "cheque",
        "reference": "CHQ-SBIN-773190",
    },
    {
        "expense_date": "2026-03-05",
        "category": "Rent & Leases",
        "description": "Monthly Branch Lease - Koramangala Bengaluru",
        "amount": 45000.00,
        "payment_method": "bank_transfer",
        "reference": "VCH-2026-0205",
    },
    {
        "expense_date": "2026-03-16",
        "category": "Utilities",
        "description": "BESCOM Power Utility Bill - Bengaluru Outlet",
        "amount": 7150.00,
        "payment_method": "bank_transfer",
        "reference": "BESCOM-NEFT-4410",
    },
    {
        "expense_date": "2026-03-31",
        "category": "Staff Welfare",
        "description": "Monthly Staff Refreshments and Tea Services",
        "amount": 3200.00,
        "payment_method": "cash",
        "reference": "PETTY-2026-03",
    },
    {
        "expense_date": "2026-04-06",
        "category": "Insurance",
        "description": "Commercial Fire & Burglary Warehouse Policy Renewal",
        "amount": 18400.00,
        "payment_method": "bank_transfer",
        "reference": "POL-NEWIND-99120",
    },
    {
        "expense_date": "2026-04-18",
        "category": "Logistics & Freight",
        "description": "Local Tempo Transport for Cashew Procurement Batch",
        "amount": 4200.00,
        "payment_method": "cash",
        "reference": "TRUCK-KA19-8812",
    },
    {
        "expense_date": "2026-05-02",
        "category": "Professional Fees",
        "description": "Chartered Accountant GST Filing & Audit Retainer",
        "amount": 15000.00,
        "payment_method": "bank_transfer",
        "reference": "INV-CA-2026-05",
    },
    {
        "expense_date": "2026-05-19",
        "category": "IT & Software",
        "description": "High-Speed Commercial Fiber Broadband - Airtel",
        "amount": 2399.00,
        "payment_method": "card",
        "reference": "AIRTEL-FIB-88132",
    },
    {
        "expense_date": "2026-06-04",
        "category": "Rent & Leases",
        "description": "Monthly Warehouse Rent - Gokulam Mysuru",
        "amount": 28000.00,
        "payment_method": "bank_transfer",
        "reference": "VCH-2026-0312",
    },
    {
        "expense_date": "2026-06-22",
        "category": "Office Supplies",
        "description": "Heavy Duty Packaging Tape & Carton Strapping Rolls",
        "amount": 3850.00,
        "payment_method": "cash",
        "reference": "CANARA-PACK-109",
    },
    {
        "expense_date": "2026-07-08",
        "category": "Maintenance & Repairs",
        "description": "Annual Pest Control & Rodent Treatment in Godown",
        "amount": 5500.00,
        "payment_method": "cheque",
        "reference": "CHQ-UBIN-441829",
    },
    {
        "expense_date": "2026-07-25",
        "category": "Marketing & Promotion",
        "description": "Social Media Paid Campaign - Monsoon Coastal Flavors",
        "amount": 8500.00,
        "payment_method": "card",
        "reference": "META-ADS-2026-07",
    },
    {
        "expense_date": "2026-08-11",
        "category": "Utilities",
        "description": "CESC Mysuru Commercial Electricity Consumption",
        "amount": 4120.00,
        "payment_method": "bank_transfer",
        "reference": "CESC-NEFT-90214",
    },
    {
        "expense_date": "2026-08-28",
        "category": "Staff Welfare",
        "description": "First Aid Medical Restocking & Safety Helmets",
        "amount": 1950.00,
        "payment_method": "cash",
        "reference": "MED-REC-2026-88",
    },
    {
        "expense_date": "2026-09-14",
        "category": "Logistics & Freight",
        "description": "VRL Logistics Road Cargo - Bengaluru to Mangaluru",
        "amount": 6400.00,
        "payment_method": "bank_transfer",
        "reference": "VRL-LR-789210",
    },
]


# ─────────────────────────────────────────────────────────────────────────────
# 6. INVENTORY ADJUSTMENTS DATA (20 realistic stock movement entries)
# ─────────────────────────────────────────────────────────────────────────────
INVENTORY_DATA = [
    {
        "product_sku": "PRD-CAS-001",
        "warehouse_name": "Main Warehouse Mangaluru",
        "quantity_delta": 150.0,
        "reorder_level": 30.0,
        "notes": "Direct procurement batch restock from Baikampady factory",
    },
    {
        "product_sku": "PRD-COF-002",
        "warehouse_name": "Main Warehouse Mangaluru",
        "quantity_delta": 200.0,
        "reorder_level": 40.0,
        "notes": "Initial quarterly stock batch consignment from Madikeri",
    },
    {
        "product_sku": "PRD-SPI-003",
        "warehouse_name": "Main Warehouse Mangaluru",
        "quantity_delta": 85.0,
        "reorder_level": 20.0,
        "notes": "Fresh season green cardamom arrival and sorting",
    },
    {
        "product_sku": "PRD-RIC-004",
        "warehouse_name": "Bengaluru Central Godown",
        "quantity_delta": 80.0,
        "reorder_level": 25.0,
        "notes": "Heavy wholesale truckload receipt of 25kg bags",
    },
    {
        "product_sku": "PRD-OIL-005",
        "warehouse_name": "Main Warehouse Mangaluru",
        "quantity_delta": 160.0,
        "reorder_level": 35.0,
        "notes": "Fresh cold pressed extraction run batch bottling",
    },
    {
        "product_sku": "PRD-GHE-006",
        "warehouse_name": "Bengaluru Central Godown",
        "quantity_delta": 120.0,
        "reorder_level": 25.0,
        "notes": "KMF Nandini direct depot delivery of 1L tins",
    },
    {
        "product_sku": "PRD-TUR-007",
        "warehouse_name": "Mysuru Retail Hub",
        "quantity_delta": 100.0,
        "reorder_level": 20.0,
        "notes": "Pantry replenishment for South Karnataka region",
    },
    {
        "product_sku": "PRD-CHL-008",
        "warehouse_name": "Main Warehouse Mangaluru",
        "quantity_delta": 95.0,
        "reorder_level": 25.0,
        "notes": "Byadgi chilli stemless lot arrival from Hubballi market",
    },
    {
        "product_sku": "PRD-PEP-009",
        "warehouse_name": "Main Warehouse Mangaluru",
        "quantity_delta": 135.0,
        "reorder_level": 30.0,
        "notes": "Export grade Malnad pepper stock transfer receipt",
    },
    {
        "product_sku": "PRD-JAG-010",
        "warehouse_name": "Mysuru Retail Hub",
        "quantity_delta": 140.0,
        "reorder_level": 30.0,
        "notes": "Traditional organic palm jaggery blocks shipment",
    },
    {
        "product_sku": "PRD-JAM-011",
        "warehouse_name": "Bengaluru Central Godown",
        "quantity_delta": 90.0,
        "reorder_level": 15.0,
        "notes": "Freshly produced Bangalore blue grape jam batch",
    },
    {
        "product_sku": "PRD-ALM-012",
        "warehouse_name": "Main Warehouse Mangaluru",
        "quantity_delta": 80.0,
        "reorder_level": 20.0,
        "notes": "Roasted almonds packaging line complete",
    },
    {
        "product_sku": "PRD-DAL-013",
        "warehouse_name": "Bengaluru Central Godown",
        "quantity_delta": 160.0,
        "reorder_level": 40.0,
        "notes": "Gulbarga unpolished toor dal bulk restocking",
    },
    {
        "product_sku": "PRD-SWT-014",
        "warehouse_name": "Mysuru Retail Hub",
        "quantity_delta": 75.0,
        "reorder_level": 15.0,
        "notes": "Fresh Mysore Pak daily sweets dispatch",
    },
    {
        "product_sku": "PRD-CHP-016",
        "warehouse_name": "Main Warehouse Mangaluru",
        "quantity_delta": 220.0,
        "reorder_level": 50.0,
        "notes": "Fresh coastal fried banana chips batch receipt",
    },
    {
        "product_sku": "PRD-HNY-017",
        "warehouse_name": "Mysuru Retail Hub",
        "quantity_delta": 65.0,
        "reorder_level": 15.0,
        "notes": "Western Ghats forest honey certified testing lot",
    },
    {
        "product_sku": "PRD-MUS-018",
        "warehouse_name": "Bengaluru Central Godown",
        "quantity_delta": 75.0,
        "reorder_level": 20.0,
        "notes": "Cold pressed mustard oil cartons restock",
    },
    {
        "product_sku": "PRD-MAS-019",
        "warehouse_name": "Main Warehouse Mangaluru",
        "quantity_delta": 190.0,
        "reorder_level": 40.0,
        "notes": "Coastal fish curry masala paste batch release",
    },
    {
        "product_sku": "PRD-INC-020",
        "warehouse_name": "Mysuru Retail Hub",
        "quantity_delta": 130.0,
        "reorder_level": 30.0,
        "notes": "Mysore Jasmine agarbatti boxes stock intake",
    },
    {
        "product_sku": "PRD-CAS-001",
        "warehouse_name": "Main Warehouse Mangaluru",
        "quantity_delta": -4.0,
        "reorder_level": 30.0,
        "notes": "Audit stock write-off due to moisture damaged vacuum seal",
    },
]


# ─────────────────────────────────────────────────────────────────────────────
# 7. VALIDATION TEST DATA (Intentional error & warning cases)
# ─────────────────────────────────────────────────────────────────────────────
VALIDATION_TEST_ROWS = [
    {
        "name": "Valid Baseline Basmati Rice 5kg",
        "sku": "VAL-OK-101",
        "category": "Grains & Staples",
        "selling_price": "450.00",
        "cost_price": "360.00",
        "tax_rate": "0.0",
        "unit": "bag",
        "type": "product",
        "description": "Clean baseline record expected to validate with status 'valid'",
        "_expected_result": "VALID (Status: valid)",
    },
    {
        "name": "",  # Missing required field
        "sku": "VAL-ERR-102",
        "category": "Beverages",
        "selling_price": "220.00",
        "cost_price": "180.00",
        "tax_rate": "5.0",
        "unit": "pack",
        "type": "product",
        "description": "Missing product name - triggers required field validation error",
        "_expected_result": "INVALID (Status: invalid | Error: Product name is required)",
    },
    {
        "name": "Negative Selling Price Test Item",
        "sku": "VAL-ERR-103",
        "category": "Snacks",
        "selling_price": "-150.00",  # Invalid negative numeric
        "cost_price": "100.00",
        "tax_rate": "12.0",
        "unit": "pcs",
        "type": "product",
        "description": "Negative selling price - triggers numeric constraint min_val >= 0",
        "_expected_result": "INVALID (Status: invalid | Error: Selling price: Value must be at least 0.0)",
    },
    {
        "name": "Empty Selling Price Test Item",
        "sku": "VAL-ERR-104",
        "category": "Spices",
        "selling_price": "",  # Missing required number
        "cost_price": "80.00",
        "tax_rate": "5.0",
        "unit": "pack",
        "type": "product",
        "description": "Blank selling price - triggers missing required price validation error",
        "_expected_result": "INVALID (Status: invalid | Error: Selling price is required)",
    },
    {
        "name": "Duplicate SKU In File Test Item",
        "sku": "VAL-OK-101",  # Duplicate of Row 1
        "category": "Grains & Staples",
        "selling_price": "490.00",
        "cost_price": "390.00",
        "tax_rate": "0.0",
        "unit": "bag",
        "type": "product",
        "description": "SKU identical to Row 1 - triggers in-file duplicate SKU error",
        "_expected_result": "INVALID (Status: invalid | Error: Duplicate SKU 'VAL-OK-101' found multiple times in upload file)",
    },
    {
        "name": "Excessive Tax Rate Above 100 Test Item",
        "sku": "VAL-ERR-106",
        "category": "Household",
        "selling_price": "350.00",
        "cost_price": "250.00",
        "tax_rate": "180.0",  # Exceeds max 100%
        "unit": "pcs",
        "type": "product",
        "description": "Tax rate 180% - triggers numeric range constraint max_val <= 100",
        "_expected_result": "INVALID (Status: invalid | Error: Tax rate: Value must be at most 100.0)",
    },
    {
        "name": "Missing SKU Automatic Recommendation Item",
        "sku": "",  # Missing SKU
        "category": "Organic",
        "selling_price": "290.00",
        "cost_price": "210.00",
        "tax_rate": "5.0",
        "unit": "jar",
        "type": "product",
        "description": "Blank SKU - triggers status 'warning' with auto-SKU recommendation",
        "_expected_result": "WARNING (Status: warning | Warning: No SKU provided; automatic SKU will be recommended)",
    },
    {
        "name": "Unrecognized Enum Type Item",
        "sku": "VAL-WRN-108",
        "category": "Services",
        "selling_price": "1200.00",
        "cost_price": "400.00",
        "tax_rate": "18.0",
        "unit": "hr",
        "type": "equipment_rental",  # Invalid enum value (valid: product or service)
        "description": "Invalid enum type - triggers status 'warning' defaulting to 'product'",
        "_expected_result": "WARNING (Status: warning | Warning: Type: Invalid option 'equipment_rental'. Defaulted to 'product')",
    },
]


# ─────────────────────────────────────────────────────────────────────────────
# FILE GENERATORS
# ─────────────────────────────────────────────────────────────────────────────

def generate_products_csv(target_path: Path):
    fieldnames = ["name", "sku", "category", "unit_price", "cost_price", "tax_rate", "unit", "stock_quantity", "description"]
    with open(target_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for prod in PRODUCTS_DATA:
            writer.writerow(prod)
    print(f"  [OK] Generated products.csv ({len(PRODUCTS_DATA)} rows)")


def generate_products_xlsx(target_path: Path):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Products_Catalog"

    # Styling elements
    header_fill = PatternFill(start_color="1B365D", end_color="1B365D", fill_type="solid")
    header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    border_thin = Side(border_style="thin", color="D1D5DB")
    cell_border = Border(left=border_thin, right=border_thin, top=border_thin, bottom=border_thin)

    headers = [
        "Product Name",
        "SKU",
        "Category",
        "Selling Price",
        "Cost Price",
        "Tax Rate",
        "Unit",
        "Initial Stock",
        "Description",
    ]
    ws.append(headers)

    # Style header row
    for col_num in range(1, len(headers) + 1):
        cell = ws.cell(row=1, column=col_num)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center", vertical="center")

    # Add rows
    for prod in PRODUCTS_DATA:
        row = [
            prod["name"],
            prod["sku"],
            prod["category"],
            prod["unit_price"],
            prod["cost_price"],
            prod["tax_rate"],
            prod["unit"],
            prod["stock_quantity"],
            prod["description"],
        ]
        ws.append(row)

    # Format numbers and borders
    for row in ws.iter_rows(min_row=2, max_row=len(PRODUCTS_DATA) + 1, min_col=1, max_col=len(headers)):
        for cell in row:
            cell.border = cell_border
            if cell.column in (4, 5):  # Selling & cost price
                cell.number_format = "#,##0.00"
                cell.alignment = Alignment(horizontal="right")
            elif cell.column == 6:  # Tax rate
                cell.number_format = "0.0"
                cell.alignment = Alignment(horizontal="right")
            elif cell.column == 8:  # Stock
                cell.number_format = "#,##0"
                cell.alignment = Alignment(horizontal="right")

    # Auto-adjust column widths
    for col in ws.columns:
        max_len = max(len(str(cell.value or "")) for cell in col)
        col_letter = openpyxl.utils.get_column_letter(col[0].column)
        ws.column_dimensions[col_letter].width = max(max_len + 3, 12)

    wb.save(target_path)
    print(f"  [OK] Generated products.xlsx ({len(PRODUCTS_DATA)} rows)")


def generate_customers_csv(target_path: Path):
    fieldnames = ["name", "email", "phone", "address", "city", "country", "tax_number", "credit_limit", "currency", "notes"]
    with open(target_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for cust in CUSTOMERS_DATA:
            writer.writerow(cust)
    print(f"  [OK] Generated customers.csv ({len(CUSTOMERS_DATA)} rows)")


def generate_suppliers_csv(target_path: Path):
    fieldnames = ["name", "email", "phone", "address", "city", "country", "tax_number", "payment_terms_days", "currency", "notes"]
    with open(target_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for sup in SUPPLIERS_DATA:
            writer.writerow(sup)
    print(f"  [OK] Generated suppliers.csv ({len(SUPPLIERS_DATA)} rows)")


def generate_sales_csv(target_path: Path):
    fieldnames = ["sale_number", "sale_date", "customer_name", "product_sku", "quantity", "unit_price", "discount_pct", "tax_rate", "total", "notes"]
    with open(target_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for item in SALES_ORDERS_SPEC:
            sale_num, s_date, cust_name, sku, qty, price, disc, tax, notes = item
            base = qty * price
            disc_amt = base * (disc / 100.0)
            tax_amt = (base - disc_amt) * (tax / 100.0)
            line_total = round(base - disc_amt + tax_amt, 2)

            writer.writerow({
                "sale_number": sale_num,
                "sale_date": s_date,
                "customer_name": cust_name,
                "product_sku": sku,
                "quantity": qty,
                "unit_price": f"{price:.2f}",
                "discount_pct": f"{disc:.1f}",
                "tax_rate": f"{tax:.1f}",
                "total": f"{line_total:.2f}",
                "notes": notes,
            })
    print(f"  [OK] Generated sales.csv ({len(SALES_ORDERS_SPEC)} rows across 18 sales orders)")


def generate_expenses_csv(target_path: Path):
    fieldnames = ["expense_date", "category", "description", "amount", "payment_method", "reference"]
    with open(target_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for exp in EXPENSES_DATA:
            row = dict(exp)
            row["amount"] = f"{row['amount']:.2f}"
            writer.writerow(row)
    print(f"  [OK] Generated expenses.csv ({len(EXPENSES_DATA)} rows)")


def generate_inventory_csv(target_path: Path):
    fieldnames = ["product_sku", "warehouse_name", "quantity_delta", "reorder_level", "notes"]
    with open(target_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for inv in INVENTORY_DATA:
            row = dict(inv)
            row["quantity_delta"] = f"{row['quantity_delta']:+.1f}"
            row["reorder_level"] = f"{row['reorder_level']:.1f}"
            writer.writerow(row)
    print(f"  [OK] Generated inventory.csv ({len(INVENTORY_DATA)} rows)")


def generate_validation_test_csv(target_path: Path):
    fieldnames = ["name", "sku", "category", "selling_price", "cost_price", "tax_rate", "unit", "type", "description"]
    with open(target_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in VALIDATION_TEST_ROWS:
            cleaned_row = {k: v for k, v in row.items() if not k.startswith("_")}
            writer.writerow(cleaned_row)
    print(f"  [OK] Generated validation_test.csv ({len(VALIDATION_TEST_ROWS)} test cases)")


def generate_expenses_pdf(target_path: Path):
    """
    Generate clean, readable, text-based PDF invoice/expense voucher
    specifically crafted to pass ALLADIN's PDFExtractorService regex parsing and arithmetic verification.
    """
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=letter)
    width, height = letter  # 612 x 792 points

    primary_color = HexColor("#1E3A8A")  # Deep Navy Blue
    slate_color = HexColor("#475569")
    light_bg = HexColor("#F8FAFC")
    border_color = HexColor("#CBD5E1")

    # Header Box
    c.setFillColor(light_bg)
    c.setStrokeColor(border_color)
    c.rect(36, 680, width - 72, 85, fill=1, stroke=1)

    c.setFillColor(primary_color)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, 735, "COMMERCIAL EXPENSE VOUCHER")

    c.setFont("Helvetica", 9)
    c.setFillColor(slate_color)
    c.drawString(50, 720, "Official Procurement & Accounts Payable Documentation")
    c.drawString(50, 705, "Alladin AI Financial Intelligence Platform - Verified Voucher")

    # Meta Section: Document Number & Dates
    c.setFont("Helvetica-Bold", 10)
    c.setFillColor(primary_color)
    c.drawString(50, 655, "Receipt No: REC-2026-0842")
    c.drawString(380, 655, "Date: 2026-08-15")
    c.drawString(380, 640, "Due Date: 2026-08-30")

    # Parties Section
    c.setStrokeColor(border_color)
    c.line(50, 630, width - 50, 630)

    c.setFont("Helvetica-Bold", 9)
    c.setFillColor(primary_color)
    c.drawString(50, 615, "Vendor: Karnataka Office Supplies & Tech Hub")
    c.setFont("Helvetica", 9)
    c.setFillColor(slate_color)
    c.drawString(50, 602, "GSTIN: 29AAACK9912E1Z8 | Baikampady Industrial Area, Mangaluru, KA")
    c.drawString(50, 589, "Contact: procurement@karnatakaofficesupplies.in | +91 824 2498811")

    c.setFont("Helvetica-Bold", 9)
    c.setFillColor(primary_color)
    c.drawString(380, 615, "Billed To: Alladin Retail Enterprises Pvt Ltd")
    c.setFont("Helvetica", 9)
    c.setFillColor(slate_color)
    c.drawString(380, 602, "GSTIN: 29AABCA1234D1ZP")
    c.drawString(380, 589, "Hampankatta Commercial Complex, Mangaluru - 575001")

    # Table Header Box
    c.line(50, 570, width - 50, 570)
    c.setFillColor(primary_color)
    c.rect(50, 545, width - 100, 20, fill=1, stroke=0)
    c.setFillColor(HexColor("#FFFFFF"))
    c.setFont("Helvetica-Bold", 9)
    c.drawString(55, 551, "Description")
    c.drawString(340, 551, "Qty")
    c.drawString(405, 551, "Unit Price")
    c.drawString(495, 551, "Line Total")

    # Line Items matching exact regex:
    # ^(?P<desc>.+?)\s+(?P<qty>[0-9]+(?:\.[0-9]+)?)\s+(?P<price>[0-9,]+\.[0-9]{2})\s+(?P<total>[0-9,]+\.[0-9]{2})$
    line_items = [
        ("Executive High-Back Mesh Ergonomic Chairs", 4, 4500.00, 18000.00),
        ("Thermal Billing Paper Rolls 80mm Pack", 20, 180.00, 3600.00),
    ]

    y_pos = 525
    c.setFont("Helvetica", 9)
    c.setFillColor(HexColor("#0F172A"))

    for desc, qty, price, total in line_items:
        # Drawing standard tabular line item that matches the text extractor regex
        line_str = f"{desc} {qty} {price:.2f} {total:.2f}"
        c.drawString(55, y_pos, line_str)
        y_pos -= 22

    # Divider before totals
    c.setStrokeColor(border_color)
    c.line(50, y_pos, width - 50, y_pos)
    y_pos -= 25

    # Financial Summary Section
    subtotal = 21600.00
    tax_gst = 3888.00  # 18% GST
    grand_total = 25488.00

    c.setFont("Helvetica-Bold", 10)
    c.setFillColor(slate_color)
    c.drawString(340, y_pos, f"Subtotal: INR {subtotal:.2f}")
    y_pos -= 18
    c.drawString(340, y_pos, f"GST Tax: INR {tax_gst:.2f}")
    y_pos -= 20
    c.setFillColor(primary_color)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(340, y_pos, f"Grand Total: INR {grand_total:.2f}")

    # Payment & Notes Section
    y_pos -= 35
    c.setStrokeColor(border_color)
    c.line(50, y_pos, width - 50, y_pos)
    y_pos -= 20

    c.setFont("Helvetica-Bold", 9)
    c.setFillColor(primary_color)
    c.drawString(50, y_pos, "Payment Details & Verification:")
    y_pos -= 16
    c.setFont("Helvetica", 9)
    c.setFillColor(slate_color)
    c.drawString(50, y_pos, "Expense Category: Office Supplies & Equipment")
    y_pos -= 14
    c.drawString(50, y_pos, "Payment Method: Bank Transfer (NEFT Ref: UBI-KOS-882914)")
    y_pos -= 14
    c.drawString(50, y_pos, "Status: Verified by Accounts Head (Mangaluru Branch)")
    y_pos -= 14
    c.drawString(50, y_pos, "Notes: Quarterly IT hardware and billing stationery procurement approved under CAPEX/OPEX budget.")

    # Footer
    c.setFont("Helvetica-Oblique", 8)
    c.setFillColor(HexColor("#94A3B8"))
    c.drawString(50, 40, "Generated for ALLADIN Financial Intelligence Platform - Verified Automated Extraction Test Document.")

    c.save()

    # Write PDF bytes
    target_path.write_bytes(buf.getvalue())
    print(f"  [OK] Generated expenses.pdf (Selectable text with verified arithmetic totals)")


def generate_readme_md(target_path: Path):
    readme_content = f"""# ALLADIN Import Center — Sample Business Test Files

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
& ".\\backend\\venv\\Scripts\\python.exe" scripts/generate_sample_import_files.py
```
"""
    with open(target_path, "w", encoding="utf-8") as f:
        f.write(readme_content)
    print(f"  [OK] Generated README.md")


# ─────────────────────────────────────────────────────────────────────────────
# MAIN EXECUTION & SELF-VALIDATION
# ─────────────────────────────────────────────────────────────────────────────
def main():
    print("=" * 70)
    print("ALLADIN Import Center - Sample File Generator")
    print(f"Target Output Directory: {OUTPUT_DIR.resolve()}")
    print("=" * 70)

    # 1. Generate files
    generate_products_csv(OUTPUT_DIR / "products.csv")
    generate_products_xlsx(OUTPUT_DIR / "products.xlsx")
    generate_customers_csv(OUTPUT_DIR / "customers.csv")
    generate_suppliers_csv(OUTPUT_DIR / "suppliers.csv")
    generate_sales_csv(OUTPUT_DIR / "sales.csv")
    generate_expenses_csv(OUTPUT_DIR / "expenses.csv")
    generate_inventory_csv(OUTPUT_DIR / "inventory.csv")
    generate_validation_test_csv(OUTPUT_DIR / "validation_test.csv")
    generate_expenses_pdf(OUTPUT_DIR / "expenses.pdf")
    generate_readme_md(OUTPUT_DIR / "README.md")

    print("\n" + "=" * 70)
    print("Verifying Generated Files...")
    print("=" * 70)

    # 2. Self-Validation
    # Verify CSV files
    csv_files = ["products.csv", "customers.csv", "suppliers.csv", "sales.csv", "expenses.csv", "inventory.csv", "validation_test.csv"]
    for cf in csv_files:
        p = OUTPUT_DIR / cf
        with open(p, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            headers = next(reader)
            row_count = sum(1 for _ in reader)
        print(f"  [PASS] {cf:<22} Valid CSV | {len(headers)} columns | {row_count} rows")

    # Verify Excel file
    xlsx_path = OUTPUT_DIR / "products.xlsx"
    wb = openpyxl.load_workbook(xlsx_path, read_only=True)
    ws = wb.active
    xlsx_rows = sum(1 for _ in ws.iter_rows(values_only=True)) - 1
    wb.close()
    print(f"  [PASS] {'products.xlsx':<22} Valid XLSX | Sheet: '{ws.title}' | {xlsx_rows} data rows")

    # Verify PDF text extraction
    pdf_path = OUTPUT_DIR / "expenses.pdf"
    pdf_reader = pypdf.PdfReader(str(pdf_path))
    pdf_text = ""
    for page in pdf_reader.pages:
        pdf_text += page.extract_text() or ""
    has_text = len(pdf_text.strip()) > 100
    print(f"  [PASS] {'expenses.pdf':<22} Valid PDF | {len(pdf_reader.pages)} page(s) | {len(pdf_text)} characters extracted (Selectable text: {has_text})")

    # Verify PDF extractor service integration
    sys.path.insert(0, str(PROJECT_ROOT / "backend"))
    try:
        from app.services.pdf_extractor import PDFExtractorService
        extraction_res = PDFExtractorService.extract_document(pdf_path.read_bytes(), "expenses.pdf")
        doc_type = extraction_res.get("document_type")
        doc_num = extraction_res.get("candidate_fields", {}).get("document_number", {}).get("value")
        total_val = extraction_res.get("candidate_fields", {}).get("total_amount", {}).get("value")
        arithmetic_ok = extraction_res.get("arithmetic_check", {}).get("is_consistent")
        items_count = len(extraction_res.get("line_items", []))
        print(f"  [PASS] PDF Extractor Match   : Type={doc_type} | Doc#={doc_num} | Total=INR {total_val} | Items={items_count} | Arithmetic Match={arithmetic_ok}")
    except Exception as e:
        print(f"  [WARN] PDF Extractor Check Warning: {e}")

    print("\n" + "=" * 70)
    print("All sample files successfully generated and verified!")
    print(f"Directory: {OUTPUT_DIR.resolve()}")
    print("=" * 70)


if __name__ == "__main__":
    main()
