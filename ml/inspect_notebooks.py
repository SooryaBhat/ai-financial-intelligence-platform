import json, os, sys

# Force UTF-8 output
sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', buffering=1)

notebooks_dir = r'c:\Users\soory\OneDrive\Documents\Ai_financial_intelligence_platform\ai-financial-intelligence-platform\ml\notebooks'

for nb_file in sorted(os.listdir(notebooks_dir)):
    if not nb_file.endswith('.ipynb'):
        continue
    path = os.path.join(notebooks_dir, nb_file)
    nb = json.load(open(path, encoding='utf-8'))
    print(f'\n{"="*60}')
    print(f'NOTEBOOK: {nb_file}')
    print(f'{"="*60}')
    for i, c in enumerate(nb['cells']):
        src = ''.join(c['source'])
        cell_type = c['cell_type']
        print(f'\n--- Cell {i} ({cell_type}) ---')
        print(src[:500].encode('ascii', errors='replace').decode('ascii'))
