"""
inspect_nb03_head.py
====================
Dump head cells (0 to 10) of 03_revenue_forecasting.ipynb.
"""
import json
import sys
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

nb_path = Path(r'c:\Users\soory\OneDrive\Documents\Ai_financial_intelligence_platform\ai-financial-intelligence-platform\ml\notebooks\03_revenue_forecasting.ipynb')

nb = json.load(open(nb_path, encoding='utf-8'))

for i in range(11):
    cell = nb['cells'][i]
    cell_type = cell['cell_type']
    source = ''.join(cell['source'])
    print(f"=" * 60)
    print(f"CELL {i} ({cell_type})")
    print("=" * 60)
    print(source)
    print()
