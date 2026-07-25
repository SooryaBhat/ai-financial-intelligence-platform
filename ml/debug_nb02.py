"""Check NB02 actual gross_amount code usage."""
import json
from pathlib import Path
nb = json.load(open(Path(r'c:\Users\soory\OneDrive\Documents\Ai_financial_intelligence_platform\ai-financial-intelligence-platform\ml\notebooks\02_data_preprocessing.ipynb'), encoding='utf-8'))
for i, c in enumerate(nb['cells']):
    if c['cell_type'] == 'code':
        src = ''.join(c['source'])
        if 'gross_amount' in src:
            for line in src.split('\n'):
                if 'gross_amount' in line:
                    safe = line.encode('ascii', errors='replace').decode()
                    print(f"Cell {i}: {safe}")
            # Check if it's code or comment
            code_lines = [l for l in src.split('\n') if 'gross_amount' in l and not l.strip().startswith('#')]
            if code_lines:
                print(f"  -> CODE (not comment): {code_lines[0].encode('ascii', errors='replace').decode()}")
            else:
                print(f"  -> Only in comments/strings - OK")
