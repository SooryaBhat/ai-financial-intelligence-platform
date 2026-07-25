"""Helper to dump all notebook code cells to text files for inspection."""
import json, os, sys

notebooks_dir = r'c:\Users\soory\OneDrive\Documents\Ai_financial_intelligence_platform\ai-financial-intelligence-platform\ml\notebooks'
out_dir = r'c:\Users\soory\OneDrive\Documents\Ai_financial_intelligence_platform\ai-financial-intelligence-platform\ml\nb_dumps'
os.makedirs(out_dir, exist_ok=True)

for nb_file in sorted(os.listdir(notebooks_dir)):
    if not nb_file.endswith('.ipynb'):
        continue
    path = os.path.join(notebooks_dir, nb_file)
    nb = json.load(open(path, encoding='utf-8'))
    out_path = os.path.join(out_dir, nb_file.replace('.ipynb', '.txt'))
    with open(out_path, 'w', encoding='utf-8') as fout:
        for i, c in enumerate(nb['cells']):
            src = ''.join(c['source'])
            fout.write(f'\n{"="*60}\n')
            fout.write(f'Cell {i} ({c["cell_type"]})\n')
            fout.write(f'{"="*60}\n')
            fout.write(src + '\n')
    print(f'Dumped: {nb_file}')

print('Done.')
