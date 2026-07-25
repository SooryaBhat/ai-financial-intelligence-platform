"""
verify_nb03_code.py
===================
Inspect Cell 1, Cell 11, and Cell 13 code in 03_revenue_forecasting.ipynb with UTF-8 encoding.
"""
import json
import sys
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

nb_path = Path(r'c:\Users\soory\OneDrive\Documents\Ai_financial_intelligence_platform\ai-financial-intelligence-platform\ml\notebooks\03_revenue_forecasting.ipynb')

nb = json.load(open(nb_path, encoding='utf-8'))

print("=== CELL 1 ===")
print(''.join(nb['cells'][1]['source']))

print("=== CELL 11 ===")
print(''.join(nb['cells'][11]['source']))

print("=== CELL 13 ===")
print(''.join(nb['cells'][13]['source']))
