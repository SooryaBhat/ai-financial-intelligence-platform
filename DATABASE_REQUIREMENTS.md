# Database Requirements

Use PostgreSQL.

Target database: Supabase.

Requirements:

- Multi-tenant SaaS architecture.
- Every company has completely isolated data.
- Support multiple users per company.
- Support multiple branches in the future.
- Use UUID primary keys.
- Use foreign keys.
- Use indexes where appropriate.
- Use created_at and updated_at timestamps.
- Use soft delete where appropriate.
- Use normalized database design.
- Avoid duplicate data.
- Design for scalability.

The platform should support:

Platform
---------
Companies
Subscriptions
Plans
Users
Roles
Permissions

Business
---------
Customers
Suppliers
Products
Categories
Inventory
Warehouses
Stock Movements
Sales
Sale Items
Purchases
Purchase Items
Invoices
Payments
Expenses
Expense Categories

AI
---------
ML Models
Predictions
Prediction Logs
Chat Sessions
Chat Messages
Reports

System
---------
Notifications
Audit Logs
Activity Logs
Settings
Integrations

Future integrations:

- CSV
- Excel
- Odoo
- ERPNext
- Zoho
- QuickBooks
- Bank APIs

Do NOT create duplicate tables.

Design a production-quality schema.

Think like a senior backend architect.