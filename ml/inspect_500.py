import pandas as pd

df = pd.read_csv('C:/Users/soory/Downloads/SUPER MARKET DATA - supermarket_sales_500_rows.csv')
print("=== Columns ===")
print(list(df.columns))

print("\n=== Date Range ===")
print("Min Date:", df['Date'].min())
print("Max Date:", df['Date'].max())

print("\n=== Branches and Cities ===")
print(df[['Branch', 'City']].drop_duplicates())

print("\n=== Customer Types ===")
print(df['Customer Type'].value_counts())

print("\n=== Payment Methods ===")
print(df['Payment'].value_counts())

print("\n=== Categories and Products ===")
for cat, grp in df.groupby('Category'):
    print(f"\nCategory: {cat} (Total rows: {len(grp)})")
    prods = grp.groupby('Product').agg(
        count=('Invoice ID', 'count'),
        min_p=('Unit Price', 'min'),
        max_p=('Unit Price', 'max'),
        mean_p=('Unit Price', 'mean'),
        min_qty=('Quantity', 'min'),
        max_qty=('Quantity', 'max'),
        total_sales=('Sales', 'sum')
    )
    print(prods)
