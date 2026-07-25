"""Inspect drops in NB01."""
json_path = r'c:\Users\soory\OneDrive\Documents\Ai_financial_intelligence_platform\ai-financial-intelligence-platform\ml\notebooks\01_data_exploration.ipynb'
import json

nb = json.load(open(json_path, encoding='utf-8'))
for i, cell in enumerate(nb['cells']):
    if cell['cell_type'] == 'code':
        src = ''.join(cell['source'])
        if 'drop' in src:
            print(f"Cell {i}:")
            for line in src.split('\n'):
                if 'drop' in line:
                    print("  ", line)
