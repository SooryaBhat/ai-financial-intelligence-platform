"""
fix_nb03_mape.py
================
Fix MAPE dictionary key and Unicode checkmark in 03_revenue_forecasting.ipynb.
"""
import json
from pathlib import Path

nb_path = Path(r'c:\Users\soory\OneDrive\Documents\Ai_financial_intelligence_platform\ai-financial-intelligence-platform\ml\notebooks\03_revenue_forecasting.ipynb')

nb = json.load(open(nb_path, encoding='utf-8'))

for cell in nb['cells']:
    if cell['cell_type'] == 'code':
        src = ''.join(cell['source'])

        # Fix Cell 11 eval_metrics return dictionary
        if 'def eval_metrics(y_true, y_pred, model_name):' in src:
            src = src.replace("'MAPE_%'", "'MAPE'")

        # Fix Cell 13 results_df sorting and checkmark print
        if "results_df = pd.DataFrame(results).sort_values('MAPE_%')" in src:
            src = src.replace("results_df = pd.DataFrame(results).sort_values('MAPE_%')", "results_df = pd.DataFrame(results).sort_values('MAPE')")
        
        if r"\u2713" in src or "✓" in src:
            src = src.replace("✓", "[Best]").replace(r"\u2713", "[Best]")

        lines = src.split('\n')
        cell['source'] = [l + '\n' for l in lines[:-1]] + ([lines[-1]] if lines[-1] else [])

with open(nb_path, 'w', encoding='utf-8') as f:
    json.dump(nb, f, ensure_ascii=False, indent=1)

print("NB03 MAPE key & Unicode checkmark fixed.")
