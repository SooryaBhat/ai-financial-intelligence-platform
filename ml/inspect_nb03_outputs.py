"""
inspect_nb03_outputs.py
=======================
Print all cell text and output of 03_revenue_forecasting.ipynb after execution.
"""
import json
import sys
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

nb_path = Path(r'c:\Users\soory\OneDrive\Documents\Ai_financial_intelligence_platform\ai-financial-intelligence-platform\ml\notebooks\03_revenue_forecasting.ipynb')

nb = json.load(open(nb_path, encoding='utf-8'))

for i, cell in enumerate(nb['cells']):
    if cell['cell_type'] == 'code':
        print(f"=== CELL {i} OUTPUT ===")
        for out in cell.get('outputs', []):
            if out.get('output_type') == 'stream':
                print(''.join(out.get('text', [])))
            elif out.get('output_type') in ['execute_result', 'display_data']:
                data = out.get('data', {})
                if 'text/plain' in data:
                    print(''.join(data['text/plain']))
            elif out.get('output_type') == 'error':
                print(f"ERROR: {out.get('ename')}: {out.get('evalue')}")
