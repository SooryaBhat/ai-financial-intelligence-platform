"""
fix_nb01_cell11.py
==================
Fix Cell 11 in 01_data_exploration.ipynb where drop(columns=['id']) fails due to id_x/id_y suffixes.
"""
import json
from pathlib import Path

nb_path = Path(r'c:\Users\soory\OneDrive\Documents\Ai_financial_intelligence_platform\ai-financial-intelligence-platform\ml\notebooks\01_data_exploration.ipynb')

nb = json.load(open(nb_path, encoding='utf-8'))
for cell in nb['cells']:
    if cell['cell_type'] == 'code':
        src = ''.join(cell['source'])
        if "items_full.drop(columns=['id'])" in src:
            src = src.replace("items_full.drop(columns=['id'])", "items_full.drop(columns=['id', 'id_x', 'id_y'], errors='ignore')")
            lines = src.split('\n')
            cell['source'] = [l + '\n' for l in lines[:-1]] + ([lines[-1]] if lines[-1] else [])

with open(nb_path, 'w', encoding='utf-8') as f:
    json.dump(nb, f, ensure_ascii=False, indent=1)

print("NB01 Cell 11 fixed.")
