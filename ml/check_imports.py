"""Check if any notebook imports from scripts/."""
import json
from pathlib import Path

nb_dir = Path(r'c:\Users\soory\OneDrive\Documents\Ai_financial_intelligence_platform\ai-financial-intelligence-platform\ml\notebooks')

for nb_file in sorted(nb_dir.glob('*.ipynb')):
    nb = json.load(open(nb_file, encoding='utf-8'))
    for cell in nb['cells']:
        if cell['cell_type'] == 'code':
            src = ''.join(cell['source'])
            if 'from scripts' in src or 'import scripts' in src or 'sys.path' in src:
                print(f"{nb_file.name}: imports scripts")
                break
    else:
        pass

print("Done checking script imports.")
